"""Strict linear SVG subset and source-relative FracPaQ TXT conversion.

No browser rendering, curve approximation, transform application or CSS engine.
Unsupported geometry rejects the whole input before any file replacement.
"""

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import tempfile

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from pyfracpaq.domain import Dataset, InputMode, TraceInput, build_dataset
from pyfracpaq.geometry import GeometryError
from pyfracpaq.io.colours import hex_rgb, normalise_hex

LOG = logging.getLogger(__name__)
NUMBER = r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'
TOKEN = re.compile(NUMBER + r'|[A-Za-z]')
SVG_NAMESPACE = 'http://www.w3.org/2000/svg'
MAX_SVG_BYTES = 32 * 1024 * 1024
KINDS = ('path', 'polyline', 'line')


class SvgInputError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SvgElement:
    kind: str
    index: int
    identifier: str
    colour_hex: str
    points: tuple[tuple[float, float], ...]


@dataclass(frozen=True, slots=True)
class ConvertedTable:
    path: Path
    content: str
    colour_hex: str
    elements: tuple[SvgElement, ...]


@dataclass(frozen=True, slots=True)
class SvgImport:
    dataset: Dataset
    tables: tuple[ConvertedTable, ...]


def _tokens(text: str, *, commands: bool = False) -> list[str]:
    tokens, end = [], 0
    for match in TOKEN.finditer(text):
        separator = text[end:match.start()]
        if separator.strip(' \t\r\n,') or separator.count(',') > 1:
            raise SvgInputError('Invalid SVG numeric separators.')
        token = match[0]
        if ',' in separator and (not tokens or re.fullmatch(NUMBER, token) is None):
            raise SvgInputError('Unexpected comma in SVG coordinates.')
        if not commands and re.fullmatch(NUMBER, token) is None:
            raise SvgInputError(f'Unsupported token in SVG coordinates: {token!r}.')
        tokens.append(token)
        end = match.end()
    if text[end:].strip(' \t\r\n'):
        raise SvgInputError('Invalid SVG coordinate text.')
    return tokens


def _points(tokens: list[str]) -> tuple[tuple[float, float], ...]:
    if len(tokens) < 4 or len(tokens) % 2:
        raise SvgInputError('A trace must contain at least two complete X/Y pairs.')
    try:
        values = [float(t) for t in tokens]
        record = TraceInput(tuple(zip(values[::2], values[1::2])))
    except (ValueError, OverflowError) as error:
        raise SvgInputError(f'Invalid SVG coordinates: {error}') from error
    return record.points


def _path(text: str) -> tuple[tuple[float, float], ...]:
    tokens = _tokens(text, commands=True)
    if not tokens or tokens[0] != 'M':
        raise SvgInputError('SVG paths must start with an absolute M command.')
    numbers = []
    for index, token in enumerate(tokens[1:], 1):
        if re.fullmatch(NUMBER, token):
            numbers.append(token)
        elif token == 'L':
            if len(numbers) < 2 or len(numbers) % 2:
                raise SvgInputError('Incomplete X/Y pair before SVG L command.')
            if index + 2 >= len(tokens) or any(
                    re.fullmatch(NUMBER, t) is None for t in tokens[index + 1:index + 3]):
                raise SvgInputError('Each L command must be followed by an X/Y pair.')
        else:
            raise SvgInputError(f'Unsupported SVG path command {token!r}; '
                                'only one M followed by absolute L/pairs is supported.')
    return _points(numbers)


def _properties(element, inherited: dict[str, str]) -> dict[str, str]:
    properties = dict(inherited)
    for name in ('stroke', 'display', 'visibility', 'opacity', 'stroke-opacity'):
        if name in element.attrib:
            properties[name] = element.attrib[name].strip()
    for declaration in element.get('style', '').split(';'):
        if not declaration.strip():
            continue
        if ':' not in declaration:
            raise SvgInputError('Malformed SVG style declaration.')
        name, value = (s.strip() for s in declaration.split(':', 1))
        if name in ('stroke', 'display', 'visibility', 'opacity', 'stroke-opacity'):
            properties[name] = value
        if name in ('transform', 'clip-path', 'mask', 'filter'):
            raise SvgInputError(f'Unsupported SVG style property: {name}.')
    return properties


def _parse_elements(path: Path) -> tuple[SvgElement, ...]:
    if path.stat().st_size > MAX_SVG_BYTES:
        raise SvgInputError('SVG exceeds the 32 MiB parser limit.')
    try:
        root = ET.parse(path, forbid_entities=True, forbid_external=True).getroot()
    except (ET.ParseError, DefusedXmlException, OSError) as error:
        raise SvgInputError(f'Cannot parse SVG {path}: {error}') from error
    if root.tag not in ('svg', f'{{{SVG_NAMESPACE}}}svg'):
        raise SvgInputError('The root element must be SVG.')
    if root.get('version', '1.1') != '1.1':
        raise SvgInputError('Only the documented SVG 1.1 subset is supported.')
    result = []

    def visit(element, inherited: dict[str, str], *, top: bool = False) -> None:
        tag = element.tag.split('}')[-1]
        if element.tag.startswith('{') and not element.tag.startswith('{' + SVG_NAMESPACE + '}'):
            if tag not in ('metadata', 'title', 'desc'):
                raise SvgInputError(f'Unsupported SVG namespace on <{tag}>.')
        if tag in ('metadata', 'title', 'desc', 'defs', 'image'):
            if tag in ('defs', 'image'):
                LOG.info('SVG: ignoring %s content (not trace geometry).', tag)
            return
        if tag == 'style':
            if (element.text or '').strip():
                raise SvgInputError('CSS stylesheets are unsupported; put stroke on '
                                    'each element or in inline/group style.')
            return
        if tag not in ('svg', 'g', *KINDS):
            raise SvgInputError(f'Unsupported SVG element <{tag}>; polygon, curves '
                                'and referenced shapes are not converted silently.')
        if tag == 'svg' and not top:
            raise SvgInputError('Nested SVG viewports are unsupported.')
        for attribute in ('transform', 'clip-path', 'mask', 'filter', 'class'):
            if element.get(attribute):
                raise SvgInputError(f'Unsupported SVG {attribute} on <{tag}>.')
        properties = _properties(element, inherited)
        for name in ('opacity', 'stroke-opacity'):
            try:
                opaque = float(properties.get(name, '1')) == 1.
            except ValueError:
                opaque = False
            if not opaque:
                raise SvgInputError('Transparent SVG trace geometry is unsupported.')
        if tag in KINDS:
            if properties.get('display') == 'none' or properties.get('visibility') in (
                    'hidden', 'collapse'):
                raise SvgInputError('Hidden SVG trace geometry is unsupported.')
            stroke = properties.get('stroke', '#000000')
            stroke = {'black': '#000000', 'white': '#FFFFFF'}.get(stroke.lower(), stroke)
            try:
                colour = normalise_hex(stroke) if stroke.startswith('#') else None
            except ValueError as error:
                raise SvgInputError(str(error)) from error
            if colour is None:
                raise SvgInputError(f'Unsupported SVG stroke {stroke!r}; use #RGB/#RRGGBB.')
            try:
                if tag == 'line':
                    tokens = [element.get(name, '0').strip() for name in ('x1', 'y1', 'x2', 'y2')]
                    if any(re.fullmatch(NUMBER, token) is None for token in tokens):
                        raise SvgInputError('Line coordinates must be unitless numbers.')
                    points = _points(tokens)
                elif tag == 'polyline':
                    points = _points(_tokens(element.get('points', '')))
                else:
                    points = _path(element.get('d', ''))
            except SvgInputError as error:
                raise SvgInputError(f'<{tag}> id={element.get("id", "(none)")}: {error}') from error
            result.append(SvgElement(tag, len(result), element.get('id', ''), colour, points))
        for child in element:
            visit(child, properties)

    visit(root, {}, top=True)
    if not result:
        raise SvgInputError('SVG contains no supported trace geometry.')
    return tuple(result)


def read_svg(path: Path | str, *, pixels_per_metre: float | None = None) -> SvgImport:
    """Prepare a fully validated conversion without writing any files."""
    path = Path(path).expanduser().resolve()
    elements = _parse_elements(path)
    colours = sorted({e.colour_hex for e in elements})
    # Match legacy paths, polylines, lines order within alphabetical colour files.
    ordered = sorted(elements, key=lambda e: (e.colour_hex, KINDS.index(e.kind), e.index))
    last_line = max((e.index for e in elements if e.kind == 'line'), default=-1)
    tables, records = [], []
    for colour in colours:
        group = tuple(e for e in ordered if e.colour_hex == colour)
        name = path.stem + (f'_colour{colour}' if len(colours) > 1 else '') + '_converted.txt'
        contents = []
        for line_number, element in enumerate(group, 1):
            fields = [f'{coordinate:12.8f}' for point in element.points for coordinate in point]
            text = '\t'.join(fields)
            if element.kind != 'line':
                text += '\t\r\n'
            elif element.index != last_line:
                text += '\r\n'
            contents.append(text)
            coordinates = [float(s) for s in fields]
            rounded = tuple(zip(coordinates[::2], coordinates[1::2]))
            records.append(TraceInput(rounded, hex_rgb(colour), line_number))
        tables.append(ConvertedTable(path.with_name(name), ''.join(contents), colour, group))
    try:
        dataset = build_dataset(records, source=path, input_mode=InputMode.SVG,
                                pixels_per_metre=pixels_per_metre)
    except GeometryError as error:
        raise SvgInputError(f'SVG conversion geometry at eight decimal places: {error}') from error
    LOG.info('SVG: %s traces; %s colour sets; coordinates in raw SVG user units.',
             dataset.n_traces, len(colours))
    return SvgImport(dataset, tuple(tables))


def write_conversion(result: SvgImport) -> tuple[Path, ...]:
    """Publish only this conversion's nonempty tables, leaving other files alone."""
    staged = []
    try:
        for table in result.tables:
            with tempfile.NamedTemporaryFile(mode='w', encoding='ascii', newline='',
                                             prefix='.pyfracpaq-svg-', suffix='.txt',
                                             dir=table.path.parent, delete=False) as stream:
                staged.append(Path(stream.name))
                stream.write(table.content)
        for temporary, table in zip(staged, result.tables):
            os.replace(temporary, table.path)
            LOG.info('Saved converted SVG nodes: %s', table.path)
        return tuple(table.path for table in result.tables)
    finally:
        for temporary in staged:
            if temporary.exists():
                temporary.unlink()


def convert_svg(path: Path | str, *, pixels_per_metre: float | None = None) -> SvgImport:
    result = read_svg(path, pixels_per_metre=pixels_per_metre)
    write_conversion(result)
    return result

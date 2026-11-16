"""Strict tab-delimited node files, with atomic import and physical line errors."""

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
import re

from pyfracpaq.domain import (
    Colour, Dataset, InputMode, TraceGeometryError, TraceInput,
    build_dataset, validate_scale,
)
from pyfracpaq.geometry import GeometryError
from pyfracpaq.io.colours import filename_colour

NUMBER = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z')


@dataclass(frozen=True, slots=True)
class InputIssue:
    line: int | None
    column: int | None
    code: str
    message: str


class NodeFileError(ValueError):
    """No dataset is returned when any record or the file is invalid."""

    def __init__(self, path: Path, issues: tuple[InputIssue, ...]) -> None:
        self.path = path
        self.issues = issues
        descriptions = []
        for issue in issues:
            location = str(path)
            if issue.line is not None:
                location += f':{issue.line}'
            if issue.column is not None:
                location += f':{issue.column}'
            descriptions.append(f'{location}: {issue.message}')
        super().__init__('\n'.join(descriptions))


def _parse_line(
    text: str, line: int, colour: Colour,
) -> TraceInput | InputIssue:
    fields = text.rstrip('\r\n').split('\t')
    # SVG conversions in the reference distribution append empty TAB fields.
    while fields and not fields[-1].strip():
        fields.pop()
    if len(fields) % 2:
        return InputIssue(line, len(fields), 'incomplete_pair',
                          'Expected complete tab-delimited X/Y pairs.')
    if len(fields) < 4:
        return InputIssue(line, None, 'too_few_nodes',
                          'A trace needs at least two tab-delimited X/Y pairs.')
    coordinates = []
    for column, field in enumerate(fields, 1):
        field = field.strip()
        if not field:
            return InputIssue(line, column, 'empty_coordinate',
                              'Empty coordinate inside a trace.')
        try:
            value = float(field)
        except ValueError:
            return InputIssue(line, column, 'invalid_number',
                              f'Invalid coordinate {field!r}; expected a real number.')
        if not isfinite(value):
            return InputIssue(line, column, 'nonfinite_coordinate',
                              'Coordinates must be finite float64 values.')
        if NUMBER.fullmatch(field) is None:
            return InputIssue(line, column, 'invalid_number',
                              f'Invalid numeric syntax {field!r}.')
        coordinates.append(value)
    points = tuple(zip(coordinates[::2], coordinates[1::2]))
    if all(point == points[0] for point in points):
        return InputIssue(line, None, 'degenerate_trace',
                          'A trace must contain a nonzero segment.')
    return TraceInput(points, colour, line)


def read_txt(
    path: Path | str, *, pixels_per_metre: float | None = None,
    colour: Colour | None = None,
) -> Dataset:
    """Read all valid records or raise NodeFileError; never return a partial map.

Blank physical lines and trailing empty TAB fields are allowed. Empty internal
fields, comments, commas, nonfinite values and incomplete pairs are errors.
The source is read as UTF-8 (an initial BOM is accepted) without any writes.
"""
    pixels_per_metre = validate_scale(pixels_per_metre)
    path = Path(path).expanduser().resolve()
    colour = filename_colour(path) if colour is None else colour
    # Validate metadata even for an empty or unreadable file.
    TraceInput((), colour)
    records = []
    issues = []
    try:
        with path.open(encoding='utf-8-sig') as stream:
            for line_number, text in enumerate(stream, 1):
                if not text.strip():
                    continue
                record = _parse_line(text, line_number, colour)
                if isinstance(record, InputIssue):
                    issues.append(record)
                else:
                    records.append(record)
    except UnicodeError as error:
        # Text buffering makes the exact line of a decoding error uncertain.
        raise NodeFileError(path, (InputIssue(
            None, None, 'encoding', 'Expected UTF-8 encoded node coordinates.',
        ),)) from error
    except OSError as error:
        raise NodeFileError(path, (InputIssue(
            None, None, 'io', f'Cannot read node file: {error.strerror}.',
        ),)) from error
    if issues:
        raise NodeFileError(path, tuple(issues))
    if not records:
        raise NodeFileError(path, (InputIssue(
            None, None, 'empty_file', 'The file contains no traces.',
        ),))
    try:
        return build_dataset(records, source=path, input_mode=InputMode.TXT,
                             pixels_per_metre=pixels_per_metre)
    except TraceGeometryError as error:
        raise NodeFileError(path, (InputIssue(
            error.source_line, None, 'invalid_geometry', str(error),
        ),)) from error
    except GeometryError as error:
        raise NodeFileError(path, (InputIssue(
            None, None, 'invalid_geometry', str(error),
        ),)) from error

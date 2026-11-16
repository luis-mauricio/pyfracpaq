"""Explicit RGB conventions for SVG strokes and individual converted TXT sets."""

from pathlib import Path
import re

from pyfracpaq.domain import Colour

BLUE: Colour = (0., 0., 1.)
BLACK: Colour = (0., 0., 0.)


def normalise_hex(value: str) -> str:
    text = value.strip().removeprefix('#')
    if re.fullmatch(r'[0-9a-fA-F]{3}', text):
        text = ''.join(c * 2 for c in text)
    if re.fullmatch(r'[0-9a-fA-F]{6}', text) is None:
        raise ValueError(f'Expected an RGB hexadecimal stroke, got {value!r}.')
    return text.upper()


def hex_rgb(value: str) -> Colour:
    value = normalise_hex(value)
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def filename_colour(path: Path | str, default: Colour = BLUE) -> Colour:
    name = Path(path).name
    match = re.search(r'_colour([0-9a-f]{6})(?:_converted)?\.txt\Z', name, re.I)
    if match:
        return hex_rgb(match[1])
    if re.search(r'_colour[^.]*\.txt\Z', name, re.I):
        raise ValueError('A colour TXT filename must end in colourHHHHHH'
                         '[_converted].txt with six hexadecimal digits.')
    return default

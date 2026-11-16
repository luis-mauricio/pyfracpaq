"""Project-authored closed rectangles and directed profile fixtures (MIT)."""

from dataclasses import replace

from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.geometry.profiles import ProfileLine
from sprint3_reference import reference_config


def block_dataset(*, scale=None, shift=(0, 0)):
    paths = (((10, 10), (50, 10), (50, 50), (10, 50), (10, 10)),
             ((70, 30), (110, 30), (110, 70), (70, 70), (70, 30)))
    return build_dataset([TraceInput(tuple((x + shift[0], y + shift[1]) for x, y in path))
                          for path in paths], pixels_per_metre=scale)


def graph_dataset():
    return build_dataset([TraceInput(((-6, -3), (-3, 3), (3, 3), (6, -3))),
                          TraceInput(((0, -.5), (0, .5)))])


def configuration(selected, *, line=ProfileLine((-6, 0), (6, 0)), **changes):
    return replace(reference_config(selected, edit_numscancirclesgraph='3', **changes),
                   profile_line=line)

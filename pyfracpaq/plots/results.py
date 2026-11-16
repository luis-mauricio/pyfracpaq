"""Rendered figure outputs, created on the main thread by analysis renderers."""

from dataclasses import dataclass

from matplotlib.figure import Figure


@dataclass(frozen=True, slots=True)
class FigureOutput:
    basename: str
    figure: Figure

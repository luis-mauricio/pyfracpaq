"""PyFracPaQ: Fracture trace analysis in Python.

This package provides minimal building blocks to load fracture traces
from plain text files, compute basic statistics (lengths, orientations),
and generate common plots (trace map, rose diagram).

Modules are intentionally small and focused to make extension easy.
"""

from .types import Segment, Trace, TraceMap

__all__ = [
    "Segment",
    "Trace",
    "TraceMap",
]

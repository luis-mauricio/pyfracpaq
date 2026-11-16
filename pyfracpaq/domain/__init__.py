"""Public immutable geometry and the common importer construction contract."""

from .construction import TraceGeometryError, build_dataset, validate_scale
from .models import (
    BLACK, Colour, Dataset, GeometryArrays, ImportDiagnostic, InputMode, Node,
    Segment, Trace, TraceInput,
)

__all__ = [
    'BLACK', 'Colour', 'Dataset', 'GeometryArrays', 'ImportDiagnostic',
    'InputMode', 'Node', 'Segment', 'Trace', 'TraceGeometryError', 'TraceInput',
    'build_dataset', 'validate_scale',
]

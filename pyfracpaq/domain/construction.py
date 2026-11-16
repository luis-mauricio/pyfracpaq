"""Build complete geometry from unscaled ordered input records."""

from collections.abc import Iterable
from pathlib import Path

from pyfracpaq.geometry.primitives import (
    Bounds, GeometryError, bounds_from_points, finite_number,
)

from .models import (
    Dataset, ImportDiagnostic, InputMode, Node, Trace, TraceInput,
)


class TraceGeometryError(GeometryError):
    def __init__(self, message: str, trace_id: int, source_line: int | None) -> None:
        self.trace_id = trace_id
        self.source_line = source_line
        super().__init__(message)


def validate_scale(pixels_per_metre: float | None) -> float | None:
    if pixels_per_metre is None:
        return None
    scale = finite_number(pixels_per_metre, 'Pixels per metre')
    if scale <= 0:
        raise GeometryError('Pixels per metre must be positive, or None for pixels.')
    return scale


def _build_trace(
    raw: TraceInput, trace_id: int, scale: float,
) -> tuple[Trace, tuple[ImportDiagnostic, ...]]:
    nodes = []
    diagnostics = []
    previous = None
    for index, point in enumerate(raw.points):
        if point == previous:
            diagnostics.append(ImportDiagnostic(
                'consecutive_duplicate', trace_id, raw.source_line, index,
                nodes[-1].id, 'Consecutive duplicate node removed.',
            ))
            continue
        scaled = point[0] / scale, point[1] / scale
        if any(raw_value != 0 and value == 0
               for raw_value, value in zip(point, scaled)):
            raise GeometryError('Scaling underflows float64 coordinate range.')
        nodes.append(Node((trace_id, index), *scaled))
        previous = point
    if len(nodes) < 2:
        raise GeometryError('A trace needs two distinct consecutive nodes.')
    trace = Trace(trace_id, tuple(nodes), raw.colour, raw.source_line)
    return trace, tuple(diagnostics)


def build_dataset(
    records: Iterable[TraceInput], *, source: Path | str | None = None,
    input_mode: InputMode = InputMode.TXT,
    pixels_per_metre: float | None = None,
    source_bounds: Bounds | None = None,
) -> Dataset:
    """Normalize exact duplicates, preserving IDs, provenance and trace order."""
    pixels_per_metre = validate_scale(pixels_per_metre)
    original = tuple(records)
    traces = []
    diagnostics = []
    for trace_id, record in enumerate(original):
        if not isinstance(record, TraceInput):
            raise GeometryError('Each input record must be a TraceInput.')
        try:
            trace, removed = _build_trace(record, trace_id, pixels_per_metre or 1.)
        except GeometryError as error:
            raise TraceGeometryError(
                str(error), trace_id, record.source_line,
            ) from error
        traces.append(trace)
        diagnostics.extend(removed)
    bounds = bounds_from_points([n.point for t in traces for n in t.nodes])
    if source_bounds is not None:
        scale = pixels_per_metre or 1.
        extent = Bounds(*(value / scale for value in (
            source_bounds.x_min, source_bounds.y_min,
            source_bounds.x_max, source_bounds.y_max)))
        if (bounds.x_min < extent.x_min or bounds.y_min < extent.y_min
                or bounds.x_max > extent.x_max or bounds.y_max > extent.y_max):
            raise GeometryError('Trace coordinates lie outside the supplied source domain.')
        bounds = extent
    return Dataset(
        tuple(traces), bounds, original, Path(source) if source is not None else None,
        InputMode(input_mode), pixels_per_metre, tuple(diagnostics), source_bounds,
    )

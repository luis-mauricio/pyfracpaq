"""Immutable geometry shared by TXT, SVG and image import pipelines."""

from dataclasses import dataclass, field
from enum import StrEnum
from math import atan, degrees, fsum
from pathlib import Path
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from pyfracpaq.geometry.primitives import (
    Bounds, GeometryError, Point, as_point, finite_number, point_distance,
)

Identifier: TypeAlias = tuple[int, int]
Colour: TypeAlias = tuple[float, float, float]
BLACK: Colour = (0., 0., 0.)


def validate_colour(value: Colour) -> Colour:
    if len(value) != 3:
        raise GeometryError('Colour must contain three RGB components.')
    result = tuple(finite_number(v, 'Colour component') for v in value)
    if not all(0 <= v <= 1 for v in result):
        raise GeometryError('RGB components must be between zero and one.')
    return result


def _index(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GeometryError(f'{name} must be a nonnegative integer.')


def _identifier(value: Identifier) -> Identifier:
    if len(value) != 2:
        raise GeometryError('An identifier is a (trace index, local index) pair.')
    for item in value:
        _index(item, 'Identifier')
    return tuple(value)


class InputMode(StrEnum):
    TXT = 'txt'
    SVG = 'svg'
    IMAGE = 'image'


@dataclass(frozen=True, slots=True)
class Node:
    id: Identifier
    x: float
    y: float

    def __post_init__(self) -> None:
        object.__setattr__(self, 'id', _identifier(self.id))
        object.__setattr__(self, 'x', finite_number(self.x, 'X'))
        object.__setattr__(self, 'y', finite_number(self.y, 'Y'))

    @property
    def point(self) -> Point:
        return self.x, self.y


@dataclass(frozen=True, slots=True)
class Segment:
    id: Identifier
    trace_id: int
    start: Node
    end: Node
    start_length: float = 0.
    length: float = field(init=False)
    raw_angle: float = field(init=False)
    midpoint: Point = field(init=False)
    end_length: float = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'id', _identifier(self.id))
        _index(self.trace_id, 'Trace index')
        if any(i != self.trace_id for i in
               (self.id[0], self.start.id[0], self.end.id[0])):
            raise GeometryError('Segment and endpoint IDs must belong to one trace.')
        length = point_distance(self.start.point, self.end.point)
        if length == 0:
            raise GeometryError('A segment must have positive length.')
        start_length = finite_number(self.start_length, 'Cumulative length')
        if start_length < 0:
            raise GeometryError('Cumulative length cannot be negative.')
        dx, dy = self.end.x - self.start.x, self.end.y - self.start.y
        # Keep the original atan(dx/dy) axial convention. In particular, a
        # reversed vertical segment remains 0 degrees rather than 180 degrees.
        angle = 90. if dy == 0 else degrees(atan(dx / dy))
        if angle < 0:
            angle += 180.
        midpoint = (self.start.x / 2 + self.end.x / 2,
                    self.start.y / 2 + self.end.y / 2)
        object.__setattr__(self, 'start_length', start_length)
        object.__setattr__(self, 'length', length)
        object.__setattr__(self, 'raw_angle', angle)
        object.__setattr__(self, 'midpoint', midpoint)
        object.__setattr__(self, 'end_length', finite_number(
            start_length + length, 'Cumulative length',
        ))


@dataclass(frozen=True, slots=True)
class Trace:
    id: int
    nodes: tuple[Node, ...]
    colour: Colour = BLACK
    source_line: int | None = None
    segments: tuple[Segment, ...] = field(init=False)
    total_length: float = field(init=False)
    euclidean_length: float = field(init=False)
    midpoint: Point = field(init=False)

    def __post_init__(self) -> None:
        _index(self.id, 'Trace index')
        if self.source_line is not None:
            _index(self.source_line, 'Source line')
            if self.source_line == 0:
                raise GeometryError('Source line numbers are one-based.')
        nodes = tuple(self.nodes)
        if len(nodes) < 2:
            raise GeometryError('A trace must contain at least two distinct nodes.')
        if len({n.id for n in nodes}) != len(nodes):
            raise GeometryError('Node identifiers must be unique within a trace.')
        if any(n.id[0] != self.id for n in nodes):
            raise GeometryError('All nodes must belong to their trace.')
        segments = []
        cumulative = 0.
        for i, (start, end) in enumerate(zip(nodes, nodes[1:])):
            segment = Segment((self.id, i), self.id, start, end, cumulative)
            segments.append(segment)
            cumulative = segment.end_length
        halfway = cumulative / 2
        centre = nodes[-1].point
        for segment in segments:
            if halfway <= segment.end_length:
                t = (halfway - segment.start_length) / segment.length
                centre = ((1 - t) * segment.start.x + t * segment.end.x,
                          (1 - t) * segment.start.y + t * segment.end.y)
                break
        object.__setattr__(self, 'nodes', nodes)
        object.__setattr__(self, 'colour', validate_colour(self.colour))
        object.__setattr__(self, 'segments', tuple(segments))
        object.__setattr__(self, 'total_length', cumulative)
        object.__setattr__(self, 'euclidean_length', point_distance(
            nodes[0].point, nodes[-1].point,
        ))
        object.__setattr__(self, 'midpoint', centre)


@dataclass(frozen=True, slots=True)
class TraceInput:
    """Unscaled coordinates and per-trace provenance for any future reader."""

    points: tuple[Point, ...]
    colour: Colour = BLACK
    source_line: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, 'points', tuple(as_point(p) for p in self.points))
        object.__setattr__(self, 'colour', validate_colour(self.colour))
        if self.source_line is not None:
            _index(self.source_line, 'Source line')
            if self.source_line == 0:
                raise GeometryError('Source line numbers are one-based.')


@dataclass(frozen=True, slots=True)
class ImportDiagnostic:
    code: str
    trace_id: int
    source_line: int | None
    source_node_index: int
    retained_node_id: Identifier
    message: str


@dataclass(frozen=True, slots=True)
class GeometryArrays:
    """Detached, read-only arrays in trace/segment input order."""

    node_coordinates: NDArray[np.float64]
    node_ids: NDArray[np.int64]
    segment_coordinates: NDArray[np.float64]
    segment_lengths: NDArray[np.float64]
    raw_angles: NDArray[np.float64]
    segment_midpoints: NDArray[np.float64]
    start_lengths: NDArray[np.float64]
    end_lengths: NDArray[np.float64]
    segment_ids: NDArray[np.int64]
    segment_trace_ids: NDArray[np.int64]
    segment_node_ids: NDArray[np.int64]
    trace_lengths: NDArray[np.float64]
    trace_midpoints: NDArray[np.float64]
    trace_colours: NDArray[np.float64]


def _array(values: list, *, integers: bool = False) -> NDArray:
    result = np.array(values, dtype=np.int64 if integers else np.float64)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class Dataset:
    traces: tuple[Trace, ...]
    bounds: Bounds
    source_traces: tuple[TraceInput, ...]
    source: Path | None = None
    input_mode: InputMode = InputMode.TXT
    pixels_per_metre: float | None = None
    diagnostics: tuple[ImportDiagnostic, ...] = ()
    source_bounds: Bounds | None = None
    nodes: tuple[Node, ...] = field(init=False)
    segments: tuple[Segment, ...] = field(init=False)
    total_length: float = field(init=False)

    def __post_init__(self) -> None:
        traces = tuple(self.traces)
        if not traces:
            raise GeometryError('A dataset must contain at least one valid trace.')
        if tuple(t.id for t in traces) != tuple(range(len(traces))):
            raise GeometryError('Trace IDs must follow zero-based input order.')
        if len(self.source_traces) != len(traces):
            raise GeometryError('Each trace must retain its unscaled input.')
        from .construction import validate_scale

        object.__setattr__(
            self, 'pixels_per_metre', validate_scale(self.pixels_per_metre),
        )
        object.__setattr__(self, 'traces', traces)
        object.__setattr__(self, 'source_traces', tuple(self.source_traces))
        object.__setattr__(self, 'diagnostics', tuple(self.diagnostics))
        object.__setattr__(self, 'input_mode', InputMode(self.input_mode))
        object.__setattr__(self, 'source', Path(self.source) if self.source else None)
        object.__setattr__(self, 'nodes', tuple(n for t in traces for n in t.nodes))
        object.__setattr__(self, 'segments', tuple(
            s for t in traces for s in t.segments
        ))
        try:
            total = fsum(t.total_length for t in traces)
        except OverflowError as error:
            raise GeometryError('Dataset length exceeds float64 range.') from error
        object.__setattr__(self, 'total_length', finite_number(total, 'Dataset length'))

    @property
    def n_traces(self) -> int:
        return len(self.traces)

    @property
    def n_segments(self) -> int:
        return len(self.segments)

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @property
    def area(self) -> float:
        return self.bounds.area

    @property
    def length_unit(self) -> str:
        return 'metres' if self.pixels_per_metre is not None else 'pixels'

    @property
    def area_unit(self) -> str:
        return f'{self.length_unit}^2'

    @property
    def permeability_unit(self) -> str:
        return self.area_unit

    @property
    def intensity_unit(self) -> str:
        return f'{self.length_unit}^-1'

    @property
    def density_unit(self) -> str:
        return f'{self.length_unit}^-2'

    @property
    def colours(self) -> tuple[Colour, ...]:
        return tuple(dict.fromkeys(t.colour for t in self.traces))

    def with_scale(self, pixels_per_metre: float | None) -> 'Dataset':
        """Rebuild from unscaled input; never scale an already scaled geometry."""
        from .construction import build_dataset

        return build_dataset(
            self.source_traces, source=self.source, input_mode=self.input_mode,
            pixels_per_metre=pixels_per_metre,
            source_bounds=self.source_bounds,
        )

    def as_arrays(self) -> GeometryArrays:
        nodes, segments, traces = self.nodes, self.segments, self.traces
        return GeometryArrays(
            node_coordinates=_array([n.point for n in nodes]),
            node_ids=_array([n.id for n in nodes], integers=True),
            segment_coordinates=_array([
                (*s.start.point, *s.end.point) for s in segments
            ]),
            segment_lengths=_array([s.length for s in segments]),
            raw_angles=_array([s.raw_angle for s in segments]),
            segment_midpoints=_array([s.midpoint for s in segments]),
            start_lengths=_array([s.start_length for s in segments]),
            end_lengths=_array([s.end_length for s in segments]),
            segment_ids=_array([s.id for s in segments], integers=True),
            segment_trace_ids=_array([s.trace_id for s in segments], integers=True),
            segment_node_ids=_array(
                [(s.start.id, s.end.id) for s in segments], integers=True,
            ),
            trace_lengths=_array([t.total_length for t in traces]),
            trace_midpoints=_array([t.midpoint for t in traces]),
            trace_colours=_array([t.colour for t in traces]),
        )

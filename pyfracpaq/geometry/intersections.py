"""Segment relations with exact predicates on the supplied float64 coordinates.

Coincident supporting lines and finite overlap are distinct. No snap tolerance
or topological I/Y/X interpretation is introduced here.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from numpy.typing import ArrayLike

from .primitives import GeometryError, Point, as_point, point_array

RationalPoint = tuple[Fraction, Fraction]


class IntersectionKind(StrEnum):
    NONE = 'none'
    POINT = 'point'
    OVERLAP = 'overlap'


@dataclass(frozen=True, slots=True)
class Intersection:
    kind: IntersectionKind
    points: tuple[Point, ...] = ()
    parameters_first: tuple[float, ...] = ()
    parameters_second: tuple[float, ...] = ()
    parallel: bool = False
    coincident: bool = False

    @property
    def intersects(self) -> bool:
        return self.kind != IntersectionKind.NONE


def _subtract(a: RationalPoint, b: RationalPoint) -> RationalPoint:
    return a[0] - b[0], a[1] - b[1]


def _cross(a: RationalPoint, b: RationalPoint) -> Fraction:
    return a[0] * b[1] - a[1] * b[0]


def _parameter(
    point: RationalPoint, start: RationalPoint, direction: RationalPoint,
) -> Fraction:
    axis = 0 if direction[0] else 1
    return (point[axis] - start[axis]) / direction[axis]


def segment_intersection(first: ArrayLike, second: ArrayLike) -> Intersection:
    """Accept two [x1,y1,x2,y2] records; include endpoints and overlaps.

Fractions prevent cancellation from silently turning near-parallel lines into
coincident ones. Classification is exact for represented inputs, not a spatial
tolerance. Output coordinates and parameters are rounded back to float64.
"""
    left, right = point_array(first, 4), point_array(second, 4)
    if len(left) != 1 or len(right) != 1:
        raise GeometryError('segment_intersection expects one segment per input.')
    a, b = as_point(left[0, :2]), as_point(left[0, 2:])
    c, d = as_point(right[0, :2]), as_point(right[0, 2:])
    aq, bq, cq, dq = [tuple(Fraction(v) for v in p) for p in (a, b, c, d)]
    r, s = _subtract(bq, aq), _subtract(dq, cq)
    if a == b or c == d:
        return _degenerate(aq, bq, cq, dq)
    delta = _subtract(cq, aq)
    denominator = _cross(r, s)
    if denominator:
        t, u = _cross(delta, s) / denominator, _cross(delta, r) / denominator
        if 0 <= t <= 1 and 0 <= u <= 1:
            point = float(aq[0] + t * r[0]), float(aq[1] + t * r[1])
            return Intersection(IntersectionKind.POINT, (point,), (float(t),),
                                (float(u),))
        return Intersection(IntersectionKind.NONE)
    if _cross(delta, r):
        return Intersection(IntersectionKind.NONE, parallel=True)
    t0, t1 = _parameter(cq, aq, r), _parameter(dq, aq, r)
    low, high = max(Fraction(0), min(t0, t1)), min(Fraction(1), max(t0, t1))
    if low > high:
        return Intersection(IntersectionKind.NONE, parallel=True, coincident=True)
    parameters = (low,) if low == high else (low, high)
    exact = [(aq[0] + t * r[0], aq[1] + t * r[1]) for t in parameters]
    points = tuple((float(p[0]), float(p[1])) for p in exact)
    return Intersection(
        IntersectionKind.POINT if low == high else IntersectionKind.OVERLAP,
        points, tuple(float(t) for t in parameters),
        tuple(float(_parameter(p, cq, s)) for p in exact),
        parallel=True, coincident=True,
    )


def _degenerate(
    a: RationalPoint, b: RationalPoint, c: RationalPoint, d: RationalPoint,
) -> Intersection:
    if a == b and c == d:
        if a == c:
            point = float(a[0]), float(a[1])
            return Intersection(IntersectionKind.POINT, (point,), (0.,), (0.,))
        return Intersection(IntersectionKind.NONE)
    reverse = a != b
    point, start, end = (c, a, b) if reverse else (a, c, d)
    direction = _subtract(end, start)
    if _cross(_subtract(point, start), direction):
        return Intersection(IntersectionKind.NONE)
    t = _parameter(point, start, direction)
    if not 0 <= t <= 1:
        return Intersection(IntersectionKind.NONE)
    first, second = ((float(t),), (0.,)) if reverse else ((0.,), (float(t),))
    rounded = float(point[0]), float(point[1])
    return Intersection(IntersectionKind.POINT, (rounded,), first, second)


def iter_segment_intersections(
    first: ArrayLike, second: ArrayLike, *, include_disjoint: bool = False,
) -> Iterator[tuple[int, int, Intersection]]:
    """Stream pairs in stable row-major order; do not allocate N-by-M matrices."""
    left, right = point_array(first, 4), point_array(second, 4)
    for i, segment in enumerate(left):
        for j, other in enumerate(right):
            result = segment_intersection(segment, other)
            if include_disjoint or result.intersects:
                yield i, j, result

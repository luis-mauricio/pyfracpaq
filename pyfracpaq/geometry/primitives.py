"""Finite Cartesian geometry, independent of Qt and the importers."""

from dataclasses import dataclass
from math import fsum, hypot, isfinite
from numbers import Real
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

Point: TypeAlias = tuple[float, float]
FloatArray: TypeAlias = NDArray[np.float64]
DEFAULT_MEMORY_LIMIT = 256 * 1024 * 1024


class GeometryError(ValueError):
    """Input or derived geometry cannot be represented as finite float64."""


def finite_number(value: Real, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise GeometryError(f'{name} must be a finite real number.')
    try:
        result = float(value)
    except (ValueError, OverflowError) as error:
        raise GeometryError(f'{name} is outside float64 range.') from error
    if not isfinite(result):
        raise GeometryError(f'{name} must be finite.')
    return result


def as_point(value: ArrayLike) -> Point:
    try:
        size = len(value)
    except TypeError as error:
        raise GeometryError('A point must contain two coordinates.') from error
    if size != 2:
        raise GeometryError('A point must contain exactly two coordinates.')
    return finite_number(value[0], 'X'), finite_number(value[1], 'Y')


def point_distance(first: ArrayLike, second: ArrayLike) -> float:
    a, b = as_point(first), as_point(second)
    return finite_number(hypot(b[0] - a[0], b[1] - a[1]), 'Distance')


@dataclass(frozen=True, slots=True)
class Bounds:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def __post_init__(self) -> None:
        for name in ('x_min', 'y_min', 'x_max', 'y_max'):
            object.__setattr__(self, name, finite_number(getattr(self, name), name))
        if self.x_max < self.x_min or self.y_max < self.y_min:
            raise GeometryError('Bounds must be ordered from minimum to maximum.')
        finite_number(self.width, 'Domain width')
        finite_number(self.height, 'Domain height')
        finite_number(self.area, 'Domain area')
        if self.width > 0 and self.height > 0 and self.area == 0:
            raise GeometryError('Domain area underflows float64 range.')

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def diagonal(self) -> float:
        return finite_number(hypot(self.width, self.height), 'Domain diagonal')


def bounds_from_points(points: ArrayLike) -> Bounds:
    values = point_array(points)
    if not len(values):
        raise GeometryError('Cannot compute bounds of an empty dataset.')
    low, high = values.min(axis=0), values.max(axis=0)
    return Bounds(low[0], low[1], high[0], high[1])


def point_array(values: ArrayLike, columns: int = 2) -> FloatArray:
    """Validate matrix inputs, accepting [] and a single flat record."""
    try:
        original = np.asarray(values)
        if original.dtype.kind not in 'fiu' and original.size:
            raise GeometryError('Coordinates must be real numeric values.')
        result = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as error:
        raise GeometryError('Invalid numeric coordinate array.') from error
    if result.ndim == 1:
        if result.size == 0:
            result = result.reshape(0, columns)
        elif result.size == columns:
            result = result.reshape(1, columns)
    if result.ndim != 2 or result.shape[1] != columns:
        raise GeometryError(f'Expected an N-by-{columns} array.')
    if not np.isfinite(result).all():
        raise GeometryError('Coordinates must be finite.')
    return result


def check_allocation(cells: int, arrays: int, max_bytes: int) -> None:
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        raise GeometryError('Memory limit must be a positive integer in bytes.')
    needed = cells * arrays * np.dtype(np.float64).itemsize
    if needed > max_bytes:
        raise MemoryError(
            f'Pairwise operation needs approximately {needed} bytes; '
            f'limit is {max_bytes}. Use smaller batches or diagonal distances.'
        )


def distance_points(
    first: ArrayLike,
    second: ArrayLike,
    *,
    norm: float = 2,
    diagonal: bool = False,
    max_bytes: int = DEFAULT_MEMORY_LIMIT,
) -> FloatArray:
    """Return N-by-M distances, or N paired distances when diagonal=True."""
    a, b = point_array(first), point_array(second)
    p = float(norm)
    if isinstance(norm, bool) or p <= 0 or np.isnan(p):
        raise GeometryError('Norm must be positive, or positive infinity.')
    if diagonal and len(a) != len(b):
        raise GeometryError('Diagonal distances require equal point counts.')
    cells = len(a) if diagonal else len(a) * len(b)
    check_allocation(cells, 8, max_bytes)
    with np.errstate(over='ignore', invalid='ignore'):
        if diagonal:
            dx, dy = np.abs(a[:, 0] - b[:, 0]), np.abs(a[:, 1] - b[:, 1])
        else:
            dx = np.abs(a[:, None, 0] - b[None, :, 0])
            dy = np.abs(a[:, None, 1] - b[None, :, 1])
        if p == 2:
            result = np.hypot(dx, dy)
        elif np.isinf(p):
            result = np.maximum(dx, dy)
        else:
            scale = np.maximum(dx, dy)
            safe = np.where(scale == 0, 1., scale)
            result = scale * ((dx / safe) ** p + (dy / safe) ** p) ** (1 / p)
    if not np.isfinite(result).all():
        raise GeometryError('Distances exceed float64 range.')
    return result


@dataclass(frozen=True, slots=True)
class Projection:
    distance: float
    parameter: float
    point: Point


def distance_point_segment(
    point: ArrayLike, start: ArrayLike, end: ArrayLike,
    *, reference_epsilon: bool = True,
) -> Projection:
    """Project onto a finite segment with the reference library's epsilon rule.

    distancePointEdge.m treats squared lengths below float64 eps as degenerate,
    using the first endpoint. This absolute, unit-dependent cutoff is retained.
    It is not a spatial snap tolerance for intersections or node normalisation.
    Set reference_epsilon=False for finite geometry without that legacy cutoff.
    """
    p, a, b = as_point(point), as_point(start), as_point(end)
    length = point_distance(a, b)
    if length == 0 or (reference_epsilon and length * length < np.finfo(np.float64).eps):
        return Projection(point_distance(p, a), 0., a)
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    try:
        along = fsum(((p[0] - a[0]) * ux, (p[1] - a[1]) * uy))
    except (ValueError, OverflowError) as error:
        raise GeometryError('Projection exceeds float64 range.') from error
    parameter = min(1., max(0., finite_number(along, 'Projection') / length))
    closest = ((1 - parameter) * a[0] + parameter * b[0],
               (1 - parameter) * a[1] + parameter * b[1])
    return Projection(point_distance(p, closest), parameter, closest)


def distance_point_segments(
    points: ArrayLike, segments: ArrayLike,
    *, max_bytes: int = DEFAULT_MEMORY_LIMIT,
) -> tuple[FloatArray, FloatArray]:
    """Return distance and clamped-parameter matrices, each NP-by-NS."""
    points = point_array(points)
    segments = point_array(segments, columns=4)
    check_allocation(len(points) * len(segments), 2, max_bytes)
    distances = np.empty((len(points), len(segments)), dtype=np.float64)
    parameters = np.empty_like(distances)
    for j, segment in enumerate(segments):
        for i, point in enumerate(points):
            result = distance_point_segment(point, segment[:2], segment[2:])
            distances[i, j] = result.distance
            parameters[i, j] = result.parameter
    return distances, parameters

"""Immutable directed scan lines and source-signed distance to their support."""

from dataclasses import dataclass
from math import hypot, isfinite

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .primitives import GeometryError, Point, as_point


@dataclass(frozen=True, slots=True)
class ProfileLine:
    start: Point
    end: Point

    def __post_init__(self) -> None:
        object.__setattr__(self, 'start', as_point(self.start))
        object.__setattr__(self, 'end', as_point(self.end))
        if not isfinite(self.length) or self.length <= 0:
            raise GeometryError('Select two distinct, representable end points.')

    @property
    def length(self) -> float:
        return hypot(self.end[0] - self.start[0], self.end[1] - self.start[1])

    @property
    def segment(self) -> tuple[float, float, float, float]:
        return (*self.start, *self.end)


def signed_profile_distances(points: ArrayLike, line: ProfileLine) -> NDArray[np.float64]:
    """FROM sign is negative on the left of the directed line; not clipped."""
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise GeometryError('Profile centres must be finite N by 2 coordinates.')
    delta = points.astype(np.longdouble) - np.asarray(line.start, dtype=np.longdouble)
    direction = (np.asarray(line.end, dtype=np.longdouble)
                 - np.asarray(line.start, dtype=np.longdouble)) / line.length
    with np.errstate(over='ignore', invalid='ignore'):
        values = np.asarray(direction[1] * delta[:, 0] - direction[0] * delta[:, 1], dtype=float)
    if not np.isfinite(values).all():
        raise GeometryError('Perpendicular distances exceed float64 range.')
    values.setflags(write=False)
    return values

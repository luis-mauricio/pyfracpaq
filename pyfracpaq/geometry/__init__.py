"""Cartesian primitives and segment relations; no GUI dependencies."""

from .intersections import (
    Intersection, IntersectionKind, iter_segment_intersections,
    segment_intersection,
)
from .primitives import (
    Bounds, GeometryError, Point, Projection, bounds_from_points,
    distance_point_segment, distance_point_segments, distance_points,
    point_distance,
)
from .profiles import ProfileLine, signed_profile_distances

__all__ = [
    'Bounds', 'GeometryError', 'Intersection', 'IntersectionKind', 'Point',
    'Projection', 'bounds_from_points', 'distance_point_segment',
    'distance_point_segments', 'distance_points', 'iter_segment_intersections',
    'point_distance', 'segment_intersection',
    'ProfileLine', 'signed_profile_distances',
]

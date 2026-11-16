"""Finite segment/circle predicates, with exact fallback at ambiguous boundaries.

Intersections are distinct points on each closed segment (a tangent counts once).
Interior endpoints are strict, and shared endpoints are counted per segment.
"""

from fractions import Fraction

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .primitives import GeometryError, as_point, finite_number


def _exact(segment, centre, radius) -> tuple[int, int]:
    f = Fraction.from_float
    px, py = (f(float(segment[i])) - f(float(centre[i])) for i in range(2))
    qx, qy = (f(float(segment[i + 2])) - f(float(centre[i])) for i in range(2))
    r = f(float(radius))
    dx, dy = qx - px, qy - py
    a = dx * dx + dy * dy
    c0, c1 = px * px + py * py - r * r, qx * qx + qy * qy - r * r
    inside = int(c0 < 0) + int(c1 < 0)
    if inside:
        return (1 if inside == 1 else 0), inside
    dot0, dot1 = px * dx + py * dy, qx * dx + qy * dy
    if c0 == 0 and c1 == 0:
        return 2, 0
    if c0 == 0:
        return 1 + int(dot0 < 0), 0
    if c1 == 0:
        return 1 + int(dot1 > 0), 0
    discriminant = r * r * a - (px * qy - py * qx) ** 2
    if discriminant == 0:
        return int(dot0 <= 0 and dot1 >= 0), 0
    return (2 if discriminant > 0 and dot0 < 0 and dot1 > 0 else 0), 0


def circle_counts(segments: ArrayLike, centre: ArrayLike, radius: float
                  ) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
    """Return intersection/interior-endpoint counts for an N×4 segment array.

    No snapping tolerance changes geometric decisions. Extended precision handles
    the common path; uncertain signs are recomputed as rational numbers from the
    original float64 coordinates. Temporary storage is O(N), never circles×N.
    """
    radius = finite_number(radius, 'Circle radius')
    lines = np.asarray(segments, dtype=np.float64)
    origin = np.asarray(as_point(centre), dtype=np.float64)
    if (lines.ndim != 2 or lines.shape[1] != 4 or origin.shape != (2,)
            or not np.isfinite(lines).all() or not np.isfinite(origin).all()
            or not np.isfinite(radius) or radius <= 0):
        raise GeometryError('Circles require finite segments, a centre and positive radius.')
    if np.any(np.all(lines[:, :2] == lines[:, 2:], axis=1)):
        raise GeometryError('Circle sampling requires nonzero segments.')
    points = lines.astype(np.longdouble).reshape(-1, 2, 2) - origin.astype(np.longdouble)
    # Scaling in extended precision avoids overflow/underflow across float64 units.
    scale = np.maximum(np.max(np.abs(points), axis=(1, 2), initial=0), radius)
    points /= scale[:, None, None]
    r = np.longdouble(radius) / scale
    p, q = points[:, 0], points[:, 1]
    d = q - p
    a = np.sum(d * d, axis=1)
    rr = r * r
    pp, qq = np.sum(p * p, axis=1), np.sum(q * q, axis=1)
    c0, c1 = pp - rr, qq - rr
    dot0, dot1 = np.sum(p * d, axis=1), np.sum(q * d, axis=1)
    cross = p[:, 0] * q[:, 1] - p[:, 1] * q[:, 0]
    delta = rr * a - cross * cross
    m = (c0 < 0).astype(np.int64) + (c1 < 0)
    n = (m == 1).astype(np.int64)
    outside = m == 0
    n[outside & (delta > 0) & (dot0 < 0) & (dot1 > 0)] = 2
    # Every exact boundary/tangency is ambiguous on the fast path and handled
    # below; the bound is an arithmetic error detector, not a geometric epsilon.
    eps = 128 * np.finfo(np.longdouble).eps
    d_error = eps * (np.abs(p) + np.abs(q))
    a_error = np.sum(2 * np.abs(d) * d_error + d_error * d_error, axis=1)
    cross_error = eps * (np.abs(p[:, 0] * q[:, 1]) + np.abs(p[:, 1] * q[:, 0]))
    delta_error = (eps * (rr * a + cross * cross) + rr * a_error
                   + 2 * np.abs(cross) * cross_error + cross_error * cross_error)
    dot0_error = eps * np.sum(np.abs(p * d), axis=1) + np.sum(np.abs(p) * d_error, axis=1)
    dot1_error = eps * np.sum(np.abs(q * d), axis=1) + np.sum(np.abs(q) * d_error, axis=1)
    uncertain = ((np.abs(c0) <= eps * (pp + rr))
                 | (np.abs(c1) <= eps * (qq + rr))
                 | (outside & ((np.abs(delta) <= delta_error)
                               | (np.abs(dot0) <= dot0_error)
                               | (np.abs(dot1) <= dot1_error))))
    for index in np.flatnonzero(uncertain):
        n[index], m[index] = _exact(lines[index], origin, radius)
    n.setflags(write=False)
    m.setflags(write=False)
    return n, m

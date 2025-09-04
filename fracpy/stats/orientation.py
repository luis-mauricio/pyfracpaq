from __future__ import annotations

from math import pi
from typing import Iterable, Tuple

import numpy as np

from ..types import Segment, TraceMap


def orientations_deg(segments: Iterable[Segment]) -> np.ndarray:
    """Return orientation angles (degrees) folded to [0, 180)."""
    return np.array([s.angle_deg() for s in segments], dtype=float)


def rose_hist(
    angles_deg: np.ndarray,
    bins: int = 18,
    bidirectional: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute a rose-diagram style histogram.

    - angles_deg: array of orientations in degrees (0..180 if bidirectional)
    - bins: number of bins around the circle (e.g., 18 → 10° bins)
    - bidirectional: if True, fold to 0..180 and mirror to 0..360

    Returns (theta, radii) suitable for polar bar plotting, where theta are
    bin centers in radians from 0..2π, and radii are counts per mirrored bin.
    """
    a = np.asarray(angles_deg, dtype=float)
    if bidirectional:
        a = np.mod(a, 180.0)
        # Mirror to 0..360 by duplicating with +180
        a_full = np.concatenate([a, (a + 180.0)])
        bins_deg = np.linspace(0.0, 360.0, bins + 1)
    else:
        a_full = np.mod(a, 360.0)
        bins_deg = np.linspace(0.0, 360.0, bins + 1)

    counts, edges = np.histogram(a_full, bins=bins_deg)
    centers_deg = (edges[:-1] + edges[1:]) / 2.0
    theta = np.deg2rad(centers_deg)
    return theta, counts.astype(float)


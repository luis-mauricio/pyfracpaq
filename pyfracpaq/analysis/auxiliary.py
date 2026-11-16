"""Complementary APIs; never add controls to the FracPaQ 2.8 main window.

Tensor16 follows Healy/Oda; probePlane intentionally retains its historical
origin and x>0 intersection convention, rather than silently correcting them.
"""

from dataclasses import dataclass

import numpy as np

from pyfracpaq.analysis.compatibility import readonly, cosd, sind
from pyfracpaq.analysis.tensors import TensorRank, _inputs
from pyfracpaq.geometry import IntersectionKind, segment_intersection
from pyfracpaq.geometry.primitives import Bounds, DEFAULT_MEMORY_LIMIT, point_array


def crack_tensor16(lengths, poles, area: float, *, interrupted=lambda: False) -> TensorRank:
    lengths, poles = _inputs(lengths, poles, area)
    weights = (lengths / np.sqrt(area)) ** 2
    directions = np.column_stack((cosd(poles), sind(poles)))
    moments = np.array([np.sum(weights * directions[:, 0] ** (16 - k) * directions[:, 1] ** k)
                        for k in range(17)])
    components = moments[np.fromiter((i.bit_count() for i in range(65536)), int)].reshape((2,) * 16)
    alpha = np.linspace(0, 2 * np.pi, 361)
    vectors = np.column_stack((np.cos(alpha), np.sin(alpha)))
    polar = np.zeros(361)
    for start in range(0, len(lengths), 1024):
        if interrupted():
            raise InterruptedError('Tensor16 cancelled.')
        polar += weights[start:start + 1024] @ (directions[start:start + 1024] @ vectors.T) ** 16
    if not np.isfinite(components).all() or not np.isfinite(polar).all():
        raise ValueError('Tensor16 exceeds float64 range.')
    return TensorRank(16, readonly(components), readonly(polar))


@dataclass(frozen=True, slots=True)
class ProbeResult:
    m: float
    m_ij: float
    mq: np.ndarray
    scanlines: np.ndarray


def probe_plane(plane: int, bounds: Bounds, segments, orientations: int,
                *, interrupted=lambda: False) -> ProbeResult:
    if plane not in (1, 2, 3) or isinstance(orientations, bool) \
            or not isinstance(orientations, int) or orientations < 2 or orientations % 2:
        raise ValueError('Probe plane needs plane 1/2/3 and a positive even orientation count.')
    segments = np.asarray(segments, float)
    if segments.ndim != 2 or segments.shape[1] != 4:
        raise ValueError('Probe segments must have four coordinates.')
    segments = point_array(segments[~np.isnan(segments).any(axis=1)], 4)
    if (len(segments) + orientations) * 256 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Probe data exceed the working memory budget.')
    length = .95 * min(bounds.width, bounds.height)
    if length <= 0:
        raise ValueError('Probe plane requires a two-dimensional domain.')
    centre = np.array([bounds.width / 2, bounds.height / 2])
    angles = np.arange(orientations) * np.pi / orientations
    offsets = np.column_stack((np.sin(angles), np.cos(angles)) if plane == 2
                               else (np.cos(angles), np.sin(angles))) * length / 2
    lines = np.column_stack((centre + offsets, centre - offsets))
    mq = np.zeros(orientations)
    for i, line in enumerate(lines):
        if interrupted():
            raise InterruptedError('Probe plane cancelled.')
        count = 0
        for segment in segments:
            hit = segment_intersection(line, segment)
            count += int(hit.kind == IntersectionKind.POINT and not hit.coincident and hit.points[0][0] > 0)
        # max(size(find(...))) in the source reports one even for an empty find.
        mq[i] = max(1, count) / length
    if plane == 2:
        half = orientations // 2
        mq = mq[np.r_[np.arange(half, -1, -1), np.arange(orientations - 1, half, -1)]]
    return ProbeResult(float(2 * np.pi * mq.sum() / orientations),
        float(np.pi * (mq * np.sin(2 * angles)).sum() / orientations), readonly(mq), readonly(lines))

"""ALONG intersections, circular sampling and signed FROM profiles.

Source ordering and repeated hits are retained. North/axis flips are display
options, not transformations of profile values. Q-20 finite circle predicates
are shared with Maps; P20 normalization is recorded with its scientific decision.
"""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from math import hypot, pi

import numpy as np
from numpy.typing import NDArray

from pyfracpaq.analysis.compatibility import readonly
from pyfracpaq.domain import Dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.geometry import GeometryError, IntersectionKind, segment_intersection
from pyfracpaq.geometry.circles import circle_counts
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT
from pyfracpaq.geometry.profiles import ProfileLine, signed_profile_distances

ALONG = ('GRA-03', 'GRA-04', 'GRA-05')
CIRCULAR = ('GRA-06', 'GRA-07')
FROM = ('GRA-10', 'GRA-11', 'GRA-12')
LOG = logging.getLogger(__name__)


def _integers(values) -> NDArray[np.int64]:
    result = np.array(values, dtype=np.int64, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class AlongProfile:
    points: NDArray[np.float64]
    distances: NDArray[np.float64]
    trace_lengths: NDArray[np.float64]
    segment_lengths: NDArray[np.float64]
    raw_angles: NDArray[np.float64]
    trace_ids: NDArray[np.int64]
    segment_ids: NDArray[np.int64]


def along_profile(dataset: Dataset, line: ProfileLine, *,
                   progress: Callable[[int, str], None] = lambda *_: None,
                   interrupted: Callable[[], bool] = lambda: False) -> AlongProfile:
    if dataset.n_segments * 256 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('ALONG profile exceeds the 256 MiB memory budget.')
    points, distances, traces, lengths, angles, tids, sids = [], [], [], [], [], [], []
    for index, segment in enumerate(dataset.segments):
        if interrupted():
            raise InterruptedError('ALONG intersections cancelled.')
        hit = segment_intersection(line.segment, (*segment.start.point, *segment.end.point))
        # The source excludes coincident supports, including collinear endpoint
        # contact. A shared noncollinear vertex is still one hit per segment.
        if hit.kind == IntersectionKind.POINT and not hit.coincident:
            point = hit.points[0]
            points.append(point)
            distances.append(hypot(point[0] - line.start[0], point[1] - line.start[1]))
            traces.append(dataset.traces[segment.trace_id].total_length)
            lengths.append(segment.length)
            angles.append(segment.raw_angle)
            tids.append(segment.trace_id)
            sids.append(segment.id)
        if index % max(1, dataset.n_segments // 100) == 0:
            progress(round(100 * (index + 1) / dataset.n_segments), 'Intersecting profile line...')
    return AlongProfile(readonly(np.asarray(points).reshape(-1, 2)), readonly(distances),
                         readonly(traces), readonly(lengths), readonly(angles),
                         _integers(tids), _integers(np.asarray(sids).reshape(-1, 2)))


@dataclass(frozen=True, slots=True)
class CircularProfile:
    centres: NDArray[np.float64]
    distances: NDArray[np.float64]
    radius: float
    intersections: NDArray[np.int64]
    endpoints_inside: NDArray[np.int64]
    intensity: NDArray[np.float64]
    density: NDArray[np.float64]


def circular_profile(dataset: Dataset, line: ProfileLine, count: int, *,
                      progress: Callable[[int, str], None] = lambda *_: None,
                      interrupted: Callable[[], bool] = lambda: False) -> CircularProfile:
    if isinstance(count, bool) or not isinstance(count, int) or count < 2:
        raise GeometryError('Use at least two scan circles along the line.')
    if dataset.n_segments * 1024 + count * 128 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Profile circles exceed the 256 MiB memory budget.')
    radius = line.length / count / 2
    with np.errstate(over='ignore', under='ignore', invalid='ignore'):
        denominators = np.array([4 * np.float64(radius), 2 * pi * np.square(np.float64(radius))])
    if radius <= 0 or not np.isfinite(denominators).all() or np.any(denominators <= 0):
        raise GeometryError('Circle radius or estimate denominators are unrepresentable.')
    fractions = (np.arange(count, dtype=float) + .5) / count
    centres = ((1 - fractions[:, None]) * np.asarray(line.start)
               + fractions[:, None] * np.asarray(line.end))
    if not np.isfinite(centres).all() or len(np.unique(centres, axis=0)) != count:
        raise GeometryError('Scan circle centres collapse at this coordinate scale.')
    distances = np.linspace(radius, line.length - radius, count)
    lines = dataset.as_arrays().segment_coordinates
    n, m = np.empty(count, dtype=np.int64), np.empty(count, dtype=np.int64)
    for index, centre in enumerate(centres):
        if interrupted():
            raise InterruptedError('Profile circles cancelled.')
        hits, endpoints = circle_counts(lines, centre, radius)
        n[index], m[index] = hits.sum(), endpoints.sum()
        if index % max(1, count // 100) == 0 or index + 1 == count:
            progress(round(100 * (index + 1) / count), 'Sampling profile circles...')
    intensity, density = n / denominators[0], m / denominators[1]
    if not np.isfinite(intensity).all() or not np.isfinite(density).all():
        raise GeometryError('Circular profile estimates exceed float64 range.')
    return CircularProfile(readonly(centres), readonly(distances), radius, _integers(n), _integers(m),
                            readonly(intensity), readonly(density))


@dataclass(frozen=True, slots=True)
class GraphResult:
    dataset: Dataset
    line: ProfileLine
    along: AlongProfile | None
    circles: CircularProfile | None
    trace_distances: NDArray[np.float64] | None
    segment_distances: NDArray[np.float64] | None


def compute_graphs(dataset: Dataset, context: RunContext,
                    progress: Callable[[int, str], None], *,
                    interrupted: Callable[[], bool] = lambda: False) -> GraphResult:
    config, line = context.config, context.config.profile_line
    if not isinstance(line, ProfileLine):
        raise FieldError('pushbutton_selectgraphendpoints', 'Select two distinct end points first.')
    if dataset.n_segments * 512 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Graph working data exceed the 256 MiB memory budget.')
    along = circles = td = sd = None
    if any(key in config.selected for key in ALONG):
        along = along_profile(dataset, line, interrupted=interrupted,
            progress=lambda value, message: progress(round(value * .4), message))
        LOG.info('ALONG: %d segment intersections in input order.', len(along.distances))
        if not len(along.distances):
            LOG.info('No noncoincident intersections with the selected finite line.')
    if any(key in config.selected for key in CIRCULAR):
        try:
            circles = circular_profile(dataset, line, int(float(config.value('edit_numscancirclesgraph'))),
                interrupted=interrupted,
                progress=lambda value, message: progress(40 + round(value * .5), message))
        except (GeometryError, MemoryError) as error:
            raise FieldError('edit_numscancirclesgraph', str(error)) from error
        LOG.info('ALONG: %d circles, radius=%g %s; P21=n/(4r), P20=m/(2*pi*r^2).',
                 len(circles.distances), circles.radius, dataset.length_unit)
    if any(key in config.selected for key in FROM):
        arrays = dataset.as_arrays()
        if 'GRA-10' in config.selected:
            td = signed_profile_distances(arrays.trace_midpoints, line)
        if any(key in config.selected for key in ('GRA-11', 'GRA-12')):
            sd = signed_profile_distances(arrays.segment_midpoints, line)
    if interrupted():
        raise InterruptedError('Graphs cancelled.')
    progress(100, 'Graphs completed.')
    return GraphResult(dataset, line, along, circles, td, sd)

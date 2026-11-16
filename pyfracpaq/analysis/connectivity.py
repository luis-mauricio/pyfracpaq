"""Trace-aware I/Y/X events, local endpoint proximity and source-style heatmaps.

Geometry is never rewritten. Junction coordinates are deduplicated exactly,
with incident trace/segment provenance; self intersections and positive-length
collinear overlaps are not inter-trace junctions.
"""

from collections.abc import Callable
from dataclasses import dataclass
from heapq import heappop, heappush
import logging
from math import hypot

import numpy as np
from numpy.typing import NDArray
from scipy.spatial import cKDTree

from pyfracpaq.analysis.compatibility import matlab_round, readonly
from pyfracpaq.domain import Dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.geometry import GeometryError, IntersectionKind, segment_intersection
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT, distance_point_segment, finite_number

LOG = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TopologyNodes:
    coordinates: NDArray[np.float64]
    trace_ids: tuple[tuple[int, ...], ...]
    segment_ids: tuple[tuple[tuple[int, int], ...], ...]


@dataclass(frozen=True, slots=True)
class Snap:
    endpoint_id: tuple[int, int]
    original: tuple[float, float]
    junction: tuple[float, float]
    target_segment_id: tuple[int, int]
    distance: float


@dataclass(frozen=True, slots=True)
class TopologyResult:
    dataset: Dataset
    i_nodes: TopologyNodes
    y_nodes: TopologyNodes
    x_nodes: TopologyNodes
    initial_counts: tuple[int, int, int]
    exact_pair_intersections: int
    overlap_pairs: int
    snaps: tuple[Snap, ...]

    @property
    def counts(self) -> tuple[int, int, int]:
        return tuple(len(nodes.coordinates) for nodes in (self.i_nodes, self.y_nodes, self.x_nodes))


def _node_set(records, segment_ids) -> TopologyNodes:
    points = sorted(records)
    return TopologyNodes(readonly(np.asarray(points).reshape(-1, 2)),
                         tuple(tuple(sorted(records[p]['traces'])) for p in points),
                         tuple(tuple(sorted(tuple(map(int, segment_ids[s]))
                                            for s in records[p]['segments'])) for p in points))


class _NearSegments:
    """Length-bucketed midpoint trees bound segment distance without NxM storage."""
    def __init__(self, coordinates, lengths, midpoints, trace_ids):
        self.coordinates, self.trace_ids = coordinates, trace_ids
        groups = np.floor(np.log2(lengths)).astype(int)
        self.trees = []
        for value in np.unique(groups):
            indices = np.flatnonzero(groups == value)
            self.trees.append((indices, float(lengths[indices].max() / 2), cKDTree(midpoints[indices])))

    def closest(self, point, owner, tolerance):
        best = None
        for indices, radius, tree in self.trees:
            for local in tree.query_ball_point(point, min(np.finfo(float).max, radius + tolerance), p=np.inf):
                index = int(indices[local])
                if self.trace_ids[index] == owner:
                    continue
                projection = distance_point_segment(point, self.coordinates[index, :2],
                                                    self.coordinates[index, 2:], reference_epsilon=False)
                if projection.distance <= tolerance:
                    key = (projection.distance, *projection.point, int(self.trace_ids[index]), index)
                    if best is None or key < best[0]:
                        best = key, index, projection
        return None if best is None else best[1:]


def classify_connectivity(dataset: Dataset, tolerance: float = 0, *,
                           progress: Callable[[int, str], None] = lambda *_: None,
                           interrupted: Callable[[], bool] = lambda: False) -> TopologyResult:
    tolerance = finite_number(tolerance, 'I-to-Y distance')
    if tolerance < 0:
        raise GeometryError('I-to-Y distance must be nonnegative.')
    arrays = dataset.as_arrays()
    lines, tids, sids = arrays.segment_coordinates, arrays.segment_trace_ids, arrays.segment_ids
    if len(lines) * 1024 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Connectivity exceeds the 256 MiB working memory budget.')
    ends, by_trace, end_segment = {}, {}, {}
    offset = 0
    for trace in dataset.traces:
        by_trace[trace.id] = []
        if trace.nodes[0].point != trace.nodes[-1].point:
            for node, segment in ((trace.nodes[0], offset),
                                   (trace.nodes[-1], offset + len(trace.segments) - 1)):
                ends[node.id] = node.point
                by_trace[trace.id].append(node.id)
                end_segment[node.id] = segment
        offset += len(trace.segments)
    events, connected = {}, set()
    raw_y = raw_x = pairs = overlaps = 0

    def event(point, participants, *, force_y=False):
        nonlocal raw_y, raw_x
        owners = {int(tids[s]) for s in participants}
        terminal = []
        for owner in owners:
            for endpoint in by_trace[owner]:
                if hypot(ends[endpoint][0] - point[0], ends[endpoint][1] - point[1]) <= tolerance:
                    terminal.append(endpoint)
        is_x = not terminal and not force_y
        raw_x += int(is_x)
        raw_y += int(not is_x)
        point = tuple(map(float, point))
        record = events.setdefault(point, {'traces': set(), 'segments': set(), 'x': False})
        record['traces'].update(owners)
        record['segments'].update(participants)
        record['x'] |= is_x
        connected.update(terminal)
        if len(events) * 1024 + len(lines) * 1024 > DEFAULT_MEMORY_LIMIT:
            raise MemoryError('Connectivity junctions exceed the 256 MiB working memory budget.')

    lower = np.minimum(lines[:, :2], lines[:, 2:])
    upper = np.maximum(lines[:, :2], lines[:, 2:])
    active, expiry = set(), []
    for step, i in enumerate(np.argsort(lower[:, 0], kind='stable')):
        if interrupted():
            raise InterruptedError('Connectivity cancelled.')
        while expiry and expiry[0][0] < lower[i, 0]:
            _, expired = heappop(expiry)
            active.discard(expired)
        if active:
            candidates = np.array(sorted(active), dtype=int)
            candidates = candidates[(tids[candidates] != tids[i])
                                    & (lower[candidates, 1] <= upper[i, 1])
                                    & (upper[candidates, 1] >= lower[i, 1])]
            for j in candidates:
                if interrupted():
                    raise InterruptedError('Connectivity cancelled.')
                hit = segment_intersection(lines[i], lines[j])
                if hit.kind == IntersectionKind.OVERLAP:
                    overlaps += 1
                elif hit.kind == IntersectionKind.POINT:
                    pairs += 1
                    event(hit.points[0], (int(i), int(j)))
        active.add(int(i))
        heappush(expiry, (float(upper[i, 0]), int(i)))
        if step % max(1, len(lines) // 100) == 0:
            progress(round(60 * (step + 1) / len(lines)), 'Connectivity: trace intersections...')
    snaps = []
    if tolerance > 0:
        near = _NearSegments(lines, arrays.segment_lengths, arrays.segment_midpoints, tids)
        for step, (endpoint, point) in enumerate(ends.items()):
            if interrupted():
                raise InterruptedError('Connectivity proximity cancelled.')
            if endpoint in connected:
                continue
            closest = near.closest(point, endpoint[0], tolerance)
            if closest is not None:
                target, projection = closest
                hit = segment_intersection(lines[end_segment[endpoint]], lines[target])
                if hit.kind == IntersectionKind.NONE:
                    event(projection.point, (end_segment[endpoint], target), force_y=True)
                    connected.add(endpoint)
                    snaps.append(Snap(endpoint, point, projection.point,
                                      tuple(map(int, sids[target])), projection.distance))
                # A nearby overshoot intersection was already classified above;
                # a distant intersection does not create a second inferred Y.
            if step % max(1, len(ends) // 100) == 0:
                progress(60 + round(30 * (step + 1) / max(1, len(ends))),
                         'Connectivity: checking endpoint proximity...')
    isolated = {}
    b = dataset.bounds
    initial_i = sum(endpoint not in connected for endpoint in ends)
    for endpoint, point in ends.items():
        if endpoint in connected or point[0] in (b.x_min, b.x_max) or point[1] in (b.y_min, b.y_max):
            continue
        record = isolated.setdefault(point, {'traces': set(), 'segments': set()})
        record['traces'].add(endpoint[0])
        record['segments'].add(end_segment[endpoint])
    y = {p: r for p, r in events.items() if not r['x']}
    x = {p: r for p, r in events.items() if r['x']}
    # Exact endpoint rows cannot survive at a junction, even with tolerance zero.
    isolated = {p: r for p, r in isolated.items() if p not in events}
    return TopologyResult(dataset, _node_set(isolated, sids), _node_set(y, sids), _node_set(x, sids),
                           (initial_i, raw_y, raw_x), pairs, overlaps, tuple(snaps))


@dataclass(frozen=True, slots=True)
class NodeHeatmap:
    values: NDArray[np.int64]
    x: NDArray[np.float64]
    y: NDArray[np.float64]
    extent: tuple[float, float, float, float]


def node_histogram(points, nx, ny, bounds) -> NodeHeatmap:
    """Source hist3(NBins): bins use each nonempty class's own coordinate range."""
    coordinates = np.asarray(points, dtype=float).reshape(-1, 2)
    centres, indices, extents = [], [], []
    for axis, count, low, high in ((0, nx, bounds.x_min, bounds.x_max),
                                    (1, ny, bounds.y_min, bounds.y_max)):
        if len(coordinates):
            low, high = float(coordinates[:, axis].min()), float(coordinates[:, axis].max())
            if low == high:
                low, high = low - np.floor(count / 2) - .5, high + np.ceil(count / 2) - .5
        step = (high - low) / count
        if not np.isfinite(step) or step <= 0:
            raise GeometryError('Connectivity heatmap spacing cannot be represented.')
        edges = low + np.arange(count + 1) * step
        centre = edges[:-1] + step / 2
        if not np.all(np.diff(centre) > 0):
            raise GeometryError('Connectivity heatmap centres collapse at this coordinate scale.')
        centres.append(readonly(centre))
        extents.extend((float(edges[0]), float(edges[-1])))
        indices.append(np.clip(np.searchsorted(edges, coordinates[:, axis], side='right') - 1, 0, count - 1))
    values = np.bincount(indices[1] * nx + indices[0], minlength=nx * ny).reshape(ny, nx)
    values.setflags(write=False)
    return NodeHeatmap(values, *centres, tuple(extents))


@dataclass(frozen=True, slots=True)
class ConnectivityResult:
    topology: TopologyResult
    xy_heatmap: NodeHeatmap
    i_heatmap: NodeHeatmap
    maximum: int


def connectivity_maps(topology: TopologyResult, blocks: int) -> ConnectivityResult:
    b = topology.dataset.bounds
    if isinstance(blocks, bool) or not isinstance(blocks, int) or blocks < 2:
        raise GeometryError('Use at least two blocks on the shorter side.')
    if b.width <= 0 or b.height <= 0:
        raise GeometryError('Connectivity heatmaps require a positive two-dimensional domain.')
    ratio = max(b.width, b.height) / min(b.width, b.height)
    if not np.isfinite(ratio) or ratio * blocks > DEFAULT_MEMORY_LIMIT / 64:
        raise MemoryError('Connectivity grid exceeds the 256 MiB memory budget.')
    long = int(matlab_round(ratio * blocks))
    nx, ny = (long, blocks) if b.width > b.height else (blocks, long)
    if nx * ny * 64 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Connectivity grid exceeds the 256 MiB memory budget.')
    xy = np.vstack((topology.x_nodes.coordinates, topology.y_nodes.coordinates))
    hxy = node_histogram(xy, nx, ny, b)
    hi = node_histogram(topology.i_nodes.coordinates, nx, ny, b)
    return ConnectivityResult(topology, hxy, hi, int(max(hxy.values.max(), hi.values.max())))


def compute_connectivity(dataset: Dataset, context: RunContext,
                         progress: Callable[[int, str], None], *,
                         interrupted: Callable[[], bool] = lambda: False) -> ConnectivityResult:
    from pyfracpaq.io.connectivity import export_connectivity
    config = context.config
    topology = classify_connectivity(dataset, float(config.value('edit_numpixelsItoY')),
                                      progress=progress, interrupted=interrupted)
    try:
        result = connectivity_maps(topology, int(float(config.value('edit_numblocksmap'))))
    except (GeometryError, MemoryError) as error:
        raise FieldError('edit_numblocksmap', str(error)) from error
    if interrupted():
        raise InterruptedError('Connectivity cancelled before export.')
    export_connectivity(topology.counts, config.tag, context.output_directory)
    LOG.info('Tolerance for accepting I node as Y: %g %s',
             float(config.value('edit_numpixelsItoY')), dataset.length_unit)
    LOG.info('Initial I/Y/X after proximity checks: %s', topology.initial_counts)
    ni, ny, nx = topology.counts
    total = ni + ny + nx
    LOG.info('After boundary/duplicate cleanup: I=%d, Y=%d, X=%d; total=%d', ni, ny, nx, total)
    LOG.info('Y:X:I = %s', f'{ny/total:.2f}:{nx/total:.2f}:{ni/total:.2f}' if total else 'undefined (total=0)')
    LOG.info('Exact segment pairs=%d; ignored overlapping pairs=%d; inferred endpoint junctions=%d',
             topology.exact_pair_intersections, topology.overlap_pairs, len(topology.snaps))
    progress(100, 'Connectivity completed.')
    return result

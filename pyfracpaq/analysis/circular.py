"""Circular P21/P20 sampling, independent of plotting and the GUI."""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from math import floor, isfinite, pi

import numpy as np
from numpy.typing import NDArray

from pyfracpaq.domain import Dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.geometry import Bounds, GeometryError
from pyfracpaq.geometry.circles import circle_counts
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT
from pyfracpaq.io.circular import export_circular


def _readonly(values, dtype=np.float64):
    result = np.array(values, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class CircleGrid:
    x: NDArray[np.float64]
    y: NDArray[np.float64]
    dx: float
    dy: float
    radius: float

    @property
    def shape(self) -> tuple[int, int]:
        return len(self.y), len(self.x)

    @property
    def centres(self) -> NDArray[np.float64]:
        """Original traversal/export order: X outermost, Y innermost."""
        return _readonly(np.column_stack((np.repeat(self.x, len(self.y)),
                                         np.tile(self.y, len(self.x)))))

    @property
    def extent(self) -> tuple[float, float, float, float]:
        # imagesc pixel edges, not the bounding rectangle of the full map.
        return (self.x[0] - self.dx / 2, self.x[-1] + self.dx / 2,
                self.y[0] - self.dy / 2, self.y[-1] + self.dy / 2)


def circle_grid(bounds: Bounds, count: int) -> CircleGrid:
    if isinstance(count, bool) or not isinstance(count, int) or count < 2:
        raise GeometryError('Use at least two circles on the shorter side.')
    width, height = bounds.x_max - bounds.x_min, bounds.y_max - bounds.y_min
    if not (isfinite(width) and isfinite(height) and width > 0 and height > 0
            and isfinite(width * height) and width * height > 0):
        raise GeometryError('Circular maps require finite positive width, height and area.')
    if count > DEFAULT_MEMORY_LIMIT // 128:
        raise GeometryError('Circular grid exceeds the sampling memory limit (256 MiB).')
    if width > height:
        ny = count
        dy = height / (ny + 1)
        radius = .99 * dy / 2
        dx = radius * 2 / .99
        ratio = width / dx if dx > 0 else float('inf')
        nx = floor(ratio - 1) if isfinite(ratio) else 0
    elif width < height:
        nx = count
        dx = width / (nx + 1)
        radius = .99 * dx / 2
        dy = radius * 2 / .99
        ratio = height / dy if dy > 0 else float('inf')
        ny = floor(ratio - 1) if isfinite(ratio) else 0
    else:
        nx = ny = count
        dx, dy = width / (nx + 1), height / (ny + 1)
        radius = .99 * min(dx, dy) / 2
    if (nx < 1 or ny < 1 or radius <= 0
            or nx * ny > DEFAULT_MEMORY_LIMIT // 128):
        raise GeometryError('Circular grid is unrepresentable or exceeds the sampling memory limit (256 MiB).')
    x, y = bounds.x_min + dx * np.arange(1, nx + 1), bounds.y_min + dy * np.arange(1, ny + 1)
    if (not np.isfinite(x).all() or not np.isfinite(y).all()
            or np.any(np.diff(x) <= 0) or np.any(np.diff(y) <= 0)
            or x[0] <= bounds.x_min or x[-1] >= bounds.x_max
            or y[0] <= bounds.y_min or y[-1] >= bounds.y_max):
        raise GeometryError('Circle centres cannot be represented at this coordinate scale.')
    return CircleGrid(_readonly(x), _readonly(y), dx, dy, radius)


@dataclass(frozen=True, slots=True)
class CircularResult:
    dataset: Dataset
    grid: CircleGrid
    intersections: NDArray[np.int64]
    endpoints_inside: NDArray[np.int64]
    intensity: NDArray[np.float64]
    density: NDArray[np.float64]
    global_intensity: float
    global_density: float


def sample_circles(dataset: Dataset, count: int, *,
                   progress: Callable[[int, str], None] = lambda *_: None,
                   interrupted: Callable[[], bool] = lambda: False) -> CircularResult:
    grid = circle_grid(dataset.bounds, count)
    denominators = 4 * grid.radius, 2 * pi * grid.radius ** 2
    if any(not isfinite(d) or d <= 0 for d in denominators):
        raise GeometryError('Circular estimates cannot be represented at this unit scale.')
    lines = dataset.as_arrays().segment_coordinates
    # Account conservatively for extended-precision vector temporaries too.
    if len(lines) * 1024 + len(grid.x) * len(grid.y) * 128 > DEFAULT_MEMORY_LIMIT:
        raise GeometryError('Circular sampling exceeds the working memory limit (256 MiB).')
    n, m = np.empty(grid.shape, dtype=np.int64), np.empty(grid.shape, dtype=np.int64)
    total = n.size
    for i, x in enumerate(grid.x):
        for j, y in enumerate(grid.y):
            if interrupted():
                raise InterruptedError('Circular sampling cancelled.')
            hits, endpoints = circle_counts(lines, (x, y), grid.radius)
            n[j, i], m[j, i] = hits.sum(), endpoints.sum()
            step = i * len(grid.y) + j + 1
            if step == total or step % max(1, total // 100) == 0:
                progress(round(100 * step / total), f'Circular scan windows: {step}/{total}')
    with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
        intensity, density = n / denominators[0], m / denominators[1]
    globals_ = dataset.total_length / dataset.area, dataset.n_segments / dataset.area
    if not (np.isfinite(intensity).all() and np.isfinite(density).all()
            and all(isfinite(value) for value in globals_)):
        raise GeometryError('Circular estimates cannot be represented at this unit scale.')
    return CircularResult(dataset, grid, _readonly(n, np.int64), _readonly(m, np.int64),
                          _readonly(intensity), _readonly(density), *globals_)


def compute_circular(dataset: Dataset, context: RunContext,
                     progress: Callable[[int, str], None], *,
                     interrupted: Callable[[], bool] = lambda: False) -> CircularResult:
    try:
        result = sample_circles(dataset, int(float(context.config.value('edit_numscancircles'))),
                                progress=progress, interrupted=interrupted)
    except GeometryError as error:
        raise FieldError('edit_numscancircles', str(error)) from error
    if interrupted():
        raise InterruptedError('Circular sampling cancelled.')
    export_circular(result.grid.centres, result.intensity.ravel(order='F'),
                    result.density.ravel(order='F'), context.config.tag,
                    context.output_directory)
    log = logging.getLogger(__name__)
    unit = 'metre' if dataset.pixels_per_metre is not None else 'pixel'
    log.info('Circular scan windows: increment X=%8.2E, Y=%8.2E, radius=%8.2E %ss',
             result.grid.dx, result.grid.dy, result.grid.radius, unit)
    if 'MAP-07' in context.config.selected:
        log.info('Global intensity of segments (P21): %8.2E %s^-1', result.global_intensity, unit)
    if 'MAP-08' in context.config.selected:
        log.info('Global density of segments (P20): %8.2E %s^-2', result.global_density, unit)
    return result

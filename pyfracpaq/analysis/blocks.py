"""White 8-connected components and calibrated areas/centres (Q-14)."""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from pyfracpaq.analysis.compatibility import readonly
from pyfracpaq.analysis.lengths import complementary_distribution, length_histogram
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT


def _frozen(values, dtype):
    result = np.array(values, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class Components:
    binary: np.ndarray
    pixel_areas: np.ndarray
    pixel_centroids: np.ndarray
    touches_border: np.ndarray
    threshold: float


def white_components(image) -> Components:
    """MATLAB graythresh plateau averaging; column-major component ordering.

    RGB BMPs should first be converted to L; native indexed BMPs must retain
    their indices when reproducing source imbinarize(indexed), as in fixtures.
    Centroids follow regionprops' one-based (column,row) pixel convention.
    """
    image = np.asarray(image)
    if image.ndim != 2 or image.dtype != np.uint8 or not image.size:
        raise ValueError('Block raster must be a nonempty 8-bit grayscale image.')
    if image.size * 64 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Block components exceed the 256 MiB memory budget.')
    histogram = np.bincount(image.ravel(), minlength=256).astype(float)
    probabilities = histogram / image.size
    omega = np.cumsum(probabilities)
    mu = np.cumsum(probabilities * np.arange(1, 257))
    denominator = omega * (1 - omega)
    variance = np.full(256, np.nan)
    np.divide((mu[-1] * omega - mu) ** 2, denominator,
              out=variance, where=denominator > 0)
    finite = np.isfinite(variance)
    threshold = (float(np.flatnonzero(variance == np.nanmax(variance)).mean()) / 255
                 if finite.any() else 0.)
    binary = image.astype(float) / 255 > threshold
    labels, count = ndimage.label(binary, structure=np.ones((3, 3), dtype=bool))
    ids = np.arange(1, count + 1)
    areas = np.bincount(labels.ravel(), minlength=count + 1)[1:]
    # scipy scans rows; MATLAB bwconncomp scans columns. Reorder explicitly.
    first = np.full(count + 1, labels.size, dtype=np.int64)
    np.minimum.at(first, labels.ravel(order='F'), np.arange(labels.size))
    order = np.argsort(first[1:], kind='stable')
    if count:
        centres = np.asarray(ndimage.center_of_mass(binary, labels, ids))[:, ::-1] + 1
    else:
        centres = np.empty((0, 2))
    border_ids = np.unique(np.concatenate((labels[0], labels[-1], labels[:, 0], labels[:, -1])))
    return Components(_frozen(binary, bool), _frozen(areas[order], np.int64),
        readonly(centres[order]), _frozen(np.isin(ids, border_ids)[order], bool), threshold)


@dataclass(frozen=True, slots=True)
class BlockResult:
    dataset: object
    raster: np.ndarray
    components: Components
    kept: np.ndarray
    areas: np.ndarray
    centroids: np.ndarray
    pixel_size: tuple[float, float]
    histogram: object | None
    complementary: object | None


def compute_blocks(dataset, *, exclude_border: bool,
                   progress=lambda *_: None, interrupted=lambda: False) -> BlockResult:
    """Explicit border policy; the approved Run population excludes border regions."""
    from pyfracpaq.io.block_raster import rasterize_blocks

    if interrupted():
        raise InterruptedError('Block raster cancelled.')
    progress(10, 'Rasterizing block boundaries at fixed input resolution...')
    raster, low, high = rasterize_blocks(dataset)
    if interrupted():
        raise InterruptedError('Block components cancelled.')
    progress(40, 'Binarizing and labeling white 8-connected components...')
    components = white_components(raster)
    keep = ~components.touches_border if exclude_border else np.ones(len(components.pixel_areas), bool)
    dx, dy = (high[0] - low[0]) / raster.shape[1], (high[1] - low[1]) / raster.shape[0]
    areas = components.pixel_areas[keep] * dx * dy
    centres = components.pixel_centroids[keep]
    world = np.column_stack((low[0] + (centres[:, 0] - .5) * dx,
                             high[1] - (centres[:, 1] - .5) * dy))
    if not np.isfinite(areas).all() or np.any(areas <= 0) or not np.isfinite(world).all():
        raise ValueError('Calibrated block areas/centres exceed float64 range.')
    histogram = length_histogram(areas, 30) if len(areas) else None
    complementary = complementary_distribution(areas, scaled=True) if len(areas) else None
    if interrupted():
        raise InterruptedError('Block statistics cancelled.')
    progress(100, f'Block statistics: {len(areas)} enclosed components.')
    return BlockResult(dataset, raster, components, _frozen(keep, bool), readonly(areas),
                        readonly(world), (dx, dy), histogram, complementary)

"""Six photographic preparation stages from FracPaQ2D_imagePreprocess.

MATLAB conventions: RGB weights, even 20x20 zero-padded median with averaged
middle ranks, saturating uint8 subtraction, Sobel RMS cutoff and strict cross
maxima, 3x3 closing, Guo-Hall thinning to convergence and inversion.
"""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage
from skimage.morphology import thin

from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT


@dataclass(frozen=True, slots=True)
class PreprocessResult:
    grayscale: np.ndarray
    median: np.ndarray
    difference: np.ndarray
    edges: np.ndarray
    closed: np.ndarray
    processed: np.ndarray


def sobel_edges(image) -> np.ndarray:
    """Source RMS threshold and strict maxima on the dominant gradient axis."""
    image = np.asarray(image)
    values = image.astype(float) / 255 if image.dtype == np.uint8 else np.asarray(image, float)
    if values.ndim != 2 or not values.size or not np.isfinite(values).all():
        raise ValueError('Sobel input must be a finite two-dimensional image.')
    gx = ndimage.sobel(values, axis=1, mode='nearest') / 8
    gy = ndimage.sobel(values, axis=0, mode='nearest') / 8
    squared = gx ** 2 + gy ** 2
    cutoff = 4 * squared.mean()
    left = ndimage.shift(squared, (0, 1), order=0, mode='nearest')
    right = ndimage.shift(squared, (0, -1), order=0, mode='nearest')
    up = ndimage.shift(squared, (1, 0), order=0, mode='nearest')
    down = ndimage.shift(squared, (-1, 0), order=0, mode='nearest')
    return (((abs(gx) >= abs(gy)) & (squared > left) & (squared > right))
            | ((abs(gy) >= abs(gx)) & (squared > up) & (squared > down))) & (squared > cutoff)


def preprocess_image(image, *, progress=lambda *_: None, interrupted=lambda: False):
    image = np.asarray(image)
    if image.dtype != np.uint8 or image.ndim not in (2, 3) \
            or (image.ndim == 3 and image.shape[2] != 3) or not image.size:
        raise ValueError('Preprocessing requires a grayscale or RGB uint8 image; no alpha channel.')
    if image.size * 128 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Image preprocessing exceeds the 256 MiB memory budget.')
    if interrupted():
        raise InterruptedError('Image preprocessing cancelled.')
    gray = image.copy() if image.ndim == 2 else np.floor(
        image @ np.array([.298936021293776, .587043074451121, .114020904255103]) + .5).astype(np.uint8)
    progress(10, 'Grayscale conversion...')
    lower = ndimage.rank_filter(gray, 199, size=20, mode='constant', cval=0, origin=-1)
    upper = ndimage.rank_filter(gray, 200, size=20, mode='constant', cval=0, origin=-1)
    median = np.floor((lower.astype(float) + upper) / 2 + .5).astype(np.uint8)
    difference = np.maximum(median.astype(np.int16) - gray, 0).astype(np.uint8)
    if interrupted():
        raise InterruptedError('Image preprocessing cancelled.')
    progress(50, 'Sobel edges...')
    edges = sobel_edges(difference)
    closed = ndimage.binary_erosion(ndimage.binary_dilation(edges, structure=np.ones((3, 3))),
                                     structure=np.ones((3, 3)), border_value=1)
    progress(80, 'Thinning and inversion...')
    processed = ~thin(closed)
    if interrupted():
        raise InterruptedError('Image preprocessing cancelled before export.')
    outputs = [gray, median, difference, edges, closed, processed]
    for array in outputs:
        array.setflags(write=False)
    progress(100, 'Image preparation finished.')
    return PreprocessResult(*outputs)

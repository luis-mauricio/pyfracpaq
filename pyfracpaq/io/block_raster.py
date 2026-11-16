"""Deterministic, offscreen scientific raster and the visible legacy BMP.

No Qt/pyplot, screen dimensions or global rc mutations are involved. Resolution
is fixed in input coordinates, independently of physical calibration.
"""

import os
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image

from pyfracpaq.domain import Dataset
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT


def rasterize_blocks(dataset: Dataset):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    points = np.array([point for trace in dataset.source_traces for point in trace.points])
    low, high = points.min(axis=0), points.max(axis=0)
    spans = high - low
    if not np.isfinite(spans).all() or np.any(spans <= 0):
        raise ValueError('Block analysis requires a finite, two-dimensional envelope.')
    width, height = (int(np.ceil(value)) for value in spans)
    if width * height * 64 + len(points) * 128 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Block raster exceeds the 256 MiB memory budget. '
                          'Review the input coordinate resolution.')
    # A tiny positive offset avoids float rounding truncating integer dimensions
    # inside RendererAgg; data limits remain the exact input envelope.
    figure = Figure(figsize=((width + 1e-7) / 300, (height + 1e-7) / 300),
                    dpi=300, facecolor='white')
    canvas = FigureCanvasAgg(figure)
    axes = figure.add_axes((0, 0, 1, 1), facecolor='white')
    axes.set(xlim=(low[0], high[0]), ylim=(low[1], high[1]), aspect='auto')
    axes.set_axis_off()
    for trace in dataset.source_traces:
        xy = np.asarray(trace.points)
        axes.plot(xy[:, 0], xy[:, 1], color='black', linewidth=.5,
                  antialiased=True, snap=False, solid_capstyle='butt',
                  solid_joinstyle='round')
    canvas.draw()
    image = np.asarray(canvas.buffer_rgba())[:, :, 0].copy()
    figure.clear()
    if image.shape != (height, width):
        raise RuntimeError('Unexpected block raster dimensions.')
    image.setflags(write=False)
    scale = dataset.pixels_per_metre or 1.
    return image, tuple(low / scale), tuple(high / scale)


def export_block_raster(image, directory: Path | str) -> Path:
    """Keep the fixed public BMP name; remove only our own temporary file."""
    directory = Path(directory).resolve()
    target = directory / 'FracPaQ2D_blocksize.bmp'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.pyfracpaq-', suffix='.bmp',
                                         dir=directory, delete=False) as stream:
            temporary = Path(stream.name)
            Image.fromarray(image).save(stream, format='BMP')
        os.replace(temporary, target)
        return target
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()

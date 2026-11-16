"""Wavelet raster and theta exports; fixed raster name and tagged scale TXT."""

import os
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image

from pyfracpaq.io.figures import validate_tag


def rasterize_wavelets(dataset):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(27, 27), dpi=72, facecolor='white')
    canvas = FigureCanvasAgg(figure)
    axes = figure.add_axes((.13, .11, .775, .815), facecolor='white')
    points = np.asarray([node.point for node in dataset.nodes])
    low, high = points.min(axis=0), points.max(axis=0)
    for i in range(2):
        if low[i] == high[i]:
            pad = max(1., abs(low[i])) * .05
            low[i] -= pad
            high[i] += pad
    axes.set(xlim=(low[0], high[0]), ylim=(low[1], high[1]), aspect='equal')
    axes.set_axis_off()
    maximum = max(trace.total_length for trace in dataset.traces)
    for trace in dataset.traces:
        xy = np.asarray([node.point for node in trace.nodes])
        axes.plot(xy[:, 0], xy[:, 1], color='black',
                  linewidth=4 if trace.total_length >= maximum * .45 else 1,
                  solid_capstyle='butt', solid_joinstyle='round', antialiased=True, snap=False)
    canvas.draw()
    image = np.asarray(canvas.buffer_rgba())[:, :, 0].copy()
    figure.clear()
    image.setflags(write=False)
    return image


def normalize_raster(image):
    image = np.asarray(image)
    if image.ndim != 2 or min(image.shape) < 2 or image.dtype != np.uint8:
        raise ValueError('Wavelet raster must be a grayscale uint8 image at least 2 by 2.')
    maximum = int(image.max())
    if maximum == 0:
        raise ValueError('A wholly black raster has no representable source normalization.')
    return (maximum - image.astype(float)) / maximum


def _atomic(target: Path, writer):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.pyfracpaq-', suffix=target.suffix,
                                         dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            writer(stream)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def export_wavelets(result, tag: str, directory, *, raster=None, auxiliary=False):
    validate_tag(tag)
    directory = Path(directory).resolve()
    outputs = []
    if raster is not None:
        target = directory / 'FracPaQ2D_wavelet_traces.png'
        _atomic(target, lambda stream: Image.fromarray(raster).save(stream, format='PNG', dpi=(72, 72)))
        outputs.append(target)
    for scale in result.scales:
        suffix = '' if auxiliary else '_' + tag
        target = directory / f'FracPaQ2Dwavelet_theta_a{scale.scale}{suffix}.txt'
        def write(stream, values=scale.doubled_degrees):
            np.savetxt(stream, values, fmt='%g')
        _atomic(target, write)
        outputs.append(target)
    return tuple(outputs)

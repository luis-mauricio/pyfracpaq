"""Wavelet subplot-local colourbars preserve alignment/physical clearance."""

from dataclasses import replace

from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from PIL import Image
import pytest

from pyfracpaq.analysis.wavelets import analyse_wavelet_image, WaveletParameters
from pyfracpaq.io.figures import export_png
from pyfracpaq.plots.wavelets import render_wavelets
from reference_common import REFERENCE
from sprint3_reference import reference_config


@pytest.mark.parametrize('shape', [(8, 8), (6, 10)])
@pytest.mark.parametrize('flips', [False, True])
def test_all_wavelet_panels_and_two_vertical_bars_at_all_sizes(tmp_path, shape, flips):
    image = np.zeros(shape);image[2, 2:-1] = 1
    result = analyse_wavelet_image(image, WaveletParameters((2,), (2,), 45, 'morlet'), flip_x=flips, flip_y=flips)
    config = replace(reference_config(('WAV-01',)), flip_x=flips, flip_y=flips)
    output, = render_wavelets(result, config)
    assert output.basename == 'FracPaQ2Dwavelet_a2'
    figure = output.figure;canvas = FigureCanvasAgg(figure)
    assert len(figure.axes) == 6
    assert [axes.get_title().strip() for axes in (figure.axes[0], figure.axes[2])] == ['Binary image', 'WC map, a=2']
    for size in ((8, 8), (12, 5), (5, 12), (4, 3.2), (8, 8)):
        figure.set_size_inches(*size);canvas.draw()
        for host, bar in ((figure.axes[0], figure.axes[1]), (figure.axes[2], figure.axes[3])):
            p, b = host.get_window_extent(), bar.get_window_extent()
            np.testing.assert_allclose([p.y0, p.y1], [b.y0, b.y1], atol=1e-8, rtol=0)
            tight = host.yaxis.get_tightbbox(canvas.get_renderer())
            right = max(p.x1, tight.x1)
            gap = (b.x0 - right) / canvas.get_renderer().points_to_pixels(1)
            assert gap == pytest.approx(25, abs=1e-7)
            assert host.xaxis_inverted() == flips
            assert host.yaxis_inverted() != flips
    path = export_png(figure, output.basename, 'bars', tmp_path)
    with Image.open(path) as image:
        assert image.size == (4724, 4724)
    figure.clear()

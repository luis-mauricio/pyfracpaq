"""Live Qt canvas resizes share responsive colourbar geometry with PNG export."""

import numpy as np
import pytest
from PySide6.QtWidgets import QMainWindow

from pyfracpaq.app import configure_application
from pyfracpaq.gui.figures import FigureWindow
from pyfracpaq.plots.colourbars import colourbar
from pyfracpaq.plots.style import figure_axes
from matplotlib.transforms import Bbox


@pytest.mark.parametrize('location', ['bottom', 'right'])
def test_live_figure_window_bar_tracks_plot_after_growing_and_shrinking(qapp, qtbot, location):
    configure_application(qapp)
    figure, host = figure_axes((.2, .25, .55, .5))
    host.set_box_aspect(1)
    host.set_xlabel('X coordinate, metres')
    host.set_ylabel('Y coordinate, metres')
    if location == 'right':
        host.yaxis.set_label_position('right')
        host.yaxis.tick_right()
    bar = colourbar(host, location=location)
    bar.set_label('Estimated quantity, metre$^{-1}$')
    owner = QMainWindow()
    qtbot.addWidget(owner)
    window = FigureWindow(figure, 'Responsive colourbar', owner)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    for width, height in ((700, 700), (1100, 450), (340, 280), (450, 900), (600, 600)):
        window.resize(width, height)
        qapp.processEvents()
        window.canvas.draw()
        renderer = window.canvas.get_renderer()
        a, b = host.get_window_extent(renderer), bar.ax.get_window_extent(renderer)
        expected, actual = ((a.x0, a.x1), (b.x0, b.x1)) if location == 'bottom' else (
            (a.y0, a.y1), (b.y0, b.y1))
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-8)
        axis = host.xaxis if location == 'bottom' else host.yaxis
        facing = Bbox.union([a, axis.get_tightbbox(renderer)])
        gap = facing.y0 - b.y1 if location == 'bottom' else b.x0 - facing.x1
        assert gap / renderer.points_to_pixels(1) == pytest.approx(25, abs=1e-8)
    window.showMaximized()
    qapp.processEvents()
    window.canvas.draw()
    renderer = window.canvas.get_renderer()
    a, b = host.get_window_extent(renderer), bar.ax.get_window_extent(renderer)
    axis = host.xaxis if location == 'bottom' else host.yaxis
    facing = Bbox.union([a, axis.get_tightbbox(renderer)])
    gap = facing.y0 - b.y1 if location == 'bottom' else b.x0 - facing.x1
    assert gap / renderer.points_to_pixels(1) == pytest.approx(25, abs=1e-8)

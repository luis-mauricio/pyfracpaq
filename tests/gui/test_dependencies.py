"""Verify Qt Widgets, pytest-qt and QtAgg without claiming GUI parity."""

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QApplication


def test_qt_and_matplotlib_render_together(qtbot):
    QApplication.setStyle('Fusion')
    figure = Figure(figsize=(3, 2), dpi=100)
    axes = figure.add_subplot()
    axes.plot([0, 1, 2], [0, 1, 0], color='black')
    canvas = FigureCanvasQTAgg(figure)
    qtbot.addWidget(canvas)
    canvas.draw()
    pixels = np.asarray(canvas.buffer_rgba())
    assert pixels.shape == (200, 300, 4)
    assert np.any(pixels[:, :, :3] < 100)
    assert np.any(pixels[:, :, :3] > 240)

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6 import QtCore, QtGui


class MplCanvas(FigureCanvas):
    def __init__(self, width: float = 5, height: float = 4, dpi: int = 100, polar: bool = False):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        if polar:
            self.ax = self.figure.add_subplot(111, projection="polar")
        else:
            self.ax = self.figure.add_subplot(111)
        # Initialize QWidget/QT base before using QWidget methods
        super().__init__(self.figure)
        # Avoid transparent repaints that can show seam artifacts
        self.figure.set_facecolor("white")
        try:
            self.ax.set_facecolor("white")
        except Exception:
            pass
        # Improve autosizing of the axes within the available canvas area
        try:
            self.figure.set_constrained_layout(True)
        except Exception:
            pass
        # Hint Qt that we paint opaquely to reduce edge artifacts
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent, True)

    def set_placeholder_background(self, color: QtGui.QColor) -> None:
        """Set a neutral background and hide axes for placeholder state.

        The color should typically come from the surrounding Qt palette.
        """
        try:
            rgb = (color.redF(), color.greenF(), color.blueF())
            self.figure.set_facecolor(rgb)
            self.ax.set_facecolor(rgb)
        except Exception:
            # Fallback to a light gray if no QColor provided
            self.figure.set_facecolor((0.9, 0.9, 0.9))
            self.ax.set_facecolor((0.9, 0.9, 0.9))
        self.ax.axis('off')
        self.draw_idle()

    def set_plot_background_white(self) -> None:
        """Set a white plot background and show axes for plotted state."""
        self.figure.set_facecolor("white")
        try:
            self.ax.set_facecolor("white")
        except Exception:
            pass
        self.ax.axis('on')
        self.draw_idle()

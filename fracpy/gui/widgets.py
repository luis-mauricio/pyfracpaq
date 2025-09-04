from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):
    def __init__(self, width: float = 5, height: float = 4, dpi: int = 100, polar: bool = False):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        if polar:
            self.ax = self.figure.add_subplot(111, projection="polar")
        else:
            self.ax = self.figure.add_subplot(111)
        super().__init__(self.figure)


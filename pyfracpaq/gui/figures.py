"""Independent figure windows owned exclusively by the application window."""

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg, NavigationToolbar2QT,
)
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget


class FigureWindow(QMainWindow):
    def __init__(self, figure: Figure, title: str, owner: QMainWindow) -> None:
        super().__init__(owner, Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(title)
        self._close_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Close), self)
        self._close_shortcut.activated.connect(self.close)
        self.canvas = FigureCanvasQTAgg(figure)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setCentralWidget(content)
        self.resize(700, 700)

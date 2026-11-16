"""Local Qt entrypoint and singleton main-window lifecycle."""

import logging
import sys

from PySide6.QtGui import QColor, QFontDatabase, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QStyleFactory
from shiboken6 import isValid

from pyfracpaq import __version__
from pyfracpaq.gui import MainWindow
from pyfracpaq.gui.controls import reference_font
from pyfracpaq.gui.style import ReferenceStyle
from pyfracpaq.resources import resource_bytes, resource_text

_window: MainWindow | None = None


def configure_application(app: QApplication) -> None:
    app.setApplicationName('PyFracPaQ')
    app.setApplicationVersion(__version__)
    app.setStyle(ReferenceStyle(QStyleFactory.create('Fusion')))
    palette = QPalette()
    for role, colour in ((QPalette.ColorRole.Window, '#f0f0f0'),
                         (QPalette.ColorRole.WindowText, '#171717'),
                         (QPalette.ColorRole.Base, '#ffffff'),
                         (QPalette.ColorRole.Text, '#171717'),
                         (QPalette.ColorRole.Button, '#fafafa'),
                         (QPalette.ColorRole.ButtonText, '#171717'),
                         (QPalette.ColorRole.Highlight, '#3975ab'),
                         (QPalette.ColorRole.HighlightedText, '#ffffff')):
        palette.setColor(role, QColor(colour))
    app.setPalette(palette)
    font = reference_font()
    if font.family() not in QFontDatabase.families():
        fallback = 'Arial' if 'Arial' in QFontDatabase.families() else 'DejaVu Sans'
        logging.getLogger(__name__).warning('%s unavailable; using %s.', font.family(), fallback)
        font.setFamily(fallback)
    app.setFont(font)
    app.setStyleSheet(resource_text('base.qss'))
    pixmap = QPixmap()
    pixmap.loadFromData(resource_bytes('FracPaQicon.jpeg'))
    app.setWindowIcon(QIcon(pixmap))


def create_main_window() -> MainWindow:
    global _window
    if _window is None or not isValid(_window):
        _window = MainWindow()
    _window.show()
    _window.raise_()
    _window.activateWindow()
    return _window


def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
    app = QApplication.instance() or QApplication(sys.argv)
    configure_application(app)
    create_main_window()
    return app.exec()

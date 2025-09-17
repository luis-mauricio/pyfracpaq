from __future__ import annotations

import sys

from PySide6 import QtCore, QtWidgets as QtW

from .main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    app = QtW.QApplication(sys.argv if argv is None else argv)
    win = MainWindow()
    # Show first
    win.show()
    # Defer maximize to next tick to satisfy some Ubuntu/Wayland WMs
    def _force_maximize():
        win.setWindowState(win.windowState() | QtCore.Qt.WindowMaximized)
        win.raise_()
        win.activateWindow()
    QtCore.QTimer.singleShot(0, _force_maximize)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

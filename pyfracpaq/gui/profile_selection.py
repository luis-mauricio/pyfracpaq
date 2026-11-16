"""Two clicks on the cached preview; no re-import or image-specific reader path."""

from collections.abc import Callable
from math import isfinite

from matplotlib.backend_bases import MouseButton
from PySide6.QtCore import Qt

from pyfracpaq.geometry import GeometryError
from pyfracpaq.geometry.profiles import ProfileLine


class ProfilePicker:
    def __init__(self, canvas, *, changed: Callable[[], None],
                 status: Callable[[str], None], can_pick: Callable[[], bool]) -> None:
        self.canvas, self.changed, self.status, self.can_pick = canvas, changed, status, can_pick
        self.line: ProfileLine | None = None
        self.pending: tuple[float, float] | None = None
        self.active = False
        canvas.mpl_connect('button_press_event', self._click)
        canvas.mpl_connect('key_press_event', self._key)

    def start(self) -> None:
        if not self.can_pick():
            return
        self.pending, self.active = None, True
        self.canvas.setCursor(Qt.CursorShape.CrossCursor)
        self.canvas.setFocus()
        self.changed()
        self.status('Select point 1 on the preview. Escape cancels selection.')

    def clear(self) -> None:
        self.line, self.pending, self.active = None, None, False
        self.canvas.unsetCursor()

    def cancel(self) -> None:
        if self.active:
            self.pending, self.active = None, False
            self.canvas.unsetCursor()
            self.changed()
            self.status('Line selection cancelled.')

    def _key(self, event) -> None:
        if event.key == 'escape':
            self.cancel()

    def _click(self, event) -> None:
        if not self.active or not self.can_pick():
            return
        if event.button == MouseButton.RIGHT:
            self.cancel()
            return
        axes = self.canvas.figure.axes[0] if self.canvas.figure.axes else None
        if event.button != MouseButton.LEFT or event.inaxes is not axes \
                or event.xdata is None or event.ydata is None:
            return
        point = float(event.xdata), float(event.ydata)
        if not all(isfinite(value) for value in point):
            return
        if self.pending is None:
            self.pending = point
            self.changed()
            self.status('Select point 2, distinct from point 1.')
            return
        try:
            selected = ProfileLine(self.pending, point)
        except GeometryError:
            self.status('Select a second point distinct from point 1.')
            return
        self.line, self.pending, self.active = selected, None, False
        self.canvas.unsetCursor()
        self.changed()
        self.status('Profile line selected. Click Run to generate profiles.')

    def draw(self, axes) -> None:
        if self.active and self.pending is not None:
            axes.plot(*self.pending, marker='s', color='red', markerfacecolor='none', zorder=5)
        elif not self.active and self.line is not None:
            axes.plot([self.line.start[0], self.line.end[0]],
                      [self.line.start[1], self.line.end[1]], '-sr', linewidth=1,
                      markerfacecolor='none', zorder=5)

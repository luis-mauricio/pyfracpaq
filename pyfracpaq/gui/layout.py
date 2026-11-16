"""Parent-relative FIG geometry, without layout-driven control redistribution."""

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QGroupBox, QLabel, QLineEdit,
    QRadioButton, QStackedWidget, QWidget,
)

from .controls import Controls, PANELS

# Client aspect measured in the supplied manual screenshots (Retina / 2).
# FIG root units are characters, so treating them as pixels would be incorrect.
REFERENCE_SIZE = QSize(1250, 739)
MINIMUM_BOARD_SIZE = QSize(1000, 591)


def initial_window_size(available: QSize) -> QSize:
    """Open as a normal, centred window with room for OS chrome on this screen."""
    factor = min(1., .9 * available.width() / REFERENCE_SIZE.width(),
                 .9 * max(1, available.height() - 32) / REFERENCE_SIZE.height())
    return QSize(max(1, round(REFERENCE_SIZE.width() * factor)),
                 max(1, round(REFERENCE_SIZE.height() * factor)))


def reference_rect(position, width: int, height: int) -> QRect:
    x, y, w, h = position
    return QRect(round(x * width), round((1 - y - h) * height),
                 round(w * width), round(h * height))


class ReferenceBoard(QWidget):
    def __init__(self, controls: Controls) -> None:
        super().__init__()
        self.controls = controls
        self.setMinimumSize(MINIMUM_BOARD_SIZE)
        self.anchors: dict[str, tuple[QWidget, list[float]]] = {}
        self.children_by_parent: dict[str, list[str]] = {}

    def anchor(self, name: str, widget: QWidget) -> None:
        widget.setParent(self)
        self.anchors[name] = widget, self.controls.specs[name]['Position']

    def resizeEvent(self, event) -> None:
        self.apply_geometry()
        super().resizeEvent(event)

    def apply_geometry(self) -> None:
        scale = min(1., self.width() / REFERENCE_SIZE.width(),
                    self.height() / REFERENCE_SIZE.height())
        for name, widget in self.controls.widgets.items():
            spec = self.controls.specs[name]
            if spec['type'] in ('axes', 'figure'):
                continue
            font = QFont(widget.font())
            font.setPixelSize(max(8, round(spec.get('FontSize', 12) * scale)))
            font.setBold(spec.get('FontWeight') == 'bold')
            widget.setFont(font)
        for name, (widget, position) in self.anchors.items():
            rect = reference_rect(position, self.width(), self.height())
            if name == 'axes_tracemap':
                # Position is the data rectangle, not the whole Matplotlib canvas.
                rect.adjust(-round(48 * scale), -round(8 * scale),
                            round(12 * scale), round(36 * scale))
            widget.setGeometry(rect)

        def descendants(parent_name: str) -> None:
            parent = self.controls[parent_name]
            inner = parent.rect()
            if isinstance(parent, QGroupBox) and parent.property('referenceBorder') != 'none':
                # GUIDE coordinates use the panel's inner drawable area. Qt's
                # style has different title metrics; keep children below it.
                font = QFont(parent.font())
                while (font.pixelSize() > 8 and parent.fontMetrics().horizontalAdvance(
                        parent.title().replace('&&', '&')) + 16 > parent.width()):
                    font.setPixelSize(font.pixelSize() - 1)
                    parent.setFont(font)
                inner.adjust(2, parent.fontMetrics().height() + 2, -2, -2)
            for name in self.children_by_parent.get(parent_name, ()):
                widget = self.controls[name]
                rect = reference_rect(self.controls.specs[name]['Position'],
                                      inner.width(), inner.height())
                rect.translate(inner.topLeft())
                rect = rect.intersected(inner)
                widget.setGeometry(rect)
                descendants(name)

        for name in self.anchors:
            if name != 'uibgTabMaps':
                descendants(name)
        # All pages occupy Maps' opening rectangle; hidden pages keep their size.
        for name in PANELS:
            self.controls[name].resize(self.anchors['uibgTabMaps'][0].size())
            descendants(name)
        for widget in self.controls.widgets.values():
            if isinstance(widget, QLabel) and widget.buddy() is not None:
                buddy = widget.buddy()
                if (buddy.parentWidget() is widget.parentWidget()
                        and widget.geometry().intersects(buddy.geometry())
                        and buddy.x() > widget.x()):
                    widget.resize(max(1, buddy.x() - widget.x() - 3), widget.height())
                # Some FIG labels deliberately overrun the neighbouring field
                # or clip their second line. Fit those few labels locally.
                rect = widget.fontMetrics().boundingRect(
                    QRect(0, 0, widget.width(), 10000), Qt.TextFlag.TextWordWrap, widget.text())
                if rect.height() > widget.height():
                    widget.resize(widget.width(), rect.height())
            elif isinstance(widget, (QCheckBox, QRadioButton)):
                font = QFont(widget.font())
                while font.pixelSize() > 8 and widget.sizeHint().width() > widget.width():
                    font.setPixelSize(font.pixelSize() - 1)
                    widget.setFont(font)
        self.position_preview_axes()

    def position_preview_axes(self) -> None:
        canvas = self.controls['axes_tracemap']
        if canvas.figure.axes and canvas.width() > 0 and canvas.height() > 0:
            scale = min(1., self.width() / REFERENCE_SIZE.width(),
                        self.height() / REFERENCE_SIZE.height())
            w, h = canvas.width(), canvas.height()
            canvas.figure.axes[0].set_position((round(48 * scale) / w, round(36 * scale) / h,
                                               (w - round(60 * scale)) / w,
                                               (h - round(44 * scale)) / h))
            logical_dpi = canvas.figure.dpi / canvas.device_pixel_ratio
            points = self.controls.specs['axes_tracemap']['FontSize'] * scale * 72 / logical_dpi
            axes = canvas.figure.axes[0]
            axes.tick_params(labelsize=points)
            axes.xaxis.label.set_fontsize(points * 1.1)
            axes.yaxis.label.set_fontsize(points * 1.1)


def build_forms(c: Controls, board: ReferenceBoard) -> QStackedWidget:
    for spec in c.reference['objects']:
        name = spec['tag']
        if name in c.widgets or spec['type'] in ('axes', 'figure'):
            continue
        c.make(name)
    stack = QStackedWidget(board)
    stack.setObjectName('analysis_stack')
    stack.setContentsMargins(0, 0, 0, 0)
    for name in PANELS:
        stack.addWidget(c[name])
    board.anchor('uibgTabMaps', stack)
    stack.hide()
    for spec in c.reference['objects']:
        name, parent = spec['tag'], spec['parent']
        if name == 'figure_main' or name in PANELS or spec['type'] == 'axes':
            continue
        widget = c[name]
        if parent == 'figure_main':
            board.anchor(name, widget)
        else:
            widget.setParent(c[parent])
            board.children_by_parent.setdefault(parent, []).append(name)
    c['text4'].setText(c['text4'].text().strip())
    c['text4'].setAlignment(Qt.AlignmentFlag.AlignCenter)
    c['text_message'].setWordWrap(False)
    c['label_stats'].setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    for name in ('pushbutton_flipx', 'pushbutton_flipy'):
        c[name].setCheckable(True)
    for label, field in [('text3', 'edit_filename'), ('text13', 'edit_scaling'),
                         ('text55', 'edit_FilenameTag')]:
        c[label].setBuddy(c[field])
        c[field].setAccessibleName(c[label].text())
    for name, widget in c.widgets.items():
        if isinstance(widget, QLineEdit):
            label = name.replace('edit_', 'label_')
            if label in c.widgets and isinstance(c[label], QLabel):
                c[label].setBuddy(widget)
                widget.setAccessibleName(c[label].text().replace('\n', ' '))
    c.radio_groups = []
    for names in [('radiobutton_image', 'radiobutton_node'),
                  ('radiobutton_fixedaperture', 'radiobutton_scaledaperture'),
                  ('radiobutton_Morlet', 'radiobutton_Mexican')]:
        group = QButtonGroup(board)
        for name in names:
            group.addButton(c[name])
        c.radio_groups.append(group)
    board.apply_geometry()
    return stack

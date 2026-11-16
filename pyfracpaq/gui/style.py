"""Compact macOS-style choice indicators from the supplied GUI screenshots."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QProxyStyle, QStyle


class ReferenceStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None) -> None:
        if element not in (QStyle.PrimitiveElement.PE_IndicatorCheckBox,
                           QStyle.PrimitiveElement.PE_IndicatorRadioButton):
            return super().drawPrimitive(element, option, painter, widget)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(option.rect)
        rect.adjust(1, 1, -1, -1)
        enabled = bool(option.state & QStyle.StateFlag.State_Enabled)
        checked = bool(option.state & QStyle.StateFlag.State_On)
        mixed = bool(option.state & QStyle.StateFlag.State_NoChange)
        blue = QColor('#3388ff') if enabled else QColor('#aaa')
        edge = blue if checked or mixed else QColor('#bdbdbd' if enabled else '#d0d0d0')
        painter.setPen(QPen(edge, 1))
        painter.setBrush(blue if checked or mixed else QColor('white' if enabled else '#f0f0f0'))
        if element == QStyle.PrimitiveElement.PE_IndicatorRadioButton:
            painter.drawEllipse(rect)
            if checked:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor('white'))
                painter.drawEllipse(rect.adjusted(rect.width() * .3, rect.height() * .3,
                                                 -rect.width() * .3, -rect.height() * .3))
        else:
            painter.drawRoundedRect(rect, 2, 2)
            if checked or mixed:
                path = QPainterPath()
                path.moveTo(rect.left() + rect.width() * .22, rect.center().y())
                if mixed:
                    path.lineTo(rect.right() - rect.width() * .22, rect.center().y())
                else:
                    path.lineTo(rect.left() + rect.width() * .43, rect.top() + rect.height() * .73)
                    path.lineTo(rect.left() + rect.width() * .8, rect.top() + rect.height() * .26)
                painter.setPen(QPen(QColor('white'), 1.5, Qt.PenStyle.SolidLine,
                                    Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.drawPath(path)
        painter.restore()

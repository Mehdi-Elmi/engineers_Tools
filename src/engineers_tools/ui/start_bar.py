"""Reusable icon-based Start Bar component.

The Start Bar is intentionally separated from the mother window. Each module can
provide a different tool list while keeping the same visual and behavioral shell.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


@dataclass(frozen=True)
class StartBarTool:
    key: str
    label: str
    tooltip: str
    properties_schema: tuple[str, ...] = ()


DEFAULT_START_BAR_TOOLS: tuple[StartBarTool, ...] = (
    StartBarTool("select", "Select", "Select objects", ("Selection", "Coordinates", "Size", "Style")),
    StartBarTool("line", "Line", "Draw a line", ("Start", "End", "Stroke", "Behavior")),
    StartBarTool("vector", "Vector", "Draw a vector", ("Magnitude", "Angle", "Components", "Style")),
    StartBarTool("angle", "Angle", "Draw or measure an angle", ("Center", "Start", "End", "Unit")),
    StartBarTool("text", "Text", "Add text", ("Content", "Font", "Size", "Direction")),
    StartBarTool("grid", "Grid", "Grid settings", ("Spacing", "Snap", "Visibility", "Unit")),
    StartBarTool("snap", "Snap", "Snap settings", ("Mode", "Tolerance", "Targets")),
    StartBarTool("ruler", "Ruler", "Show ruler", ("Unit", "Origin", "Scale")),
    StartBarTool("zoom", "Zoom", "Zoom in, zoom out, or fit", ("Zoom In", "Zoom Out", "Zoom Fit")),
)


def _tool_icon(key: str) -> QIcon:
    pixmap = QPixmap(34, 34)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    badge = QPainterPath()
    badge.addRoundedRect(QRectF(2, 2, 30, 30), 9, 9)
    gradient = QLinearGradient(2, 2, 32, 32)
    gradient.setColorAt(0.0, QColor("#ffffff"))
    gradient.setColorAt(0.52, QColor("#eaf6ff"))
    gradient.setColorAt(1.0, QColor("#78b9ff"))
    painter.fillPath(badge, gradient)
    painter.setPen(QPen(QColor("#66809e"), 1.0))
    painter.drawPath(badge)
    painter.setPen(QPen(QColor("#132238"), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)

    if key == "select":
        painter.drawPolygon(QPolygonF([QPointF(10, 8), QPointF(23, 18), QPointF(17, 19), QPointF(20, 27), QPointF(16, 28), QPointF(13, 20), QPointF(9, 24)]))
    elif key == "line":
        painter.drawLine(QPointF(9, 24), QPointF(25, 10))
        painter.setBrush(QColor("#43d3bd"))
        painter.drawEllipse(QPointF(9, 24), 2.2, 2.2)
        painter.drawEllipse(QPointF(25, 10), 2.2, 2.2)
    elif key == "vector":
        painter.drawLine(QPointF(8, 24), QPointF(25, 10))
        painter.drawLine(QPointF(25, 10), QPointF(22, 17))
        painter.drawLine(QPointF(25, 10), QPointF(18, 12))
    elif key == "angle":
        painter.drawLine(QPointF(10, 25), QPointF(25, 25))
        painter.drawLine(QPointF(10, 25), QPointF(21, 12))
        painter.drawArc(QRectF(11, 14, 15, 15), 0, 70 * 16)
    elif key == "text":
        painter.setPen(QPen(QColor("#132238"), 2.0))
        painter.drawText(QRectF(7, 6, 21, 24), Qt.AlignCenter, "T")
    elif key == "grid":
        painter.setPen(QPen(QColor("#132238"), 1.4))
        for pos in (11, 17, 23):
            painter.drawLine(QPointF(pos, 8), QPointF(pos, 26))
            painter.drawLine(QPointF(8, pos), QPointF(26, pos))
    elif key == "snap":
        painter.drawPath(QPainterPath())
        painter.drawLine(QPointF(10, 25), QPointF(10, 12))
        painter.drawLine(QPointF(24, 25), QPointF(24, 12))
        painter.drawArc(QRectF(10, 7, 14, 14), 180 * 16, -180 * 16)
    elif key == "ruler":
        painter.drawRoundedRect(QRectF(8, 12, 20, 10), 2, 2)
        painter.setPen(QPen(QColor("#132238"), 1.2))
        for x in (12, 16, 20, 24):
            painter.drawLine(QPointF(x, 12), QPointF(x, 17))
    elif key == "zoom":
        painter.drawEllipse(QPointF(15, 15), 7, 7)
        painter.drawLine(QPointF(20, 20), QPointF(27, 27))
        painter.drawLine(QPointF(11, 15), QPointF(19, 15))
        painter.drawLine(QPointF(15, 11), QPointF(15, 19))
    else:
        painter.drawEllipse(QPointF(17, 17), 8, 8)

    painter.end()
    return QIcon(pixmap)


class StartBar(QWidget):
    def __init__(self, tools: tuple[StartBarTool, ...] = DEFAULT_START_BAR_TOOLS) -> None:
        super().__init__()
        self.setObjectName("StartBar")
        self.setFixedHeight(62)
        self.tools = tools
        self._buttons: dict[str, QPushButton] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(8)

        for tool in tools:
            button = QPushButton()
            button.setObjectName("ToolButton")
            button.setToolTip(tool.tooltip)
            button.setIcon(_tool_icon(tool.key))
            button.setIconSize(QSize(34, 34))
            button.setFixedSize(46, 42)
            button.setProperty("toolKey", tool.key)
            button.setProperty("propertiesSchema", tool.properties_schema)
            self._buttons[tool.key] = button
            layout.addWidget(button)

        layout.addStretch(1)

    def set_tool_visible(self, key: str, visible: bool) -> None:
        button = self._buttons.get(key)
        if button is not None:
            button.setVisible(visible)

    def is_tool_visible(self, key: str) -> bool:
        button = self._buttons.get(key)
        return bool(button is not None and button.isVisible())

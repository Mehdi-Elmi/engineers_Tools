"""Reusable icon-based Start Bar component.

The Start Bar is intentionally separated from the mother window. Each module can
provide a different tool list while keeping the same visual and behavioral shell.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, QSize, Signal, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


@dataclass(frozen=True)
class StartBarTool:
    key: str
    label: str
    tooltip: str
    properties_schema: tuple[str, ...] = ()


DEFAULT_START_BAR_TOOLS: tuple[StartBarTool, ...] = (
    StartBarTool("select", "Select", "Select and edit objects", ("Selection", "Transform", "Layer")),
    StartBarTool("line", "Line", "Draw line", ("Start", "End", "Stroke", "Unit")),
    StartBarTool("vector", "Vector", "Draw vector", ("Magnitude", "Direction", "Angle", "Unit")),
    StartBarTool("angle", "Angle", "Measure or draw angle", ("Start Ray", "End Ray", "Theta", "Unit")),
    StartBarTool("text", "Text", "Add text", ("Content", "Font", "Size", "Direction")),
    StartBarTool("grid", "Grid", "Grid settings", ("Spacing", "Snap", "Visibility", "Unit")),
    StartBarTool("snap", "Snap", "Snap settings", ("Mode", "Tolerance", "Targets")),
    StartBarTool("unit", "Unit", "Set workspace unit", ("Millimeter", "Centimeter", "Meter", "Pixel", "Inch")),
    StartBarTool("ruler", "Ruler", "Show ruler", ("Unit", "Origin", "Scale")),
    StartBarTool("zoom", "Zoom", "Zoom in, zoom out, or fit", ("Zoom In", "Zoom Out", "Zoom Fit")),
)


def _rounded_badge(painter: QPainter, rect: QRectF, accent: QColor) -> None:
    badge = QPainterPath()
    badge.addRoundedRect(rect, 9, 9)
    shadow = QPainterPath()
    shadow.addRoundedRect(rect.translated(1.8, 2.2), 9, 9)
    shadow_color = QColor("#465c78")
    shadow_color.setAlpha(70)
    painter.fillPath(shadow, shadow_color)
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, QColor("#ffffff"))
    gradient.setColorAt(0.48, QColor("#edf7ff"))
    gradient.setColorAt(1.0, accent)
    painter.fillPath(badge, gradient)
    painter.setPen(QPen(QColor("#6e86a4"), 1.1))
    painter.drawPath(badge)


def _draw_arrow_head(painter: QPainter, tip: QPointF, back: QPointF, size: float = 6.0) -> None:
    direction = tip - back
    length = max(0.01, (direction.x() ** 2 + direction.y() ** 2) ** 0.5)
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    left = QPointF(tip.x() - unit.x() * size + normal.x() * size * 0.46, tip.y() - unit.y() * size + normal.y() * size * 0.46)
    right = QPointF(tip.x() - unit.x() * size - normal.x() * size * 0.46, tip.y() - unit.y() * size - normal.y() * size * 0.46)
    painter.drawLine(tip, left)
    painter.drawLine(tip, right)


def _tool_icon(key: str) -> QIcon:
    pixmap = QPixmap(36, 36)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    accents = {
        "select": "#8dc1ff",
        "line": "#72d6c7",
        "vector": "#8bbcff",
        "angle": "#f0c86a",
        "text": "#d8b6ff",
        "grid": "#b8d4ef",
        "snap": "#93d6bd",
        "unit": "#ffd36e",
        "ruler": "#ffc35a",
        "zoom": "#9bc8ff",
    }
    _rounded_badge(painter, QRectF(3, 3, 30, 30), QColor(accents.get(key, "#9bc8ff")))
    ink = QColor("#132238")
    painter.setPen(QPen(ink, 2.15, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)

    if key == "select":
        painter.setBrush(QColor("#132238"))
        painter.drawPolygon(QPolygonF([QPointF(10, 8), QPointF(25, 19), QPointF(18, 20), QPointF(22, 29), QPointF(17, 30), QPointF(14, 22), QPointF(9, 26)]))
    elif key == "line":
        painter.drawLine(QPointF(9, 26), QPointF(27, 10))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QPointF(9, 26), 2.6, 2.6)
        painter.drawEllipse(QPointF(27, 10), 2.6, 2.6)
    elif key == "vector":
        painter.drawLine(QPointF(8, 27), QPointF(27, 10))
        _draw_arrow_head(painter, QPointF(27, 10), QPointF(20, 16), 7.0)
    elif key == "angle":
        painter.drawLine(QPointF(9, 27), QPointF(28, 27))
        painter.drawLine(QPointF(9, 27), QPointF(23, 10))
        painter.setPen(QPen(QColor("#e6822a"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawArc(QRectF(11, 15, 16, 16), 0, 66 * 16)
    elif key == "text":
        font = painter.font()
        font.setFamily("Times New Roman")
        font.setBold(True)
        font.setItalic(False)
        font.setPointSize(18)
        painter.setFont(font)
        painter.drawText(QRectF(6, 4, 24, 27), Qt.AlignCenter, "T")
    elif key == "grid":
        painter.setPen(QPen(ink, 1.35))
        for pos in (11, 18, 25):
            painter.drawLine(QPointF(pos, 8), QPointF(pos, 28))
            painter.drawLine(QPointF(8, pos), QPointF(28, pos))
    elif key == "snap":
        painter.drawLine(QPointF(10, 26), QPointF(10, 13))
        painter.drawLine(QPointF(26, 26), QPointF(26, 13))
        painter.drawArc(QRectF(10, 8, 16, 16), 180 * 16, -180 * 16)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QPointF(18, 12), 2.5, 2.5)
    elif key == "unit":
        font = painter.font()
        font.setFamily("Times New Roman")
        font.setBold(True)
        font.setItalic(False)
        font.setPointSize(11)
        painter.setFont(font)
        painter.drawRoundedRect(QRectF(8, 10, 20, 14), 3, 3)
        painter.drawText(QRectF(7, 8, 22, 18), Qt.AlignCenter, "mm")
        painter.setPen(QPen(QColor("#7e5b10"), 1.1))
        painter.drawLine(QPointF(10, 26), QPointF(26, 26))
        for x in (10, 14, 18, 22, 26):
            painter.drawLine(QPointF(x, 24), QPointF(x, 28))
    elif key == "ruler":
        painter.drawRoundedRect(QRectF(8, 12, 21, 11), 2, 2)
        painter.setPen(QPen(ink, 1.1))
        for index, x in enumerate((12, 16, 20, 24)):
            painter.drawLine(QPointF(x, 12), QPointF(x, 19 if index % 2 == 0 else 17))
    elif key == "zoom":
        painter.drawEllipse(QPointF(15, 15), 7.2, 7.2)
        painter.drawLine(QPointF(20, 20), QPointF(28, 28))
        painter.setPen(QPen(QColor("#2f7df6"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(11, 15), QPointF(19, 15))
        painter.drawLine(QPointF(15, 11), QPointF(15, 19))
    else:
        painter.drawEllipse(QPointF(18, 18), 8, 8)

    painter.end()
    return QIcon(pixmap)


class StartBar(QWidget):
    tool_requested = Signal(str)

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
            button.setIconSize(QSize(36, 36))
            button.setFixedSize(48, 42)
            button.setProperty("toolKey", tool.key)
            button.setProperty("toolLabel", tool.label)
            button.setProperty("propertiesSchema", tool.properties_schema)
            button.clicked.connect(lambda checked=False, key=tool.key: self.tool_requested.emit(key))
            self._buttons[tool.key] = button
            layout.addWidget(button)

        layout.addStretch(1)

    def button(self, key: str) -> QPushButton | None:
        return self._buttons.get(key)

    def set_tool_visible(self, key: str, visible: bool) -> None:
        button = self._buttons.get(key)
        if button is not None:
            button.setVisible(visible)

    def set_tool_callback(self, key: str, callback: Callable[[], None]) -> None:
        button = self._buttons.get(key)
        if button is not None:
            button.clicked.connect(callback)

"""Reusable icon-based Start Bar component.

The Start Bar is intentionally separated from the mother window. Each module can
provide a different tool list while keeping the same visual and behavioral shell.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Signal, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QDialog, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


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

UNIT_TO_MM = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "px": 25.4 / 96.0,
    "in": 25.4,
}


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
        "unit": "#78e1cf",
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
        painter.save()
        body = QPainterPath()
        body.addRoundedRect(QRectF(7, 8, 22, 20), 5, 5)
        body_gradient = QLinearGradient(7, 8, 29, 28)
        body_gradient.setColorAt(0.0, QColor("#ffffff"))
        body_gradient.setColorAt(0.52, QColor("#e9fff9"))
        body_gradient.setColorAt(1.0, QColor("#38c9b5"))
        painter.fillPath(body, body_gradient)
        painter.setPen(QPen(QColor("#2e6574"), 1.05))
        painter.drawPath(body)

        painter.setPen(QPen(QColor("#132238"), 1.65, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(10, 22), QPointF(26, 22))
        painter.drawLine(QPointF(10, 22), QPointF(10, 15))
        painter.drawLine(QPointF(26, 22), QPointF(26, 15))
        for index, x in enumerate((13, 16, 19, 22)):
            painter.drawLine(QPointF(x, 22), QPointF(x, 17 if index % 2 == 0 else 19))

        painter.setPen(QPen(QColor("#ff8a35"), 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(11, 12), QPointF(25, 12))
        _draw_arrow_head(painter, QPointF(11, 12), QPointF(16, 12), 3.8)
        _draw_arrow_head(painter, QPointF(25, 12), QPointF(20, 12), 3.8)

        font = painter.font()
        font.setFamily("Times New Roman")
        font.setBold(True)
        font.setItalic(False)
        font.setPointSize(7)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#132238"), 1.0))
        painter.drawText(QRectF(9, 23, 18, 7), Qt.AlignCenter, "mm")
        painter.restore()
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
    zoom_requested = Signal(str)
    ruler_changed = Signal(bool, str)
    grid_changed = Signal(bool, float, str)
    unit_changed = Signal(str)

    def __init__(self, tools: tuple[StartBarTool, ...] = DEFAULT_START_BAR_TOOLS) -> None:
        super().__init__()
        self.setObjectName("StartBar")
        self.setFixedHeight(62)
        self.tools = tools
        self._buttons: dict[str, QPushButton] = {}
        self._popup: QDialog | None = None
        self._unit = "mm"
        self._grid_enabled = True
        self._grid_spacing = 4.0
        self._ruler_enabled = False

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
            button.clicked.connect(lambda checked=False, key=tool.key: self._handle_tool_click(key))
            self._buttons[tool.key] = button
            layout.addWidget(button)

        layout.addStretch(1)
        self._refresh_tooltips()

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

    def _handle_tool_click(self, key: str) -> None:
        if key == "zoom":
            self._show_zoom_popup(key)
            return
        if key == "ruler":
            self._show_ruler_popup(key)
            return
        if key == "grid":
            self._show_grid_popup(key)
            return
        if key == "unit":
            self._show_unit_popup(key)
            return
        self.tool_requested.emit(key)

    def _popup_base(self, title: str, width: int = 210) -> tuple[QDialog, QVBoxLayout]:
        if self._popup is not None:
            self._popup.close()
        popup = QDialog(self)
        popup.setObjectName("StartToolPopup")
        popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        popup.setAttribute(Qt.WA_TranslucentBackground)
        shell = QWidget()
        shell.setObjectName("StartToolPopupShell")
        root = QVBoxLayout(popup)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        heading = QLabel(title)
        heading.setObjectName("StartToolPopupTitle")
        layout.addWidget(heading)
        shell.setStyleSheet(
            "QWidget#StartToolPopupShell {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.48 #eef8ff, stop:1 #fff3d4); border:1px solid #8fa2bb; border-radius:12px;}"
            "QLabel {background:transparent; color:#1f3148;}"
            "QLabel#StartToolPopupTitle {background:transparent; color:#132238; font-size:12px; font-style:italic; font-weight:900; padding:2px 4px;}"
            "QPushButton#PopupChoice {background:rgba(255,255,255,210); border:1px solid #b8c5d4; border-left:3px solid #43d3bd; border-radius:7px; color:#1f3148; font-size:12px; font-style:italic; font-weight:800; padding:5px 9px; text-align:left;}"
            "QPushButton#PopupChoice:hover {background:#fff4cf; border-color:#ff8a35; border-left-color:#d91f5c;}"
            "QPushButton#PopupChoice:checked {background:#dff6ff; border-color:#2f7df6; border-left-color:#2f7df6;}"
            "QDoubleSpinBox#PopupSpin {background:#ffffff; border:1px solid #9fb0c5; border-radius:7px; color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:4px 7px;}"
        )
        popup.setFixedWidth(width)
        self._popup = popup
        return popup, layout

    def _show_popup_near(self, key: str, popup: QDialog) -> None:
        button = self._buttons.get(key)
        if button is None:
            popup.move(self.mapToGlobal(QPoint(0, self.height())))
        else:
            popup.move(button.mapToGlobal(QPoint(0, button.height() + 4)))
        popup.show()

    def _choice_button(self, label: str, checked: bool, callback: Callable[[], None]) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("PopupChoice")
        button.setCheckable(True)
        button.setChecked(checked)
        button.clicked.connect(callback)
        return button

    def _host(self) -> QWidget:
        return self.window()

    def _set_host_status(self, message: str) -> None:
        setter = getattr(self._host(), "_set_status", None)
        if callable(setter):
            setter(message)

    def _apply_grid_to_host(self) -> None:
        host = self._host()
        view_state = getattr(host, "_view_state", None)
        if isinstance(view_state, dict):
            view_state["grid"] = self._grid_enabled
        canvas = getattr(host, "_canvas", None)
        if canvas is not None and hasattr(canvas, "set_grid_visible"):
            canvas.set_grid_visible(self._grid_enabled)
        self._set_host_status(f"Grid {'On' if self._grid_enabled else 'Off'} | spacing {self._grid_spacing:.3f} {self._unit}")

    def _apply_ruler_to_host(self) -> None:
        host = self._host()
        view_state = getattr(host, "_view_state", None)
        if isinstance(view_state, dict):
            view_state["ruler"] = self._ruler_enabled
        self._set_host_status(f"Ruler {'On' if self._ruler_enabled else 'Off'} | unit {self._unit}")

    def _apply_unit_to_host(self) -> None:
        host = self._host()
        for item in getattr(host, "_status_items", []):
            if hasattr(item, "text") and item.text().startswith("Unit:"):
                item.setText(f"Unit: {self._unit}")
                break
        self._set_host_status(f"Unit {self._unit}")

    def _apply_zoom_to_host(self, mode: str) -> None:
        host = self._host()
        canvas = getattr(host, "_canvas", None)
        current_zoom = getattr(canvas, "_zoom", 1.0) * 100.0 if canvas is not None else 100.0
        if mode == "zoom_fit":
            value = 100.0
        elif mode == "zoom_in":
            value = min(500.0, current_zoom * 1.25)
        else:
            value = max(5.0, current_zoom / 1.25)
        setter = getattr(host, "_set_zoom", None)
        if callable(setter):
            setter(value)
        elif canvas is not None and hasattr(canvas, "set_zoom"):
            canvas.set_zoom(value)
            self._set_host_status(f"Zoom {value:.2f}%")

    def _show_zoom_popup(self, key: str) -> None:
        popup, layout = self._popup_base("Zoom", 176)
        for label, action in (("Zoom In", "zoom_in"), ("Zoom Out", "zoom_out"), ("Zoom Fit", "zoom_fit")):
            layout.addWidget(self._choice_button(label, False, lambda checked=False, mode=action: self._activate_zoom(mode)))
        self._show_popup_near(key, popup)

    def _activate_zoom(self, mode: str) -> None:
        self._apply_zoom_to_host(mode)
        self.zoom_requested.emit(mode)
        self.tool_requested.emit(mode)
        if self._popup is not None:
            self._popup.close()

    def _show_ruler_popup(self, key: str) -> None:
        popup, layout = self._popup_base("Ruler", 190)
        layout.addWidget(self._choice_button("Ruler On", self._ruler_enabled, lambda checked=False: self._set_ruler(True)))
        layout.addWidget(self._choice_button("Ruler Off", not self._ruler_enabled, lambda checked=False: self._set_ruler(False)))
        layout.addWidget(QLabel(f"Origin unit: {self._unit}"))
        self._show_popup_near(key, popup)

    def _set_ruler(self, enabled: bool) -> None:
        self._ruler_enabled = enabled
        self._apply_ruler_to_host()
        self.ruler_changed.emit(enabled, self._unit)
        self.tool_requested.emit("ruler_on" if enabled else "ruler_off")
        self._refresh_tooltips()
        if self._popup is not None:
            self._popup.close()

    def _show_grid_popup(self, key: str) -> None:
        popup, layout = self._popup_base("Grid", 218)
        layout.addWidget(self._choice_button("Grid On", self._grid_enabled, lambda checked=False: self._set_grid_enabled(True)))
        layout.addWidget(self._choice_button("Grid Off", not self._grid_enabled, lambda checked=False: self._set_grid_enabled(False)))
        spin = QDoubleSpinBox()
        spin.setObjectName("PopupSpin")
        spin.setRange(0.01, 100000.0)
        spin.setDecimals(3)
        spin.setSingleStep(1.0)
        spin.setSuffix(f" {self._unit}")
        spin.setValue(self._grid_spacing)
        spin.valueChanged.connect(self._set_grid_spacing)
        layout.addWidget(QLabel("Grid spacing"))
        layout.addWidget(spin)
        self._show_popup_near(key, popup)

    def _set_grid_enabled(self, enabled: bool) -> None:
        self._grid_enabled = enabled
        self._apply_grid_to_host()
        self.grid_changed.emit(self._grid_enabled, self._grid_spacing, self._unit)
        self.tool_requested.emit("grid_on" if enabled else "grid_off")
        self._refresh_tooltips()
        if self._popup is not None:
            self._popup.close()

    def _set_grid_spacing(self, value: float) -> None:
        self._grid_spacing = value
        self._apply_grid_to_host()
        self.grid_changed.emit(self._grid_enabled, self._grid_spacing, self._unit)
        self._refresh_tooltips()

    def _show_unit_popup(self, key: str) -> None:
        popup, layout = self._popup_base("Unit", 188)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(5)
        for index, unit in enumerate(("mm", "cm", "m", "px", "in")):
            grid.addWidget(self._choice_button(unit, unit == self._unit, lambda checked=False, selected=unit: self._set_unit(selected)), index // 2, index % 2)
        layout.addLayout(grid)
        self._show_popup_near(key, popup)

    def _set_unit(self, unit: str) -> None:
        if unit == self._unit:
            if self._popup is not None:
                self._popup.close()
            return
        spacing_mm = self._grid_spacing * UNIT_TO_MM[self._unit]
        self._unit = unit
        self._grid_spacing = spacing_mm / UNIT_TO_MM[self._unit]
        self._apply_unit_to_host()
        self._apply_grid_to_host()
        self.unit_changed.emit(unit)
        self.grid_changed.emit(self._grid_enabled, self._grid_spacing, self._unit)
        self.tool_requested.emit(f"unit_{unit}")
        self._refresh_tooltips()
        if self._popup is not None:
            self._popup.close()

    def _refresh_tooltips(self) -> None:
        grid = self._buttons.get("grid")
        if grid is not None:
            grid.setToolTip(f"Grid: {'On' if self._grid_enabled else 'Off'} | spacing {self._grid_spacing:.3f} {self._unit}")
        ruler = self._buttons.get("ruler")
        if ruler is not None:
            ruler.setToolTip(f"Ruler: {'On' if self._ruler_enabled else 'Off'} | unit {self._unit}")
        unit = self._buttons.get("unit")
        if unit is not None:
            unit.setToolTip(f"Unit: {self._unit}")
        zoom = self._buttons.get("zoom")
        if zoom is not None:
            zoom.setToolTip("Zoom in, zoom out, or fit")

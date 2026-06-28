"""Reusable icon-based Start Bar component."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, QSize, Signal, Qt
from PySide6.QtGui import QColor, QCursor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QRubberBand, QVBoxLayout, QWidget


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

UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "px": 25.4 / 96.0, "in": 25.4, "pt": 25.4 / 72.0}
UNIT_ORDER = ("mm", "cm", "m", "px", "in", "pt")
MM_TO_SCREEN_PX = 96.0 / 25.4


def _badge(painter: QPainter, rect: QRectF, accent: QColor) -> None:
    shadow = QPainterPath()
    shadow.addRoundedRect(rect.translated(1.8, 2.2), 9, 9)
    shadow_color = QColor("#465c78")
    shadow_color.setAlpha(70)
    painter.fillPath(shadow, shadow_color)
    path = QPainterPath()
    path.addRoundedRect(rect, 9, 9)
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, QColor("#ffffff"))
    gradient.setColorAt(0.48, QColor("#edf7ff"))
    gradient.setColorAt(1.0, accent)
    painter.fillPath(path, gradient)
    painter.setPen(QPen(QColor("#6e86a4"), 1.1))
    painter.drawPath(path)


def _arrow_head(painter: QPainter, tip: QPointF, back: QPointF, size: float = 6.0) -> None:
    direction = tip - back
    length = max(0.01, (direction.x() ** 2 + direction.y() ** 2) ** 0.5)
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    left = QPointF(tip.x() - unit.x() * size + normal.x() * size * 0.48, tip.y() - unit.y() * size + normal.y() * size * 0.48)
    right = QPointF(tip.x() - unit.x() * size - normal.x() * size * 0.48, tip.y() - unit.y() * size - normal.y() * size * 0.48)
    painter.drawLine(tip, left)
    painter.drawLine(tip, right)


def _paint_magnifier(painter: QPainter, mode: str, center: QPointF = QPointF(15, 15)) -> None:
    painter.setPen(QPen(QColor("#132238"), 2.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(center, 7.1, 7.1)
    painter.drawLine(QPointF(center.x() + 5, center.y() + 5), QPointF(center.x() + 13, center.y() + 13))
    painter.setPen(QPen(QColor("#2f7df6"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if mode == "fit":
        painter.drawLine(QPointF(center.x() - 5, center.y() + 5), QPointF(center.x() + 5, center.y() - 5))
        painter.drawLine(QPointF(center.x() + 5, center.y() - 5), QPointF(center.x() + 5, center.y() + 1))
        painter.drawLine(QPointF(center.x() + 5, center.y() - 5), QPointF(center.x() - 1, center.y() - 5))
    else:
        painter.drawLine(QPointF(center.x() - 4, center.y()), QPointF(center.x() + 4, center.y()))
        if mode == "in":
            painter.drawLine(QPointF(center.x(), center.y() - 4), QPointF(center.x(), center.y() + 4))


def _zoom_cursor(mode: str) -> QCursor:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    _paint_magnifier(painter, "in" if mode == "zoom_in" else "out", QPointF(12, 12))
    painter.end()
    return QCursor(pixmap, 12, 12)


def _icon_button_icon(key: str) -> QIcon:
    pixmap = QPixmap(36, 36)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    accents = {"select": "#8dc1ff", "line": "#72d6c7", "vector": "#8bbcff", "angle": "#f0c86a", "text": "#d8b6ff", "grid": "#b8d4ef", "snap": "#93d6bd", "unit": "#78e1cf", "ruler": "#ffc35a", "zoom": "#9bc8ff"}
    _badge(painter, QRectF(3, 3, 30, 30), QColor(accents.get(key, "#9bc8ff")))
    ink = QColor("#132238")
    painter.setPen(QPen(ink, 2.15, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    if key == "select":
        painter.setBrush(ink)
        painter.drawPolygon(QPolygonF([QPointF(10, 8), QPointF(25, 19), QPointF(18, 20), QPointF(22, 29), QPointF(17, 30), QPointF(14, 22), QPointF(9, 26)]))
    elif key == "line":
        painter.drawLine(QPointF(9, 26), QPointF(27, 10))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QPointF(9, 26), 2.6, 2.6)
        painter.drawEllipse(QPointF(27, 10), 2.6, 2.6)
    elif key == "vector":
        painter.drawLine(QPointF(8, 27), QPointF(27, 10))
        _arrow_head(painter, QPointF(27, 10), QPointF(20, 16), 7.0)
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
        painter.drawLine(QPointF(10, 22), QPointF(26, 22))
        painter.drawLine(QPointF(10, 22), QPointF(10, 15))
        painter.drawLine(QPointF(26, 22), QPointF(26, 15))
        painter.setPen(QPen(QColor("#ff8a35"), 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(11, 12), QPointF(25, 12))
        _arrow_head(painter, QPointF(11, 12), QPointF(16, 12), 3.8)
        _arrow_head(painter, QPointF(25, 12), QPointF(20, 12), 3.8)
        font = painter.font()
        font.setFamily("Times New Roman")
        font.setBold(True)
        font.setPointSize(7)
        painter.setFont(font)
        painter.setPen(QPen(ink, 1.0))
        painter.drawText(QRectF(9, 23, 18, 7), Qt.AlignCenter, "mm")
    elif key == "ruler":
        painter.drawRoundedRect(QRectF(8, 12, 21, 11), 2, 2)
        painter.setPen(QPen(ink, 1.1))
        for index, x in enumerate((12, 16, 20, 24)):
            painter.drawLine(QPointF(x, 12), QPointF(x, 19 if index % 2 == 0 else 17))
    elif key == "zoom":
        _paint_magnifier(painter, "in")
    else:
        painter.drawEllipse(QPointF(18, 18), 8, 8)
    painter.end()
    return QIcon(pixmap)


def _mini_zoom_icon(action: str) -> QIcon:
    pixmap = QPixmap(34, 34)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    _badge(painter, QRectF(3, 3, 28, 28), QColor({"zoom_in": "#8dc1ff", "zoom_out": "#b8d4ef", "zoom_fit": "#78e1cf"}[action]))
    _paint_magnifier(painter, {"zoom_in": "in", "zoom_out": "out", "zoom_fit": "fit"}[action])
    painter.end()
    return QIcon(pixmap)


class _RulerOverlay(QWidget):
    def __init__(self, start_bar: "StartBar", orientation: str, parent: QWidget) -> None:
        super().__init__(parent)
        self._start_bar = start_bar
        self._orientation = orientation
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(20, 37, 58, 230))
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        spacing = self._start_bar._unit_to_canvas_px(1.0, self._start_bar._unit)
        spacing = max(2.0, spacing)
        length = self.width() if self._orientation == "top" else self.height()
        zero = self._start_bar._ruler_origin.x() if self._orientation == "top" else self._start_bar._ruler_origin.y()
        index = int(-zero / spacing) - 2
        while True:
            position = zero + index * spacing
            if position > length + spacing:
                break
            if position >= 0:
                abs_index = abs(index)
                if abs_index % 10 == 0:
                    tick = 22
                elif abs_index % 5 == 0:
                    tick = 15
                else:
                    tick = 8
                if self._orientation == "top":
                    painter.drawLine(QPointF(position, self.height()), QPointF(position, self.height() - tick))
                    if abs_index % 10 == 0:
                        painter.drawText(QRectF(position + 2, 1, 52, 14), Qt.AlignLeft | Qt.AlignVCenter, str(index))
                else:
                    painter.drawLine(QPointF(self.width(), position), QPointF(self.width() - tick, position))
                    if abs_index % 10 == 0:
                        painter.drawText(QRectF(2, position + 2, self.width() - 4, 14), Qt.AlignLeft | Qt.AlignVCenter, str(index))
            index += 1
        painter.end()


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
        self._unit_buttons: dict[str, QPushButton] = {}
        self._grid_buttons: dict[str, QPushButton] = {}
        self._popup: QDialog | None = None
        self._unit = "mm"
        self._grid_enabled = True
        self._grid_spacing = 4.0
        self._ruler_enabled = False
        self._zoom_mode: str | None = None
        self._zoom_origin: QPoint | None = None
        self._rubber_band: QRubberBand | None = None
        self._ruler_top: _RulerOverlay | None = None
        self._ruler_left: _RulerOverlay | None = None
        self._ruler_origin = QPointF(0, 0)
        self._hooked_canvas: QWidget | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(8)
        for tool in tools:
            button = QPushButton()
            button.setObjectName("ToolButton")
            button.setToolTip(tool.tooltip)
            button.setIcon(_icon_button_icon(tool.key))
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

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        canvas = self._canvas()
        if watched is canvas:
            if event.type() == QEvent.Type.Resize:
                self._position_rulers()
                return False
            if self._zoom_mode in {"zoom_in", "zoom_out"}:
                if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                    self._zoom_origin = event.position().toPoint()
                    self._ensure_rubber_band()
                    if self._rubber_band is not None:
                        self._rubber_band.setGeometry(QRect(self._zoom_origin, QSize()))
                        self._rubber_band.show()
                    return True
                if event.type() == QEvent.Type.MouseMove and self._zoom_origin is not None:
                    self._ensure_rubber_band()
                    if self._rubber_band is not None:
                        self._rubber_band.setGeometry(QRect(self._zoom_origin, event.position().toPoint()).normalized())
                    return True
                if event.type() == QEvent.Type.MouseButtonRelease and self._zoom_origin is not None:
                    rect = QRect(self._zoom_origin, event.position().toPoint()).normalized()
                    if self._rubber_band is not None:
                        self._rubber_band.hide()
                    mode = self._zoom_mode
                    self._zoom_mode = None
                    self._zoom_origin = None
                    if canvas is not None:
                        canvas.unsetCursor()
                    if mode is not None:
                        self._apply_drag_zoom(mode, rect)
                    return True
        return super().eventFilter(watched, event)

    def _handle_tool_click(self, key: str) -> None:
        self._ensure_canvas_hooks()
        if key == "zoom":
            self._show_zoom_popup(key)
        elif key == "ruler":
            self._set_ruler(not self._ruler_enabled)
        elif key == "grid":
            self._show_grid_popup(key)
        elif key == "unit":
            self._show_unit_popup(key)
        else:
            self.tool_requested.emit(key)

    def _host(self) -> QWidget:
        return self.window()

    def _canvas(self):
        return getattr(self._host(), "_canvas", None)

    def _set_host_status(self, message: str) -> None:
        setter = getattr(self._host(), "_set_status", None)
        if callable(setter):
            setter(message)

    def _unit_to_canvas_px(self, value: float, unit: str) -> float:
        return max(1.0, value * UNIT_TO_MM[unit] * MM_TO_SCREEN_PX)

    def _spacing_text(self) -> str:
        return f"{self._grid_spacing:.6f}".rstrip("0").rstrip(".") or "0"

    def _ensure_canvas_hooks(self) -> None:
        canvas = self._canvas()
        if canvas is None:
            return
        if canvas is not self._hooked_canvas:
            if self._hooked_canvas is not None:
                self._hooked_canvas.removeEventFilter(self)
            canvas.installEventFilter(self)
            self._hooked_canvas = canvas
            self._ruler_origin = QPointF(canvas.width() / 2.0, canvas.height() / 2.0)
        if not getattr(canvas, "_start_bar_grid_hooked", False):
            def paint_grid(canvas_self, painter: QPainter) -> None:
                if not getattr(canvas_self, "_grid_visible", True):
                    return
                spacing = max(4.0, min(self._unit_to_canvas_px(self._grid_spacing, self._unit), 10000.0))
                origin = self._ruler_origin
                painter.setPen(QPen(QColor(70, 96, 130, 42), 1))
                x = origin.x()
                while x <= canvas_self.width():
                    painter.drawLine(QPointF(x, 0), QPointF(x, canvas_self.height()))
                    x += spacing
                x = origin.x() - spacing
                while x >= 0:
                    painter.drawLine(QPointF(x, 0), QPointF(x, canvas_self.height()))
                    x -= spacing
                y = origin.y()
                while y <= canvas_self.height():
                    painter.drawLine(QPointF(0, y), QPointF(canvas_self.width(), y))
                    y += spacing
                y = origin.y() - spacing
                while y >= 0:
                    painter.drawLine(QPointF(0, y), QPointF(canvas_self.width(), y))
                    y -= spacing
            canvas._paint_grid = paint_grid.__get__(canvas, canvas.__class__)
            canvas._start_bar_grid_hooked = True
        canvas._grid_spacing = self._grid_spacing
        canvas._grid_unit = self._unit

    def _ensure_rubber_band(self) -> None:
        canvas = self._canvas()
        if canvas is not None and (self._rubber_band is None or self._rubber_band.parent() is not canvas):
            self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, canvas)

    def _popup_base(self, width: int) -> tuple[QDialog, QVBoxLayout]:
        if self._popup is not None:
            self._popup.close()
        popup = QDialog(self)
        popup.setObjectName("StartToolPopup")
        popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        shell = QWidget()
        shell.setObjectName("StartToolPopupShell")
        root = QVBoxLayout(popup)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        shell.setStyleSheet(
            "QWidget#StartToolPopupShell {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.48 #eef8ff, stop:1 #fff3d4); border:1px solid #8fa2bb; border-radius:12px;}"
            "QLabel {background:transparent; color:#1f3148; font-size:11px; font-style:italic; font-weight:800;}"
            "QPushButton#IconChoice {background:rgba(255,255,255,220); border:1px solid #b8c5d4; border-radius:10px;}"
            "QPushButton#IconChoice:hover {background:#fff4cf; border-color:#ff8a35;}"
            "QPushButton#RadioChoice {background:rgba(255,255,255,220); border:1px solid #b8c5d4; border-radius:8px; color:#1f3148; font-size:12px; font-style:italic; font-weight:900; padding:5px 8px; text-align:left;}"
            "QPushButton#RadioChoice:hover {background:#fff4cf; border-color:#ff8a35;}"
            "QPushButton#RadioChoice:checked {background:#dff6ff; border-color:#2f7df6;}"
            "QDoubleSpinBox#PopupSpin {background:#ffffff; border:1px solid #9fb0c5; border-radius:7px; color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:4px 7px;}"
        )
        popup.setFixedWidth(width)
        self._popup = popup
        return popup, layout

    def _show_popup_near(self, key: str, popup: QDialog) -> None:
        button = self._buttons.get(key)
        target = button.mapToGlobal(QPoint(0, button.height() + 4)) if button is not None else self.mapToGlobal(QPoint(0, self.height()))
        popup.move(target)
        popup.show()

    def _radio_text(self, label: str, checked: bool) -> str:
        return f"{'●' if checked else '○'}  {label}"

    def _radio_button(self, key: str, label: str, checked: bool, callback: Callable[[], None]) -> QPushButton:
        button = QPushButton(self._radio_text(label, checked))
        button.setObjectName("RadioChoice")
        button.setCheckable(True)
        button.setChecked(checked)
        button.clicked.connect(callback)
        return button

    def _show_zoom_popup(self, key: str) -> None:
        popup, layout = self._popup_base(172)
        row = QHBoxLayout()
        row.setContentsMargins(2, 2, 2, 2)
        row.setSpacing(6)
        for action, tooltip in (("zoom_in", "Zoom In"), ("zoom_out", "Zoom Out"), ("zoom_fit", "Zoom Fit")):
            button = QPushButton()
            button.setObjectName("IconChoice")
            button.setToolTip(tooltip)
            button.setIcon(_mini_zoom_icon(action))
            button.setIconSize(QSize(34, 34))
            button.setFixedSize(46, 42)
            button.clicked.connect(lambda checked=False, mode=action: self._activate_zoom(mode))
            row.addWidget(button)
        layout.addLayout(row)
        self._show_popup_near(key, popup)

    def _activate_zoom(self, mode: str) -> None:
        self._ensure_canvas_hooks()
        if self._popup is not None:
            self._popup.close()
        if mode == "zoom_fit":
            self._set_zoom_value(100.0)
        else:
            self._zoom_mode = mode
            canvas = self._canvas()
            if canvas is not None:
                canvas.setCursor(_zoom_cursor(mode))
            self._set_host_status(f"{'Zoom In' if mode == 'zoom_in' else 'Zoom Out'}: drag a region on the main page")
        self.zoom_requested.emit(mode)
        self.tool_requested.emit(mode)

    def _set_zoom_value(self, value: float) -> None:
        host = self._host()
        zoom_input = getattr(host, "_zoom_input", None)
        if zoom_input is not None and hasattr(zoom_input, "blockSignals"):
            blocked = zoom_input.blockSignals(True)
            zoom_input.setValue(value)
            zoom_input.blockSignals(blocked)
        setter = getattr(host, "_set_zoom", None)
        if callable(setter):
            setter(value)
            return
        canvas = self._canvas()
        if canvas is not None and hasattr(canvas, "set_zoom"):
            canvas.set_zoom(value)
        self._set_host_status(f"Zoom {value:.2f}%")

    def _apply_drag_zoom(self, mode: str, rect: QRect) -> None:
        canvas = self._canvas()
        if canvas is None or rect.width() < 8 or rect.height() < 8:
            self._set_host_status("Zoom canceled")
            return
        current_zoom = getattr(canvas, "_zoom", 1.0) * 100.0
        factor = min(canvas.width() / max(1, rect.width()), canvas.height() / max(1, rect.height()))
        factor = max(1.05, min(factor, 12.0))
        value = current_zoom * factor if mode == "zoom_in" else current_zoom / factor
        self._set_zoom_value(max(5.0, min(3200.0, value)))

    def _show_unit_popup(self, key: str) -> None:
        self._unit_buttons = {}
        popup, layout = self._popup_base(156)
        rows = (UNIT_ORDER[:3], UNIT_ORDER[3:])
        for row_units in rows:
            row = QHBoxLayout()
            row.setSpacing(5)
            for unit in row_units:
                button = self._radio_button(unit, unit, unit == self._unit, lambda checked=False, selected=unit: self._set_unit(selected))
                button.setFixedWidth(44)
                self._unit_buttons[unit] = button
                row.addWidget(button)
            layout.addLayout(row)
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

    def _show_grid_popup(self, key: str) -> None:
        self._grid_buttons = {}
        popup, layout = self._popup_base(204)
        row = QHBoxLayout()
        on_button = self._radio_button("on", "Grid On", self._grid_enabled, lambda: self._set_grid_enabled(True))
        off_button = self._radio_button("off", "Grid Off", not self._grid_enabled, lambda: self._set_grid_enabled(False))
        self._grid_buttons = {"on": on_button, "off": off_button}
        row.addWidget(on_button)
        row.addWidget(off_button)
        layout.addLayout(row)
        spin = QDoubleSpinBox()
        spin.setObjectName("PopupSpin")
        spin.setRange(0.000001, 1000000.0)
        spin.setDecimals(6)
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

    def _apply_grid_to_host(self) -> None:
        self._ensure_canvas_hooks()
        host = self._host()
        view_state = getattr(host, "_view_state", None)
        if isinstance(view_state, dict):
            view_state["grid"] = self._grid_enabled
        canvas = self._canvas()
        if canvas is not None:
            if hasattr(canvas, "set_grid_visible"):
                canvas.set_grid_visible(self._grid_enabled)
            canvas.update()
        self._set_host_status(f"Grid {'On' if self._grid_enabled else 'Off'} | spacing {self._spacing_text()} {self._unit}")

    def _apply_unit_to_host(self) -> None:
        host = self._host()
        for item in getattr(host, "_status_items", []):
            if hasattr(item, "text") and item.text().startswith("Unit:"):
                item.setText(f"Unit: {self._unit}")
                break
        self._set_host_status(f"Unit {self._unit}")

    def _set_ruler(self, enabled: bool) -> None:
        self._ruler_enabled = enabled
        host = self._host()
        view_state = getattr(host, "_view_state", None)
        if isinstance(view_state, dict):
            view_state["ruler"] = enabled
        self._sync_rulers()
        self.ruler_changed.emit(enabled, self._unit)
        self.tool_requested.emit("ruler_on" if enabled else "ruler_off")
        self._refresh_tooltips()
        self._set_host_status(f"Ruler {'On' if enabled else 'Off'} | unit {self._unit}")

    def _sync_rulers(self) -> None:
        canvas = self._canvas()
        if canvas is None:
            return
        if self._ruler_enabled:
            if self._ruler_top is None or self._ruler_top.parent() is not canvas:
                self._ruler_top = _RulerOverlay(self, "top", canvas)
            if self._ruler_left is None or self._ruler_left.parent() is not canvas:
                self._ruler_left = _RulerOverlay(self, "left", canvas)
            self._position_rulers()
            self._ruler_top.show()
            self._ruler_left.show()
            self._ruler_top.raise_()
            self._ruler_left.raise_()
        else:
            if self._ruler_top is not None:
                self._ruler_top.hide()
            if self._ruler_left is not None:
                self._ruler_left.hide()

    def _position_rulers(self) -> None:
        canvas = self._canvas()
        if canvas is None:
            return
        if self._ruler_top is not None:
            self._ruler_top.setGeometry(30, 0, max(0, canvas.width() - 30), 24)
            self._ruler_top.update()
        if self._ruler_left is not None:
            self._ruler_left.setGeometry(0, 24, 30, max(0, canvas.height() - 24))
            self._ruler_left.update()

    def _refresh_tooltips(self) -> None:
        if (grid := self._buttons.get("grid")) is not None:
            grid.setToolTip(f"Grid: {'On' if self._grid_enabled else 'Off'} | spacing {self._spacing_text()} {self._unit}")
        if (ruler := self._buttons.get("ruler")) is not None:
            ruler.setToolTip(f"Ruler: {'On' if self._ruler_enabled else 'Off'} | unit {self._unit}")
        if (unit := self._buttons.get("unit")) is not None:
            unit.setToolTip(f"Unit: {self._unit}")
        if (zoom := self._buttons.get("zoom")) is not None:
            zoom.setToolTip("Zoom in, zoom out, or fit")

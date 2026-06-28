"""Reusable icon-based Start Bar component."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, QSize, Signal, Qt
from PySide6.QtGui import QColor, QCursor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QMenu, QPushButton, QRubberBand, QVBoxLayout, QWidget


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
UNIT_LABELS = {"mm": "millimeter", "cm": "centimeter", "m": "meter", "px": "pixel", "pt": "point", "in": "inch"}
UNIT_ORDER = ("mm", "cm", "m", "px", "pt", "in")
MM_TO_SCREEN_PX = 96.0 / 25.4
RULER_THICKNESS = 28
GUIDE_COLOR = QColor(255, 138, 53, 205)


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
        painter.drawRoundedRect(QRectF(center.x() - 4.2, center.y() - 4.2, 8.4, 8.4), 1.5, 1.5)
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


def _radio_icon(checked: bool) -> QIcon:
    pixmap = QPixmap(22, 22)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(QPen(QColor("#18314f"), 2.0))
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(QPointF(11, 11), 8.0, 8.0)
    if checked:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2f7df6"))
        painter.drawEllipse(QPointF(11, 11), 4.6, 4.6)
    painter.end()
    return QIcon(pixmap)


def _tool_icon(key: str) -> QIcon:
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
    elif key == "ruler":
        painter.drawRoundedRect(QRectF(8, 12, 21, 11), 2, 2)
        painter.setPen(QPen(ink, 1.1))
        for index, x in enumerate((12, 16, 20, 24)):
            painter.drawLine(QPointF(x, 12), QPointF(x, 19 if index % 2 == 0 else 17))
    elif key == "zoom":
        _paint_magnifier(painter, "in")
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


def _style_guide_menu(menu: QMenu) -> None:
    menu.setStyleSheet(
        "QMenu {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.55 #edf8ff, stop:1 #fff1d3); border:1px solid #8fa2bb; border-radius:10px; padding:6px;}"
        "QMenu::item {color:#1f3148; padding:6px 24px 6px 12px; border-radius:7px; font-size:12px; font-style:italic; font-weight:800;}"
        "QMenu::item:selected {background:#fff4cf; color:#132238;}"
    )


class _GuideLine(QWidget):
    def __init__(self, orientation: str, position: float, parent: QWidget, start_bar: "StartBar | None" = None, persistent: bool = True) -> None:
        super().__init__(parent)
        self.orientation = orientation
        self.position = position
        self._start_bar = start_bar
        self._persistent = persistent
        self._dragging = False
        self.setCursor(Qt.CursorShape.SizeVerCursor if orientation == "horizontal" else Qt.CursorShape.SizeHorCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._place()
        if self._start_bar is not None and self._persistent:
            self._start_bar._register_ruler_guide(self)
        self.show()

    def _place(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        if self.orientation == "horizontal":
            self.setGeometry(0, int(self.position) - 2, parent.width(), 5)
        else:
            self.setGeometry(int(self.position) - 2, 0, 5, parent.height())
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(GUIDE_COLOR, 1.6, Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap))
        if self.orientation == "horizontal":
            painter.drawLine(0, 2, self.width(), 2)
        else:
            painter.drawLine(2, 0, 2, self.height())
        painter.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._dragging and self.parentWidget() is not None:
            point = self.parentWidget().mapFromGlobal(event.globalPosition().toPoint())
            self.position = point.y() if self.orientation == "horizontal" else point.x()
            self._place()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._dragging = False
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = QMenu(self)
        _style_guide_menu(menu)
        delete = menu.addAction("Delete")
        chosen = menu.exec(event.globalPos())
        if chosen == delete:
            if self._start_bar is not None:
                self._start_bar._unregister_ruler_guide(self)
            self.deleteLater()


class _RulerOverlay(QWidget):
    def __init__(self, start_bar: "StartBar", orientation: str, parent: QWidget) -> None:
        super().__init__(parent)
        self._start_bar = start_bar
        self._orientation = orientation
        self._dragging_guide = False
        self._active_guide: _GuideLine | None = None
        self.setCursor(Qt.CursorShape.SizeVerCursor if orientation == "top" else Qt.CursorShape.SizeHorCursor)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(20, 37, 58, 230))
        font = painter.font()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        spacing = max(1.0, self._start_bar._unit_to_canvas_px(1.0, self._start_bar._unit))
        length = self.width() if self._orientation == "top" else self.height()
        zero = self._start_bar._ruler_origin.x() - self.x() if self._orientation == "top" else self._start_bar._ruler_origin.y() - self.y()
        index = int(-zero / spacing) - 2
        while True:
            position = zero + index * spacing
            if position > length + spacing:
                break
            if position >= 0:
                abs_index = abs(index)
                tick = 23 if abs_index % 10 == 0 else 16 if abs_index % 5 == 0 else 8
                if self._orientation == "top":
                    painter.drawLine(QPointF(position, self.height()), QPointF(position, self.height() - tick))
                    if abs_index % 10 == 0:
                        painter.drawText(QRectF(position + 2, 1, 46, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
                else:
                    painter.drawLine(QPointF(self.width(), position), QPointF(self.width() - tick, position))
                    if abs_index % 10 == 0:
                        painter.drawText(QRectF(2, position + 1, self.width() - 4, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
            index += 1
        painter.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging_guide = True
            self._create_or_move_guide(event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._dragging_guide:
            self._create_or_move_guide(event.globalPosition().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._dragging_guide:
            self._dragging_guide = False
            self._active_guide = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _create_or_move_guide(self, global_point: QPoint) -> None:
        canvas = self.parentWidget()
        if canvas is None:
            return
        point = canvas.mapFromGlobal(global_point)
        orientation = "horizontal" if self._orientation == "top" else "vertical"
        position = point.y() if orientation == "horizontal" else point.x()
        if self._active_guide is None:
            self._active_guide = _GuideLine(orientation, position, canvas, self._start_bar)
        else:
            self._active_guide.position = position
            self._active_guide._place()


class _RulerCorner(QWidget):
    def __init__(self, start_bar: "StartBar", parent: QWidget) -> None:
        super().__init__(parent)
        self._start_bar = start_bar
        self._dragging = False
        self._pressed = False
        self._press_pos: QPointF | None = None
        self._origin_h_guide: _GuideLine | None = None
        self._origin_v_guide: _GuideLine | None = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(13, 29, 48, 240))
        rect = QRectF(4, 4, self.width() - 8, self.height() - 8)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if self._pressed:
            gradient.setColorAt(0.0, QColor("#7f95b2"))
            gradient.setColorAt(1.0, QColor("#213d5f"))
        else:
            gradient.setColorAt(0.0, QColor("#ffffff"))
            gradient.setColorAt(0.48, QColor("#dff4ff"))
            gradient.setColorAt(1.0, QColor("#ffbf69"))
        path = QPainterPath()
        path.addRoundedRect(rect, 7, 7)
        painter.fillPath(path, gradient)
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        painter.drawPath(path)
        painter.setPen(QPen(QColor("#132238"), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(10, 18), QPointF(10, 9))
        painter.drawLine(QPointF(10, 18), QPointF(21, 18))
        painter.setBrush(QColor("#2f7df6"))
        painter.drawEllipse(QPointF(10, 18), 2.4, 2.4)
        painter.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._pressed = True
            self._press_pos = event.position()
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._dragging and self.parentWidget() is not None:
            if self._press_pos is not None:
                delta = event.position() - self._press_pos
                if abs(delta.x()) + abs(delta.y()) >= 4:
                    self._pressed = False
                    self.update()
                    self._preview_origin(event.globalPosition().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._dragging:
            self._dragging = False
            canvas = self.parentWidget()
            if canvas is not None:
                delta = QPointF(0, 0) if self._press_pos is None else event.position() - self._press_pos
                moved = abs(delta.x()) + abs(delta.y())
                if moved < 4:
                    self._start_bar._set_ruler_origin(QPointF(RULER_THICKNESS, RULER_THICKNESS), custom=True)
                else:
                    point = canvas.mapFromGlobal(event.globalPosition().toPoint())
                    self._start_bar._set_ruler_origin(QPointF(point), custom=True)
            self._pressed = False
            self._clear_origin_preview()
            self._press_pos = None
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _preview_origin(self, global_point: QPoint) -> None:
        canvas = self.parentWidget()
        if canvas is None:
            return
        point = canvas.mapFromGlobal(global_point)
        if self._origin_h_guide is None:
            self._origin_h_guide = _GuideLine("horizontal", point.y(), canvas, persistent=False)
        else:
            self._origin_h_guide.position = point.y()
            self._origin_h_guide._place()
        if self._origin_v_guide is None:
            self._origin_v_guide = _GuideLine("vertical", point.x(), canvas, persistent=False)
        else:
            self._origin_v_guide.position = point.x()
            self._origin_v_guide._place()

    def _clear_origin_preview(self) -> None:
        for guide in (self._origin_h_guide, self._origin_v_guide):
            if guide is not None:
                guide.deleteLater()
        self._origin_h_guide = None
        self._origin_v_guide = None


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
        self._zoom_mode: str | None = None
        self._zoom_origin: QPoint | None = None
        self._rubber_band: QRubberBand | None = None
        self._ruler_top: _RulerOverlay | None = None
        self._ruler_left: _RulerOverlay | None = None
        self._ruler_corner: _RulerCorner | None = None
        self._ruler_origin = QPointF(0, 0)
        self._ruler_origin_custom = False
        self._ruler_guides: list[_GuideLine] = []
        self._hooked_canvas: QWidget | None = None

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

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._ensure_canvas_hooks()
        self._apply_grid_to_host()

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
                if not self._ruler_origin_custom:
                    self._center_ruler_origin()
                self._position_rulers()
                return False
            if self._zoom_mode in {"zoom_in", "zoom_out"}:
                if event.type() in {QEvent.Type.Enter, QEvent.Type.MouseMove} and self._zoom_origin is None:
                    canvas.setCursor(_zoom_cursor(self._zoom_mode))
                    return event.type() == QEvent.Type.MouseMove
                if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                    canvas.setCursor(_zoom_cursor(self._zoom_mode))
                    self._zoom_origin = event.position().toPoint()
                    self._ensure_rubber_band()
                    if self._rubber_band is not None:
                        self._rubber_band.setGeometry(QRect(self._zoom_origin, QSize()))
                        self._rubber_band.show()
                    return True
                if event.type() == QEvent.Type.MouseMove and self._zoom_origin is not None:
                    canvas.setCursor(_zoom_cursor(self._zoom_mode))
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

    def _center_ruler_origin(self) -> None:
        canvas = self._canvas()
        if canvas is not None:
            self._ruler_origin = QPointF(canvas.width() / 2.0, canvas.height() / 2.0)

    def _ensure_canvas_hooks(self) -> None:
        canvas = self._canvas()
        if canvas is None:
            return
        if canvas is not self._hooked_canvas:
            if self._hooked_canvas is not None:
                self._hooked_canvas.removeEventFilter(self)
            canvas.installEventFilter(self)
            self._hooked_canvas = canvas
            self._ruler_origin_custom = False
            self._center_ruler_origin()
        if not getattr(canvas, "_start_bar_grid_hooked", False):
            def paint_grid(canvas_self, painter: QPainter) -> None:
                if not getattr(canvas_self, "_grid_visible", True):
                    return
                spacing = max(1.0, min(self._unit_to_canvas_px(self._grid_spacing, self._unit), 10000.0))
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
        if hasattr(canvas, "set_grid_visible"):
            canvas.set_grid_visible(self._grid_enabled)
        else:
            canvas.update()

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
        popup.setStyleSheet("QDialog#StartToolPopup {background:transparent;}")
        shell = QWidget()
        shell.setObjectName("StartToolPopupShell")
        shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        shell.setMinimumWidth(width)
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
        self._popup = popup
        return popup, layout

    def _show_popup_near(self, key: str, popup: QDialog) -> None:
        button = self._buttons.get(key)
        target = button.mapToGlobal(QPoint(0, button.height() + 4)) if button is not None else self.mapToGlobal(QPoint(0, self.height()))
        popup.adjustSize()
        popup.move(target)
        popup.show()

    def _radio_button(self, label: str, checked: bool, callback: Callable[[], None]) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("RadioChoice")
        button.setCheckable(True)
        button.setChecked(checked)
        button.setIcon(_radio_icon(checked))
        button.setIconSize(QSize(22, 22))
        button.clicked.connect(callback)
        return button

    def _refresh_radio_button(self, button: QPushButton, checked: bool) -> None:
        button.setChecked(checked)
        button.setIcon(_radio_icon(checked))

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
        popup, layout = self._popup_base(228)
        rows = (("mm", "cm", "m"), ("px", "pt", "in"))
        for row_units in rows:
            row = QHBoxLayout()
            row.setSpacing(6)
            for unit in row_units:
                button = self._radio_button(unit, unit == self._unit, lambda checked=False, selected=unit: self._set_unit(selected))
                button.setToolTip(UNIT_LABELS[unit])
                button.setFixedWidth(64)
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
        if self._ruler_enabled:
            self._sync_rulers()
        self.unit_changed.emit(unit)
        self.grid_changed.emit(self._grid_enabled, self._grid_spacing, self._unit)
        self.tool_requested.emit(f"unit_{unit}")
        self._refresh_tooltips()
        if self._popup is not None:
            self._popup.close()

    def _show_grid_popup(self, key: str) -> None:
        popup, layout = self._popup_base(220)
        row = QHBoxLayout()
        row.setSpacing(6)
        on_button = self._radio_button("Grid On", self._grid_enabled, lambda: self._set_grid_enabled(True))
        off_button = self._radio_button("Grid Off", not self._grid_enabled, lambda: self._set_grid_enabled(False))
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
        self._ensure_canvas_hooks()
        self._ruler_enabled = enabled
        if enabled and not self._ruler_origin_custom:
            self._center_ruler_origin()
        if not enabled:
            self._clear_ruler_guides()
        host = self._host()
        view_state = getattr(host, "_view_state", None)
        if isinstance(view_state, dict):
            view_state["ruler"] = enabled
        self._sync_rulers()
        self.ruler_changed.emit(enabled, self._unit)
        self.tool_requested.emit("ruler_on" if enabled else "ruler_off")
        self._refresh_tooltips()
        self._set_host_status(f"Ruler {'On' if enabled else 'Off'} | unit {self._unit}")

    def _set_ruler_origin(self, origin: QPointF, custom: bool = True) -> None:
        self._ruler_origin = origin
        self._ruler_origin_custom = custom
        self._position_rulers()
        canvas = self._canvas()
        if canvas is not None:
            canvas.update()
        self._apply_grid_to_host()

    def _register_ruler_guide(self, guide: _GuideLine) -> None:
        if guide not in self._ruler_guides:
            self._ruler_guides.append(guide)

    def _unregister_ruler_guide(self, guide: _GuideLine) -> None:
        if guide in self._ruler_guides:
            self._ruler_guides.remove(guide)

    def _clear_ruler_guides(self) -> None:
        for guide in tuple(self._ruler_guides):
            guide.deleteLater()
        self._ruler_guides.clear()

    def _sync_rulers(self) -> None:
        canvas = self._canvas()
        if canvas is None:
            return
        if self._ruler_enabled:
            if self._ruler_top is None or self._ruler_top.parent() is not canvas:
                self._ruler_top = _RulerOverlay(self, "top", canvas)
            if self._ruler_left is None or self._ruler_left.parent() is not canvas:
                self._ruler_left = _RulerOverlay(self, "left", canvas)
            if self._ruler_corner is None or self._ruler_corner.parent() is not canvas:
                self._ruler_corner = _RulerCorner(self, canvas)
            self._position_rulers()
            self._ruler_top.show()
            self._ruler_left.show()
            self._ruler_corner.show()
            self._ruler_top.raise_()
            self._ruler_left.raise_()
            self._ruler_corner.raise_()
        else:
            for widget in (self._ruler_top, self._ruler_left, self._ruler_corner):
                if widget is not None:
                    widget.hide()

    def _position_rulers(self) -> None:
        canvas = self._canvas()
        if canvas is None:
            return
        if self._ruler_top is not None:
            self._ruler_top.setGeometry(RULER_THICKNESS, 0, max(0, canvas.width() - RULER_THICKNESS), RULER_THICKNESS)
            self._ruler_top.update()
        if self._ruler_left is not None:
            self._ruler_left.setGeometry(0, RULER_THICKNESS, RULER_THICKNESS, max(0, canvas.height() - RULER_THICKNESS))
            self._ruler_left.update()
        if self._ruler_corner is not None:
            self._ruler_corner.setGeometry(0, 0, RULER_THICKNESS, RULER_THICKNESS)
            self._ruler_corner.update()

    def _refresh_tooltips(self) -> None:
        if (grid := self._buttons.get("grid")) is not None:
            grid.setToolTip(f"Grid: {'On' if self._grid_enabled else 'Off'} | spacing {self._spacing_text()} {self._unit}")
        if (ruler := self._buttons.get("ruler")) is not None:
            ruler.setToolTip(f"Ruler: {'On' if self._ruler_enabled else 'Off'} | unit {self._unit}")
        if (unit := self._buttons.get("unit")) is not None:
            unit.setToolTip(f"Unit: {self._unit}")
        if (zoom := self._buttons.get("zoom")) is not None:
            zoom.setToolTip("Zoom in, zoom out, or fit")

"""Shared start-bar controls for engineering workspaces."""

from __future__ import annotations

from collections.abc import Callable
from math import isclose

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, QSize, Signal, Qt
from PySide6.QtGui import (
    QColor,
    QCursor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QRegion,
)
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QRubberBand,
    QVBoxLayout,
    QWidget,
)

UNIT_TO_MM = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "px": 25.4 / 96.0,
    "in": 25.4,
    "pt": 25.4 / 72.0,
}
UNIT_ORDER = ("mm", "m", "cm", "px", "pt", "in")
MM_TO_SCREEN_PX = 96.0 / 25.4
GUIDE_COLOR = QColor(255, 138, 53, 210)
RULER_SIZE = 28


def _apply_rounded_mask(widget: QWidget, radius: int = 12) -> None:
    if widget.width() <= 0 or widget.height() <= 0:
        return
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, widget.width(), widget.height()), radius, radius)
    widget.setMask(QRegion(path.toFillPolygon().toPolygon()))


def _unit_to_mm(value: float, unit: str) -> float:
    return value * UNIT_TO_MM.get(unit, 1.0)


def _mm_to_unit(value_mm: float, unit: str) -> float:
    factor = UNIT_TO_MM.get(unit, 1.0)
    if isclose(factor, 0.0):
        return value_mm
    return value_mm / factor


def _round_icon(size: int, painter_fn: Callable[[QPainter, QRectF], None]) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    rect = QRectF(1, 1, size - 2, size - 2)
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, QColor("#ffffff"))
    gradient.setColorAt(0.45, QColor("#e8eef8"))
    gradient.setColorAt(1.0, QColor("#92abc9"))
    painter.setBrush(gradient)
    painter.setPen(QPen(QColor("#dce8f7"), 1.4))
    painter.drawRoundedRect(rect, 8, 8)
    painter_fn(painter, rect)
    painter.end()
    return QIcon(pixmap)


def _paint_magnifier(painter: QPainter, rect: QRectF, mode: str) -> None:
    painter.setPen(QPen(QColor("#0d243d"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    center = rect.center() + QPointF(-2.0, -2.0)
    radius = rect.width() * 0.23
    painter.drawEllipse(center, radius, radius)
    painter.drawLine(center + QPointF(radius * 0.72, radius * 0.72), rect.bottomRight() - QPointF(7, 7))
    painter.setPen(QPen(QColor("#2474d6"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    if mode == "in":
        painter.drawLine(center + QPointF(-radius * 0.48, 0), center + QPointF(radius * 0.48, 0))
        painter.drawLine(center + QPointF(0, -radius * 0.48), center + QPointF(0, radius * 0.48))
    elif mode == "out":
        painter.drawLine(center + QPointF(-radius * 0.48, 0), center + QPointF(radius * 0.48, 0))
    else:
        fit_rect = QRectF(center.x() - radius * 0.58, center.y() - radius * 0.58, radius * 1.16, radius * 1.16)
        painter.drawRoundedRect(fit_rect, 1.6, 1.6)


def _mini_zoom_icon(action: str) -> QIcon:
    mode = "fit" if action == "zoom_fit" else "in" if action == "zoom_in" else "out"
    return _round_icon(32, lambda painter, rect: _paint_magnifier(painter, rect, mode))


def _paint_unit_icon(painter: QPainter, rect: QRectF) -> None:
    painter.setPen(QPen(QColor("#0d243d"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    y = rect.center().y() + 3
    x1 = rect.left() + 7
    x2 = rect.right() - 7
    painter.drawLine(QPointF(x1, y), QPointF(x2, y))
    for index, x in enumerate((x1, x1 + 8, x1 + 16, x1 + 24, x2)):
        height = 10 if index in (0, 2, 4) else 6
        painter.drawLine(QPointF(x, y), QPointF(x, y - height))
    painter.setPen(QPen(QColor("#2474d6"), 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawText(QRectF(rect.left() + 6, rect.top() + 4, rect.width() - 12, 13), Qt.AlignmentFlag.AlignCenter, "mm")


def _paint_grid_icon(painter: QPainter, rect: QRectF) -> None:
    painter.setPen(QPen(QColor("#0d243d"), 1.35))
    left = rect.left() + 8
    top = rect.top() + 8
    step = 6
    for index in range(4):
        painter.drawLine(QPointF(left, top + index * step), QPointF(left + 18, top + index * step))
        painter.drawLine(QPointF(left + index * step, top), QPointF(left + index * step, top + 18))
    painter.setPen(QPen(QColor("#2474d6"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(left + 1, top + 18), QPointF(left + 18, top + 1))


def _paint_snap_icon(painter: QPainter, rect: QRectF) -> None:
    painter.setPen(QPen(QColor("#0d243d"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawArc(QRectF(rect.left() + 8, rect.top() + 6, 16, 18), 30 * 16, 230 * 16)
    painter.drawArc(QRectF(rect.left() + 16, rect.top() + 6, 16, 18), -80 * 16, 230 * 16)
    painter.setPen(QPen(QColor("#2474d6"), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(rect.center().x(), rect.top() + 8), QPointF(rect.center().x(), rect.bottom() - 8))


def _paint_ruler_icon(painter: QPainter, rect: QRectF) -> None:
    painter.setPen(QPen(QColor("#0d243d"), 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    box = QRectF(rect.left() + 7, rect.top() + 9, rect.width() - 14, 13)
    painter.drawRoundedRect(box, 3, 3)
    for index in range(5):
        x = box.left() + 4 + index * 5
        height = 8 if index % 2 == 0 else 5
        painter.drawLine(QPointF(x, box.top()), QPointF(x, box.top() + height))


def _paint_select_icon(painter: QPainter, rect: QRectF) -> None:
    painter.setPen(QPen(QColor("#0d243d"), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    points = QPolygonF([
        QPointF(rect.left() + 9, rect.top() + 7),
        QPointF(rect.left() + 24, rect.top() + 20),
        QPointF(rect.left() + 17, rect.top() + 21),
        QPointF(rect.left() + 20, rect.top() + 27),
        QPointF(rect.left() + 16, rect.top() + 28),
        QPointF(rect.left() + 13, rect.top() + 22),
        QPointF(rect.left() + 8, rect.top() + 27),
    ])
    painter.drawPolygon(points)


def _paint_undo_icon(painter: QPainter, rect: QRectF, flipped: bool = False) -> None:
    painter.setPen(QPen(QColor("#0d243d"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    if flipped:
        painter.drawArc(QRectF(rect.left() + 8, rect.top() + 8, 18, 16), 20 * 16, 250 * 16)
        painter.drawLine(QPointF(rect.right() - 7, rect.top() + 14), QPointF(rect.right() - 14, rect.top() + 9))
        painter.drawLine(QPointF(rect.right() - 7, rect.top() + 14), QPointF(rect.right() - 13, rect.top() + 19))
    else:
        painter.drawArc(QRectF(rect.left() + 8, rect.top() + 8, 18, 16), -90 * 16, 250 * 16)
        painter.drawLine(QPointF(rect.left() + 7, rect.top() + 14), QPointF(rect.left() + 14, rect.top() + 9))
        painter.drawLine(QPointF(rect.left() + 7, rect.top() + 14), QPointF(rect.left() + 13, rect.top() + 19))


def _style_guide_menu(menu: QMenu) -> None:
    menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint)
    menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    menu.setStyleSheet(
        """
        QMenu {
            background: #eaf2fb;
            border: 1px solid #9fb2c8;
            border-radius: 10px;
            padding: 5px;
            color: #0d243d;
            font-family: "Times New Roman";
            font-style: italic;
            font-weight: 700;
        }
        QMenu::item {
            padding: 6px 20px 6px 12px;
            border-radius: 7px;
        }
        QMenu::item:selected {
            background: #d6e6f8;
            color: #0d243d;
        }
        """
    )


class _RoundedPopupDialog(QDialog):
    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        _apply_rounded_mask(self, 14)


class _StartToolButton(QPushButton):
    def __init__(self, title: str, icon: QIcon, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StartToolButton")
        self.setToolTip(title)
        self.setIcon(icon)
        self.setIconSize(QSize(30, 30))
        self.setFixedSize(38, 36)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)


class _ToolPopupShell(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StartToolPopupShell")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)


class _RadioChoiceButton(QPushButton):
    def __init__(self, label: str, checked: bool, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self._checked = checked
        self.setObjectName("RadioChoiceButton")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMinimumHeight(30)
        self.setCheckable(False)

    def set_checked(self, checked: bool) -> None:
        self._checked = checked
        self.update()

    def paintEvent(self, event):  # type: ignore[override]
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(15, self.height() / 2)
        painter.setPen(QPen(QColor("#17324c"), 1.5))
        painter.setBrush(QColor("#f8fbff"))
        painter.drawEllipse(center, 6.2, 6.2)
        if self._checked:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#2474d6"))
            painter.drawEllipse(center, 3.3, 3.3)
        painter.end()


class _GuideLine(QWidget):
    def __init__(self, orientation: str, position: float, parent: QWidget, start_bar: "StartBar" | None = None, persistent: bool = True) -> None:
        super().__init__(parent)
        self.orientation = orientation
        self.position = position
        self._start_bar = start_bar
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self._drag_start: QPoint | None = None
        self._position_start = position
        if orientation == "vertical":
            self.setGeometry(int(position) - 4, 0, 8, parent.height())
        else:
            self.setGeometry(0, int(position) - 4, parent.width(), 8)
        self.show()
        if persistent and self._start_bar is not None:
            self._start_bar._register_ruler_guide(self)

    def paintEvent(self, event):  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(GUIDE_COLOR, 1.7, Qt.PenStyle.DashLine)
        pen.setDashPattern([5, 4])
        painter.setPen(pen)
        if self.orientation == "vertical":
            x = self.width() / 2
            painter.drawLine(QPointF(x, 0), QPointF(x, self.height()))
        else:
            y = self.height() / 2
            painter.drawLine(QPointF(0, y), QPointF(self.width(), y))

    def mousePressEvent(self, event):  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint()
            self._position_start = self.position
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # type: ignore[override]
        if self._drag_start is None:
            super().mouseMoveEvent(event)
            return
        delta = event.globalPosition().toPoint() - self._drag_start
        if self.orientation == "vertical":
            self.position = max(0, min(self.parentWidget().width(), self._position_start + delta.x()))
            self.setGeometry(int(self.position) - 4, 0, 8, self.parentWidget().height())
        else:
            self.position = max(0, min(self.parentWidget().height(), self._position_start + delta.y()))
            self.setGeometry(0, int(self.position) - 4, self.parentWidget().width(), 8)
        event.accept()

    def mouseReleaseEvent(self, event):  # type: ignore[override]
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):  # type: ignore[override]
        menu = QMenu(self)
        _style_guide_menu(menu)
        delete = menu.addAction("Delete")
        chosen = menu.exec(event.globalPos())
        if chosen == delete:
            if self._start_bar is not None:
                self._start_bar._unregister_ruler_guide(self)
            self.deleteLater()


class _RulerOverlay(QWidget):
    def __init__(self, orientation: str, canvas: QWidget, start_bar: "StartBar") -> None:
        super().__init__(canvas)
        self.orientation = orientation
        self._canvas = canvas
        self._start_bar = start_bar
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._dragging = False
        self._preview: _GuideLine | None = None

    def paintEvent(self, event):  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(238, 244, 251, 238))
        painter.setPen(QPen(QColor("#a9bbcf"), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        font = painter.font()
        font.setPointSize(7)
        font.setBold(False)
        painter.setFont(font)
        unit = self._start_bar.current_unit
        step_px = max(8.0, self._start_bar._grid_spacing_mm * MM_TO_SCREEN_PX)
        origin = self._start_bar._ruler_origin
        if self.orientation == "top":
            zero = origin.x() - self.x()
            self._paint_horizontal_ticks(painter, zero, step_px, unit)
        else:
            zero = origin.y() - self.y()
            self._paint_vertical_ticks(painter, zero, step_px, unit)

    def _paint_horizontal_ticks(self, painter: QPainter, zero: float, step_px: float, unit: str) -> None:
        width = self.width()
        painter.setPen(QPen(QColor("#17324c"), 1))
        index_start = int((0 - zero) // step_px) - 2
        index_end = int((width - zero) // step_px) + 2
        for index in range(index_start, index_end + 1):
            x = zero + index * step_px
            if x < 0 or x > width:
                continue
            magnitude = abs(index)
            if magnitude % 10 == 0:
                length = 17
                label = str(int(_mm_to_unit(index * self._start_bar._grid_spacing_mm, unit)))
                painter.drawText(QRectF(x - 16, 1, 32, 10), Qt.AlignmentFlag.AlignCenter, label)
            elif magnitude % 5 == 0:
                length = 12
            else:
                length = 7
            painter.drawLine(QPointF(x, self.height()), QPointF(x, self.height() - length))

    def _paint_vertical_ticks(self, painter: QPainter, zero: float, step_px: float, unit: str) -> None:
        height = self.height()
        painter.setPen(QPen(QColor("#17324c"), 1))
        index_start = int((0 - zero) // step_px) - 2
        index_end = int((height - zero) // step_px) + 2
        for index in range(index_start, index_end + 1):
            y = zero + index * step_px
            if y < 0 or y > height:
                continue
            magnitude = abs(index)
            if magnitude % 10 == 0:
                length = 17
                label = str(int(_mm_to_unit(index * self._start_bar._grid_spacing_mm, unit)))
                painter.save()
                painter.translate(2, y + 10)
                painter.rotate(-90)
                painter.drawText(QRectF(-16, -2, 32, 10), Qt.AlignmentFlag.AlignCenter, label)
                painter.restore()
            elif magnitude % 5 == 0:
                length = 12
            else:
                length = 7
            painter.drawLine(QPointF(self.width(), y), QPointF(self.width() - length, y))

    def mousePressEvent(self, event):  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # type: ignore[override]
        if not self._dragging:
            super().mouseMoveEvent(event)
            return
        pos = self.mapToParent(event.position().toPoint())
        if self._preview is None:
            orientation = "horizontal" if self.orientation == "top" else "vertical"
            self._preview = _GuideLine(orientation, pos.y() if orientation == "horizontal" else pos.x(), self._canvas, self._start_bar, persistent=False)
        else:
            if self._preview.orientation == "horizontal":
                self._preview.position = pos.y()
                self._preview.setGeometry(0, int(pos.y()) - 4, self._canvas.width(), 8)
            else:
                self._preview.position = pos.x()
                self._preview.setGeometry(int(pos.x()) - 4, 0, 8, self._canvas.height())
        event.accept()

    def mouseReleaseEvent(self, event):  # type: ignore[override]
        if self._dragging:
            pos = self.mapToParent(event.position().toPoint())
            orientation = "horizontal" if self.orientation == "top" else "vertical"
            _GuideLine(orientation, pos.y() if orientation == "horizontal" else pos.x(), self._canvas, self._start_bar)
            if self._preview is not None:
                self._preview.deleteLater()
                self._preview = None
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


class _RulerCorner(QWidget):
    def __init__(self, canvas: QWidget, start_bar: "StartBar") -> None:
        super().__init__(canvas)
        self._canvas = canvas
        self._start_bar = start_bar
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._dragging = False
        self._preview_h: _GuideLine | None = None
        self._preview_v: _GuideLine | None = None

    def paintEvent(self, event):  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(4, 4, self.width() - 8, self.height() - 8)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor("#ffffff"))
        gradient.setColorAt(1.0, QColor("#adc0d7"))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#7f96b0"), 1.3))
        painter.drawRoundedRect(rect, 7, 7)
        painter.setPen(QPen(QColor("#0d243d"), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(rect.center() + QPointF(-5, 0), rect.center() + QPointF(5, 0))
        painter.drawLine(rect.center() + QPointF(0, -5), rect.center() + QPointF(0, 5))

    def mousePressEvent(self, event):  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # type: ignore[override]
        if not self._dragging:
            super().mouseMoveEvent(event)
            return
        pos = self.mapToParent(event.position().toPoint())
        if self._preview_h is None:
            self._preview_h = _GuideLine("horizontal", pos.y(), self._canvas, self._start_bar, persistent=False)
            self._preview_v = _GuideLine("vertical", pos.x(), self._canvas, self._start_bar, persistent=False)
        else:
            self._preview_h.position = pos.y()
            self._preview_h.setGeometry(0, int(pos.y()) - 4, self._canvas.width(), 8)
            self._preview_v.position = pos.x()
            self._preview_v.setGeometry(int(pos.x()) - 4, 0, 8, self._canvas.height())
        event.accept()

    def mouseReleaseEvent(self, event):  # type: ignore[override]
        if self._dragging:
            pos = self.mapToParent(event.position().toPoint())
            moved = self._preview_h is not None or self._preview_v is not None
            if moved:
                self._start_bar._set_ruler_origin(QPointF(pos.x(), pos.y()), custom=True)
            else:
                self._start_bar._set_ruler_origin(QPointF(RULER_SIZE, RULER_SIZE), custom=True)
            for preview in (self._preview_h, self._preview_v):
                if preview is not None:
                    preview.deleteLater()
            self._preview_h = None
            self._preview_v = None
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


class StartBar(QWidget):
    action_requested = Signal(str)
    unit_changed = Signal(str)
    grid_changed = Signal(bool, float, str)
    snap_changed = Signal(bool)
    zoom_requested = Signal(str)

    def __init__(self, host_window: QWidget | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._host_window = host_window
        self.current_unit = "mm"
        self._grid_enabled = True
        self._grid_spacing = 4.0
        self._grid_spacing_mm = _unit_to_mm(self._grid_spacing, self.current_unit)
        self._snap_enabled = False
        self._active_zoom_mode: str | None = None
        self._rubber_band: QRubberBand | None = None
        self._rubber_origin: QPoint | None = None
        self._canvas: QWidget | None = None
        self._grid_hooked = False
        self._ruler_enabled = False
        self._ruler_origin = QPointF(0.0, 0.0)
        self._ruler_custom_origin = False
        self._top_ruler: _RulerOverlay | None = None
        self._left_ruler: _RulerOverlay | None = None
        self._ruler_corner: _RulerCorner | None = None
        self._ruler_guides: list[_GuideLine] = []
        self.setObjectName("StartBar")
        self.setMinimumHeight(50)
        self.setMaximumHeight(62)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(8)

        self._buttons: dict[str, _StartToolButton] = {}
        specs: list[tuple[str, str, QIcon, Callable[[], None]]] = [
            ("select", "Select", _round_icon(32, _paint_select_icon), lambda: self.action_requested.emit("select")),
            ("undo", "Undo", _round_icon(32, lambda painter, rect: _paint_undo_icon(painter, rect, False)), lambda: self.action_requested.emit("undo")),
            ("redo", "Redo", _round_icon(32, lambda painter, rect: _paint_undo_icon(painter, rect, True)), lambda: self.action_requested.emit("redo")),
            ("zoom", "Zoom", _mini_zoom_icon("zoom_in"), self._show_zoom_popup),
            ("ruler", "Ruler", _round_icon(32, _paint_ruler_icon), self._toggle_ruler),
            ("grid", "Grid", _round_icon(32, _paint_grid_icon), self._show_grid_popup),
            ("snap", "Snap", _round_icon(32, _paint_snap_icon), self._show_snap_popup),
            ("unit", "Unit", _round_icon(32, _paint_unit_icon), self._show_unit_popup),
        ]
        for key, title, icon, callback in specs:
            button = _StartToolButton(title, icon, self)
            button.clicked.connect(callback)
            layout.addWidget(button)
            self._buttons[key] = button
        layout.addStretch(1)
        self._refresh_buttons()

    def showEvent(self, event):  # type: ignore[override]
        super().showEvent(event)
        self.sync_with_canvas()

    def sync_with_canvas(self) -> None:
        self._ensure_canvas_hooks()
        self._apply_grid_to_host()

    def set_tool_visible(self, key: str, visible: bool) -> None:
        button = self._buttons.get(key)
        if button is not None:
            button.setVisible(visible)

    def _popup_base(self, width: int) -> tuple[QDialog, QVBoxLayout]:
        popup = _RoundedPopupDialog(self)
        popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        popup.setFixedWidth(width)
        root = QVBoxLayout(popup)
        root.setContentsMargins(0, 0, 0, 0)
        shell = _ToolPopupShell(popup)
        shell.setStyleSheet(
            """
            #StartToolPopupShell {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fbff, stop:0.55 #e9f1fb, stop:1 #d3e0ef);
                border: 1px solid #9fb2c8;
                border-radius: 13px;
            }
            QPushButton {
                border: none;
                background: transparent;
                color: #0d243d;
                font-family: "Times New Roman";
                font-style: italic;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.38);
                border-radius: 8px;
            }
            #RadioChoiceButton {
                text-align: left;
                padding-left: 30px;
                padding-right: 10px;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.18);
            }
            #RadioChoiceButton:hover {
                background: rgba(255, 255, 255, 0.42);
            }
            QDoubleSpinBox {
                background: #f8fbff;
                border: 1px solid #a9bbcf;
                border-radius: 8px;
                color: #0d243d;
                font-family: "Times New Roman";
                font-style: italic;
                font-weight: 700;
                padding: 3px 8px;
            }
            QLabel {
                color: #0d243d;
                font-family: "Times New Roman";
                font-style: italic;
                font-weight: 700;
            }
            """
        )
        root.addWidget(shell)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(9, 9, 9, 9)
        layout.setSpacing(6)
        return popup, layout

    def _show_zoom_popup(self) -> None:
        popup, layout = self._popup_base(156)
        row = QHBoxLayout()
        row.setSpacing(7)
        for action, tooltip in (("zoom_in", "Zoom In"), ("zoom_out", "Zoom Out"), ("zoom_fit", "Zoom Fit")):
            button = QPushButton(popup)
            button.setToolTip(tooltip)
            button.setIcon(_mini_zoom_icon(action))
            button.setIconSize(QSize(31, 31))
            button.setFixedSize(38, 36)
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            button.clicked.connect(lambda checked=False, name=action, dialog=popup: self._choose_zoom_mode(name, dialog))
            row.addWidget(button)
        layout.addLayout(row)
        self._show_popup_under_button(popup, self._buttons["zoom"])

    def _choose_zoom_mode(self, action: str, dialog: QDialog) -> None:
        dialog.close()
        self.zoom_requested.emit(action)
        if action == "zoom_fit":
            self._active_zoom_mode = None
            self._apply_zoom_fit()
        else:
            self._active_zoom_mode = action
            self._ensure_canvas_hooks()
            if self._canvas is not None:
                self._canvas.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    def _show_unit_popup(self) -> None:
        popup, layout = self._popup_base(218)
        unit_buttons: dict[str, _RadioChoiceButton] = {}
        for row_units in (("mm", "m", "cm"), ("px", "pt", "in")):
            row = QHBoxLayout()
            row.setSpacing(6)
            for unit in row_units:
                button = _RadioChoiceButton(unit, unit == self.current_unit, popup)
                button.setFixedWidth(62)
                button.clicked.connect(lambda checked=False, name=unit, dialog=popup: self._set_unit(name, dialog))
                row.addWidget(button)
                unit_buttons[unit] = button
            layout.addLayout(row)
        self._show_popup_under_button(popup, self._buttons["unit"])

    def _show_grid_popup(self) -> None:
        popup, layout = self._popup_base(190)
        on_button = _RadioChoiceButton("Grid On", self._grid_enabled, popup)
        off_button = _RadioChoiceButton("Grid Off", not self._grid_enabled, popup)
        layout.addWidget(on_button)
        layout.addWidget(off_button)
        spacing_row = QHBoxLayout()
        spacing_label = QLabel("Spacing")
        spacing_input = QDoubleSpinBox(popup)
        spacing_input.setRange(0.01, 100000.0)
        spacing_input.setDecimals(3)
        spacing_input.setSingleStep(1.0)
        spacing_input.setValue(self._grid_spacing)
        spacing_input.setSuffix(f" {self.current_unit}")
        spacing_row.addWidget(spacing_label)
        spacing_row.addWidget(spacing_input, 1)
        layout.addLayout(spacing_row)

        def apply_state(enabled: bool) -> None:
            self._grid_enabled = enabled
            on_button.set_checked(enabled)
            off_button.set_checked(not enabled)
            self._set_grid_spacing(spacing_input.value())

        on_button.clicked.connect(lambda: apply_state(True))
        off_button.clicked.connect(lambda: apply_state(False))
        spacing_input.valueChanged.connect(self._set_grid_spacing)
        self._show_popup_under_button(popup, self._buttons["grid"])

    def _show_snap_popup(self) -> None:
        popup, layout = self._popup_base(162)
        on_button = _RadioChoiceButton("Snap On", self._snap_enabled, popup)
        off_button = _RadioChoiceButton("Snap Off", not self._snap_enabled, popup)
        layout.addWidget(on_button)
        layout.addWidget(off_button)

        def apply_state(enabled: bool) -> None:
            self._snap_enabled = enabled
            on_button.set_checked(enabled)
            off_button.set_checked(not enabled)
            self.snap_changed.emit(enabled)
            self._refresh_buttons()

        on_button.clicked.connect(lambda: apply_state(True))
        off_button.clicked.connect(lambda: apply_state(False))
        self._show_popup_under_button(popup, self._buttons["snap"])

    def _show_popup_under_button(self, popup: QDialog, button: QWidget) -> None:
        popup.adjustSize()
        _apply_rounded_mask(popup, 14)
        point = button.mapToGlobal(QPoint(0, button.height() + 4))
        popup.move(point)
        popup.show()

    def _set_unit(self, unit: str, dialog: QDialog | None = None) -> None:
        old_spacing_mm = self._grid_spacing_mm
        self.current_unit = unit
        self._grid_spacing = _mm_to_unit(old_spacing_mm, unit)
        self._grid_spacing_mm = old_spacing_mm
        self.unit_changed.emit(unit)
        self.grid_changed.emit(self._grid_enabled, self._grid_spacing, self.current_unit)
        self._apply_grid_to_host()
        self._refresh_buttons()
        if dialog is not None:
            dialog.close()

    def _set_grid_spacing(self, spacing: float) -> None:
        self._grid_spacing = spacing
        self._grid_spacing_mm = _unit_to_mm(spacing, self.current_unit)
        self.grid_changed.emit(self._grid_enabled, self._grid_spacing, self.current_unit)
        self._apply_grid_to_host()
        self._refresh_rulers()

    def _toggle_ruler(self) -> None:
        self._ruler_enabled = not self._ruler_enabled
        self._ensure_canvas_hooks()
        self._refresh_rulers()
        self._refresh_buttons()

    def _refresh_buttons(self) -> None:
        self._buttons["grid"].setProperty("active", self._grid_enabled)
        self._buttons["snap"].setProperty("active", self._snap_enabled)
        self._buttons["ruler"].setProperty("active", self._ruler_enabled)
        for button in self._buttons.values():
            button.style().unpolish(button)
            button.style().polish(button)

    def _ensure_canvas_hooks(self) -> None:
        if self._canvas is None:
            self._canvas = self._find_canvas()
        canvas = self._canvas
        if canvas is None:
            return
        canvas._grid_spacing = self._grid_spacing_mm * MM_TO_SCREEN_PX
        canvas._grid_unit = self.current_unit
        canvas._grid_origin = self._ruler_origin
        if hasattr(canvas, "set_grid_visible"):
            canvas.set_grid_visible(self._grid_enabled)
        else:
            canvas._grid_visible = self._grid_enabled
        if not self._grid_hooked:
            canvas.installEventFilter(self)
            self._grid_hooked = True
        canvas.update()

    def _find_canvas(self) -> QWidget | None:
        if self._host_window is None:
            return None
        for candidate in self._host_window.findChildren(QWidget):
            if candidate.objectName() in {"DesignCanvas", "WorkspaceCanvas", "Canvas"}:
                return candidate
        return None

    def _apply_grid_to_host(self) -> None:
        self._ensure_canvas_hooks()
        canvas = self._canvas
        if canvas is None:
            return
        canvas._grid_spacing = self._grid_spacing_mm * MM_TO_SCREEN_PX
        canvas._grid_unit = self.current_unit
        canvas._grid_origin = self._ruler_origin
        if hasattr(canvas, "set_grid_visible"):
            canvas.set_grid_visible(self._grid_enabled)
        else:
            canvas._grid_visible = self._grid_enabled
            canvas.update()
        if self._ruler_enabled:
            self._refresh_rulers()

    def _refresh_rulers(self) -> None:
        canvas = self._canvas
        if canvas is None:
            return
        if not self._ruler_custom_origin:
            self._center_ruler_origin()
        if not self._ruler_enabled:
            for widget in (self._top_ruler, self._left_ruler, self._ruler_corner):
                if widget is not None:
                    widget.hide()
            for guide in self._ruler_guides:
                guide.hide()
            return
        if self._top_ruler is None:
            self._top_ruler = _RulerOverlay("top", canvas, self)
            self._left_ruler = _RulerOverlay("left", canvas, self)
            self._ruler_corner = _RulerCorner(canvas, self)
        self._position_rulers()
        for widget in (self._top_ruler, self._left_ruler, self._ruler_corner):
            widget.show()
            widget.raise_()
            widget.update()
        for guide in self._ruler_guides:
            guide.show()
            guide.raise_()

    def _position_rulers(self) -> None:
        canvas = self._canvas
        if canvas is None or self._top_ruler is None or self._left_ruler is None or self._ruler_corner is None:
            return
        self._top_ruler.setGeometry(RULER_SIZE, 0, max(0, canvas.width() - RULER_SIZE), RULER_SIZE)
        self._left_ruler.setGeometry(0, RULER_SIZE, RULER_SIZE, max(0, canvas.height() - RULER_SIZE))
        self._ruler_corner.setGeometry(0, 0, RULER_SIZE, RULER_SIZE)
        for guide in self._ruler_guides:
            if guide.orientation == "vertical":
                guide.setGeometry(int(guide.position) - 4, 0, 8, canvas.height())
            else:
                guide.setGeometry(0, int(guide.position) - 4, canvas.width(), 8)

    def _center_ruler_origin(self) -> None:
        canvas = self._canvas
        if canvas is None:
            return
        self._ruler_origin = QPointF(canvas.width() / 2.0, canvas.height() / 2.0)
        canvas._grid_origin = self._ruler_origin

    def _set_ruler_origin(self, origin: QPointF, custom: bool = False) -> None:
        canvas = self._canvas
        if canvas is None:
            return
        self._ruler_origin = QPointF(max(0.0, min(canvas.width(), origin.x())), max(0.0, min(canvas.height(), origin.y())))
        self._ruler_custom_origin = custom
        canvas._grid_origin = self._ruler_origin
        canvas.update()
        self._refresh_rulers()

    def _register_ruler_guide(self, guide: _GuideLine) -> None:
        if guide not in self._ruler_guides:
            self._ruler_guides.append(guide)

    def _unregister_ruler_guide(self, guide: _GuideLine) -> None:
        if guide in self._ruler_guides:
            self._ruler_guides.remove(guide)

    def eventFilter(self, watched, event):  # type: ignore[override]
        canvas = self._canvas
        if watched is canvas:
            if event.type() == QEvent.Type.Resize:
                self._refresh_rulers()
            if event.type() == QEvent.Type.MouseButtonPress and self._active_zoom_mode in {"zoom_in", "zoom_out"}:
                if event.button() == Qt.MouseButton.LeftButton:
                    self._rubber_origin = event.position().toPoint()
                    if self._rubber_band is None:
                        self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, canvas)
                    self._rubber_band.setGeometry(QRect(self._rubber_origin, QSize()))
                    self._rubber_band.show()
                    return True
            if event.type() == QEvent.Type.MouseMove and self._rubber_origin is not None and self._rubber_band is not None:
                self._rubber_band.setGeometry(QRect(self._rubber_origin, event.position().toPoint()).normalized())
                return True
            if event.type() == QEvent.Type.MouseButtonRelease and self._rubber_origin is not None:
                rect = QRect(self._rubber_origin, event.position().toPoint()).normalized()
                if self._rubber_band is not None:
                    self._rubber_band.hide()
                self._apply_zoom_rect(rect)
                self._rubber_origin = None
                self._active_zoom_mode = None
                canvas.unsetCursor()
                return True
        return super().eventFilter(watched, event)

    def _apply_zoom_rect(self, rect: QRect) -> None:
        if self._canvas is None or rect.width() < 6 or rect.height() < 6:
            return
        factor = 1.25 if self._active_zoom_mode == "zoom_in" else 0.8
        host = self._host_window
        if host is not None and hasattr(host, "adjust_zoom"):
            host.adjust_zoom(factor)
        self.zoom_requested.emit(self._active_zoom_mode or "zoom_in")

    def _apply_zoom_fit(self) -> None:
        host = self._host_window
        if host is not None and hasattr(host, "set_zoom"):
            host.set_zoom(100.0)
        self.zoom_requested.emit("zoom_fit")

    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(640, 54)

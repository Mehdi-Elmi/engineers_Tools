"""Final last-mile overrides for fixed viewport resize, rulers, cursors, rotation, and F8."""

from __future__ import annotations

import logging
import math

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, QRect, QRectF, QSize, QTimer, Qt
from PySide6.QtGui import QColor, QCursor, QKeySequence, QPainter, QPainterPath, QPen, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

VERSION = "last-mile-2"
EDGE_MARGIN = 24
WORKSPACE_SIZE_MM = (400.0, 220.0)
_RESIZE_FILTER: QObject | None = None
_ORIGINAL_CANVAS_KEY_PRESS = None
_ORIGINAL_CANVAS_PAINT = None
_ORIGINAL_CANVAS_RELEASE = None
_ORIGINAL_SHORTCUT_INSTALLER = None
_ORIGINAL_RULER_OVERLAY_INIT = None
_ORIGINAL_RULER_GUIDE_INIT = None
_ORIGINAL_RULER_CORNER_INIT = None
_ORIGINAL_MENU_DIALOG_INIT = None
_TRACKED_WINDOWS: set[int] = set()


def _asset_cursor(file_name: str, fallback: QCursor, hot_x: int = 10, hot_y: int = 8, size: int = 20) -> QCursor:
    try:
        from . import engineering_ui_small_fixes_patch as small

        return small._asset_cursor(file_name, fallback, hot_x, hot_y, size)
    except Exception:
        return fallback


def _usable_area(canvas) -> QRectF:
    ruler_left = 0
    ruler_top = 0
    try:
        start_bar = getattr(canvas.window(), "_start_bar_widget", None)
        if start_bar is not None and getattr(start_bar, "_ruler_enabled", False):
            from src.engineers_tools.ui import start_bar as sb

            ruler_left = sb.RULER_THICKNESS
            ruler_top = sb.RULER_THICKNESS
    except Exception:
        ruler_left = 0
        ruler_top = 0
    return QRectF(
        ruler_left + 6,
        ruler_top + 3,
        max(80.0, float(canvas.width() - ruler_left - 12)),
        max(80.0, float(canvas.height() - ruler_top - 8)),
    )


def _page_rect(canvas) -> QRectF:
    area = _usable_area(canvas)
    ratio = WORKSPACE_SIZE_MM[1] / WORKSPACE_SIZE_MM[0]
    width = min(area.width(), area.height() / ratio)
    height = width * ratio
    if height > area.height():
        height = area.height()
        width = height / ratio
    return QRectF(area.center().x() - width / 2.0, area.center().y() - height / 2.0, width, height)


def _unit_factor(unit: str) -> float:
    try:
        from src.engineers_tools.ui import start_bar as sb

        return float(sb.UNIT_TO_MM.get(unit, 1.0))
    except Exception:
        return 1.0


def _unit_to_canvas_px(start_bar, value: float, unit: str, orientation: str = "top") -> float:
    canvas = start_bar._canvas() if hasattr(start_bar, "_canvas") else None
    if canvas is None:
        return max(1.0, float(value))
    page = _page_rect(canvas)
    mm_value = float(value) * _unit_factor(unit)
    if orientation in {"left", "vertical", "y"}:
        return max(1.0, mm_value * page.height() / WORKSPACE_SIZE_MM[1])
    return max(1.0, mm_value * page.width() / WORKSPACE_SIZE_MM[0])


def _window_edges(window, pos: QPoint) -> set[str]:
    if getattr(window, "_is_manually_maximized", False) or window.isMaximized() or window.isMinimized():
        return set()
    rect = window.rect()
    if pos.x() < 0 or pos.y() < 0 or pos.x() > rect.width() or pos.y() > rect.height():
        return set()
    edges: set[str] = set()
    if pos.x() <= EDGE_MARGIN:
        edges.add("left")
    if pos.x() >= rect.width() - EDGE_MARGIN:
        edges.add("right")
    if pos.y() <= EDGE_MARGIN:
        edges.add("top")
    if pos.y() >= rect.height() - EDGE_MARGIN:
        edges.add("bottom")
    return edges


def _resize_cursor(edges: set[str]) -> QCursor:
    if {"left", "top"} <= edges or {"right", "bottom"} <= edges:
        return _asset_cursor("corner_resize_a.svg", QCursor(Qt.CursorShape.SizeFDiagCursor), 12, 12, 22)
    if {"right", "top"} <= edges or {"left", "bottom"} <= edges:
        return _asset_cursor("corner_resize_b.svg", QCursor(Qt.CursorShape.SizeBDiagCursor), 12, 12, 22)
    if "left" in edges or "right" in edges:
        return _asset_cursor("resize_horizontal.svg", QCursor(Qt.CursorShape.SizeHorCursor), 12, 12, 22)
    if "top" in edges or "bottom" in edges:
        return _asset_cursor("resize_vertical.svg", QCursor(Qt.CursorShape.SizeVerCursor), 12, 12, 22)
    return QCursor(Qt.CursorShape.ArrowCursor)


def _minimum_resize_size(window) -> QSize:
    hint = window.minimumSizeHint()
    min_w = max(int(window.minimumWidth()), int(hint.width()), 360)
    min_h = max(int(window.minimumHeight()), int(hint.height()), 240)
    if window.__class__.__name__ == "ModuleWindow":
        min_w = max(760, min_w)
        min_h = max(500, min_h)
    return QSize(min_w, min_h)


def _apply_window_resize(window, global_pos: QPoint) -> None:
    edges = (
        getattr(window, "_last_mile_resize_edges", None)
        or getattr(window, "_fixed_resize_edges", None)
        or getattr(window, "_window_resize_edges", set())
    )
    start_global = (
        getattr(window, "_last_mile_resize_start_global", None)
        or getattr(window, "_fixed_resize_start_global", None)
        or getattr(window, "_window_resize_start_global", global_pos)
    )
    start_rect = (
        getattr(window, "_last_mile_resize_start_geometry", None)
        or getattr(window, "_fixed_resize_start_geometry", None)
        or getattr(window, "_window_resize_start_geometry", window.geometry())
    )
    delta = global_pos - start_global
    rect = QRect(start_rect)
    minimum = _minimum_resize_size(window)
    if "left" in edges:
        rect.setLeft(min(start_rect.left() + delta.x(), start_rect.right() - minimum.width()))
    if "right" in edges:
        rect.setRight(max(start_rect.right() + delta.x(), start_rect.left() + minimum.width()))
    if "top" in edges:
        rect.setTop(min(start_rect.top() + delta.y(), start_rect.bottom() - minimum.height()))
    if "bottom" in edges:
        rect.setBottom(max(start_rect.bottom() + delta.y(), start_rect.top() + minimum.height()))
    window.setGeometry(rect.normalized())


def _is_control_button(widget: QWidget | None) -> bool:
    current = widget
    depth = 0
    while isinstance(current, QWidget) and depth < 4:
        if isinstance(current, QPushButton):
            text = current.text().strip()
            name = current.objectName().lower()
            if text in {"×", "x", "□", "❐", "[]", "[ ]", "-", "_"}:
                return True
            if any(key in name for key in ("close", "max", "min", "windowcontrol")):
                return True
        current = current.parentWidget()
        depth += 1
    return False


def _resizable_toplevel(widget) -> QWidget | None:
    if not isinstance(widget, QWidget):
        return None
    window = widget.window()
    if not isinstance(window, QWidget):
        return None
    flags = window.windowFlags()
    if flags & Qt.WindowType.Popup:
        return None
    if not (flags & Qt.WindowType.FramelessWindowHint):
        return None
    if not window.isVisible() or window.isMinimized() or window.isMaximized():
        return None
    return window


def _global_position(event) -> QPoint | None:
    getter = getattr(event, "globalPosition", None)
    if callable(getter):
        return getter().toPoint()
    getter = getattr(event, "globalPos", None)
    return getter() if callable(getter) else None


def _prepare_tracking(window: QWidget) -> None:
    key = id(window)
    if key in _TRACKED_WINDOWS:
        return
    _TRACKED_WINDOWS.add(key)
    for child in [window, *window.findChildren(QWidget)]:
        try:
            child.setMouseTracking(True)
            child.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        except Exception:
            pass


def _sync_rulers(window) -> None:
    canvas = getattr(window, "_canvas", None)
    start_bar = getattr(window, "_start_bar_widget", None)
    if canvas is None or start_bar is None:
        return
    try:
        canvas._page_setup_size_mm = WORKSPACE_SIZE_MM
        page = _page_rect(canvas)
        if getattr(start_bar, "_ruler_enabled", False):
            if getattr(start_bar, "_ruler_corner_origin_active", False):
                start_bar._set_ruler_origin(QPointF(page.topLeft()), custom=True)
            elif not getattr(start_bar, "_ruler_origin_custom", False):
                start_bar._set_ruler_origin(QPointF(page.center()), custom=False)
            if hasattr(start_bar, "_position_rulers"):
                start_bar._position_rulers()
        canvas.update()
    except Exception:
        logging.exception("engineering_last_mile_patch: ruler sync failed")


class _ResizeFilter(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._target: QWidget | None = None
        self._cursor_widget: QWidget | None = None

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        event_type = event.type()
        if event_type not in {QEvent.Type.MouseButtonPress, QEvent.Type.MouseMove, QEvent.Type.MouseButtonRelease, QEvent.Type.Leave, QEvent.Type.HoverMove}:
            return False
        widget = watched if isinstance(watched, QWidget) else None
        global_pos = _global_position(event)
        if event_type == QEvent.Type.MouseButtonRelease and self._target is not None:
            self._finish()
            event.accept()
            return True
        if self._target is not None and event_type in {QEvent.Type.MouseMove, QEvent.Type.HoverMove} and global_pos is not None:
            buttons = getattr(event, "buttons", lambda: Qt.MouseButton.NoButton)()
            if buttons & Qt.MouseButton.LeftButton:
                _apply_window_resize(self._target, global_pos)
                _sync_rulers(self._target)
                event.accept()
                return True
        window = _resizable_toplevel(widget)
        if window is None:
            return False
        _prepare_tracking(window)
        if global_pos is None:
            return False
        edges = _window_edges(window, window.mapFromGlobal(global_pos))
        if event_type == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton and edges and not _is_control_button(widget):
            self._target = window
            self._cursor_widget = widget or window
            window._last_mile_resize_edges = edges
            window._last_mile_resize_start_global = global_pos
            window._last_mile_resize_start_geometry = QRect(window.geometry())
            cursor = _resize_cursor(edges)
            try:
                window.grabMouse(cursor)
            except Exception:
                pass
            window.setCursor(cursor)
            if self._cursor_widget is not None:
                self._cursor_widget.setCursor(cursor)
            event.accept()
            return True
        if event_type in {QEvent.Type.MouseMove, QEvent.Type.HoverMove}:
            buttons = getattr(event, "buttons", lambda: Qt.MouseButton.NoButton)()
            if not (buttons & Qt.MouseButton.LeftButton):
                if edges and not _is_control_button(widget):
                    cursor = _resize_cursor(edges)
                    window.setCursor(cursor)
                    if widget is not None:
                        widget.setCursor(cursor)
                    self._cursor_widget = widget
                elif self._cursor_widget is widget:
                    widget.unsetCursor()
                    window.unsetCursor()
                    self._cursor_widget = None
        elif event_type == QEvent.Type.Leave and self._cursor_widget is widget:
            widget.unsetCursor()
            window.unsetCursor()
            self._cursor_widget = None
        return False

    def _finish(self) -> None:
        target = self._target
        if target is not None:
            target._last_mile_resize_edges = set()
            target._last_mile_resize_start_global = None
            target._last_mile_resize_start_geometry = None
            try:
                target.releaseMouse()
            except Exception:
                pass
            target.unsetCursor()
            _sync_rulers(target)
        if self._cursor_widget is not None:
            self._cursor_widget.unsetCursor()
        self._target = None
        self._cursor_widget = None


def _ruler_paint(self, event) -> None:
    QWidget.paintEvent(self, event)
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.fillRect(self.rect(), QColor(20, 37, 58, 230))
    orientation = getattr(self, "_orientation", "top")
    canvas = self.parentWidget()
    if canvas is None:
        painter.end()
        return
    page = _page_rect(canvas)
    spacing = max(1.0, _unit_to_canvas_px(self._start_bar, 1.0, self._start_bar._unit, "left" if orientation != "top" else "top"))
    length = float(self.width() if orientation == "top" else self.height())
    zero = self._start_bar._ruler_origin.x() - self.x() if orientation == "top" else self._start_bar._ruler_origin.y() - self.y()
    page_start = page.left() - self.x() if orientation == "top" else page.top() - self.y()
    page_end = page.right() - self.x() if orientation == "top" else page.bottom() - self.y()
    page_start = max(0.0, min(length, page_start))
    page_end = max(0.0, min(length, page_end))
    if page_end < page_start:
        page_start, page_end = page_end, page_start
    page_band = QRectF(page_start, 0, max(0.0, page_end - page_start), self.height()) if orientation == "top" else QRectF(0, page_start, self.width(), max(0.0, page_end - page_start))
    painter.fillRect(page_band, QColor(255, 255, 255, 18))
    font = painter.font()
    font.setPointSize(7)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QPen(QColor("#ffffff"), 1.0))
    index = int(math.floor((page_start - zero) / spacing)) - 1
    while True:
        position = zero + index * spacing
        if position > page_end + spacing:
            break
        if page_start <= position <= page_end:
            abs_index = abs(index)
            tick = 23 if abs_index % 10 == 0 else 16 if abs_index % 5 == 0 else 8
            if orientation == "top":
                painter.drawLine(QPointF(position, self.height()), QPointF(position, self.height() - tick))
                if abs_index % 10 == 0:
                    painter.drawText(QRectF(position + 2, 1, 52, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
            else:
                painter.drawLine(QPointF(self.width(), position), QPointF(self.width() - tick, position))
                if abs_index % 10 == 0:
                    painter.drawText(QRectF(2, position + 1, self.width() - 4, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
        index += 1
    painter.end()


def _install_ruler_overrides() -> None:
    global _ORIGINAL_RULER_OVERLAY_INIT, _ORIGINAL_RULER_GUIDE_INIT, _ORIGINAL_RULER_CORNER_INIT
    try:
        from src.engineers_tools.ui import start_bar as sb
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_last_mile_patch: ruler imports failed")
        return
    edw.EngineeringCanvas._page_rect = _page_rect
    sb.StartBar._unit_to_canvas_px = _unit_to_canvas_px

    def center_ruler_origin(self) -> None:
        canvas = self._canvas()
        if canvas is None:
            return
        self._ruler_origin = QPointF(_page_rect(canvas).center())
        self._ruler_corner_origin_active = False
        self._ruler_previous_origin = None
        self._ruler_previous_origin_custom = False

    def toggle_corner_origin(self) -> None:
        canvas = self._canvas()
        if canvas is None:
            return
        if getattr(self, "_ruler_corner_origin_active", False):
            previous = QPointF(self._ruler_previous_origin) if self._ruler_previous_origin is not None else QPointF(_page_rect(canvas).center())
            previous_custom = bool(getattr(self, "_ruler_previous_origin_custom", False))
            self._ruler_corner_origin_active = False
            self._ruler_previous_origin = None
            self._ruler_previous_origin_custom = False
            self._set_ruler_origin(previous, custom=previous_custom)
            return
        self._ruler_previous_origin = QPointF(self._ruler_origin)
        self._ruler_previous_origin_custom = bool(self._ruler_origin_custom)
        self._ruler_corner_origin_active = True
        self._set_ruler_origin(QPointF(_page_rect(canvas).topLeft()), custom=True)

    sb.StartBar._center_ruler_origin = center_ruler_origin
    sb.StartBar._toggle_ruler_corner_origin = toggle_corner_origin
    sb._RulerOverlay.paintEvent = _ruler_paint

    if _ORIGINAL_RULER_OVERLAY_INIT is None:
        _ORIGINAL_RULER_OVERLAY_INIT = getattr(sb._RulerOverlay, "__init__")
    if _ORIGINAL_RULER_GUIDE_INIT is None:
        _ORIGINAL_RULER_GUIDE_INIT = getattr(sb._GuideLine, "__init__")
    if _ORIGINAL_RULER_CORNER_INIT is None:
        _ORIGINAL_RULER_CORNER_INIT = getattr(sb._RulerCorner, "__init__")

    def overlay_init(self, start_bar, orientation, parent) -> None:
        _ORIGINAL_RULER_OVERLAY_INIT(self, start_bar, orientation, parent)
        self.setCursor(_asset_cursor("mouse_scroll.svg", QCursor(Qt.CursorShape.OpenHandCursor), 10, 10, 20))

    def guide_init(self, orientation, position, parent, start_bar=None, persistent=True) -> None:
        _ORIGINAL_RULER_GUIDE_INIT(self, orientation, position, parent, start_bar, persistent)
        self.setCursor(_asset_cursor("mouse_scroll.svg", QCursor(Qt.CursorShape.OpenHandCursor), 10, 10, 20))

    def corner_init(self, start_bar, parent) -> None:
        _ORIGINAL_RULER_CORNER_INIT(self, start_bar, parent)
        self.setCursor(_asset_cursor("hand_pointer.svg", QCursor(Qt.CursorShape.PointingHandCursor), 9, 3, 18))

    sb._RulerOverlay.__init__ = overlay_init
    sb._GuideLine.__init__ = guide_init
    sb._RulerCorner.__init__ = corner_init


def _can_rotate_selection(canvas) -> bool:
    selected = getattr(canvas, "selected_indices", set())
    objects = getattr(canvas, "objects", [])
    if not selected:
        return False
    for index in selected:
        if not 0 <= index < len(objects):
            return False
        obj = objects[index]
        if getattr(obj, "locked", False) or not getattr(obj, "rotation_handle_visible", True):
            return False
    return True


def _selection_angle(canvas) -> float:
    selected = sorted(getattr(canvas, "selected_indices", set()))
    objects = getattr(canvas, "objects", [])
    if not selected or not 0 <= selected[0] < len(objects):
        return 0.0
    return float(getattr(objects[selected[0]], "rotation", 0.0)) % 360.0


def _set_selection_angle(canvas, target_degrees: float) -> bool:
    if not _can_rotate_selection(canvas):
        return False
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_last_mile_patch: rotate imports failed")
        return False
    current = _selection_angle(canvas)
    target = float(target_degrees) % 360.0
    delta = target - current
    if delta > 180.0:
        delta -= 360.0
    elif delta < -180.0:
        delta += 360.0
    selected = sorted(getattr(canvas, "selected_indices", set()))
    objects = getattr(canvas, "objects", [])
    if hasattr(canvas, "_push_undo"):
        canvas._push_undo()
    center = canvas._group_bounds().center() if len(selected) > 1 and hasattr(canvas, "_group_bounds") else objects[selected[0]].rect.center()
    for index in selected:
        obj = objects[index]
        start_rect = QRectF(obj.rect)
        new_center = center + edw._rotate_vector(start_rect.center() - center, delta)
        obj.rect = QRectF(new_center.x() - start_rect.width() / 2.0, new_center.y() - start_rect.height() / 2.0, start_rect.width(), start_rect.height())
        obj.rotation = (float(getattr(obj, "rotation", 0.0)) + delta) % 360.0
    canvas._last_rotation_degrees = target
    canvas._rotation_overlay_angle = target
    if hasattr(canvas, "_emit_object_changes"):
        canvas._emit_object_changes()
    canvas.update()
    return True


def _snap_rotation_to_axis(canvas) -> bool:
    if not _can_rotate_selection(canvas):
        return False
    current = _selection_angle(canvas)
    target = (math.floor((current + 45.0) / 90.0) * 90.0) % 360.0
    return _set_selection_angle(canvas, target)


def _rotation_label_anchor(canvas) -> QPointF | None:
    selected = getattr(canvas, "selected_indices", set())
    if not selected:
        return None
    if len(selected) > 1 and hasattr(canvas, "_group_bounds"):
        rect = canvas._group_bounds().adjusted(-6, -6, 6, 6)
        return QPointF(rect.right() + 10, rect.top() - 34)
    objects = getattr(canvas, "objects", [])
    index = next(iter(selected))
    if not 0 <= index < len(objects):
        return None
    obj = objects[index]
    local = QPointF(obj.rect.width() / 2.0 + 12, -obj.rect.height() / 2.0 - 34)
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        return obj.rect.center() + edw._rotate_vector(local, float(getattr(obj, "rotation", 0.0)))
    except Exception:
        return obj.rect.center() + local


def _draw_rotation_angle(canvas) -> None:
    anchor = _rotation_label_anchor(canvas)
    if anchor is None:
        return
    angle = _selection_angle(canvas)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    text = f"{angle:.2f}°"
    rect = QRectF(anchor.x(), anchor.y(), 70, 22)
    path = QPainterPath()
    path.addRoundedRect(rect, 8, 8)
    painter.fillPath(path, QColor(255, 249, 222, 235))
    painter.setPen(QPen(QColor("#7e5b10"), 1.1))
    painter.drawPath(path)
    painter.setPen(QColor("#132238"))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
    painter.end()


def _style_rotate_dialog(dialog: QDialog) -> None:
    dialog.setStyleSheet(
        "QWidget#RotateShell{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.55 #edf6ff,stop:1 #dbe6f4);border:1px solid #8fa2bb;border-radius:16px;}"
        "QWidget#RotateHeader,QWidget#RotateFooter{background:#132238;}"
        "QWidget#RotateHeader{border-top-left-radius:16px;border-top-right-radius:16px;}"
        "QWidget#RotateFooter{border-bottom-left-radius:16px;border-bottom-right-radius:16px;}"
        "QLabel#RotateTitle{background:transparent;color:#ffffff;font-size:14px;font-weight:900;}"
        "QLabel#RotateLabel{background:transparent;color:#1f3148;font-size:12px;font-weight:900;}"
        "QLabel#RotateHint{background:rgba(255,255,255,150);border:1px solid #c3d0df;border-radius:8px;color:#39516f;font-size:10px;font-weight:700;padding:5px;}"
        "QDoubleSpinBox#RotateDegreeInput{background:#fff9de;border:1px solid #b38621;border-radius:8px;color:#132238;font-size:12px;font-weight:900;padding:2px 22px 2px 7px;selection-background-color:#43d3bd;}"
        "QDoubleSpinBox#RotateDegreeInput::up-button,QDoubleSpinBox#RotateDegreeInput::down-button{width:18px;border:0;background:#ffc35a;subcontrol-origin:border;}"
        "QDoubleSpinBox#RotateDegreeInput::up-button{subcontrol-position:top right;border-top-right-radius:7px;}"
        "QDoubleSpinBox#RotateDegreeInput::down-button{subcontrol-position:bottom right;border-bottom-right-radius:7px;}"
        "QDoubleSpinBox#RotateDegreeInput::up-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:6px solid #132238;}"
        "QDoubleSpinBox#RotateDegreeInput::down-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid #132238;}"
        "QPushButton#RotatePrimary,QPushButton#RotateSecondary{border-radius:8px;font-size:12px;font-weight:900;padding:4px 12px;}"
        "QPushButton#RotatePrimary{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.45 #fff1bf,stop:1 #ff8a35);border:1px solid #7e5b10;color:#132238;}"
        "QPushButton#RotateSecondary{background:#ffffff;border:1px solid #95a9c1;color:#223650;}"
        "QPushButton#RotateClose{background:transparent;border:0;color:#ffffff;font-size:18px;font-weight:900;}"
    )


def _ask_rotation_degrees(parent, current_angle: float) -> tuple[bool, float]:
    dialog = QDialog(parent)
    dialog.setWindowTitle("Rotate")
    dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    dialog.setModal(True)
    dialog.resize(350, 190)
    _style_rotate_dialog(dialog)
    shell = QWidget(dialog)
    shell.setObjectName("RotateShell")
    root = QVBoxLayout(dialog)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(shell)
    layout = QVBoxLayout(shell)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    header = QWidget()
    header.setObjectName("RotateHeader")
    header.setFixedHeight(42)
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(12, 0, 8, 0)
    mark_builder = getattr(parent, "_build_window_mark", None)
    mark = mark_builder() if callable(mark_builder) else QLabel("AT")
    mark.setFixedSize(34, 30)
    mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title = QLabel("Rotate")
    title.setObjectName("RotateTitle")
    close = QPushButton("×")
    close.setObjectName("RotateClose")
    close.setFixedSize(28, 26)
    close.clicked.connect(dialog.reject)
    header_layout.addWidget(mark)
    header_layout.addWidget(title, 1)
    header_layout.addWidget(close)
    layout.addWidget(header)
    body = QWidget()
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(14, 12, 14, 10)
    body_layout.setSpacing(8)
    row = QHBoxLayout()
    row.setSpacing(8)
    label = QLabel("Degree")
    label.setObjectName("RotateLabel")
    label.setFixedWidth(62)
    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    spin = QDoubleSpinBox()
    spin.setObjectName("RotateDegreeInput")
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    spin.setRange(-3600.0, 3600.0)
    spin.setDecimals(2)
    spin.setSingleStep(1.0)
    spin.setSuffix(" °")
    spin.setValue(float(current_angle))
    spin.setFixedWidth(118)
    row.addWidget(label)
    row.addWidget(spin)
    row.addStretch(1)
    body_layout.addLayout(row)
    hint = QLabel(f"Current angle from zero: {current_angle:.2f}°")
    hint.setObjectName("RotateHint")
    body_layout.addWidget(hint)
    layout.addWidget(body, 1)
    footer = QWidget()
    footer.setObjectName("RotateFooter")
    footer.setFixedHeight(44)
    footer_layout = QHBoxLayout(footer)
    footer_layout.setContentsMargins(12, 6, 12, 6)
    footer_layout.addStretch(1)
    apply_button = QPushButton("Apply")
    apply_button.setObjectName("RotatePrimary")
    cancel_button = QPushButton("Cancel")
    cancel_button.setObjectName("RotateSecondary")
    apply_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    footer_layout.addWidget(apply_button)
    footer_layout.addWidget(cancel_button)
    layout.addWidget(footer)
    return (dialog.exec() == QDialog.DialogCode.Accepted, float(spin.value()))


def _install_rotation_overrides() -> None:
    global _ORIGINAL_CANVAS_KEY_PRESS, _ORIGINAL_CANVAS_PAINT, _ORIGINAL_CANVAS_RELEASE, _ORIGINAL_SHORTCUT_INSTALLER, _ORIGINAL_MENU_DIALOG_INIT
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import module_window as mw
        from . import engineering_fixed_page_rotation_patch as fixed
    except Exception:
        logging.exception("engineering_last_mile_patch: rotation imports failed")
        return
    fixed._rotate_selection_by = lambda canvas, degrees: _set_selection_angle(canvas, _selection_angle(canvas) + float(degrees))
    fixed._snap_rotation_to_axis = _snap_rotation_to_axis
    edw.EngineeringCanvas.rotate_selection_by = lambda canvas, degrees: _set_selection_angle(canvas, _selection_angle(canvas) + float(degrees))
    edw.EngineeringCanvas.can_rotate_selection = _can_rotate_selection
    edw.EngineeringCanvas.set_selection_rotation_angle = _set_selection_angle
    edw.EngineeringCanvas.snap_rotation_to_axis = _snap_rotation_to_axis
    if _ORIGINAL_CANVAS_PAINT is None:
        _ORIGINAL_CANVAS_PAINT = edw.EngineeringCanvas.paintEvent
        def paint_event(self, event) -> None:
            _ORIGINAL_CANVAS_PAINT(self, event)
            _draw_rotation_angle(self)
        edw.EngineeringCanvas.paintEvent = paint_event
    if _ORIGINAL_CANVAS_RELEASE is None:
        _ORIGINAL_CANVAS_RELEASE = edw.EngineeringCanvas.mouseReleaseEvent
        def mouse_release(self, event) -> None:
            _ORIGINAL_CANVAS_RELEASE(self, event)
            if getattr(self, "_drag_action", None) is None:
                self._rotation_overlay_angle = _selection_angle(self)
                self.update()
        edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    if _ORIGINAL_CANVAS_KEY_PRESS is None:
        _ORIGINAL_CANVAS_KEY_PRESS = edw.EngineeringCanvas.keyPressEvent
        def key_press(self, event) -> None:
            if event.key() == Qt.Key_F8 and _snap_rotation_to_axis(self):
                event.accept()
                return
            _ORIGINAL_CANVAS_KEY_PRESS(self, event)
        edw.EngineeringCanvas.keyPressEvent = key_press
    if _ORIGINAL_MENU_DIALOG_INIT is None:
        _ORIGINAL_MENU_DIALOG_INIT = mw.ProjectMenuDialog.__init__
        def menu_dialog_init(self, title, items, parent=None):
            _ORIGINAL_MENU_DIALOG_INIT(self, title, items, parent)
            buttons = [button for button in self.findChildren(QPushButton) if button.objectName() == "MenuItemButton"]
            for item, button in zip(items, buttons):
                if getattr(item, "handler", None) is None:
                    button.setEnabled(False)
                    button.setToolTip("Disabled")
        mw.ProjectMenuDialog.__init__ = menu_dialog_init

    def rotate_selection(self) -> None:
        canvas = getattr(self, "_canvas", None)
        if canvas is None or not _can_rotate_selection(canvas):
            self._set_status("Rotate disabled")
            return
        current = _selection_angle(canvas)
        accepted, target = _ask_rotation_degrees(self, current)
        if not accepted:
            self._set_status("Rotate canceled")
            return
        if _set_selection_angle(canvas, target):
            self._set_status(f"Rotate angle {_selection_angle(canvas):.2f}°")
        else:
            self._set_status("Rotate disabled")

    def snap_rotation(self) -> None:
        canvas = getattr(self, "_canvas", None)
        if canvas is not None and _snap_rotation_to_axis(canvas):
            self._set_status(f"F8 Rotate snap {_selection_angle(canvas):.2f}°")
        else:
            self._set_status("F8 Rotate snap disabled")

    def show_canvas_context_menu(self, global_pos: QPoint) -> None:
        canvas = getattr(self, "_canvas", None)
        rotate_handler = self._rotation if canvas is not None and _can_rotate_selection(canvas) else None
        self._show_menu_at("Object", (
            mw.MenuItemSpec("Repeat", self._repeat_last_tools),
            mw.MenuItemSpec("Copy", self._copy),
            mw.MenuItemSpec("Cut", self._cut),
            mw.MenuItemSpec("Paste", self._paste),
            mw.MenuItemSpec("Delete", self._delete),
            mw.MenuItemSpec("Rotate", rotate_handler),
            mw.MenuItemSpec("Bring to Front", self._bring_to_front),
            mw.MenuItemSpec("Send to Back", self._send_to_back),
            mw.MenuItemSpec("Group", self._group),
            mw.MenuItemSpec("Ungroup", self._ungroup),
        ), global_pos)

    edw.EngineeringDesignWorkspace._rotate_selection = rotate_selection
    edw.EngineeringDesignWorkspace._rotation = rotate_selection
    edw.EngineeringDesignWorkspace._snap_rotation_to_axis = snap_rotation
    edw.EngineeringDesignWorkspace._show_canvas_context_menu = show_canvas_context_menu
    if _ORIGINAL_SHORTCUT_INSTALLER is None:
        _ORIGINAL_SHORTCUT_INSTALLER = edw.EngineeringDesignWorkspace._install_engineering_shortcuts
        def install_shortcuts(self) -> None:
            _ORIGINAL_SHORTCUT_INSTALLER(self)
            if getattr(self, "_f8_rotate_snap_installed", False):
                return
            shortcut = QShortcut(QKeySequence("F8"), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(lambda: self._snap_rotation_to_axis())
            shortcut.activatedAmbiguously.connect(lambda: self._snap_rotation_to_axis())
            if not hasattr(self, "_engineering_shortcuts") or self._engineering_shortcuts is None:
                self._engineering_shortcuts = []
            self._engineering_shortcuts.append(shortcut)
            self._f8_rotate_snap_installed = True
        edw.EngineeringDesignWorkspace._install_engineering_shortcuts = install_shortcuts


def _install_shortcut_registry_patch() -> None:
    try:
        from . import engineering_properties_patch as props
    except Exception:
        logging.exception("engineering_last_mile_patch: properties shortcut patch failed")
        return
    spec = ("orthogonal_angle_snap", "Orthogonal Angle Snap", "F8", "_snap_rotation_to_axis")
    if not any(item[0] == spec[0] for item in props.SHORTCUT_SPECS):
        props.SHORTCUT_SPECS = tuple(props.SHORTCUT_SPECS) + (spec,)
    props.DEFAULT_SHORTCUTS = {key: sequence for key, _label, sequence, _method in props.SHORTCUT_SPECS}


def _install_resize_overrides() -> None:
    global _RESIZE_FILTER
    try:
        from . import engineering_fixed_page_rotation_patch as fixed
        from . import engineering_fixed_viewport_patch as viewport
        from . import engineering_window_geometry_patch as geometry
        from .module_window import ModuleWindow
    except Exception:
        logging.exception("engineering_last_mile_patch: resize override imports failed")
        return
    for module in (fixed, viewport, geometry):
        module.EDGE_MARGIN = EDGE_MARGIN
        module._window_edges = _window_edges
        module._resize_cursor = _resize_cursor
        module._apply_window_resize = _apply_window_resize
    viewport._disable_shell_edge_resize = lambda _patch_module: None
    fixed._page_rect = _page_rect
    viewport._page_rect = _page_rect
    fixed._unit_to_canvas_px = _unit_to_canvas_px
    viewport._unit_to_canvas_px = _unit_to_canvas_px
    original_resize = getattr(ModuleWindow, "resizeEvent", None)
    def resize_event(self, event) -> None:
        if callable(original_resize):
            original_resize(self, event)
        QTimer.singleShot(0, lambda: _sync_rulers(self))
    ModuleWindow.resizeEvent = resize_event
    app = QApplication.instance()
    if app is not None and _RESIZE_FILTER is None:
        _RESIZE_FILTER = _ResizeFilter()
        app.installEventFilter(_RESIZE_FILTER)


def apply_engineering_last_mile_patch() -> None:
    try:
        from .module_window import ModuleWindow
    except Exception:
        logging.exception("engineering_last_mile_patch: module window import failed")
        return
    if getattr(ModuleWindow, "_last_mile_patch_version", "") == VERSION:
        return
    _install_resize_overrides()
    _install_ruler_overrides()
    _install_rotation_overrides()
    _install_shortcut_registry_patch()
    ModuleWindow._last_mile_patch_version = VERSION
    logging.info("engineering_last_mile_patch: installed version=%s", VERSION)

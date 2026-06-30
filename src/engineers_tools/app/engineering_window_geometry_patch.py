"""Window geometry, ruler scale, resize, cursor and rotate behavior patch."""

from __future__ import annotations

import logging

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, QRect, QRectF, QSize, QTimer, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen
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

VERSION = "window-geometry-3"
EDGE_MARGIN = 14
RESTORE_SCALE = 0.58
WORKSPACE_SIZE_MM = (400.0, 220.0)

_ORIGINAL_MODULE_PRESS = None
_ORIGINAL_MODULE_MOVE = None
_ORIGINAL_MODULE_RELEASE = None
_ORIGINAL_MODULE_RESIZE = None
_ORIGINAL_TOGGLE_MAXIMIZE = None
_ORIGINAL_RESTORE_MAXIMIZE = None
_ORIGINAL_MENU_DIALOG_INIT = None
_ORIGINAL_CONTEXT_MENU = None
_ORIGINAL_CANVAS_KEY_PRESS = None
_ORIGINAL_CANVAS_PAINT_SELECTION = None
_ORIGINAL_CANVAS_PAINT_GROUP = None
_ORIGINAL_RULER_CORNER_INIT = None
_ORIGINAL_RULER_OVERLAY_INIT = None
_ORIGINAL_GUIDE_INIT = None
_WINDOW_RESIZE_FILTER = None


def _available_geometry(window) -> QRect:
    screen = window.windowHandle().screen() if window.windowHandle() is not None else window.screen()
    if screen is None:
        return QRect(80, 60, 1280, 720)
    return screen.availableGeometry()


def _proportional_restore_geometry(window) -> QRect:
    available = _available_geometry(window)
    min_w = max(960, int(window.minimumWidth()))
    min_h = max(620, int(window.minimumHeight()))
    width = max(min_w, int(available.width() * RESTORE_SCALE))
    height = max(min_h, int(available.height() * RESTORE_SCALE))
    width = min(width, max(min_w, int(available.width() * 0.86)))
    height = min(height, max(min_h, int(available.height() * 0.86)))
    left = available.left() + max(0, (available.width() - width) // 2)
    top = available.top() + max(0, (available.height() - height) // 2)
    return QRect(left, top, width, height)


def _window_edges(window, pos: QPoint) -> set[str]:
    if getattr(window, "_is_manually_maximized", False) or window.isMaximized():
        return set()
    rect = window.rect()
    edges: set[str] = set()
    if pos.x() <= EDGE_MARGIN:
        edges.add("left")
    elif pos.x() >= rect.width() - EDGE_MARGIN:
        edges.add("right")
    if pos.y() <= EDGE_MARGIN:
        edges.add("top")
    elif pos.y() >= rect.height() - EDGE_MARGIN:
        edges.add("bottom")
    return edges


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
    if not window.isVisible() or window.isMinimized():
        return None
    return window


def _global_event_position(event) -> QPoint | None:
    global_position = getattr(event, "globalPosition", None)
    if callable(global_position):
        return global_position().toPoint()
    global_pos = getattr(event, "globalPos", None)
    if callable(global_pos):
        return global_pos()
    return None


def _resize_cursor(edges: set[str]) -> QCursor:
    if {"left", "top"} <= edges or {"right", "bottom"} <= edges:
        return QCursor(Qt.CursorShape.SizeFDiagCursor)
    if {"right", "top"} <= edges or {"left", "bottom"} <= edges:
        return QCursor(Qt.CursorShape.SizeBDiagCursor)
    if "left" in edges or "right" in edges:
        return QCursor(Qt.CursorShape.SizeHorCursor)
    if "top" in edges or "bottom" in edges:
        return QCursor(Qt.CursorShape.SizeVerCursor)
    return QCursor(Qt.CursorShape.ArrowCursor)


def _minimum_resize_size(window) -> QSize:
    hint = window.minimumSizeHint()
    min_w = max(int(window.minimumWidth()), int(hint.width()), 260)
    min_h = max(int(window.minimumHeight()), int(hint.height()), 160)
    if window.__class__.__name__ == "ModuleWindow":
        min_w = max(min_w, 960)
        min_h = max(min_h, 620)
    return QSize(min_w, min_h)


def _set_resize_cursor(widget: QWidget, edges: set[str]) -> None:
    cursor = _resize_cursor(edges)
    widget.setCursor(cursor)
    window = widget.window()
    if isinstance(window, QWidget):
        window.setCursor(cursor)


def _apply_window_resize(window, global_pos: QPoint) -> None:
    edges: set[str] = getattr(window, "_window_resize_edges", set())
    start_global: QPoint = getattr(window, "_window_resize_start_global", global_pos)
    start_rect: QRect = getattr(window, "_window_resize_start_geometry", window.geometry())
    delta = global_pos - start_global
    rect = QRect(start_rect)
    minimum = _minimum_resize_size(window)
    min_w = minimum.width()
    min_h = minimum.height()
    if "left" in edges:
        rect.setLeft(min(start_rect.left() + delta.x(), start_rect.right() - min_w))
    if "right" in edges:
        rect.setRight(max(start_rect.right() + delta.x(), start_rect.left() + min_w))
    if "top" in edges:
        rect.setTop(min(start_rect.top() + delta.y(), start_rect.bottom() - min_h))
    if "bottom" in edges:
        rect.setBottom(max(start_rect.bottom() + delta.y(), start_rect.top() + min_h))
    window.setGeometry(rect.normalized())


class _FramelessResizeFilter(QObject):
    """Resize every frameless top-level window from all edges and corners."""

    def __init__(self) -> None:
        super().__init__()
        self._target: QWidget | None = None
        self._cursor_widget: QWidget | None = None

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        event_type = event.type()
        if event_type not in {QEvent.Type.MouseButtonPress, QEvent.Type.MouseMove, QEvent.Type.MouseButtonRelease, QEvent.Type.Leave}:
            return False
        widget = watched if isinstance(watched, QWidget) else None
        if event_type == QEvent.Type.MouseButtonRelease and self._target is not None:
            self._finish_resize()
            event.accept()
            return True
        window = _resizable_toplevel(widget)
        if window is None:
            return False
        global_pos = _global_event_position(event)
        if global_pos is None:
            return False
        if self._target is not None:
            if event_type == QEvent.Type.MouseMove and event.buttons() & Qt.MouseButton.LeftButton:
                _apply_window_resize(self._target, global_pos)
                _sync_workspace_after_resize(self._target)
                event.accept()
                return True
            return False
        edges = _window_edges(window, window.mapFromGlobal(global_pos))
        if event_type == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton and edges:
            window._window_resize_edges = edges
            window._window_resize_start_global = global_pos
            window._window_resize_start_geometry = QRect(window.geometry())
            self._target = window
            self._cursor_widget = widget or window
            try:
                window.grabMouse(_resize_cursor(edges))
            except Exception:
                pass
            _set_resize_cursor(widget or window, edges)
            event.accept()
            return True
        if event_type == QEvent.Type.MouseMove and not (event.buttons() & Qt.MouseButton.LeftButton):
            if edges:
                _set_resize_cursor(widget or window, edges)
                self._cursor_widget = widget or window
            elif self._cursor_widget is widget:
                widget.unsetCursor()
                window.unsetCursor()
                self._cursor_widget = None
        elif event_type == QEvent.Type.Leave and self._cursor_widget is widget:
            widget.unsetCursor()
            window.unsetCursor()
            self._cursor_widget = None
        return False

    def _finish_resize(self) -> None:
        target = self._target
        if target is not None:
            target._window_resize_edges = set()
            target._window_resize_start_global = None
            target._window_resize_start_geometry = None
            try:
                target.releaseMouse()
            except Exception:
                pass
            target.unsetCursor()
            _sync_workspace_after_resize(target)
        if self._cursor_widget is not None:
            self._cursor_widget.unsetCursor()
        self._target = None
        self._cursor_widget = None


def _page_rect(canvas) -> QRectF:
    width, height = getattr(canvas, "_page_setup_size_mm", WORKSPACE_SIZE_MM)
    width = max(1.0, float(width))
    height = max(1.0, float(height))
    available = QRectF(6, 3, max(80, canvas.width() - 12), max(80, canvas.height() - 8))
    ratio = height / width
    page_width = min(available.width(), available.height() / ratio)
    page_height = page_width * ratio
    if page_height > available.height():
        page_height = available.height()
        page_width = page_height / ratio
    return QRectF(available.center().x() - page_width / 2, available.center().y() - page_height / 2, page_width, page_height)


def _unit_to_canvas_px(start_bar, value: float, unit: str) -> float:
    try:
        from src.engineers_tools.ui import start_bar as sb
    except Exception:
        return max(1.0, value)
    canvas = start_bar._canvas() if hasattr(start_bar, "_canvas") else None
    if canvas is None:
        return max(1.0, value * sb.UNIT_TO_MM[unit] * sb.MM_TO_SCREEN_PX)
    page = _page_rect(canvas)
    page_width_mm, _page_height_mm = getattr(canvas, "_page_setup_size_mm", WORKSPACE_SIZE_MM)
    page_width_mm = max(1.0, float(page_width_mm))
    mm_value = float(value) * sb.UNIT_TO_MM[unit]
    return max(1.0, mm_value * page.width() / page_width_mm)


def _set_origin_to_page_center(start_bar) -> None:
    canvas = start_bar._canvas() if hasattr(start_bar, "_canvas") else None
    if canvas is None:
        return
    start_bar._ruler_origin = QPointF(_page_rect(canvas).center())
    start_bar._ruler_corner_origin_active = False
    start_bar._ruler_previous_origin = None
    start_bar._ruler_previous_origin_custom = False


def _set_origin_to_page_top_left(start_bar) -> None:
    canvas = start_bar._canvas() if hasattr(start_bar, "_canvas") else None
    if canvas is None:
        return
    start_bar._set_ruler_origin(QPointF(_page_rect(canvas).topLeft()), custom=True)


def _sync_workspace_after_resize(window) -> None:
    canvas = getattr(window, "_canvas", None)
    start_bar = getattr(window, "_start_bar_widget", None)
    if canvas is None or start_bar is None:
        return
    try:
        if hasattr(start_bar, "_ensure_canvas_hooks"):
            start_bar._ensure_canvas_hooks()
        if getattr(start_bar, "_ruler_enabled", False):
            if getattr(start_bar, "_ruler_corner_origin_active", False):
                _set_origin_to_page_top_left(start_bar)
            elif not getattr(start_bar, "_ruler_origin_custom", False):
                _set_origin_to_page_center(start_bar)
            if hasattr(start_bar, "_position_rulers"):
                start_bar._position_rulers()
        canvas.update()
    except Exception:
        logging.exception("engineering_window_geometry_patch: resize sync failed")


def _patch_ruler_math_and_cursors() -> None:
    global _ORIGINAL_RULER_CORNER_INIT, _ORIGINAL_RULER_OVERLAY_INIT, _ORIGINAL_GUIDE_INIT
    try:
        from src.engineers_tools.ui import start_bar as sb
        from . import engineering_ui_small_fixes_patch as small
    except Exception:
        logging.exception("engineering_window_geometry_patch: ruler patch imports failed")
        return
    sb.StartBar._unit_to_canvas_px = _unit_to_canvas_px

    def center_ruler_origin(self) -> None:
        _set_origin_to_page_center(self)

    def toggle_ruler_corner_origin(self) -> None:
        if self._ruler_corner_origin_active:
            previous = QPointF(self._ruler_previous_origin) if self._ruler_previous_origin is not None else None
            previous_custom = self._ruler_previous_origin_custom
            self._ruler_corner_origin_active = False
            self._ruler_previous_origin = None
            self._ruler_previous_origin_custom = False
            if previous is None:
                _set_origin_to_page_center(self)
                self._set_ruler_origin(QPointF(self._ruler_origin), custom=False)
            else:
                self._set_ruler_origin(previous, custom=previous_custom)
            return
        self._ruler_previous_origin = QPointF(self._ruler_origin)
        self._ruler_previous_origin_custom = self._ruler_origin_custom
        self._ruler_corner_origin_active = True
        _set_origin_to_page_top_left(self)

    sb.StartBar._center_ruler_origin = center_ruler_origin
    sb.StartBar._toggle_ruler_corner_origin = toggle_ruler_corner_origin

    if _ORIGINAL_RULER_CORNER_INIT is None:
        _ORIGINAL_RULER_CORNER_INIT = sb._RulerCorner.__init__
        def corner_init(self, *args, **kwargs):
            _ORIGINAL_RULER_CORNER_INIT(self, *args, **kwargs)
            self.setCursor(small._asset_cursor("hand_pointer.svg", QCursor(Qt.CursorShape.PointingHandCursor), 10, 3, 20))
        sb._RulerCorner.__init__ = corner_init

    if _ORIGINAL_RULER_OVERLAY_INIT is None:
        _ORIGINAL_RULER_OVERLAY_INIT = sb._RulerOverlay.__init__
        def overlay_init(self, start_bar, orientation, parent):
            _ORIGINAL_RULER_OVERLAY_INIT(self, start_bar, orientation, parent)
            if orientation == "top":
                self.setCursor(small._asset_cursor("resize_vertical.svg", QCursor(Qt.CursorShape.SizeVerCursor), 12, 12, 22))
            else:
                self.setCursor(small._asset_cursor("resize_horizontal.svg", QCursor(Qt.CursorShape.SizeHorCursor), 12, 12, 22))
        sb._RulerOverlay.__init__ = overlay_init

    if _ORIGINAL_GUIDE_INIT is None:
        _ORIGINAL_GUIDE_INIT = sb._GuideLine.__init__
        def guide_init(self, orientation, position, parent, start_bar=None, persistent=True):
            _ORIGINAL_GUIDE_INIT(self, orientation, position, parent, start_bar, persistent)
            if orientation == "horizontal":
                self.setCursor(small._asset_cursor("resize_vertical.svg", QCursor(Qt.CursorShape.SizeVerCursor), 12, 12, 22))
            else:
                self.setCursor(small._asset_cursor("resize_horizontal.svg", QCursor(Qt.CursorShape.SizeHorCursor), 12, 12, 22))
        sb._GuideLine.__init__ = guide_init


def _patch_canvas_cursors() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import engineering_ui_small_fixes_patch as small
    except Exception:
        logging.exception("engineering_window_geometry_patch: cursor patch imports failed")
        return
    edw.EngineeringCanvas._page_rect = _page_rect

    def set_canvas_hover_cursor(canvas, hover: str | None) -> None:
        if hover == "move":
            canvas.setCursor(small._asset_cursor("move_cursor.svg", QCursor(Qt.CursorShape.SizeAllCursor), 12, 12, 22))
        elif hover == "rotate":
            if getattr(canvas, "_drag_action", None) == "rotate":
                canvas.setCursor(small._asset_cursor("hand_closed.svg", QCursor(Qt.CursorShape.ClosedHandCursor), 10, 8, 18))
            else:
                canvas.setCursor(small._asset_cursor("hand_open.svg", QCursor(Qt.CursorShape.OpenHandCursor), 10, 8, 18))
        elif hover in {"resize_n", "resize_s"}:
            canvas.setCursor(small._asset_cursor("resize_vertical.svg", QCursor(Qt.CursorShape.SizeVerCursor), 12, 12, 22))
        elif hover in {"resize_e", "resize_w"}:
            canvas.setCursor(small._asset_cursor("resize_horizontal.svg", QCursor(Qt.CursorShape.SizeHorCursor), 12, 12, 22))
        elif hover in {"resize_ne", "resize_sw"}:
            canvas.setCursor(small._asset_cursor("corner_resize_b.svg", QCursor(Qt.CursorShape.SizeBDiagCursor), 12, 12, 22))
        elif hover in {"resize_nw", "resize_se"}:
            canvas.setCursor(small._asset_cursor("corner_resize_a.svg", QCursor(Qt.CursorShape.SizeFDiagCursor), 12, 12, 22))
        else:
            canvas.unsetCursor()
    small._set_canvas_hover_cursor = set_canvas_hover_cursor


def _selected_rotation_angle(canvas) -> float:
    selected = sorted(getattr(canvas, "selected_indices", set()))
    objects = getattr(canvas, "objects", [])
    if not selected:
        return 0.0
    index = selected[0]
    if not 0 <= index < len(objects):
        return 0.0
    return float(getattr(objects[index], "rotation", 0.0))


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


def _rotate_selection_by(canvas, degrees: float) -> bool:
    if not _can_rotate_selection(canvas):
        return False
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_window_geometry_patch: rotate imports failed")
        return False
    selected = sorted(getattr(canvas, "selected_indices", set()))
    objects = getattr(canvas, "objects", [])
    if not selected:
        return False
    if hasattr(canvas, "_push_undo"):
        canvas._push_undo()
    center = canvas._group_bounds().center() if len(selected) > 1 and hasattr(canvas, "_group_bounds") else objects[selected[0]].rect.center()
    for index in selected:
        obj = objects[index]
        start_rect = QRectF(obj.rect)
        new_center = center + edw._rotate_vector(start_rect.center() - center, degrees)
        obj.rect = QRectF(new_center.x() - start_rect.width() / 2, new_center.y() - start_rect.height() / 2, start_rect.width(), start_rect.height())
        obj.rotation = float(getattr(obj, "rotation", 0.0)) + degrees
    canvas._last_rotation_degrees = degrees
    if hasattr(canvas, "_emit_object_changes"):
        canvas._emit_object_changes()
    canvas.update()
    return True


def _orthogonalize_canvas(canvas) -> bool:
    if not _can_rotate_selection(canvas):
        return False
    current = _selected_rotation_angle(canvas)
    target = round(current / 90.0) * 90.0
    delta = target - current
    if abs(delta) < 0.0001:
        canvas._last_rotation_degrees = 0.0
        canvas.update()
        return True
    return _rotate_selection_by(canvas, delta)


def _style_rotate_dialog(dialog: QDialog) -> None:
    dialog.setStyleSheet(
        "QWidget#RotateShell{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.55 #edf6ff,stop:1 #dbe6f4);border:1px solid #8fa2bb;border-radius:16px;}"
        "QWidget#RotateHeader,QWidget#RotateFooter{background:#132238;}"
        "QWidget#RotateHeader{border-top-left-radius:16px;border-top-right-radius:16px;}"
        "QWidget#RotateFooter{border-bottom-left-radius:16px;border-bottom-right-radius:16px;}"
        "QLabel#RotateTitle{background:transparent;color:#ffffff;font-size:14px;font-weight:900;}"
        "QLabel#RotateLabel{background:transparent;color:#1f3148;font-size:12px;font-weight:900;}"
        "QLabel#RotateHint{background:rgba(255,255,255,150);border:1px solid #c3d0df;border-radius:8px;color:#39516f;font-size:10px;font-weight:700;padding:5px;}"
        "QDoubleSpinBox#RotateDegreeSpin{background:#fff9de;border:1px solid #b38621;border-radius:8px;color:#132238;font-size:12px;font-weight:900;padding:2px 22px 2px 7px;selection-background-color:#43d3bd;}"
        "QDoubleSpinBox#RotateDegreeSpin::up-button,QDoubleSpinBox#RotateDegreeSpin::down-button{width:18px;border:0;background:#ffc35a;subcontrol-origin:border;}"
        "QDoubleSpinBox#RotateDegreeSpin::up-button{subcontrol-position:top right;border-top-right-radius:7px;}"
        "QDoubleSpinBox#RotateDegreeSpin::down-button{subcontrol-position:bottom right;border-bottom-right-radius:7px;}"
        "QDoubleSpinBox#RotateDegreeSpin::up-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:6px solid #132238;}"
        "QDoubleSpinBox#RotateDegreeSpin::down-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid #132238;}"
        "QPushButton#RotatePrimary,QPushButton#RotateSecondary{border-radius:8px;font-size:12px;font-weight:900;padding:4px 12px;}"
        "QPushButton#RotatePrimary{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.45 #fff1bf,stop:1 #ff8a35);border:1px solid #7e5b10;color:#132238;}"
        "QPushButton#RotateSecondary{background:#ffffff;border:1px solid #95a9c1;color:#223650;}"
        "QPushButton#RotateClose{background:transparent;border:0;color:#ffffff;font-size:18px;font-weight:900;}"
    )


def _ask_rotation_degrees(parent, default_value: float = 10.0, current_angle: float = 0.0) -> tuple[bool, float]:
    dialog = QDialog(parent)
    dialog.setObjectName("RotateDialog")
    dialog.setWindowTitle("Rotate")
    dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    dialog.setModal(True)
    dialog.resize(360, 190)
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
    degree_label = QLabel("Degree")
    degree_label.setObjectName("RotateLabel")
    degree_label.setFixedWidth(62)
    degree_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    spin = QDoubleSpinBox()
    spin.setObjectName("RotateDegreeSpin")
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    spin.setRange(-3600.0, 3600.0)
    spin.setDecimals(2)
    spin.setSingleStep(1.0)
    spin.setSuffix(" °")
    spin.setValue(default_value)
    row.addWidget(degree_label)
    row.addWidget(spin, 1)
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


def _paint_angle_badge(canvas, painter: QPainter, anchor: QPointF, angle: float) -> None:
    text = f"{angle % 360.0:.2f}°"
    font = painter.font()
    font.setPointSize(8)
    font.setBold(True)
    painter.save()
    painter.setFont(font)
    metrics = painter.fontMetrics()
    width = max(48, metrics.horizontalAdvance(text) + 14)
    rect = QRectF(anchor.x(), anchor.y(), width, 20)
    path = QPainterPath()
    path.addRoundedRect(rect, 7, 7)
    painter.fillPath(path, QColor("#fff9de"))
    painter.setPen(QPen(QColor("#7e5b10"), 1.1))
    painter.drawPath(path)
    painter.setPen(QColor("#132238"))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
    painter.restore()


def _install_selection_angle_paint_patch() -> None:
    global _ORIGINAL_CANVAS_PAINT_SELECTION, _ORIGINAL_CANVAS_PAINT_GROUP
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_window_geometry_patch: paint patch imports failed")
        return
    if _ORIGINAL_CANVAS_PAINT_SELECTION is None:
        _ORIGINAL_CANVAS_PAINT_SELECTION = edw.EngineeringCanvas._paint_selection_frame
        def paint_selection_frame(self, painter: QPainter, obj) -> None:
            _ORIGINAL_CANVAS_PAINT_SELECTION(self, painter, obj)
            bounds = self._object_scene_bounds(obj) if hasattr(self, "_object_scene_bounds") else obj.rect
            _paint_angle_badge(self, painter, QPointF(bounds.right() + 8, bounds.top() - 24), float(getattr(obj, "rotation", 0.0)))
        edw.EngineeringCanvas._paint_selection_frame = paint_selection_frame
    if _ORIGINAL_CANVAS_PAINT_GROUP is None:
        _ORIGINAL_CANVAS_PAINT_GROUP = edw.EngineeringCanvas._paint_group_selection
        def paint_group_selection(self, painter: QPainter) -> None:
            _ORIGINAL_CANVAS_PAINT_GROUP(self, painter)
            if not self.selected_indices:
                return
            objects = getattr(self, "objects", [])
            first = min(self.selected_indices)
            if not 0 <= first < len(objects):
                return
            rect = self._group_bounds().adjusted(-6, -6, 6, 6)
            _paint_angle_badge(self, painter, QPointF(rect.right() + 8, rect.top() - 24), float(getattr(objects[first], "rotation", 0.0)))
        edw.EngineeringCanvas._paint_group_selection = paint_group_selection


def _install_rotation_patch() -> None:
    global _ORIGINAL_CONTEXT_MENU, _ORIGINAL_MENU_DIALOG_INIT, _ORIGINAL_CANVAS_KEY_PRESS
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import module_window as mw
    except Exception:
        logging.exception("engineering_window_geometry_patch: rotation patch imports failed")
        return
    edw.EngineeringCanvas.rotate_selection_by = _rotate_selection_by
    edw.EngineeringCanvas.can_rotate_selection = _can_rotate_selection
    edw.EngineeringCanvas.orthogonalize_selection = _orthogonalize_canvas
    if _ORIGINAL_CANVAS_KEY_PRESS is None:
        _ORIGINAL_CANVAS_KEY_PRESS = edw.EngineeringCanvas.keyPressEvent
        def canvas_key_press(self, event) -> None:
            if event.key() == Qt.Key_F8:
                if _orthogonalize_canvas(self):
                    event.accept()
                    return
            _ORIGINAL_CANVAS_KEY_PRESS(self, event)
        edw.EngineeringCanvas.keyPressEvent = canvas_key_press
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
        current = _selected_rotation_angle(canvas)
        default_value = float(getattr(canvas, "_last_rotation_degrees", 10.0))
        accepted, degrees = _ask_rotation_degrees(self, default_value, current)
        if not accepted:
            self._set_status("Rotate canceled")
            return
        if _rotate_selection_by(canvas, degrees):
            new_angle = _selected_rotation_angle(canvas)
            self._set_status(f"Rotate {degrees:.2f}° | angle {new_angle:.2f}°")
        else:
            self._set_status("Rotate disabled")

    def orthogonalize_selection(self) -> None:
        canvas = getattr(self, "_canvas", None)
        if canvas is None or not _can_rotate_selection(canvas):
            self._set_status("F8 angle snap disabled")
            return
        before = _selected_rotation_angle(canvas)
        if _orthogonalize_canvas(canvas):
            after = _selected_rotation_angle(canvas)
            self._set_status(f"F8 angle snap {before:.2f}° → {after:.2f}°")
        else:
            self._set_status("F8 angle snap disabled")

    def rotation(self) -> None:
        rotate_selection(self)

    def show_canvas_context_menu(self, global_pos: QPoint) -> None:
        canvas = getattr(self, "_canvas", None)
        rotate_handler = self._rotation if canvas is not None and _can_rotate_selection(canvas) else None
        self._show_menu_at("Object", (
            mw.MenuItemSpec("Repeat", self._repeat_last_tools),
            mw.MenuItemSpec("Copy", self._copy),
            mw.MenuItemSpec("Cut", self._cut),
            mw.MenuItemSpec("Paste", self._paste),
            mw.MenuItemSpec("Rotate", rotate_handler),
            mw.MenuItemSpec("Bring to Front", self._bring_to_front),
            mw.MenuItemSpec("Send to Back", self._send_to_back),
            mw.MenuItemSpec("Group", self._group),
            mw.MenuItemSpec("Ungroup", self._ungroup),
        ), global_pos)

    if _ORIGINAL_CONTEXT_MENU is None:
        _ORIGINAL_CONTEXT_MENU = edw.EngineeringDesignWorkspace._show_canvas_context_menu
    edw.EngineeringDesignWorkspace._rotate_selection = rotate_selection
    edw.EngineeringDesignWorkspace._rotation = rotation
    edw.EngineeringDesignWorkspace._orthogonalize_selection = orthogonalize_selection
    edw.EngineeringDesignWorkspace._show_canvas_context_menu = show_canvas_context_menu


def _install_shortcut_registry_patch() -> None:
    try:
        from . import engineering_properties_patch as props
    except Exception:
        logging.exception("engineering_window_geometry_patch: properties shortcut patch failed")
        return
    spec = ("orthogonal_angle_snap", "Orthogonal Angle Snap", "F8", "_orthogonalize_selection")
    if not any(item[0] == spec[0] for item in props.SHORTCUT_SPECS):
        props.SHORTCUT_SPECS = tuple(props.SHORTCUT_SPECS) + (spec,)
    props.DEFAULT_SHORTCUTS = {key: sequence for key, _label, sequence, _method in props.SHORTCUT_SPECS}
    logging.info("engineering_window_geometry_patch: F8 shortcut registered")


def _install_global_resize_filter() -> None:
    global _WINDOW_RESIZE_FILTER
    app = QApplication.instance()
    if app is None:
        return
    if _WINDOW_RESIZE_FILTER is None:
        _WINDOW_RESIZE_FILTER = _FramelessResizeFilter()
        app.installEventFilter(_WINDOW_RESIZE_FILTER)


def apply_engineering_window_geometry_patch() -> None:
    global _ORIGINAL_MODULE_PRESS, _ORIGINAL_MODULE_MOVE, _ORIGINAL_MODULE_RELEASE
    global _ORIGINAL_MODULE_RESIZE, _ORIGINAL_TOGGLE_MAXIMIZE, _ORIGINAL_RESTORE_MAXIMIZE
    try:
        from .module_window import ModuleWindow
    except Exception:
        logging.exception("engineering_window_geometry_patch: module window import failed")
        return
    if getattr(ModuleWindow, "_window_geometry_patch_version", "") == VERSION:
        return
    if _ORIGINAL_MODULE_PRESS is None:
        _ORIGINAL_MODULE_PRESS = ModuleWindow.mousePressEvent
    if _ORIGINAL_MODULE_MOVE is None:
        _ORIGINAL_MODULE_MOVE = ModuleWindow.mouseMoveEvent
    if _ORIGINAL_MODULE_RELEASE is None:
        _ORIGINAL_MODULE_RELEASE = ModuleWindow.mouseReleaseEvent
    if _ORIGINAL_MODULE_RESIZE is None:
        _ORIGINAL_MODULE_RESIZE = getattr(ModuleWindow, "resizeEvent", None)
    if _ORIGINAL_TOGGLE_MAXIMIZE is None:
        _ORIGINAL_TOGGLE_MAXIMIZE = ModuleWindow._toggle_maximize
    if _ORIGINAL_RESTORE_MAXIMIZE is None:
        _ORIGINAL_RESTORE_MAXIMIZE = ModuleWindow._restore_from_maximize

    def toggle_maximize(self) -> None:
        if getattr(self, "_is_manually_maximized", False) or self.isMaximized():
            self._restore_from_maximize()
            return
        self._normal_geometry = _proportional_restore_geometry(self)
        self.setGeometry(_available_geometry(self))
        self._is_manually_maximized = True
        if getattr(self, "_maximize_button", None) is not None:
            self._maximize_button.setText("❐")
            self._maximize_button.setToolTip("Restore")
        QTimer.singleShot(0, lambda: _sync_workspace_after_resize(self))

    def restore_from_maximize(self) -> None:
        self.showNormal()
        self.setGeometry(_proportional_restore_geometry(self))
        self._is_manually_maximized = False
        if getattr(self, "_maximize_button", None) is not None:
            self._maximize_button.setText("□")
            self._maximize_button.setToolTip("Maximize")
        QTimer.singleShot(0, lambda: _sync_workspace_after_resize(self))

    def mouse_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            edges = _window_edges(self, event.position().toPoint())
            if edges:
                self._window_resize_edges = edges
                self._window_resize_start_global = event.globalPosition().toPoint()
                self._window_resize_start_geometry = QRect(self.geometry())
                try:
                    self.grabMouse(_resize_cursor(edges))
                except Exception:
                    pass
                self.setCursor(_resize_cursor(edges))
                event.accept()
                return
        _ORIGINAL_MODULE_PRESS(self, event)

    def mouse_move(self, event) -> None:
        if getattr(self, "_window_resize_edges", None) and event.buttons() & Qt.MouseButton.LeftButton:
            _apply_window_resize(self, event.globalPosition().toPoint())
            _sync_workspace_after_resize(self)
            event.accept()
            return
        edges = _window_edges(self, event.position().toPoint())
        if edges and not (event.buttons() & Qt.MouseButton.LeftButton):
            self.setCursor(_resize_cursor(edges))
            event.accept()
            return
        if not getattr(self, "_drag_position", None):
            self.unsetCursor()
        _ORIGINAL_MODULE_MOVE(self, event)

    def mouse_release(self, event) -> None:
        if getattr(self, "_window_resize_edges", None):
            self._window_resize_edges = set()
            self._window_resize_start_global = None
            self._window_resize_start_geometry = None
            try:
                self.releaseMouse()
            except Exception:
                pass
            self.unsetCursor()
            _sync_workspace_after_resize(self)
            event.accept()
            return
        _ORIGINAL_MODULE_RELEASE(self, event)

    def resize_event(self, event) -> None:
        if callable(_ORIGINAL_MODULE_RESIZE):
            _ORIGINAL_MODULE_RESIZE(self, event)
        else:
            super(ModuleWindow, self).resizeEvent(event)
        QTimer.singleShot(0, lambda: _sync_workspace_after_resize(self))

    ModuleWindow._toggle_maximize = toggle_maximize
    ModuleWindow._restore_from_maximize = restore_from_maximize
    ModuleWindow.mousePressEvent = mouse_press
    ModuleWindow.mouseMoveEvent = mouse_move
    ModuleWindow.mouseReleaseEvent = mouse_release
    ModuleWindow.resizeEvent = resize_event
    ModuleWindow._window_geometry_patch_version = VERSION
    _install_global_resize_filter()
    _patch_canvas_cursors()
    _patch_ruler_math_and_cursors()
    _install_rotation_patch()
    _install_selection_angle_paint_patch()
    _install_shortcut_registry_patch()
    logging.info("engineering_window_geometry_patch: installed version=%s", VERSION)

"""Final fixed-page, resize, ruler cursor, and rotation behavior patch."""

from __future__ import annotations

import logging
import math

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, QRect, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QCursor, QKeySequence, QPainter, QPainterPath, QPen, QShortcut
from PySide6.QtWidgets import QApplication, QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


VERSION = "fixed-page-resize-rotation-1"
EDGE_MARGIN = 16
WORKSPACE_SIZE_MM = (400.0, 220.0)
_WINDOW_FILTER: QObject | None = None
_ORIGINAL_MODULE_PRESS = None
_ORIGINAL_MODULE_MOVE = None
_ORIGINAL_MODULE_RELEASE = None
_ORIGINAL_MODULE_RESIZE = None
_ORIGINAL_CANVAS_PAINT = None
_ORIGINAL_CANVAS_MOUSE_RELEASE = None
_ORIGINAL_SHORTCUTS = None


def _fixed_page_size(_canvas=None) -> tuple[float, float]:
    return WORKSPACE_SIZE_MM


def _page_rect(canvas) -> QRectF:
    width, height = _fixed_page_size(canvas)
    available = QRectF(6, 3, max(80, canvas.width() - 12), max(80, canvas.height() - 8))
    ratio = height / width
    page_width = min(available.width(), available.height() / ratio)
    page_height = page_width * ratio
    if page_height > available.height():
        page_height = available.height()
        page_width = page_height / ratio
    return QRectF(available.center().x() - page_width / 2, available.center().y() - page_height / 2, page_width, page_height)


def _scene_to_view(canvas, point: QPointF) -> QPointF:
    zoom = max(0.01, float(getattr(canvas, "_zoom", 1.0)))
    pan = getattr(canvas, "_pan_offset", QPointF(0, 0))
    center = QPointF(canvas.width() / 2.0, canvas.height() / 2.0)
    return QPointF(center.x() + pan.x() + (point.x() - center.x()) * zoom, center.y() + pan.y() + (point.y() - center.y()) * zoom)


def _unit_to_canvas_px(start_bar, value: float, unit: str, orientation: str = "top") -> float:
    try:
        from src.engineers_tools.ui import start_bar as sb
    except Exception:
        return max(1.0, value)
    canvas = start_bar._canvas() if hasattr(start_bar, "_canvas") else None
    if canvas is None:
        return max(1.0, float(value) * sb.UNIT_TO_MM[unit] * sb.MM_TO_SCREEN_PX)
    page = _page_rect(canvas)
    width_mm, height_mm = _fixed_page_size(canvas)
    mm_value = float(value) * sb.UNIT_TO_MM[unit]
    if orientation in {"left", "vertical", "y"}:
        return max(1.0, mm_value * page.height() / height_mm)
    return max(1.0, mm_value * page.width() / width_mm)


def _window_edges(window, pos: QPoint) -> set[str]:
    if getattr(window, "_is_manually_maximized", False) or window.isMaximized():
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
        return QCursor(Qt.CursorShape.SizeFDiagCursor)
    if {"right", "top"} <= edges or {"left", "bottom"} <= edges:
        return QCursor(Qt.CursorShape.SizeBDiagCursor)
    if "left" in edges or "right" in edges:
        return QCursor(Qt.CursorShape.SizeHorCursor)
    if "top" in edges or "bottom" in edges:
        return QCursor(Qt.CursorShape.SizeVerCursor)
    return QCursor(Qt.CursorShape.ArrowCursor)


def _apply_window_resize(window, global_pos: QPoint) -> None:
    edges: set[str] = getattr(window, "_fixed_resize_edges", set())
    start_global: QPoint = getattr(window, "_fixed_resize_start_global", global_pos)
    start_rect: QRect = getattr(window, "_fixed_resize_start_geometry", window.geometry())
    delta = global_pos - start_global
    rect = QRect(start_rect)
    min_w = max(640, int(window.minimumWidth()))
    min_h = max(420, int(window.minimumHeight()))
    if "left" in edges:
        rect.setLeft(min(start_rect.left() + delta.x(), start_rect.right() - min_w))
    if "right" in edges:
        rect.setRight(max(start_rect.right() + delta.x(), start_rect.left() + min_w))
    if "top" in edges:
        rect.setTop(min(start_rect.top() + delta.y(), start_rect.bottom() - min_h))
    if "bottom" in edges:
        rect.setBottom(max(start_rect.bottom() + delta.y(), start_rect.top() + min_h))
    window.setGeometry(rect)


def _sync_fixed_page(window) -> None:
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return
    try:
        canvas._page_setup_size_mm = WORKSPACE_SIZE_MM
        start_bar = getattr(window, "_start_bar_widget", None)
        if start_bar is not None:
            if hasattr(start_bar, "_ensure_canvas_hooks"):
                start_bar._ensure_canvas_hooks()
            page = _page_rect(canvas)
            if getattr(start_bar, "_ruler_enabled", False):
                if getattr(start_bar, "_ruler_corner_origin_active", False):
                    start_bar._set_ruler_origin(_scene_to_view(canvas, page.topLeft()), custom=True)
                elif not getattr(start_bar, "_ruler_origin_custom", False):
                    start_bar._set_ruler_origin(_scene_to_view(canvas, page.center()), custom=False)
                if hasattr(start_bar, "_position_rulers"):
                    start_bar._position_rulers()
        canvas.update()
    except Exception:
        logging.exception("engineering_fixed_page_rotation_patch: fixed page sync failed")


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


class _FixedWindowResizeFilter(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._target: QWidget | None = None
        self._cursor_widget: QWidget | None = None

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        event_type = event.type()
        if event_type not in {QEvent.Type.MouseButtonPress, QEvent.Type.MouseMove, QEvent.Type.MouseButtonRelease, QEvent.Type.Leave}:
            return False
        widget = watched if isinstance(watched, QWidget) else None
        global_pos = _global_position(event)
        if event_type == QEvent.Type.MouseButtonRelease and self._target is not None:
            self._finish()
            return True
        if self._target is not None and event_type == QEvent.Type.MouseMove and global_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            _apply_window_resize(self._target, global_pos)
            _sync_fixed_page(self._target)
            return True
        window = _resizable_toplevel(widget)
        if window is None or global_pos is None:
            return False
        edges = _window_edges(window, window.mapFromGlobal(global_pos))
        if event_type == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton and edges:
            self._target = window
            self._cursor_widget = widget or window
            window._fixed_resize_edges = edges
            window._fixed_resize_start_global = global_pos
            window._fixed_resize_start_geometry = QRect(window.geometry())
            cursor = _resize_cursor(edges)
            window.setCursor(cursor)
            if self._cursor_widget is not None:
                self._cursor_widget.setCursor(cursor)
            event.accept()
            return True
        if event_type == QEvent.Type.MouseMove and not (event.buttons() & Qt.MouseButton.LeftButton):
            if edges:
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
            target._fixed_resize_edges = set()
            target._fixed_resize_start_global = None
            target._fixed_resize_start_geometry = None
            target.unsetCursor()
            _sync_fixed_page(target)
        if self._cursor_widget is not None:
            self._cursor_widget.unsetCursor()
        self._target = None
        self._cursor_widget = None


def _install_window_resize_patch() -> None:
    global _WINDOW_FILTER, _ORIGINAL_MODULE_PRESS, _ORIGINAL_MODULE_MOVE, _ORIGINAL_MODULE_RELEASE, _ORIGINAL_MODULE_RESIZE
    try:
        from .module_window import ModuleWindow
    except Exception:
        logging.exception("engineering_fixed_page_rotation_patch: module window import failed")
        return
    if _ORIGINAL_MODULE_PRESS is None:
        _ORIGINAL_MODULE_PRESS = ModuleWindow.mousePressEvent
        _ORIGINAL_MODULE_MOVE = ModuleWindow.mouseMoveEvent
        _ORIGINAL_MODULE_RELEASE = ModuleWindow.mouseReleaseEvent
        _ORIGINAL_MODULE_RESIZE = getattr(ModuleWindow, "resizeEvent", None)

    def mouse_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            edges = _window_edges(self, event.position().toPoint())
            if edges:
                self._fixed_resize_edges = edges
                self._fixed_resize_start_global = event.globalPosition().toPoint()
                self._fixed_resize_start_geometry = QRect(self.geometry())
                self.setCursor(_resize_cursor(edges))
                event.accept()
                return
        _ORIGINAL_MODULE_PRESS(self, event)

    def mouse_move(self, event) -> None:
        if getattr(self, "_fixed_resize_edges", None) and event.buttons() & Qt.MouseButton.LeftButton:
            _apply_window_resize(self, event.globalPosition().toPoint())
            _sync_fixed_page(self)
            event.accept()
            return
        edges = _window_edges(self, event.position().toPoint())
        if edges and not (event.buttons() & Qt.MouseButton.LeftButton):
            self.setCursor(_resize_cursor(edges))
            event.accept()
            return
        _ORIGINAL_MODULE_MOVE(self, event)

    def mouse_release(self, event) -> None:
        if getattr(self, "_fixed_resize_edges", None):
            self._fixed_resize_edges = set()
            self.unsetCursor()
            _sync_fixed_page(self)
            event.accept()
            return
        _ORIGINAL_MODULE_RELEASE(self, event)

    def resize_event(self, event) -> None:
        if callable(_ORIGINAL_MODULE_RESIZE):
            _ORIGINAL_MODULE_RESIZE(self, event)
        else:
            super(ModuleWindow, self).resizeEvent(event)
        QTimer.singleShot(0, lambda: _sync_fixed_page(self))

    ModuleWindow.mousePressEvent = mouse_press
    ModuleWindow.mouseMoveEvent = mouse_move
    ModuleWindow.mouseReleaseEvent = mouse_release
    ModuleWindow.resizeEvent = resize_event
    app = QApplication.instance()
    if app is not None and _WINDOW_FILTER is None:
        _WINDOW_FILTER = _FixedWindowResizeFilter()
        app.installEventFilter(_WINDOW_FILTER)


def _install_ruler_patch() -> None:
    try:
        from . import engineering_ui_small_fixes_patch as small
        from src.engineers_tools.ui import start_bar as sb
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_fixed_page_rotation_patch: ruler imports failed")
        return
    edw.EngineeringCanvas._page_rect = _page_rect
    sb.StartBar._unit_to_canvas_px = _unit_to_canvas_px

    def center_ruler_origin(self) -> None:
        canvas = self._canvas()
        if canvas is not None:
            self._ruler_origin = _scene_to_view(canvas, _page_rect(canvas).center())
            self._ruler_corner_origin_active = False
            self._ruler_previous_origin = None
            self._ruler_previous_origin_custom = False

    def toggle_corner_origin(self) -> None:
        canvas = self._canvas()
        if canvas is None:
            return
        if getattr(self, "_ruler_corner_origin_active", False):
            previous = QPointF(self._ruler_previous_origin) if self._ruler_previous_origin is not None else _scene_to_view(canvas, _page_rect(canvas).center())
            previous_custom = bool(getattr(self, "_ruler_previous_origin_custom", False))
            self._ruler_corner_origin_active = False
            self._ruler_previous_origin = None
            self._ruler_previous_origin_custom = False
            self._set_ruler_origin(previous, custom=previous_custom)
            return
        self._ruler_previous_origin = QPointF(self._ruler_origin)
        self._ruler_previous_origin_custom = bool(self._ruler_origin_custom)
        self._ruler_corner_origin_active = True
        self._set_ruler_origin(_scene_to_view(canvas, _page_rect(canvas).topLeft()), custom=True)

    def ruler_paint(self, event) -> None:
        QWidget.paintEvent(self, event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(20, 37, 58, 230))
        font = painter.font()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        orientation = getattr(self, "_orientation", "top")
        spacing = max(1.0, _unit_to_canvas_px(self._start_bar, 1.0, self._start_bar._unit, orientation))
        length = self.width() if orientation == "top" else self.height()
        zero = self._start_bar._ruler_origin.x() - self.x() if orientation == "top" else self._start_bar._ruler_origin.y() - self.y()
        index = int(-zero / spacing) - 2
        while True:
            position = zero + index * spacing
            if position > length + spacing:
                break
            if position >= 0:
                abs_index = abs(index)
                tick = 23 if abs_index % 10 == 0 else 16 if abs_index % 5 == 0 else 8
                if orientation == "top":
                    painter.drawLine(QPointF(position, self.height()), QPointF(position, self.height() - tick))
                    if abs_index % 10 == 0:
                        painter.drawText(QRectF(position + 2, 1, 48, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
                else:
                    painter.drawLine(QPointF(self.width(), position), QPointF(self.width() - tick, position))
                    if abs_index % 10 == 0:
                        painter.drawText(QRectF(2, position + 1, self.width() - 4, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
            index += 1
        painter.end()

    original_guide_init = getattr(sb._GuideLine, "_fixed_cursor_original_init", None) or sb._GuideLine.__init__
    original_overlay_init = getattr(sb._RulerOverlay, "_fixed_cursor_original_init", None) or sb._RulerOverlay.__init__
    original_corner_init = getattr(sb._RulerCorner, "_fixed_cursor_original_init", None) or sb._RulerCorner.__init__

    def guide_init(self, orientation, position, parent, start_bar=None, persistent=True) -> None:
        original_guide_init(self, orientation, position, parent, start_bar, persistent)
        asset = "resize_vertical.svg" if orientation == "horizontal" else "resize_horizontal.svg"
        fallback = QCursor(Qt.CursorShape.SizeVerCursor if orientation == "horizontal" else Qt.CursorShape.SizeHorCursor)
        self.setCursor(small._asset_cursor(asset, fallback, 12, 12, 24))

    def overlay_init(self, start_bar, orientation, parent) -> None:
        original_overlay_init(self, start_bar, orientation, parent)
        asset = "resize_vertical.svg" if orientation == "top" else "resize_horizontal.svg"
        fallback = QCursor(Qt.CursorShape.SizeVerCursor if orientation == "top" else Qt.CursorShape.SizeHorCursor)
        self.setCursor(small._asset_cursor(asset, fallback, 12, 12, 24))

    def corner_init(self, start_bar, parent) -> None:
        original_corner_init(self, start_bar, parent)
        self.setCursor(small._asset_cursor("hand_pointer.svg", QCursor(Qt.CursorShape.PointingHandCursor), 10, 3, 22))

    sb.StartBar._center_ruler_origin = center_ruler_origin
    sb.StartBar._toggle_ruler_corner_origin = toggle_corner_origin
    sb._RulerOverlay.paintEvent = ruler_paint
    sb._GuideLine._fixed_cursor_original_init = original_guide_init
    sb._RulerOverlay._fixed_cursor_original_init = original_overlay_init
    sb._RulerCorner._fixed_cursor_original_init = original_corner_init
    sb._GuideLine.__init__ = guide_init
    sb._RulerOverlay.__init__ = overlay_init
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


def _rotate_selection_by(canvas, degrees: float) -> bool:
    if not _can_rotate_selection(canvas):
        return False
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_fixed_page_rotation_patch: rotate imports failed")
        return False
    selected = sorted(getattr(canvas, "selected_indices", set()))
    objects = getattr(canvas, "objects", [])
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
    canvas._rotation_overlay_angle = _selection_angle(canvas)
    if hasattr(canvas, "_emit_object_changes"):
        canvas._emit_object_changes()
    canvas.update()
    return True


def _selection_angle(canvas) -> float:
    selected = sorted(getattr(canvas, "selected_indices", set()))
    objects = getattr(canvas, "objects", [])
    if not selected or selected[0] >= len(objects):
        return 0.0
    return float(getattr(objects[selected[0]], "rotation", 0.0)) % 360.0


def _snap_rotation_to_axis(canvas) -> bool:
    if not _can_rotate_selection(canvas):
        return False
    current = _selection_angle(canvas)
    target = round(current / 90.0) * 90.0
    delta = target - current
    if abs(delta) < 0.001:
        canvas._rotation_overlay_angle = target % 360.0
        canvas.update()
        return True
    return _rotate_selection_by(canvas, delta)


def _rotation_label_anchor(canvas) -> QPointF | None:
    selected = getattr(canvas, "selected_indices", set())
    if not selected:
        return None
    if len(selected) > 1 and hasattr(canvas, "_group_bounds"):
        rect = canvas._group_bounds().adjusted(-6, -6, 6, 6)
        return _scene_to_view(canvas, QPointF(rect.right() + 12, rect.top() - 46))
    objects = getattr(canvas, "objects", [])
    index = next(iter(selected))
    if not 0 <= index < len(objects):
        return None
    obj = objects[index]
    half_h = obj.rect.height() / 2.0
    local = QPointF(obj.rect.width() / 2.0 + 12, -half_h - 44)
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        scene = obj.rect.center() + edw._rotate_vector(local, float(getattr(obj, "rotation", 0.0)))
    except Exception:
        scene = obj.rect.center() + local
    return _scene_to_view(canvas, scene)


def _draw_rotation_angle(canvas) -> None:
    if not getattr(canvas, "selected_indices", set()):
        return
    anchor = _rotation_label_anchor(canvas)
    if anchor is None:
        return
    angle = _selection_angle(canvas)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    text = f"{angle:.2f}°"
    rect = QRectF(anchor.x(), anchor.y(), 72, 23)
    path = QPainterPath()
    path.addRoundedRect(rect, 8, 8)
    painter.fillPath(path, QColor(255, 249, 222, 235))
    painter.setPen(QPen(QColor("#7e5b10"), 1.1))
    painter.drawPath(path)
    painter.setPen(QColor("#132238"))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
    painter.end()


def _ask_rotation_degrees(parent, default_value: float = 10.0) -> tuple[bool, float]:
    dialog = QDialog(parent)
    dialog.setObjectName("ProjectHelpDialog")
    dialog.setWindowTitle("Rotate")
    dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    dialog.setModal(True)
    dialog.resize(340, 184)
    shell = QWidget(dialog)
    shell.setObjectName("ProjectHelpShell")
    root = QVBoxLayout(dialog)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(shell)
    layout = QVBoxLayout(shell)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    header = QWidget()
    header.setObjectName("TopBar")
    header.setFixedHeight(44)
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(12, 0, 10, 0)
    if hasattr(parent, "_build_logo_mark"):
        header_layout.addWidget(parent._build_logo_mark())
    title = QLabel("Rotate")
    title.setObjectName("WindowTitle")
    header_layout.addWidget(title, 1)
    layout.addWidget(header)
    body = QWidget()
    body.setObjectName("WorkspaceArea")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(16, 14, 16, 14)
    row = QHBoxLayout()
    row.setSpacing(6)
    label = QLabel("Degree")
    label.setObjectName("PanelTitle")
    row.addWidget(label)
    spin = QDoubleSpinBox()
    spin.setObjectName("RotateDegreeInput")
    spin.setRange(-3600.0, 3600.0)
    spin.setDecimals(2)
    spin.setSingleStep(1.0)
    spin.setSuffix(" °")
    spin.setValue(default_value)
    spin.setFixedWidth(118)
    spin.setStyleSheet(
        "QDoubleSpinBox#RotateDegreeInput {background:#fff9de; border:1px solid #b38621; border-radius:8px; color:#132238; font-size:12px; font-weight:800; padding:3px 6px;}"
        "QDoubleSpinBox#RotateDegreeInput::up-button, QDoubleSpinBox#RotateDegreeInput::down-button {width:22px; border:1px solid #7e5b10; background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fff9de, stop:1 #ffc35a);}"
        "QDoubleSpinBox#RotateDegreeInput::up-button {subcontrol-origin:border; subcontrol-position:top right; border-top-right-radius:7px;}"
        "QDoubleSpinBox#RotateDegreeInput::down-button {subcontrol-origin:border; subcontrol-position:bottom right; border-bottom-right-radius:7px;}"
        "QDoubleSpinBox#RotateDegreeInput::up-arrow {width:0; height:0; border-left:5px solid transparent; border-right:5px solid transparent; border-bottom:6px solid #132238;}"
        "QDoubleSpinBox#RotateDegreeInput::down-arrow {width:0; height:0; border-left:5px solid transparent; border-right:5px solid transparent; border-top:6px solid #132238;}"
    )
    row.addWidget(spin)
    row.addStretch(1)
    body_layout.addLayout(row)
    buttons = QHBoxLayout()
    buttons.addStretch(1)
    apply_button = QPushButton("Apply")
    apply_button.setObjectName("PrimaryDialogButton")
    cancel_button = QPushButton("Cancel")
    cancel_button.setObjectName("SecondaryDialogButton")
    apply_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    buttons.addWidget(apply_button)
    buttons.addWidget(cancel_button)
    body_layout.addLayout(buttons)
    layout.addWidget(body)
    return (dialog.exec() == QDialog.DialogCode.Accepted, float(spin.value()))


def _install_rotation_patch() -> None:
    global _ORIGINAL_CANVAS_PAINT, _ORIGINAL_CANVAS_MOUSE_RELEASE, _ORIGINAL_SHORTCUTS
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import module_window as mw
    except Exception:
        logging.exception("engineering_fixed_page_rotation_patch: rotation imports failed")
        return
    if _ORIGINAL_CANVAS_PAINT is None:
        _ORIGINAL_CANVAS_PAINT = edw.EngineeringCanvas.paintEvent
        _ORIGINAL_CANVAS_MOUSE_RELEASE = edw.EngineeringCanvas.mouseReleaseEvent
        _ORIGINAL_SHORTCUTS = edw.EngineeringDesignWorkspace._install_engineering_shortcuts

    def paint_event(self, event) -> None:
        _ORIGINAL_CANVAS_PAINT(self, event)
        _draw_rotation_angle(self)

    def mouse_release(self, event) -> None:
        _ORIGINAL_CANVAS_MOUSE_RELEASE(self, event)
        if getattr(self, "_drag_action", None) is None:
            self._rotation_overlay_angle = _selection_angle(self)
            self.update()

    def rotate_selection(workspace_self) -> None:
        canvas = getattr(workspace_self, "_canvas", None)
        if canvas is None or not _can_rotate_selection(canvas):
            workspace_self._set_status("Rotate disabled")
            return
        accepted, degrees = _ask_rotation_degrees(workspace_self, float(getattr(canvas, "_last_rotation_degrees", 10.0)))
        if not accepted:
            workspace_self._set_status("Rotate canceled")
            return
        if _rotate_selection_by(canvas, degrees):
            workspace_self._set_status(f"Rotate {degrees:.2f}°")
        else:
            workspace_self._set_status("Rotate disabled")

    def snap_rotation(workspace_self) -> None:
        canvas = getattr(workspace_self, "_canvas", None)
        if canvas is not None and _snap_rotation_to_axis(canvas):
            workspace_self._set_status(f"F8 Rotate snap {_selection_angle(canvas):.2f}°")
        else:
            workspace_self._set_status("F8 Rotate snap disabled")

    def install_shortcuts(self) -> None:
        _ORIGINAL_SHORTCUTS(self)
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

    def show_canvas_context_menu(self, global_pos: QPoint) -> None:
        canvas = getattr(self, "_canvas", None)
        rotate_handler = self._rotation if canvas is not None and _can_rotate_selection(canvas) else None
        self._show_menu_at(
            "Object",
            (
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
            ),
            global_pos,
        )

    edw.EngineeringCanvas.paintEvent = paint_event
    edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    edw.EngineeringCanvas.rotate_selection_by = _rotate_selection_by
    edw.EngineeringCanvas.can_rotate_selection = _can_rotate_selection
    edw.EngineeringDesignWorkspace._rotate_selection = rotate_selection
    edw.EngineeringDesignWorkspace._rotation = rotate_selection
    edw.EngineeringDesignWorkspace._snap_rotation_to_axis = snap_rotation
    edw.EngineeringDesignWorkspace._install_engineering_shortcuts = install_shortcuts
    edw.EngineeringDesignWorkspace._show_canvas_context_menu = show_canvas_context_menu


def apply_engineering_fixed_page_rotation_patch() -> None:
    try:
        from .module_window import ModuleWindow
    except Exception:
        logging.exception("engineering_fixed_page_rotation_patch: module window import failed")
        return
    if getattr(ModuleWindow, "_fixed_page_rotation_patch_version", "") == VERSION:
        return
    _install_window_resize_patch()
    _install_ruler_patch()
    _install_rotation_patch()
    ModuleWindow._fixed_page_rotation_patch_version = VERSION
    logging.info("engineering_fixed_page_rotation_patch: installed version=%s", VERSION)

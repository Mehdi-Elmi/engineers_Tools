"""Window geometry and resize behavior patch for Engineering Design Tools."""

from __future__ import annotations

import logging

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, QRect, QRectF, QTimer, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


VERSION = "window-geometry-2"
EDGE_MARGIN = 8
RESTORE_SCALE = 0.58
WORKSPACE_SIZE_MM = (400.0, 220.0)

_ORIGINAL_MODULE_PRESS = None
_ORIGINAL_MODULE_MOVE = None
_ORIGINAL_MODULE_RELEASE = None
_ORIGINAL_MODULE_RESIZE = None
_ORIGINAL_TOGGLE_MAXIMIZE = None
_ORIGINAL_RESTORE_MAXIMIZE = None
_ORIGINAL_CANVAS_PAGE_RECT = None
_ORIGINAL_MENU_DIALOG_INIT = None
_ORIGINAL_CONTEXT_MENU = None
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
    if window.minimumWidth() <= 0 or window.minimumHeight() <= 0:
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
    min_w = window.minimumWidth()
    min_h = window.minimumHeight()
    if "left" in edges:
        rect.setLeft(min(start_rect.left() + delta.x(), start_rect.right() - min_w))
    if "right" in edges:
        rect.setRight(max(start_rect.right() + delta.x(), start_rect.left() + min_w))
    if "top" in edges:
        rect.setTop(min(start_rect.top() + delta.y(), start_rect.bottom() - min_h))
    if "bottom" in edges:
        rect.setBottom(max(start_rect.bottom() + delta.y(), start_rect.top() + min_h))
    window.setGeometry(rect)


class _FramelessResizeFilter(QObject):
    """Resize frameless windows from every edge, even when child widgets receive the mouse."""

    def __init__(self) -> None:
        super().__init__()
        self._target: QWidget | None = None
        self._edges: set[str] = set()
        self._start_global = QPoint()
        self._start_geometry = QRect()
        self._cursor_widget: QWidget | None = None

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        event_type = event.type()
        if event_type not in {
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.Leave,
        }:
            return False
        widget = watched if isinstance(watched, QWidget) else None
        window = _resizable_toplevel(widget)
        if event_type == QEvent.Type.MouseButtonRelease and self._target is not None:
            self._finish_resize()
            return False
        if window is None:
            return False
        global_pos = _global_event_position(event)
        if global_pos is None:
            return False
        local_pos = window.mapFromGlobal(global_pos)
        if self._target is not None:
            if event_type == QEvent.Type.MouseMove and event.buttons() & Qt.MouseButton.LeftButton:
                _apply_window_resize(self._target, global_pos)
                _sync_workspace_after_resize(self._target)
                return True
            return False
        edges = _window_edges(window, local_pos)
        if event_type == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton and edges:
            self._target = window
            self._edges = edges
            self._start_global = global_pos
            self._start_geometry = QRect(window.geometry())
            window._window_resize_edges = edges
            window._window_resize_start_global = global_pos
            window._window_resize_start_geometry = QRect(window.geometry())
            _set_resize_cursor(widget or window, edges)
            self._cursor_widget = widget or window
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
            return False
        if event_type == QEvent.Type.Leave and self._cursor_widget is widget:
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
            target.unsetCursor()
            _sync_workspace_after_resize(target)
        if self._cursor_widget is not None:
            self._cursor_widget.unsetCursor()
        self._target = None
        self._edges = set()
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
    return QRectF(
        available.center().x() - page_width / 2,
        available.center().y() - page_height / 2,
        page_width,
        page_height,
    )


def _unit_to_canvas_px(start_bar, value: float, unit: str) -> float:
    """Keep ruler/grid dimensions tied to the fitted page, not raw window pixels."""
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


def _scene_to_view(canvas, point: QPointF) -> QPointF:
    zoom = max(0.01, float(getattr(canvas, "_zoom", 1.0)))
    pan = getattr(canvas, "_pan_offset", QPointF(0, 0))
    center = QPointF(canvas.width() / 2.0, canvas.height() / 2.0)
    return QPointF(
        center.x() + pan.x() + (point.x() - center.x()) * zoom,
        center.y() + pan.y() + (point.y() - center.y()) * zoom,
    )


def _sync_workspace_after_resize(window) -> None:
    canvas = getattr(window, "_canvas", None)
    start_bar = getattr(window, "_start_bar_widget", None)
    if canvas is None or start_bar is None:
        return
    try:
        if hasattr(start_bar, "_ensure_canvas_hooks"):
            start_bar._ensure_canvas_hooks()
        if getattr(start_bar, "_ruler_enabled", False):
            page = _page_rect(canvas)
            if getattr(start_bar, "_ruler_corner_origin_active", False):
                start_bar._set_ruler_origin(_scene_to_view(canvas, page.topLeft()), custom=True)
            elif not getattr(start_bar, "_ruler_origin_custom", False):
                start_bar._set_ruler_origin(_scene_to_view(canvas, page.center()), custom=False)
            if hasattr(start_bar, "_position_rulers"):
                start_bar._position_rulers()
        canvas.update()
    except Exception:
        logging.exception("engineering_window_geometry_patch: resize sync failed")


def _patch_canvas_cursors() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import engineering_ui_small_fixes_patch as small
        from src.engineers_tools.ui import start_bar as sb
    except Exception:
        logging.exception("engineering_window_geometry_patch: cursor patch imports failed")
        return

    edw.EngineeringCanvas._page_rect = _page_rect
    sb.StartBar._unit_to_canvas_px = _unit_to_canvas_px

    def set_canvas_hover_cursor(canvas, hover: str | None) -> None:
        if hover == "move":
            canvas.setCursor(small._asset_cursor("move_cursor.svg", QCursor(Qt.CursorShape.SizeAllCursor), 12, 12, 24))
        elif hover == "rotate":
            if getattr(canvas, "_drag_action", None) == "rotate":
                canvas.setCursor(small._asset_cursor("hand_closed.svg", QCursor(Qt.CursorShape.ClosedHandCursor), 10, 8, 20))
            else:
                canvas.setCursor(small._asset_cursor("hand_open.svg", QCursor(Qt.CursorShape.OpenHandCursor), 10, 8, 20))
        elif hover in {"resize_n", "resize_s"}:
            canvas.setCursor(small._asset_cursor("resize_vertical.svg", QCursor(Qt.CursorShape.SizeVerCursor), 12, 12, 24))
        elif hover in {"resize_e", "resize_w"}:
            canvas.setCursor(small._asset_cursor("resize_horizontal.svg", QCursor(Qt.CursorShape.SizeHorCursor), 12, 12, 24))
        elif hover in {"resize_ne", "resize_sw"}:
            canvas.setCursor(small._asset_cursor("corner_resize_a.svg", QCursor(Qt.CursorShape.SizeBDiagCursor), 12, 12, 24))
        elif hover in {"resize_nw", "resize_se"}:
            canvas.setCursor(small._asset_cursor("corner_resize_b.svg", QCursor(Qt.CursorShape.SizeFDiagCursor), 12, 12, 24))
        else:
            canvas.unsetCursor()

    small._set_canvas_hover_cursor = set_canvas_hover_cursor


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
    if hasattr(canvas, "_push_undo"):
        canvas._push_undo()
    center = canvas._group_bounds().center() if len(selected) > 1 and hasattr(canvas, "_group_bounds") else objects[selected[0]].rect.center()
    for index in selected:
        obj = objects[index]
        start_rect = QRectF(obj.rect)
        new_center = center + edw._rotate_vector(start_rect.center() - center, degrees)
        obj.rect = QRectF(
            new_center.x() - start_rect.width() / 2,
            new_center.y() - start_rect.height() / 2,
            start_rect.width(),
            start_rect.height(),
        )
        obj.rotation = float(getattr(obj, "rotation", 0.0)) + degrees
    canvas._last_rotation_degrees = degrees
    if hasattr(canvas, "_emit_object_changes"):
        canvas._emit_object_changes()
    canvas.update()
    return True


def _ask_rotation_degrees(parent, default_value: float = 10.0) -> tuple[bool, float]:
    dialog = QDialog(parent)
    dialog.setObjectName("ProjectHelpDialog")
    dialog.setWindowTitle("Rotate")
    dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    dialog.setModal(True)
    dialog.resize(310, 150)

    shell = QWidget(dialog)
    shell.setObjectName("ProjectHelpShell")
    root = QVBoxLayout(dialog)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(shell)
    layout = QVBoxLayout(shell)
    layout.setContentsMargins(14, 12, 14, 14)
    layout.setSpacing(10)

    title = QLabel("Rotate Degree")
    title.setObjectName("HelpTitle")
    layout.addWidget(title)
    row = QHBoxLayout()
    row.setSpacing(8)
    row.addWidget(QLabel("Degree"))
    spin = QDoubleSpinBox()
    spin.setObjectName("FileNameInput")
    spin.setRange(-3600.0, 3600.0)
    spin.setDecimals(2)
    spin.setSingleStep(1.0)
    spin.setSuffix(" deg")
    spin.setValue(default_value)
    row.addWidget(spin, 1)
    layout.addLayout(row)

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
    layout.addLayout(buttons)
    return (dialog.exec() == QDialog.DialogCode.Accepted, float(spin.value()))


def _install_rotation_patch() -> None:
    global _ORIGINAL_CONTEXT_MENU, _ORIGINAL_MENU_DIALOG_INIT
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import module_window as mw
    except Exception:
        logging.exception("engineering_window_geometry_patch: rotation patch imports failed")
        return

    edw.EngineeringCanvas.rotate_selection_by = _rotate_selection_by
    edw.EngineeringCanvas.can_rotate_selection = _can_rotate_selection

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
        default_value = float(getattr(canvas, "_last_rotation_degrees", 10.0))
        accepted, degrees = _ask_rotation_degrees(self, default_value)
        if not accepted:
            self._set_status("Rotate canceled")
            return
        if _rotate_selection_by(canvas, degrees):
            self._set_status(f"Rotate {degrees:.2f} deg")
        else:
            self._set_status("Rotate disabled")

    def rotation(self) -> None:
        rotate_selection(self)

    if _ORIGINAL_CONTEXT_MENU is None:
        _ORIGINAL_CONTEXT_MENU = edw.EngineeringDesignWorkspace._show_canvas_context_menu

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
                mw.MenuItemSpec("Rotate", rotate_handler),
                mw.MenuItemSpec("Bring to Front", self._bring_to_front),
                mw.MenuItemSpec("Send to Back", self._send_to_back),
                mw.MenuItemSpec("Group", self._group),
                mw.MenuItemSpec("Ungroup", self._ungroup),
            ),
            global_pos,
        )

    edw.EngineeringDesignWorkspace._rotate_selection = rotate_selection
    edw.EngineeringDesignWorkspace._rotation = rotation
    edw.EngineeringDesignWorkspace._show_canvas_context_menu = show_canvas_context_menu


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
                self.setCursor(_resize_cursor(edges))
                event.accept()
                return
        _ORIGINAL_MODULE_PRESS(self, event)

    def mouse_move(self, event) -> None:
        if getattr(self, "_window_resize_edges", None) and event.buttons() & Qt.MouseButton.LeftButton:
            _apply_window_resize(self, event.globalPosition().toPoint())
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
    _patch_canvas_cursors()
    _install_rotation_patch()
    _install_global_resize_filter()
    logging.info("engineering_window_geometry_patch: installed version=%s", VERSION)

"""Move-only behavior for the Engineering Design Tools shell.

The main shell is frameless, but at this stage it must not expose manual
edge/corner resize. The only direct window interaction allowed here is moving the
restored window from the top bar area. Maximize/restore stays controlled by the
window button.
"""

from __future__ import annotations

import sys
from ctypes import wintypes

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtWidgets import QApplication, QAbstractButton, QAbstractSpinBox, QLineEdit, QWidget

PATCH_VERSION = "engineering-window-move-only-2026-06-30-e"
MOVE_BAND_HEIGHT = 46
WORKSPACE_SIZE_MM = (400.0, 220.0)
WM_NCHITTEST = 0x0084
HTCLIENT = 1
_FILTER: QObject | None = None

_INTERACTIVE_NAMES = {
    "WindowButton",
    "CloseButton",
    "HomeButton",
    "MenuButton",
    "ToolButton",
    "ToolIconButton",
    "LayerIconButton",
    "LayerExpandButton",
    "PageButton",
    "PageButtonActive",
    "AddPageButton",
    "IconChoice",
    "RadioChoice",
}

_CANVAS_NAMES = {"GridCanvas", "EngineeringCanvas"}
_SHELL_ARROW_NAMES = {
    "WindowRoot",
    "WorkspaceArea",
    "PageBar",
    "PageStrip",
    "StatusBar",
    "StatusItem",
}


def _window_edges(_window: QWidget, _pos: QPoint) -> frozenset[str]:
    return frozenset()


def _cursor_kind(_edges: frozenset[str]) -> str | None:
    return None


def _set_window_cursor(window: QWidget, kind: str | None) -> None:
    app = QApplication.instance()
    if app is None:
        return
    if kind is not None:
        return
    if bool(getattr(window, "_engineering_window_cursor_active", False)):
        app.restoreOverrideCursor()
    window._engineering_window_cursor_active = False
    window._engineering_window_cursor_kind = None


def _interactive_child(widget: QWidget, window: QWidget) -> bool:
    current: QWidget | None = widget
    while current is not None and current is not window:
        if isinstance(current, (QAbstractButton, QAbstractSpinBox, QLineEdit)):
            return True
        if current.objectName() in _INTERACTIVE_NAMES:
            return True
        current = current.parentWidget()
    return False


def _is_canvas_surface(widget: QWidget, window: QWidget) -> bool:
    current: QWidget | None = widget
    while current is not None and current is not window:
        if current.objectName() in _CANVAS_NAMES:
            return True
        current = current.parentWidget()
    return False


def _is_move_surface(widget: QWidget, window: QWidget, window_pos: QPoint) -> bool:
    if getattr(window, "_is_manually_maximized", False) or window.isMaximized():
        return False
    if window_pos.y() > MOVE_BAND_HEIGHT:
        return False
    return not _interactive_child(widget, window)


def _force_arrow_cursor(widget: QWidget) -> None:
    widget.setMouseTracking(True)
    widget.setCursor(Qt.CursorShape.ArrowCursor)


def _install_shell_cursor_policy(window: QWidget) -> None:
    window.setMouseTracking(True)
    window.setCursor(Qt.CursorShape.ArrowCursor)
    for widget in window.findChildren(QWidget):
        if _is_canvas_surface(widget, window):
            continue
        widget.setMouseTracking(True)
        if widget.objectName() in _SHELL_ARROW_NAMES:
            _force_arrow_cursor(widget)


def _clear_shell_cursor(widget: QWidget, window: QWidget) -> None:
    if _is_canvas_surface(widget, window):
        return
    _set_window_cursor(window, None)
    window.setCursor(Qt.CursorShape.ArrowCursor)
    if widget.objectName() in _SHELL_ARROW_NAMES or not _interactive_child(widget, window):
        widget.setCursor(Qt.CursorShape.ArrowCursor)


def _apply_window_move(window: QWidget, global_pos: QPoint) -> None:
    start_global: QPoint = getattr(window, "_engineering_move_start_global", global_pos)
    start_geometry = getattr(window, "_engineering_move_start_geometry", window.geometry())
    window.move(start_geometry.topLeft() + (global_pos - start_global))


def _sync_fixed_workspace_metadata(window: QWidget) -> None:
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return
    canvas._engineering_workspace_size_mm = WORKSPACE_SIZE_MM
    canvas._page_setup_size_mm = WORKSPACE_SIZE_MM
    canvas.update()
    start_bar = getattr(window, "_start_bar_widget", None)
    if start_bar is not None and getattr(start_bar, "_ruler_enabled", False):
        position = getattr(start_bar, "_position_rulers", None)
        if callable(position):
            position()


class _WindowMoveFilter(QObject):
    def __init__(self, module_window_cls: type[QWidget]) -> None:
        super().__init__()
        self._module_window_cls = module_window_cls

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if not isinstance(watched, QWidget):
            return False
        window = watched.window()
        if not isinstance(window, self._module_window_cls):
            return False
        event_type = event.type()
        if event_type not in {QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.Leave}:
            return False

        if event_type == QEvent.Type.Leave:
            _clear_shell_cursor(watched, window)
            return False

        try:
            local_pos = event.position().toPoint()
            window_pos = watched.mapTo(window, local_pos)
            global_pos = event.globalPosition().toPoint()
        except AttributeError:
            return False

        if event_type == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            if _is_move_surface(watched, window, window_pos):
                window._engineering_move_active = True
                window._engineering_move_start_global = global_pos
                window._engineering_move_start_geometry = window.geometry()
                window._drag_position = None
                event.accept()
                return True
            window._engineering_move_active = False
            _clear_shell_cursor(watched, window)
            return False

        if event_type == QEvent.Type.MouseMove:
            if getattr(window, "_engineering_move_active", False):
                _apply_window_move(window, global_pos)
                event.accept()
                return True
            if _is_move_surface(watched, window, window_pos):
                return False
            _clear_shell_cursor(watched, window)
            return False

        if event_type == QEvent.Type.MouseButtonRelease:
            if getattr(window, "_engineering_move_active", False):
                window._engineering_move_active = False
                event.accept()
                return True
            _clear_shell_cursor(watched, window)

        return False


def apply_window_resize_fixes() -> None:
    global _FILTER
    from src.engineers_tools.app.module_window import ModuleWindow

    if getattr(ModuleWindow, "_engineering_window_resize_patch", "") == PATCH_VERSION:
        return

    original_init = ModuleWindow.__init__
    original_resize_event = ModuleWindow.resizeEvent
    original_native_event = ModuleWindow.nativeEvent

    def init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        self._engineering_move_active = False
        self._drag_position = None
        _install_shell_cursor_policy(self)

    def resize_event(self, event) -> None:
        original_resize_event(self, event)
        _sync_fixed_workspace_metadata(self)
        _install_shell_cursor_policy(self)

    def native_event(self, event_type, message):
        if sys.platform == "win32":
            try:
                msg = wintypes.MSG.from_address(int(message))
            except (AttributeError, TypeError, ValueError):
                msg = None
            if msg is not None and msg.message == WM_NCHITTEST:
                return True, HTCLIENT
        return original_native_event(self, event_type, message)

    ModuleWindow.__init__ = init
    ModuleWindow.resizeEvent = resize_event
    ModuleWindow.nativeEvent = native_event
    ModuleWindow._engineering_window_resize_patch = PATCH_VERSION

    app = QApplication.instance()
    if app is not None and _FILTER is None:
        _FILTER = _WindowMoveFilter(ModuleWindow)
        app.installEventFilter(_FILTER)

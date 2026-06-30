"""Window resize behavior for the Engineering Design Tools shell.

The main window is frameless, so Qt does not provide native resize borders.
This module adds project-styled edge/corner resize behavior without changing the
engineering page size. Window resize changes the viewport only.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, Qt
from PySide6.QtWidgets import QApplication, QWidget

from .interaction_fixes import project_cursor

PATCH_VERSION = "engineering-window-resize-2026-06-30-a"
RESIZE_MARGIN = 12
WORKSPACE_SIZE_MM = (400.0, 220.0)
_FILTER: QObject | None = None


def _window_edges(window: QWidget, pos: QPoint) -> frozenset[str]:
    if getattr(window, "_is_manually_maximized", False) or window.isMaximized():
        return frozenset()
    rect = window.rect()
    if pos.x() < 0 or pos.y() < 0 or pos.x() > rect.width() or pos.y() > rect.height():
        return frozenset()
    edges: set[str] = set()
    if pos.x() <= RESIZE_MARGIN:
        edges.add("left")
    if pos.x() >= rect.width() - RESIZE_MARGIN:
        edges.add("right")
    if pos.y() <= RESIZE_MARGIN:
        edges.add("top")
    if pos.y() >= rect.height() - RESIZE_MARGIN:
        edges.add("bottom")
    return frozenset(edges)


def _cursor_kind(edges: frozenset[str]) -> str | None:
    if not edges:
        return None
    if {"left", "top"}.issubset(edges) or {"right", "bottom"}.issubset(edges):
        return "resize_fdiag"
    if {"right", "top"}.issubset(edges) or {"left", "bottom"}.issubset(edges):
        return "resize_bdiag"
    if "left" in edges or "right" in edges:
        return "resize_h"
    if "top" in edges or "bottom" in edges:
        return "resize_v"
    return None


def _apply_window_resize(window: QWidget, global_pos: QPoint) -> None:
    edges: frozenset[str] = getattr(window, "_engineering_resize_edges", frozenset())
    start_global: QPoint = getattr(window, "_engineering_resize_start_global", global_pos)
    start_geometry: QRect = getattr(window, "_engineering_resize_start_geometry", window.geometry())
    delta = global_pos - start_global
    rect = QRect(start_geometry)
    min_w = max(720, int(window.minimumWidth()))
    min_h = max(460, int(window.minimumHeight()))

    if "left" in edges:
        rect.setLeft(min(start_geometry.left() + delta.x(), start_geometry.right() - min_w))
    if "right" in edges:
        rect.setRight(max(start_geometry.right() + delta.x(), start_geometry.left() + min_w))
    if "top" in edges:
        rect.setTop(min(start_geometry.top() + delta.y(), start_geometry.bottom() - min_h))
    if "bottom" in edges:
        rect.setBottom(max(start_geometry.bottom() + delta.y(), start_geometry.top() + min_h))

    window.setGeometry(rect)
    _sync_fixed_workspace_metadata(window)


def _set_edge_cursor(widget: QWidget, window: QWidget, edges: frozenset[str]) -> None:
    kind = _cursor_kind(edges)
    previous = getattr(window, "_engineering_resize_cursor_widget", None)
    if previous is not None and previous is not widget:
        try:
            previous.unsetCursor()
        except RuntimeError:
            pass
    if kind is None:
        if previous is not None:
            try:
                previous.unsetCursor()
            except RuntimeError:
                pass
        window._engineering_resize_cursor_widget = None
        return
    widget.setCursor(project_cursor(kind))
    window._engineering_resize_cursor_widget = widget


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


class _WindowResizeFilter(QObject):
    def __init__(self, module_window_cls: type[QWidget]) -> None:
        super().__init__()
        self._module_window_cls = module_window_cls

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if not isinstance(watched, QWidget):
            return False
        window = watched.window()
        if not isinstance(window, self._module_window_cls):
            return False
        if getattr(window, "_is_manually_maximized", False) or window.isMaximized():
            return False
        event_type = event.type()
        if event_type not in {QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease}:
            return False

        try:
            local_pos = event.position().toPoint()
            window_pos = watched.mapTo(window, local_pos)
            global_pos = event.globalPosition().toPoint()
        except AttributeError:
            return False

        if event_type == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            edges = _window_edges(window, window_pos)
            if edges:
                window._engineering_resize_active = True
                window._engineering_resize_edges = edges
                window._engineering_resize_start_global = global_pos
                window._engineering_resize_start_geometry = QRect(window.geometry())
                _set_edge_cursor(watched, window, edges)
                event.accept()
                return True
            return False

        if event_type == QEvent.Type.MouseMove:
            if getattr(window, "_engineering_resize_active", False):
                _apply_window_resize(window, global_pos)
                _set_edge_cursor(watched, window, getattr(window, "_engineering_resize_edges", frozenset()))
                event.accept()
                return True
            if event.buttons() & Qt.MouseButton.LeftButton:
                return False
            edges = _window_edges(window, window_pos)
            _set_edge_cursor(watched, window, edges)
            return False

        if event_type == QEvent.Type.MouseButtonRelease and getattr(window, "_engineering_resize_active", False):
            window._engineering_resize_active = False
            window._engineering_resize_edges = frozenset()
            _set_edge_cursor(watched, window, frozenset())
            _sync_fixed_workspace_metadata(window)
            event.accept()
            return True

        return False


def apply_window_resize_fixes() -> None:
    global _FILTER
    from src.engineers_tools.app.module_window import ModuleWindow

    if getattr(ModuleWindow, "_engineering_window_resize_patch", "") == PATCH_VERSION:
        return

    original_resize_event = ModuleWindow.resizeEvent

    def resize_event(self, event) -> None:
        original_resize_event(self, event)
        _sync_fixed_workspace_metadata(self)

    ModuleWindow.resizeEvent = resize_event
    ModuleWindow._engineering_window_resize_patch = PATCH_VERSION

    app = QApplication.instance()
    if app is not None and _FILTER is None:
        _FILTER = _WindowResizeFilter(ModuleWindow)
        app.installEventFilter(_FILTER)

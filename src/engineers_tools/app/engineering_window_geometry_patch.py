"""Window geometry and resize behavior patch for Engineering Design Tools."""

from __future__ import annotations

import logging

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QTimer, Qt
from PySide6.QtGui import QCursor


VERSION = "window-geometry-1"
EDGE_MARGIN = 8
RESTORE_SCALE = 0.58
WORKSPACE_SIZE_MM = (400.0, 220.0)

_ORIGINAL_MODULE_PRESS = None
_ORIGINAL_MODULE_MOVE = None
_ORIGINAL_MODULE_RELEASE = None
_ORIGINAL_MODULE_RESIZE = None
_ORIGINAL_TOGGLE_MAXIMIZE = None
_ORIGINAL_RESTORE_MAXIMIZE = None


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
    except Exception:
        logging.exception("engineering_window_geometry_patch: cursor patch imports failed")
        return

    edw.EngineeringCanvas._page_rect = _page_rect

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
    logging.info("engineering_window_geometry_patch: installed version=%s", VERSION)

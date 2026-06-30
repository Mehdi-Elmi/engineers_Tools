"""Strict fixed-page viewport behavior for Engineering Design Tools."""

from __future__ import annotations

import logging

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QCursor


VERSION = "fixed-viewport-v4"
WORKSPACE_SIZE_MM = (400.0, 220.0)
EDGE_MARGIN = 0


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


def _fit_page_in(area: QRectF) -> QRectF:
    ratio = WORKSPACE_SIZE_MM[1] / WORKSPACE_SIZE_MM[0]
    page_width = min(area.width(), area.height() / ratio)
    page_height = page_width * ratio
    if page_height > area.height():
        page_height = area.height()
        page_width = page_height / ratio
    return QRectF(
        area.center().x() - page_width / 2.0,
        area.center().y() - page_height / 2.0,
        page_width,
        page_height,
    )


def _baseline_size(canvas, candidate: QRectF) -> tuple[float, float]:
    """Lock the approved page display size; never grow past it during resize."""
    window = canvas.window()
    is_maximized = bool(getattr(window, "_is_manually_maximized", False) or window.isMaximized())
    baseline = getattr(canvas, "_fixed_viewport_page_px", None)
    locked = bool(getattr(canvas, "_fixed_viewport_page_locked", False))

    if baseline is None:
        baseline = (candidate.width(), candidate.height())
        canvas._fixed_viewport_page_px = baseline
        canvas._fixed_viewport_page_locked = is_maximized
        return baseline

    if is_maximized and not locked:
        baseline = (candidate.width(), candidate.height())
        canvas._fixed_viewport_page_px = baseline
        canvas._fixed_viewport_page_locked = True
        return baseline

    return float(baseline[0]), float(baseline[1])


def _page_rect(canvas) -> QRectF:
    """Return a fixed approved page rect; window resize changes viewport fit only."""
    area = _usable_area(canvas)
    candidate = _fit_page_in(area)
    baseline_w, baseline_h = _baseline_size(canvas, candidate)

    # If the viewport becomes smaller than the approved page display, scale down.
    # If it becomes larger, keep the approved display size centered in the area.
    scale = min(1.0, candidate.width() / max(1.0, baseline_w), candidate.height() / max(1.0, baseline_h))
    width = max(1.0, baseline_w * scale)
    height = max(1.0, baseline_h * scale)
    return QRectF(area.center().x() - width / 2.0, area.center().y() - height / 2.0, width, height)


def _unit_to_canvas_px(start_bar, value: float, unit: str, orientation: str = "top") -> float:
    try:
        from src.engineers_tools.ui import start_bar as sb
    except Exception:
        return max(1.0, float(value))
    canvas = start_bar._canvas() if hasattr(start_bar, "_canvas") else None
    if canvas is None:
        return max(1.0, float(value) * sb.UNIT_TO_MM[unit] * sb.MM_TO_SCREEN_PX)
    page = _page_rect(canvas)
    mm_value = float(value) * sb.UNIT_TO_MM[unit]
    if orientation in {"left", "vertical", "y"}:
        return max(1.0, mm_value * page.height() / WORKSPACE_SIZE_MM[1])
    return max(1.0, mm_value * page.width() / WORKSPACE_SIZE_MM[0])


def _asset_cursor(file_name: str, fallback: QCursor, hot_x: int = 12, hot_y: int = 12, size: int = 24) -> QCursor:
    try:
        from . import engineering_ui_small_fixes_patch as small

        return small._asset_cursor(file_name, fallback, hot_x, hot_y, size)
    except Exception:
        return fallback


def _resize_cursor(edges: set[str]) -> QCursor:
    if {"left", "top"} <= edges or {"right", "bottom"} <= edges:
        return _asset_cursor("corner_resize_a.svg", QCursor(Qt.CursorShape.SizeFDiagCursor))
    if {"right", "top"} <= edges or {"left", "bottom"} <= edges:
        return _asset_cursor("corner_resize_b.svg", QCursor(Qt.CursorShape.SizeBDiagCursor))
    if "left" in edges or "right" in edges:
        return _asset_cursor("resize_horizontal.svg", QCursor(Qt.CursorShape.SizeHorCursor))
    if "top" in edges or "bottom" in edges:
        return _asset_cursor("resize_vertical.svg", QCursor(Qt.CursorShape.SizeVerCursor))
    return QCursor(Qt.CursorShape.ArrowCursor)


def _disable_shell_edge_resize(patch_module) -> None:
    """Keep the main shell move-only; canvas object resize remains separate."""
    patch_module.EDGE_MARGIN = 0
    patch_module._window_edges = lambda _window, _pos: set()

    def no_window_resize(window, _global_pos) -> None:
        window._fixed_resize_edges = set()
        window._fixed_resize_start_global = None
        window._fixed_resize_start_geometry = None
        window._window_resize_edges = set()
        window._window_resize_start_global = None
        window._window_resize_start_geometry = None
        try:
            window.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        except Exception:
            pass

    patch_module._apply_window_resize = no_window_resize


def _sync_open_rulers(start_bar, canvas) -> None:
    try:
        canvas._page_setup_size_mm = WORKSPACE_SIZE_MM
        if getattr(start_bar, "_ruler_enabled", False):
            page = _page_rect(canvas)
            if getattr(start_bar, "_ruler_corner_origin_active", False):
                start_bar._set_ruler_origin(QPointF(page.topLeft()), custom=True)
            elif not getattr(start_bar, "_ruler_origin_custom", False):
                start_bar._set_ruler_origin(QPointF(page.center()), custom=False)
            if hasattr(start_bar, "_position_rulers"):
                start_bar._position_rulers()
        canvas.update()
    except Exception:
        logging.exception("engineering_fixed_viewport_patch: ruler sync failed")


def _install_rotation_drag_cursor() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_fixed_viewport_patch: canvas import failed")
        return
    if getattr(edw.EngineeringCanvas, "_fixed_viewport_cursor_version", "") == VERSION:
        return
    original_press = edw.EngineeringCanvas.mousePressEvent
    original_move = edw.EngineeringCanvas.mouseMoveEvent

    def set_closed_hand(canvas) -> None:
        canvas.setCursor(_asset_cursor("hand_closed.svg", QCursor(Qt.CursorShape.ClosedHandCursor), 11, 8, 23))

    def mouse_press(self, event) -> None:
        original_press(self, event)
        if getattr(self, "_drag_action", None) == "rotate":
            set_closed_hand(self)

    def mouse_move(self, event) -> None:
        original_move(self, event)
        if getattr(self, "_drag_action", None) == "rotate":
            set_closed_hand(self)

    edw.EngineeringCanvas.mousePressEvent = mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas._fixed_viewport_cursor_version = VERSION


def apply_engineering_fixed_viewport_patch() -> None:
    try:
        from . import engineering_fixed_page_rotation_patch as fixed
        from . import engineering_window_geometry_patch as geometry
        from .module_window import ModuleWindow
        from modules.mechanics_dynamics_statics import workspace as edw
        from src.engineers_tools.ui import start_bar as sb
    except Exception:
        logging.exception("engineering_fixed_viewport_patch: imports failed")
        return

    if getattr(ModuleWindow, "_fixed_viewport_patch_version", "") == VERSION:
        return

    fixed.WORKSPACE_SIZE_MM = WORKSPACE_SIZE_MM
    fixed._fixed_page_size = lambda _canvas=None: WORKSPACE_SIZE_MM
    fixed._page_rect = _page_rect
    fixed._unit_to_canvas_px = _unit_to_canvas_px
    fixed._resize_cursor = _resize_cursor
    _disable_shell_edge_resize(geometry)
    _disable_shell_edge_resize(fixed)
    edw.EngineeringCanvas._page_rect = _page_rect
    sb.StartBar._unit_to_canvas_px = _unit_to_canvas_px

    original_resize = getattr(ModuleWindow, "resizeEvent", None)

    def resize_event(self, event) -> None:
        if callable(original_resize):
            original_resize(self, event)
        canvas = getattr(self, "_canvas", None)
        start_bar = getattr(self, "_start_bar_widget", None)
        if canvas is not None and start_bar is not None:
            _sync_open_rulers(start_bar, canvas)

    ModuleWindow.resizeEvent = resize_event
    _install_rotation_drag_cursor()
    ModuleWindow._fixed_viewport_patch_version = VERSION
    logging.info("engineering_fixed_viewport_patch: installed version=%s", VERSION)

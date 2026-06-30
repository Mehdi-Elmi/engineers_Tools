"""Fixed engineering workspace dimensions for viewport resize.

Window resize must not redefine the engineering page. The page remains
400 x 220 engineering units and is fitted inside the visible canvas; grid and
ruler conversions scale from that fitted page rectangle.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF

PATCH_VERSION = "engineering-fixed-workspace-dimensions-2026-06-30-a"
WORKSPACE_SIZE = (400.0, 220.0)
PAGE_MARGIN = 8.0


def _page_rect(canvas) -> QRectF:
    width, height = WORKSPACE_SIZE
    available = QRectF(
        PAGE_MARGIN,
        PAGE_MARGIN,
        max(80.0, float(canvas.width()) - PAGE_MARGIN * 2.0),
        max(80.0, float(canvas.height()) - PAGE_MARGIN * 2.0),
    )
    ratio = height / width
    page_width = min(available.width(), available.height() / ratio)
    page_height = page_width * ratio
    if page_height > available.height():
        page_height = available.height()
        page_width = page_height / ratio
    return QRectF(
        available.center().x() - page_width / 2.0,
        available.center().y() - page_height / 2.0,
        page_width,
        page_height,
    )


def apply_fixed_workspace_dimension_fixes() -> None:
    from src.engineers_tools.ui import start_bar as sb
    from . import workspace as edw

    if getattr(sb.StartBar, "_engineering_fixed_workspace_dimension_patch", "") == PATCH_VERSION:
        return

    original_resize_event = edw.EngineeringCanvas.resizeEvent

    def unit_to_canvas_px(self, value: float, unit: str) -> float:
        canvas = self._canvas()
        mm_value = float(value) * sb.UNIT_TO_MM[unit]
        if canvas is None:
            return max(1.0, mm_value * sb.MM_TO_SCREEN_PX)
        page = _page_rect(canvas)
        return max(1.0, mm_value * page.width() / WORKSPACE_SIZE[0])

    def center_ruler_origin(self) -> None:
        canvas = self._canvas()
        if canvas is not None:
            page = _page_rect(canvas)
            self._ruler_origin = QPointF(page.center())
            self._ruler_corner_origin_active = False
            self._ruler_previous_origin = None
            self._ruler_previous_origin_custom = False

    def toggle_ruler_corner_origin(self) -> None:
        if self._ruler_corner_origin_active:
            previous = QPointF(self._ruler_previous_origin) if self._ruler_previous_origin is not None else None
            previous_custom = self._ruler_previous_origin_custom
            self._ruler_corner_origin_active = False
            self._ruler_previous_origin = None
            self._ruler_previous_origin_custom = False
            if previous is None:
                self._center_ruler_origin()
                self._set_ruler_origin(QPointF(self._ruler_origin), custom=False)
            else:
                self._set_ruler_origin(previous, custom=previous_custom)
            return
        canvas = self._canvas()
        if canvas is None:
            return
        self._ruler_previous_origin = QPointF(self._ruler_origin)
        self._ruler_previous_origin_custom = self._ruler_origin_custom
        self._ruler_corner_origin_active = True
        self._set_ruler_origin(QPointF(_page_rect(canvas).topLeft()), custom=True)

    def resize_event(self, event) -> None:
        original_resize_event(self, event)
        start_bar = getattr(self.window(), "_start_bar_widget", None)
        if start_bar is not None:
            if not getattr(start_bar, "_ruler_origin_custom", False):
                start_bar._center_ruler_origin()
            if getattr(start_bar, "_ruler_enabled", False):
                start_bar._position_rulers()
            self.update()

    sb.StartBar._unit_to_canvas_px = unit_to_canvas_px
    sb.StartBar._center_ruler_origin = center_ruler_origin
    sb.StartBar._toggle_ruler_corner_origin = toggle_ruler_corner_origin
    edw.EngineeringCanvas._page_rect = _page_rect
    edw.EngineeringCanvas.resizeEvent = resize_event
    sb.StartBar._engineering_fixed_workspace_dimension_patch = PATCH_VERSION

"""Fixed engineering workspace dimensions for viewport resize.

Window resize must not redefine the engineering page. The page remains
400 x 220 engineering units and is fitted inside the visible canvas; the white
page, grid, and ruler conversions scale from that fitted page rectangle.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

PATCH_VERSION = "engineering-fixed-workspace-dimensions-2026-06-30-c"
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


def _install_page_grid(start_bar, canvas) -> None:
    def paint_grid(canvas_self, painter: QPainter) -> None:
        page = _page_rect(canvas_self)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(QRectF(0, 0, canvas_self.width(), canvas_self.height()), QColor("#edf3f8"))
        page_path = QPainterPath()
        page_path.addRoundedRect(page, 2.5, 2.5)
        painter.fillPath(page_path, QColor("#ffffff"))
        painter.setPen(QPen(QColor("#c6d4e4"), 1.0))
        painter.drawPath(page_path)

        if not getattr(canvas_self, "_grid_visible", True):
            painter.restore()
            return

        spacing = max(1.0, min(start_bar._unit_to_canvas_px(start_bar._grid_spacing, start_bar._unit), 10000.0))
        origin = getattr(start_bar, "_ruler_origin", QPointF(page.center()))
        painter.setClipRect(page.adjusted(1, 1, -1, -1))
        painter.setPen(QPen(QColor(70, 96, 130, 46), 1))

        x = origin.x()
        while x <= page.right():
            painter.drawLine(QPointF(x, page.top()), QPointF(x, page.bottom()))
            x += spacing
        x = origin.x() - spacing
        while x >= page.left():
            painter.drawLine(QPointF(x, page.top()), QPointF(x, page.bottom()))
            x -= spacing

        y = origin.y()
        while y <= page.bottom():
            painter.drawLine(QPointF(page.left(), y), QPointF(page.right(), y))
            y += spacing
        y = origin.y() - spacing
        while y >= page.top():
            painter.drawLine(QPointF(page.left(), y), QPointF(page.right(), y))
            y -= spacing

        painter.restore()

    canvas._paint_grid = paint_grid.__get__(canvas, canvas.__class__)
    canvas._start_bar_grid_hooked = True
    canvas.update()


def apply_fixed_workspace_dimension_fixes() -> None:
    from src.engineers_tools.ui import start_bar as sb
    from . import workspace as edw

    if getattr(sb.StartBar, "_engineering_fixed_workspace_dimension_patch", "") == PATCH_VERSION:
        return

    original_resize_event = edw.EngineeringCanvas.resizeEvent
    original_ensure_canvas_hooks = sb.StartBar._ensure_canvas_hooks

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

    def ensure_canvas_hooks(self) -> None:
        original_ensure_canvas_hooks(self)
        canvas = self._canvas()
        if canvas is not None:
            if not getattr(self, "_ruler_origin_custom", False):
                self._center_ruler_origin()
            _install_page_grid(self, canvas)

    def resize_event(self, event) -> None:
        original_resize_event(self, event)
        start_bar = getattr(self.window(), "_start_bar_widget", None)
        if start_bar is not None:
            if not getattr(start_bar, "_ruler_origin_custom", False):
                start_bar._center_ruler_origin()
            _install_page_grid(start_bar, self)
            if getattr(start_bar, "_ruler_enabled", False):
                start_bar._position_rulers()
            self.update()

    sb.StartBar._unit_to_canvas_px = unit_to_canvas_px
    sb.StartBar._center_ruler_origin = center_ruler_origin
    sb.StartBar._toggle_ruler_corner_origin = toggle_ruler_corner_origin
    sb.StartBar._ensure_canvas_hooks = ensure_canvas_hooks
    edw.EngineeringCanvas._page_rect = _page_rect
    edw.EngineeringCanvas.resizeEvent = resize_event
    sb.StartBar._engineering_fixed_workspace_dimension_patch = PATCH_VERSION

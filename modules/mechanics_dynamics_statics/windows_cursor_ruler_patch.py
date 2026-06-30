"""Use OS-standard cursors and restore ruler origin behavior.

Rules enforced here:
- No custom cursor assets are used at runtime.
- Normal cursor behavior uses Qt/Windows standard cursor shapes.
- Ruler default origin is the canvas center.
- Clicking the ruler corner toggles origin to the top-left ruler corner.
- Dragging from the ruler corner previews dashed X/Y guide lines and drops a new origin.
"""

from __future__ import annotations

import math
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPen

PATCH_VERSION = "engineering-windows-cursor-ruler-2026-06-30-a"


_UNIT_MINOR_STEP = {
    "mm": (1.0, 10),
    "cm": (0.1, 10),
    "m": (0.1, 10),
    "px": (1.0, 10),
    "pt": (1.0, 12),
    "in": (0.1, 10),
}


def _cursor_for_action(action: str | None) -> QCursor:
    if action == "move":
        return QCursor(Qt.CursorShape.SizeAllCursor)
    if action in {"resize_n", "resize_s"}:
        return QCursor(Qt.CursorShape.SizeVerCursor)
    if action in {"resize_e", "resize_w"}:
        return QCursor(Qt.CursorShape.SizeHorCursor)
    if action in {"resize_ne", "resize_sw"}:
        return QCursor(Qt.CursorShape.SizeBDiagCursor)
    if action in {"resize_nw", "resize_se"}:
        return QCursor(Qt.CursorShape.SizeFDiagCursor)
    return QCursor(Qt.CursorShape.ArrowCursor)


def _project_cursor(kind: str) -> QCursor:
    mapping = {
        "move": "move",
        "resize_n": "resize_n",
        "resize_s": "resize_s",
        "resize_e": "resize_e",
        "resize_w": "resize_w",
        "resize_ne": "resize_ne",
        "resize_sw": "resize_sw",
        "resize_nw": "resize_nw",
        "resize_se": "resize_se",
        "resize_horizontal": "resize_e",
        "resize_vertical": "resize_n",
        "resize_diag_f": "resize_nw",
        "resize_diag_b": "resize_ne",
    }
    return _cursor_for_action(mapping.get(kind, None))


def _format_label(index: int, minor_step: float, unit: str) -> str:
    value = index * minor_step
    if abs(value) < 1e-9:
        return "0"
    if unit in {"cm", "m", "in"}:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _ruler_corner_point(sb_module) -> QPointF:
    return QPointF(float(sb_module.RULER_THICKNESS), float(sb_module.RULER_THICKNESS))


def _clear_preview(corner: Any) -> None:
    for guide in (getattr(corner, "_origin_h_guide", None), getattr(corner, "_origin_v_guide", None)):
        if guide is not None:
            try:
                guide.deleteLater()
            except Exception:
                pass
    corner._origin_h_guide = None
    corner._origin_v_guide = None


def _install_startbar_cursors(start_bar) -> None:
    try:
        start_bar.setCursor(Qt.CursorShape.ArrowCursor)
        for button in getattr(start_bar, "_buttons", {}).values():
            button.setCursor(Qt.CursorShape.ArrowCursor)
        for child in start_bar.findChildren(object):
            if hasattr(child, "setCursor") and child.__class__.__name__ in {"QPushButton", "QToolButton"}:
                child.setCursor(Qt.CursorShape.ArrowCursor)
    except Exception:
        return


def apply_windows_cursor_ruler_patch() -> None:
    from . import cursor_unification_fixes as cuf
    from . import interaction_fixes as interaction
    from . import workspace as edw
    from src.engineers_tools.app import engineering_ui_small_fixes_patch as small_fixes
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_windows_cursor_ruler_patch", "") == PATCH_VERSION:
        return

    cuf.project_cursor = _project_cursor
    interaction.project_cursor = _project_cursor

    def asset_cursor(_file_name, fallback, _hot_x=8, _hot_y=8, _max_side=24):
        return fallback if isinstance(fallback, QCursor) else QCursor(Qt.CursorShape.ArrowCursor)

    def set_canvas_hover_cursor(canvas, hover: str | None) -> None:
        canvas.setCursor(_cursor_for_action(hover))

    small_fixes._asset_cursor = asset_cursor
    small_fixes._set_canvas_hover_cursor = set_canvas_hover_cursor
    sb._zoom_cursor = lambda _mode: QCursor(Qt.CursorShape.CrossCursor)

    original_canvas_mouse_move = edw.EngineeringCanvas.mouseMoveEvent
    original_canvas_mouse_press = edw.EngineeringCanvas.mousePressEvent
    original_canvas_mouse_release = edw.EngineeringCanvas.mouseReleaseEvent
    original_startbar_show = sb.StartBar.showEvent
    original_startbar_init = sb.StartBar.__init__
    original_ensure_hooks = sb.StartBar._ensure_canvas_hooks
    original_set_ruler = sb.StartBar._set_ruler
    original_ruler_corner_init = sb._RulerCorner.__init__

    def canvas_mouse_press(self, event) -> None:
        original_canvas_mouse_press(self, event)
        self.setCursor(_cursor_for_action(getattr(self, "_drag_action", None)))

    def canvas_mouse_move(self, event) -> None:
        original_canvas_mouse_move(self, event)
        action = getattr(self, "_drag_action", None)
        if action:
            self.setCursor(_cursor_for_action(action))
            return
        try:
            point = self._to_canvas_point(event.position())
            _index, hover = self._hit_test_object(point)
            self.setCursor(_cursor_for_action(hover))
        except Exception:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def canvas_mouse_release(self, event) -> None:
        original_canvas_mouse_release(self, event)
        try:
            point = self._to_canvas_point(event.position())
            _index, hover = self._hit_test_object(point)
            self.setCursor(_cursor_for_action(hover))
        except Exception:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def startbar_init(self, *args, **kwargs) -> None:
        original_startbar_init(self, *args, **kwargs)
        _install_startbar_cursors(self)

    def startbar_show(self, event) -> None:
        original_startbar_show(self, event)
        _install_startbar_cursors(self)

    def center_ruler_origin(self) -> None:
        canvas = self._canvas()
        if canvas is not None:
            self._ruler_origin = QPointF(canvas.width() / 2.0, canvas.height() / 2.0)
        else:
            self._ruler_origin = QPointF(0, 0)
        self._ruler_origin_custom = False
        self._ruler_corner_origin_active = False
        self._ruler_previous_origin = None
        self._ruler_previous_origin_custom = False

    def toggle_ruler_corner_origin(self) -> None:
        if self._ruler_corner_origin_active:
            previous = QPointF(self._ruler_previous_origin) if self._ruler_previous_origin is not None else QPointF(0, 0)
            previous_custom = bool(self._ruler_previous_origin_custom)
            self._ruler_corner_origin_active = False
            self._ruler_previous_origin = None
            self._ruler_previous_origin_custom = False
            self._set_ruler_origin(previous, custom=previous_custom)
            return
        self._ruler_previous_origin = QPointF(self._ruler_origin)
        self._ruler_previous_origin_custom = bool(self._ruler_origin_custom)
        self._ruler_corner_origin_active = True
        self._set_ruler_origin(_ruler_corner_point(sb), custom=True)

    def ensure_hooks(self) -> None:
        original_ensure_hooks(self)
        _install_startbar_cursors(self)
        canvas = self._canvas()
        if canvas is None:
            return

        def paint_grid(canvas_self, painter: QPainter) -> None:
            if not getattr(canvas_self, "_grid_visible", True):
                return
            unit = getattr(self, "_unit", "mm")
            spacing_value = max(0.000001, float(getattr(self, "_grid_spacing", 1.0)))
            spacing = max(1.0, min(self._unit_to_canvas_px(spacing_value, unit), 10000.0))
            origin = QPointF(getattr(self, "_ruler_origin", QPointF(canvas_self.width() / 2.0, canvas_self.height() / 2.0)))
            page_getter = getattr(canvas_self, "_page_rect", None)
            page = QRectF(page_getter()) if callable(page_getter) else QRectF(0, 0, max(1, canvas_self.width()), max(1, canvas_self.height()))
            painter.save()
            painter.setClipRect(page)
            minor = QPen(QColor(70, 96, 130, 42), 1)
            major = QPen(QColor(39, 74, 116, 72), 1)
            first_x = origin.x() + math.floor((page.left() - origin.x()) / spacing) * spacing
            x = first_x
            while x <= page.right() + 0.5:
                index = int(round((x - origin.x()) / spacing))
                painter.setPen(major if index % 10 == 0 else minor)
                painter.drawLine(QPointF(x, page.top()), QPointF(x, page.bottom()))
                x += spacing
            first_y = origin.y() + math.floor((page.top() - origin.y()) / spacing) * spacing
            y = first_y
            while y <= page.bottom() + 0.5:
                index = int(round((y - origin.y()) / spacing))
                painter.setPen(major if index % 10 == 0 else minor)
                painter.drawLine(QPointF(page.left(), y), QPointF(page.right(), y))
                y += spacing
            painter.restore()

        canvas._paint_grid = paint_grid.__get__(canvas, canvas.__class__)
        canvas._grid_spacing = self._grid_spacing
        canvas._grid_unit = self._unit

    def set_ruler(self, enabled: bool) -> None:
        original_set_ruler(self, enabled)
        if enabled and not getattr(self, "_ruler_origin_custom", False) and not getattr(self, "_ruler_corner_origin_active", False):
            center_ruler_origin(self)
            self._sync_rulers()

    def ruler_overlay_init(self, start_bar, orientation: str, parent) -> None:
        sb._RulerOverlay.__bases__[0].__init__(self, parent)
        self._start_bar = start_bar
        self._orientation = orientation
        self._dragging_guide = False
        self._active_guide = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def ruler_overlay_paint(self, event) -> None:  # noqa: ARG001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(20, 37, 58, 230))
        unit = getattr(self._start_bar, "_unit", "mm")
        minor_value, major_every = _UNIT_MINOR_STEP.get(unit, (1.0, 10))
        spacing = max(1.0, self._start_bar._unit_to_canvas_px(minor_value, unit))
        length = self.width() if self._orientation == "top" else self.height()
        zero = self._start_bar._ruler_origin.x() - self.x() if self._orientation == "top" else self._start_bar._ruler_origin.y() - self.y()
        font = painter.font()
        font.setFamily("Times New Roman")
        font.setPointSize(7)
        font.setBold(True)
        font.setItalic(False)
        painter.setFont(font)
        start_index = math.floor((0 - zero) / spacing) - 2
        index = start_index
        while True:
            position = zero + index * spacing
            if position > length + spacing:
                break
            if position >= 0:
                tick = 23 if index % major_every == 0 else 15 if index % max(1, major_every // 2) == 0 else 8
                painter.setPen(QPen(QColor("#ffffff"), 1.0))
                label = _format_label(index, minor_value, unit)
                if self._orientation == "top":
                    painter.drawLine(QPointF(position, self.height()), QPointF(position, self.height() - tick))
                    if index % major_every == 0:
                        painter.drawText(QRectF(position + 2, 1, 54, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
                else:
                    painter.drawLine(QPointF(self.width(), position), QPointF(self.width() - tick, position))
                    if index % major_every == 0:
                        painter.drawText(QRectF(2, position + 1, self.width() - 4, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
            index += 1
        painter.end()

    def ruler_corner_init(self, start_bar, parent) -> None:
        original_ruler_corner_init(self, start_bar, parent)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def ruler_corner_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._pressed = True
            self._press_pos = event.position()
            _clear_preview(self)
            self.update()
            event.accept()
            return
        super(sb._RulerCorner, self).mousePressEvent(event)

    def ruler_corner_move(self, event) -> None:
        if self._dragging and self.parentWidget() is not None:
            delta = event.position() - self._press_pos if self._press_pos is not None else QPointF(0, 0)
            if abs(delta.x()) + abs(delta.y()) >= 4:
                self._pressed = False
                point = self.parentWidget().mapFromGlobal(event.globalPosition().toPoint())
                if getattr(self, "_origin_h_guide", None) is None:
                    self._origin_h_guide = sb._GuideLine("horizontal", point.y(), self.parentWidget(), None, persistent=False)
                else:
                    self._origin_h_guide.position = point.y()
                    self._origin_h_guide._place()
                if getattr(self, "_origin_v_guide", None) is None:
                    self._origin_v_guide = sb._GuideLine("vertical", point.x(), self.parentWidget(), None, persistent=False)
                else:
                    self._origin_v_guide.position = point.x()
                    self._origin_v_guide._place()
                self.update()
            event.accept()
            return
        super(sb._RulerCorner, self).mouseMoveEvent(event)

    def ruler_corner_release(self, event) -> None:
        if self._dragging:
            self._dragging = False
            canvas = self.parentWidget()
            delta = event.position() - self._press_pos if self._press_pos is not None else QPointF(0, 0)
            moved = abs(delta.x()) + abs(delta.y())
            if canvas is not None:
                if moved < 4:
                    self._start_bar._toggle_ruler_corner_origin()
                else:
                    point = canvas.mapFromGlobal(event.globalPosition().toPoint())
                    self._start_bar._ruler_corner_origin_active = False
                    self._start_bar._ruler_previous_origin = None
                    self._start_bar._ruler_previous_origin_custom = False
                    self._start_bar._set_ruler_origin(QPointF(point), custom=True)
            self._pressed = False
            self._press_pos = None
            _clear_preview(self)
            self.update()
            event.accept()
            return
        super(sb._RulerCorner, self).mouseReleaseEvent(event)

    def guide_init(self, orientation: str, position: float, parent, start_bar=None, persistent: bool = True) -> None:
        super(sb._GuideLine, self).__init__(parent)
        self.orientation = orientation
        self.position = position
        self._start_bar = start_bar
        self._persistent = persistent
        self._dragging = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._place()
        if self._start_bar is not None and self._persistent:
            self._start_bar._register_ruler_guide(self)
        self.show()

    edw.EngineeringCanvas.mousePressEvent = canvas_mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = canvas_mouse_move
    edw.EngineeringCanvas.mouseReleaseEvent = canvas_mouse_release
    sb.StartBar.__init__ = startbar_init
    sb.StartBar.showEvent = startbar_show
    sb.StartBar._center_ruler_origin = center_ruler_origin
    sb.StartBar._toggle_ruler_corner_origin = toggle_ruler_corner_origin
    sb.StartBar._ensure_canvas_hooks = ensure_hooks
    sb.StartBar._set_ruler = set_ruler
    sb._RulerOverlay.__init__ = ruler_overlay_init
    sb._RulerOverlay.paintEvent = ruler_overlay_paint
    sb._RulerCorner.__init__ = ruler_corner_init
    sb._RulerCorner.mousePressEvent = ruler_corner_press
    sb._RulerCorner.mouseMoveEvent = ruler_corner_move
    sb._RulerCorner.mouseReleaseEvent = ruler_corner_release
    sb._GuideLine.__init__ = guide_init
    edw.EngineeringDesignWorkspace._engineering_windows_cursor_ruler_patch = PATCH_VERSION

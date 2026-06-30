"""Focused interaction fixes for the Engineering Design Tools workspace.

This module keeps the current workspace stable while centralizing interaction
behavior that must become a shared project pattern: custom cursors, ruler/zoom
sync, anchored resize, angle feedback, and the F8 orthogonal snap shortcut.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QShortcut

PATCH_VERSION = "engineering-interaction-fixes-2026-06-30-b"


def _cursor_arrow(painter: QPainter, tip: QPointF, tail: QPointF, size: float = 6.0) -> None:
    direction = tip - tail
    length = max(0.01, math.hypot(direction.x(), direction.y()))
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    base = QPointF(tip.x() - unit.x() * size, tip.y() - unit.y() * size)
    left = QPointF(base.x() + normal.x() * size * 0.48, base.y() + normal.y() * size * 0.48)
    right = QPointF(base.x() - normal.x() * size * 0.48, base.y() - normal.y() * size * 0.48)
    painter.drawPolygon(QPolygonF([tip, left, right]))


def _paint_hand(painter: QPainter, closed: bool) -> None:
    ink = QColor("#132238")
    fill = QLinearGradient(7, 4, 25, 29)
    fill.setColorAt(0.0, QColor("#ffffff"))
    fill.setColorAt(0.54, QColor("#dff4ff"))
    fill.setColorAt(1.0, QColor("#ffc35a" if closed else "#8dc1ff"))
    path = QPainterPath()
    if closed:
        path.addRoundedRect(QRectF(8, 11, 17, 15), 6, 6)
        path.addRoundedRect(QRectF(9, 7, 4, 9), 2, 2)
        path.addRoundedRect(QRectF(13, 6, 4, 10), 2, 2)
        path.addRoundedRect(QRectF(17, 7, 4, 9), 2, 2)
        path.addRoundedRect(QRectF(21, 10, 4, 8), 2, 2)
    else:
        path.addRoundedRect(QRectF(8, 12, 15, 15), 6, 6)
        path.addRoundedRect(QRectF(8, 5, 4, 13), 2, 2)
        path.addRoundedRect(QRectF(12, 4, 4, 14), 2, 2)
        path.addRoundedRect(QRectF(16, 5, 4, 13), 2, 2)
        path.addRoundedRect(QRectF(20, 8, 4, 11), 2, 2)
    painter.fillPath(path, fill)
    painter.setPen(QPen(QColor("#ffffff"), 3.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)
    painter.setPen(QPen(ink, 1.35, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)


def project_cursor(kind: str) -> QCursor:
    """Return a project-styled cursor instead of Qt's default resize glyphs."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    ink = QColor("#132238")
    painter.setPen(QPen(QColor("#ffffff"), 4.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

    def stroke_line(a: QPointF, b: QPointF) -> None:
        painter.drawLine(a, b)
        painter.setPen(QPen(ink, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(a, b)
        painter.setBrush(ink)
        _cursor_arrow(painter, a, b, 5.8)
        _cursor_arrow(painter, b, a, 5.8)
        painter.setPen(QPen(QColor("#ffffff"), 4.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

    if kind in {"resize_h", "guide_v"}:
        stroke_line(QPointF(5, 16), QPointF(27, 16))
    elif kind in {"resize_v", "guide_h"}:
        stroke_line(QPointF(16, 5), QPointF(16, 27))
    elif kind == "resize_fdiag":
        stroke_line(QPointF(7, 7), QPointF(25, 25))
    elif kind == "resize_bdiag":
        stroke_line(QPointF(25, 7), QPointF(7, 25))
    elif kind == "move":
        for tip, tail in ((QPointF(16, 4), QPointF(16, 15)), (QPointF(28, 16), QPointF(17, 16)), (QPointF(16, 28), QPointF(16, 17)), (QPointF(4, 16), QPointF(15, 16))):
            painter.setPen(QPen(ink, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(tail, tip)
            painter.setBrush(ink)
            _cursor_arrow(painter, tip, tail, 5.5)
    elif kind in {"rotate", "hand_open"}:
        _paint_hand(painter, closed=False)
    elif kind == "hand_closed":
        _paint_hand(painter, closed=True)
    else:
        path = QPainterPath()
        path.moveTo(7, 5)
        path.lineTo(24, 17)
        path.lineTo(16.5, 18.4)
        path.lineTo(21.5, 28)
        path.lineTo(16.2, 29)
        path.lineTo(11.8, 19.5)
        path.lineTo(7, 24)
        path.closeSubpath()
        grad = QLinearGradient(6, 5, 24, 28)
        grad.setColorAt(0.0, QColor("#ffffff"))
        grad.setColorAt(0.58, QColor("#dff4ff"))
        grad.setColorAt(1.0, QColor("#ffc35a"))
        painter.fillPath(path, grad)
        painter.setPen(QPen(ink, 1.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)
    painter.end()
    return QCursor(pixmap, 16, 16)


def _angle_delta(a: float, b: float) -> float:
    return (a - b + 180.0) % 360.0 - 180.0


def _nearest_orthogonal(angle: float) -> float:
    return (round(angle / 90.0) * 90.0) % 360.0


def _paint_angle_badge(painter: QPainter, position: QPointF, angle: float) -> None:
    painter.save()
    rect = QRectF(position.x(), position.y(), 74, 22)
    path = QPainterPath()
    path.addRoundedRect(rect, 7, 7)
    painter.fillPath(path, QColor(16, 34, 56, 235))
    painter.setPen(QPen(QColor("#ffc35a"), 1.0))
    painter.drawPath(path)
    painter.setPen(QColor("#ffffff"))
    font = painter.font()
    font.setPointSize(8)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{angle % 360.0:.2f} deg")
    painter.restore()


def _install_start_bar_patch() -> None:
    from src.engineers_tools.ui import start_bar as sb

    if getattr(sb.StartBar, "_engineering_interaction_patch", "") == PATCH_VERSION:
        return

    original_guide_init = sb._GuideLine.__init__
    original_overlay_init = sb._RulerOverlay.__init__
    original_corner_init = sb._RulerCorner.__init__
    original_zoom_value = sb.StartBar._set_zoom_value

    def guide_init(self, orientation, position, parent, start_bar=None, persistent=True):
        original_guide_init(self, orientation, position, parent, start_bar, persistent)
        self.setCursor(project_cursor("guide_h" if orientation == "horizontal" else "guide_v"))

    def overlay_init(self, start_bar, orientation, parent):
        original_overlay_init(self, start_bar, orientation, parent)
        self.setCursor(project_cursor("guide_h" if orientation == "top" else "guide_v"))

    def corner_init(self, start_bar, parent):
        original_corner_init(self, start_bar, parent)
        self.setCursor(project_cursor("origin"))

    def guide_context_menu(self, event) -> None:
        from src.engineers_tools.app.module_window import MenuItemSpec, ProjectMenuDialog

        def delete_guide() -> None:
            if self._start_bar is not None:
                self._start_bar._unregister_ruler_guide(self)
            self.deleteLater()

        dialog = ProjectMenuDialog("Guide", (MenuItemSpec("Delete", delete_guide),), self)
        dialog.adjustSize()
        dialog.move(event.globalPos())
        dialog.exec()
        event.accept()

    def scene_axis_to_view(canvas, value: float, axis: str) -> float:
        zoom = max(0.01, float(getattr(canvas, "_zoom", 1.0)))
        center = canvas.width() / 2.0 if axis == "x" else canvas.height() / 2.0
        return center + (value - center) * zoom

    def overlay_paint(self, event) -> None:
        super(sb._RulerOverlay, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(20, 37, 58, 230))
        font = painter.font()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        canvas = self.parentWidget()
        zoom = max(0.01, float(getattr(canvas, "_zoom", 1.0))) if canvas is not None else 1.0
        spacing = max(1.0, self._start_bar._unit_to_canvas_px(1.0, self._start_bar._unit) * zoom)
        length = self.width() if self._orientation == "top" else self.height()
        if canvas is not None and self._orientation == "top":
            zero = scene_axis_to_view(canvas, self._start_bar._ruler_origin.x(), "x") - self.x()
        elif canvas is not None:
            zero = scene_axis_to_view(canvas, self._start_bar._ruler_origin.y(), "y") - self.y()
        else:
            zero = self._start_bar._ruler_origin.x() - self.x() if self._orientation == "top" else self._start_bar._ruler_origin.y() - self.y()
        index = int(-zero / spacing) - 2
        while True:
            position = zero + index * spacing
            if position > length + spacing:
                break
            if position >= 0:
                abs_index = abs(index)
                tick = 23 if abs_index % 10 == 0 else 16 if abs_index % 5 == 0 else 8
                if self._orientation == "top":
                    painter.drawLine(QPointF(position, self.height()), QPointF(position, self.height() - tick))
                    if abs_index % 10 == 0:
                        painter.drawText(QRectF(position + 2, 1, 46, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
                else:
                    painter.drawLine(QPointF(self.width(), position), QPointF(self.width() - tick, position))
                    if abs_index % 10 == 0:
                        painter.drawText(QRectF(2, position + 1, self.width() - 4, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
            index += 1
        painter.end()

    def set_zoom_value(self, value: float) -> None:
        original_zoom_value(self, value)
        if getattr(self, "_ruler_enabled", False):
            self._position_rulers()
        canvas = self._canvas()
        if canvas is not None:
            canvas.update()

    sb._GuideLine.__init__ = guide_init
    sb._GuideLine.contextMenuEvent = guide_context_menu
    sb._RulerOverlay.__init__ = overlay_init
    sb._RulerCorner.__init__ = corner_init
    sb._RulerOverlay.paintEvent = overlay_paint
    sb.StartBar._set_zoom_value = set_zoom_value
    sb.StartBar._engineering_interaction_patch = PATCH_VERSION


def _install_workspace_patch() -> None:
    from . import workspace as edw

    if getattr(edw.EngineeringCanvas, "_engineering_interaction_patch", "") == PATCH_VERSION:
        return

    original_mouse_move = edw.EngineeringCanvas.mouseMoveEvent
    original_key_press = edw.EngineeringCanvas.keyPressEvent
    original_frame = edw.EngineeringCanvas._paint_selection_frame
    original_group_frame = edw.EngineeringCanvas._paint_group_selection
    original_build_side_panel = edw.EngineeringDesignWorkspace._build_side_panel
    original_install_shortcuts = edw.EngineeringDesignWorkspace._install_engineering_shortcuts

    def resize_kind(action: str | None, dragging: bool = False) -> str | None:
        if action in {"resize_n", "resize_s"}:
            return "resize_v"
        if action in {"resize_e", "resize_w"}:
            return "resize_h"
        if action in {"resize_nw", "resize_se"}:
            return "resize_fdiag"
        if action in {"resize_ne", "resize_sw"}:
            return "resize_bdiag"
        if action == "move":
            return "move"
        if action == "rotate":
            return "hand_closed" if dragging else "hand_open"
        return None

    def hit_test_group(self, point: QPointF) -> str | None:
        if self._selection_group_id() is None:
            return None
        rect = self._group_bounds().adjusted(-8, -8, 8, 8)
        rotate_center = QPointF(rect.center().x(), rect.top() - 34)
        if math.hypot(point.x() - rotate_center.x(), point.y() - rotate_center.y()) <= 18:
            return "rotate"
        handles = {
            "resize_nw": rect.topLeft(), "resize_n": QPointF(rect.center().x(), rect.top()), "resize_ne": rect.topRight(),
            "resize_e": QPointF(rect.right(), rect.center().y()), "resize_se": rect.bottomRight(), "resize_s": QPointF(rect.center().x(), rect.bottom()),
            "resize_sw": rect.bottomLeft(), "resize_w": QPointF(rect.left(), rect.center().y()),
        }
        for action, handle in handles.items():
            if abs(point.x() - handle.x()) <= 14.0 and abs(point.y() - handle.y()) <= 14.0:
                return action
        if rect.contains(point):
            return "move"
        return None

    def hit_test_single(self, obj, point: QPointF) -> str | None:
        local = self._scene_to_object_local(obj, point)
        half_w = obj.rect.width() / 2
        half_h = obj.rect.height() / 2
        if obj.rotation_handle_visible and math.hypot(local.x(), local.y() + half_h + 34) <= 18:
            return "rotate"
        handles = {
            "resize_nw": QPointF(-half_w, -half_h), "resize_n": QPointF(0, -half_h), "resize_ne": QPointF(half_w, -half_h),
            "resize_e": QPointF(half_w, 0), "resize_se": QPointF(half_w, half_h), "resize_s": QPointF(0, half_h),
            "resize_sw": QPointF(-half_w, half_h), "resize_w": QPointF(-half_w, 0),
        }
        for action, handle in handles.items():
            if abs(local.x() - handle.x()) <= 14.0 and abs(local.y() - handle.y()) <= 14.0:
                return action
        if -half_w + 7 <= local.x() <= half_w - 7 and -half_h + 7 <= local.y() <= half_h - 7:
            return "move"
        return None

    def apply_single_resize(self, point: QPointF, handle: str) -> None:
        if not self.selected_indices:
            return
        index = next(iter(self.selected_indices))
        obj = self.objects[index]
        start_rect = self._drag_start_rects[index]
        start_rotation = self._drag_start_rotations[index]
        delta_local = edw._rotate_vector(point - self._drag_start, -start_rotation)
        left = -start_rect.width() / 2.0
        right = start_rect.width() / 2.0
        top = -start_rect.height() / 2.0
        bottom = start_rect.height() / 2.0
        if "w" in handle:
            left += delta_local.x()
        if "e" in handle:
            right += delta_local.x()
        if "n" in handle:
            top += delta_local.y()
        if "s" in handle:
            bottom += delta_local.y()
        min_size = 35.0
        if right - left < min_size:
            if "w" in handle:
                left = right - min_size
            else:
                right = left + min_size
        if bottom - top < min_size:
            if "n" in handle:
                top = bottom - min_size
            else:
                bottom = top + min_size
        width = right - left
        height = bottom - top
        center_shift = QPointF((left + right) / 2.0, (top + bottom) / 2.0)
        new_center = start_rect.center() + edw._rotate_vector(center_shift, start_rotation)
        obj.rect = QRectF(new_center.x() - width / 2.0, new_center.y() - height / 2.0, width, height)
        obj.rotation = start_rotation

    def mouse_move(self, event) -> None:
        original_mouse_move(self, event)
        drag_action = getattr(self, "_drag_action", None)
        action = drag_action
        if action is None:
            try:
                _index, action = self._hit_test_object(self._to_canvas_point(event.position()))
            except Exception:
                action = None
        cursor_name = resize_kind(action, dragging=drag_action is not None)
        if cursor_name is not None:
            self.setCursor(project_cursor(cursor_name))

    def key_press(self, event) -> None:
        if event.key() == Qt.Key_F8:
            host = self.window()
            snap = getattr(host, "_orthogonal_snap", None)
            if callable(snap):
                snap()
            else:
                self.snap_selection_to_orthogonal()
            event.accept()
            return
        original_key_press(self, event)

    def paint_selection_frame(self, painter: QPainter, obj) -> None:
        original_frame(self, painter, obj)
        if not getattr(obj, "rotation_handle_visible", True):
            return
        rect = obj.rect
        rotate_pos = rect.center() + edw._rotate_vector(QPointF(0, -rect.height() / 2.0 - 34), obj.rotation)
        _paint_angle_badge(painter, rotate_pos + QPointF(18, -15), obj.rotation)

    def paint_group_selection(self, painter: QPainter) -> None:
        original_group_frame(self, painter)
        if not self.selected_indices:
            return
        rect = self._group_bounds().adjusted(-6, -6, 6, 6)
        rotate_pos = QPointF(rect.center().x(), rect.top() - 34)
        angles = [self.objects[index].rotation for index in self.selected_indices]
        angle = sum(angles) / len(angles)
        _paint_angle_badge(painter, rotate_pos + QPointF(18, -15), angle)

    def snap_selection_to_orthogonal(self) -> bool:
        if not self.selected_indices:
            return False
        self._push_undo()
        changed = False
        for index in sorted(self.selected_indices):
            obj = self.objects[index]
            if obj.locked:
                continue
            target = _nearest_orthogonal(obj.rotation)
            if abs(_angle_delta(obj.rotation, target)) > 0.01:
                obj.rotation = target
                changed = True
        if changed:
            self._emit_object_changes()
            self.update()
        return changed

    def orthogonal_snap(self) -> None:
        canvas = getattr(self, "_canvas", None)
        if isinstance(canvas, edw.EngineeringCanvas) and canvas.snap_selection_to_orthogonal():
            self._set_status("F8 Orthogonal Snap: nearest XY axis")
        else:
            self._set_status("F8 Orthogonal Snap: select a rotated object")

    def build_side_panel(self, title: str, rows: tuple[str, ...]):
        if title == "Properties" and "F8: Orthogonal Snap" not in rows:
            rows = tuple(rows) + ("Shortcut Keys", "F8: Orthogonal Snap")
        return original_build_side_panel(self, title, rows)

    def install_shortcuts(self) -> None:
        original_install_shortcuts(self)
        if getattr(self, "_f8_orthogonal_shortcut_installed", False):
            return
        self._f8_orthogonal_shortcut_installed = True
        shortcut = QShortcut(QKeySequence("F8"), self)
        shortcut.setContext(Qt.WindowShortcut)
        shortcut.activated.connect(self._orthogonal_snap)
        shortcut.activatedAmbiguously.connect(self._orthogonal_snap)
        self._engineering_shortcuts.append(shortcut)
        canvas = getattr(self, "_canvas", None)
        if canvas is not None:
            canvas_shortcut = QShortcut(QKeySequence("F8"), canvas)
            canvas_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
            canvas_shortcut.activated.connect(self._orthogonal_snap)
            canvas_shortcut.activatedAmbiguously.connect(self._orthogonal_snap)
            self._engineering_shortcuts.append(canvas_shortcut)

    edw.EngineeringCanvas._hit_test_group_selection = hit_test_group
    edw.EngineeringCanvas._hit_test_single_object = hit_test_single
    edw.EngineeringCanvas._apply_single_resize = apply_single_resize
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas.keyPressEvent = key_press
    edw.EngineeringCanvas._paint_selection_frame = paint_selection_frame
    edw.EngineeringCanvas._paint_group_selection = paint_group_selection
    edw.EngineeringCanvas.snap_selection_to_orthogonal = snap_selection_to_orthogonal
    edw.EngineeringDesignWorkspace._orthogonal_snap = orthogonal_snap
    edw.EngineeringDesignWorkspace._build_side_panel = build_side_panel
    edw.EngineeringDesignWorkspace._install_engineering_shortcuts = install_shortcuts
    edw.EngineeringCanvas._engineering_interaction_patch = PATCH_VERSION


def apply_interaction_fixes() -> None:
    _install_start_bar_patch()
    _install_workspace_patch()

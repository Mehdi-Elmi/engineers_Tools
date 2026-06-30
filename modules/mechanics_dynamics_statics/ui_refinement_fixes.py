"""Visual and unit refinements for the Engineering Design Tools workspace.

This patch is intentionally layered after the broader interaction patch. It keeps
logic changes small while standardizing cursor colors, ruler labels, grid unit
spacing, menu typography, selection handles, and angle feedback.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QPushButton

PATCH_VERSION = "engineering-ui-refinements-2026-06-30-a"


def _cursor_arrow(painter: QPainter, tip: QPointF, tail: QPointF, size: float = 5.0) -> None:
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
    fill.setColorAt(1.0, QColor("#78b8ff" if closed else "#8dc1ff"))
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


def _refined_project_cursor(kind: str) -> QCursor:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    ink = QColor("#132238")
    glow = QColor("#ffffff")

    def stroke_line(a: QPointF, b: QPointF) -> None:
        painter.setPen(QPen(glow, 4.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(a, b)
        painter.setPen(QPen(ink, 1.85, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(a, b)
        painter.setBrush(ink)
        _cursor_arrow(painter, a, b, 5.2)
        _cursor_arrow(painter, b, a, 5.2)

    if kind in {"resize_h", "guide_v"}:
        stroke_line(QPointF(6, 16), QPointF(26, 16))
    elif kind in {"resize_v", "guide_h"}:
        stroke_line(QPointF(16, 6), QPointF(16, 26))
    elif kind == "resize_fdiag":
        stroke_line(QPointF(8, 8), QPointF(24, 24))
    elif kind == "resize_bdiag":
        stroke_line(QPointF(24, 8), QPointF(8, 24))
    elif kind == "move":
        for tip, tail in ((QPointF(16, 5), QPointF(16, 15)), (QPointF(27, 16), QPointF(17, 16)), (QPointF(16, 27), QPointF(16, 17)), (QPointF(5, 16), QPointF(15, 16))):
            painter.setPen(QPen(glow, 3.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(tail, tip)
            painter.setPen(QPen(ink, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(tail, tip)
            painter.setBrush(ink)
            _cursor_arrow(painter, tip, tail, 4.8)
    elif kind in {"rotate", "hand_open"}:
        _paint_hand(painter, closed=False)
    elif kind == "hand_closed":
        _paint_hand(painter, closed=True)
    elif kind == "origin":
        painter.setPen(QPen(QColor("#ffffff"), 3.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(8, 16), QPointF(24, 16))
        painter.drawLine(QPointF(16, 8), QPointF(16, 24))
        painter.setPen(QPen(QColor("#132238"), 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(8, 16), QPointF(24, 16))
        painter.drawLine(QPointF(16, 8), QPointF(16, 24))
        painter.setBrush(QColor("#ff8a35"))
        painter.setPen(QPen(QColor("#132238"), 1.0))
        painter.drawEllipse(QPointF(16, 16), 2.8, 2.8)
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
        grad.setColorAt(1.0, QColor("#8dc1ff"))
        painter.fillPath(path, grad)
        painter.setPen(QPen(ink, 1.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)
    painter.end()
    return QCursor(pixmap, 16, 16)


def _paint_angle_badge(painter: QPainter, position: QPointF, angle: float) -> None:
    painter.save()
    rect = QRectF(position.x(), position.y(), 64, 20)
    path = QPainterPath()
    path.addRoundedRect(rect, 7, 7)
    painter.fillPath(path, QColor(16, 34, 56, 232))
    painter.setPen(QPen(QColor("#ffc35a"), 1.0))
    painter.drawPath(path)
    painter.setPen(QColor("#ffffff"))
    font = painter.font()
    font.setPointSize(8)
    font.setBold(True)
    font.setItalic(False)
    painter.setFont(font)
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{angle % 360.0:.2f}°")
    painter.restore()


def _default_grid_spacing(unit: str) -> float:
    return {"mm": 10.0, "cm": 1.0, "m": 1.0, "px": 50.0, "pt": 12.0, "in": 0.5}.get(unit, 1.0)


def _install_start_bar_refinements() -> None:
    from src.engineers_tools.ui import start_bar as sb

    if getattr(sb.StartBar, "_engineering_ui_refinement_patch", "") == PATCH_VERSION:
        return

    original_set_unit = sb.StartBar._set_unit

    def style_guide_menu(menu) -> None:
        menu.setStyleSheet(
            "QMenu {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.55 #edf8ff, stop:1 #fff1d3); border:1px solid #8fa2bb; border-radius:10px; padding:6px;}"
            "QMenu::item {color:#1f3148; padding:6px 24px 6px 12px; border-radius:7px; font-size:12px; font-style:normal; font-weight:800;}"
            "QMenu::item:selected {background:#fff4cf; color:#132238;}"
        )

    def overlay_paint(self, event) -> None:
        super(sb._RulerOverlay, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(20, 37, 58, 230))
        font = painter.font()
        font.setPointSize(7)
        font.setBold(True)
        font.setItalic(False)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        canvas = self.parentWidget()
        zoom = max(0.01, float(getattr(canvas, "_zoom", 1.0))) if canvas is not None else 1.0
        unit = self._start_bar._unit
        spacing = max(1.0, self._start_bar._unit_to_canvas_px(1.0, unit) * zoom)
        length = self.width() if self._orientation == "top" else self.height()
        if canvas is not None and self._orientation == "top":
            zero = self._start_bar._ruler_origin.x() - self.x()
        elif canvas is not None:
            zero = self._start_bar._ruler_origin.y() - self.y()
        else:
            zero = self._start_bar._ruler_origin.x() - self.x() if self._orientation == "top" else self._start_bar._ruler_origin.y() - self.y()
        label_step = 10 if unit == "mm" else 1
        index = int(-zero / spacing) - 2
        while True:
            position = zero + index * spacing
            if position > length + spacing:
                break
            if position >= 0:
                abs_index = abs(index)
                is_label = abs_index % label_step == 0
                tick = 23 if is_label else 16 if unit == "mm" and abs_index % 5 == 0 else 8
                if self._orientation == "top":
                    painter.drawLine(QPointF(position, self.height()), QPointF(position, self.height() - tick))
                    if is_label:
                        painter.drawText(QRectF(position + 2, 1, 46, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
                else:
                    painter.drawLine(QPointF(self.width(), position), QPointF(self.width() - tick, position))
                    if is_label:
                        painter.drawText(QRectF(2, position + 1, self.width() - 4, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
            index += 1
        painter.end()

    def set_unit(self, unit: str) -> None:
        if unit == self._unit:
            return original_set_unit(self, unit)
        self._unit = unit
        self._grid_spacing = _default_grid_spacing(unit)
        self._apply_unit_to_host()
        self._apply_grid_to_host()
        if self._ruler_enabled:
            self._sync_rulers()
        self.unit_changed.emit(unit)
        self.grid_changed.emit(self._grid_enabled, self._grid_spacing, self._unit)
        self.tool_requested.emit(f"unit_{unit}")
        self._refresh_tooltips()
        if self._popup is not None:
            self._popup.close()

    sb._style_guide_menu = style_guide_menu
    sb._RulerOverlay.paintEvent = overlay_paint
    sb.StartBar._set_unit = set_unit
    sb.StartBar._engineering_ui_refinement_patch = PATCH_VERSION


def _install_menu_refinements() -> None:
    from src.engineers_tools.app import module_window as mw

    if getattr(mw.ProjectMenuDialog, "_engineering_ui_refinement_patch", "") == PATCH_VERSION:
        return

    original_init = mw.ProjectMenuDialog.__init__

    def init(self, title, items, parent=None) -> None:
        original_init(self, title, items, parent)
        for button in self.findChildren(QPushButton, "MenuItemButton"):
            font = button.font()
            font.setItalic(False)
            button.setFont(font)
            button.setStyleSheet("font-style:normal;")

    mw.ProjectMenuDialog.__init__ = init
    mw.ProjectMenuDialog._engineering_ui_refinement_patch = PATCH_VERSION


def _install_workspace_visual_refinements() -> None:
    from . import interaction_fixes as fixes
    from . import workspace as edw

    if getattr(edw.EngineeringCanvas, "_engineering_ui_refinement_patch", "") == PATCH_VERSION:
        return

    fixes.project_cursor = _refined_project_cursor
    fixes._paint_angle_badge = _paint_angle_badge

    def paint_selection_frame(self, painter: QPainter, obj) -> None:
        rect = obj.rect
        half_w = rect.width() / 2
        half_h = rect.height() / 2
        select = QColor("#2f7df6")
        painter.save()
        painter.translate(rect.center())
        painter.rotate(obj.rotation)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(select, 1.35, Qt.DashLine))
        painter.drawRect(QRectF(-half_w - 4, -half_h - 4, rect.width() + 8, rect.height() + 8))
        handles = (QPointF(-half_w, -half_h), QPointF(0, -half_h), QPointF(half_w, -half_h), QPointF(half_w, 0), QPointF(half_w, half_h), QPointF(0, half_h), QPointF(-half_w, half_h), QPointF(-half_w, 0))
        painter.setPen(QPen(QColor("#ffffff"), 0.9))
        painter.setBrush(select)
        for handle in handles:
            painter.drawRoundedRect(QRectF(handle.x() - 3, handle.y() - 3, 6, 6), 1.8, 1.8)
        if obj.rotation_handle_visible:
            rotate_center = QPointF(0, -half_h - 32)
            painter.setPen(QPen(select, 1.1, Qt.DashLine))
            painter.drawLine(QPointF(0, -half_h - 4), QPointF(0, rotate_center.y() + 11))
            painter.setBrush(QColor("#fff9de"))
            painter.setPen(QPen(QColor("#7e5b10"), 1.25))
            painter.drawEllipse(rotate_center, 11, 11)
            edw._draw_arc_arrow(painter, rotate_center, 6.4, QColor("#ff8a35"))
        painter.restore()
        if obj.rotation_handle_visible:
            rotate_pos = rect.center() + edw._rotate_vector(QPointF(0, -rect.height() / 2.0 - 32), obj.rotation)
            _paint_angle_badge(painter, rotate_pos + QPointF(16, -14), obj.rotation)

    def paint_group_selection(self, painter: QPainter) -> None:
        rect = self._group_bounds().adjusted(-5, -5, 5, 5)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#2f7df6"), 1.35, Qt.DashLine))
        painter.drawRoundedRect(rect, 4, 4)
        handles = (rect.topLeft(), QPointF(rect.center().x(), rect.top()), rect.topRight(), QPointF(rect.right(), rect.center().y()), rect.bottomRight(), QPointF(rect.center().x(), rect.bottom()), rect.bottomLeft(), QPointF(rect.left(), rect.center().y()))
        painter.setPen(QPen(QColor("#ffffff"), 0.9))
        painter.setBrush(QColor("#2f7df6"))
        for handle in handles:
            painter.drawRoundedRect(QRectF(handle.x() - 3, handle.y() - 3, 6, 6), 1.8, 1.8)
        rotate_center = QPointF(rect.center().x(), rect.top() - 32)
        painter.setPen(QPen(QColor("#2f7df6"), 1.1, Qt.DashLine))
        painter.drawLine(QPointF(rect.center().x(), rect.top()), QPointF(rotate_center.x(), rotate_center.y() + 11))
        painter.setBrush(QColor("#fff9de"))
        painter.setPen(QPen(QColor("#7e5b10"), 1.25))
        painter.drawEllipse(rotate_center, 11, 11)
        edw._draw_arc_arrow(painter, rotate_center, 6.4, QColor("#ff8a35"))
        if self.selected_indices:
            angles = [self.objects[index].rotation for index in self.selected_indices]
            _paint_angle_badge(painter, rotate_center + QPointF(16, -14), sum(angles) / len(angles))

    edw.EngineeringCanvas._paint_selection_frame = paint_selection_frame
    edw.EngineeringCanvas._paint_group_selection = paint_group_selection
    edw.EngineeringCanvas._engineering_ui_refinement_patch = PATCH_VERSION


def apply_ui_refinement_fixes() -> None:
    _install_start_bar_refinements()
    _install_menu_refinements()
    _install_workspace_visual_refinements()

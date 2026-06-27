"""Engineering Design Tools workspace.

This file keeps the approved Engineer Design workspace shell intact and scopes
canvas interaction changes to the canvas layer only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from src.engineers_tools.app.module_window import GridCanvas, MenuItemSpec, ModuleWindow
from src.engineers_tools.app.modules import LauncherModule

ENGINEERING_WORKSPACE_UI_MARKER = "ENGINEERING_WORKSPACE_VIEW_STARTBAR_2026_06_27_D"


def _rotate_vector(vector: QPointF, degrees: float) -> QPointF:
    radians = math.radians(degrees)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)
    return QPointF(vector.x() * cos_a - vector.y() * sin_a, vector.x() * sin_a + vector.y() * cos_a)


def _paint_rotation_arc(painter: QPainter, center: QPointF, radius: float, color: QColor) -> None:
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(QPen(color, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    path = QPainterPath()
    arc_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
    path.arcMoveTo(arc_rect, 35)
    path.arcTo(arc_rect, 35, 285)
    painter.drawPath(path)
    tip_angle = math.radians(-250)
    tip = QPointF(center.x() + radius * math.cos(tip_angle), center.y() + radius * math.sin(tip_angle))
    tangent = QPointF(-math.sin(tip_angle), math.cos(tip_angle))
    normal = QPointF(math.cos(tip_angle), math.sin(tip_angle))
    painter.setBrush(color)
    painter.drawPolygon(QPolygonF([tip, tip - tangent * 4.8 - normal * 3.2, tip + tangent * 4.8 - normal * 3.2]))
    painter.restore()


@dataclass
class CanvasObject:
    path: Path
    pixmap: QPixmap
    rect: QRectF
    rotation: float = 0.0
    name: str = "Object"
    visible: bool = True
    locked: bool = False
    rotation_handle_visible: bool = True
    group_id: int | None = None

    def clone(self, offset: QPointF | None = None) -> "CanvasObject":
        copied = replace(self, rect=QRectF(self.rect))
        if offset is not None:
            copied.rect.translate(offset)
        return copied


class EngineeringCanvas(GridCanvas):
    def __init__(self) -> None:
        super().__init__()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.objects: list[CanvasObject] = []
        self.selected_indices: set[int] = set()
        self._clipboard: list[CanvasObject] = []
        self._last_action: str | None = None
        self._drag_action: str | None = None
        self._drag_start = QPointF()
        self._drag_start_rects: dict[int, QRectF] = {}
        self._drag_start_rotations: dict[int, float] = {}
        self._drag_group_center = QPointF()
        self._selection_origin: QPointF | None = None
        self._selection_rect: QRectF | None = None
        self._undo_stack: list[list[CanvasObject]] = []
        self._redo_stack: list[list[CanvasObject]] = []
        self._next_group_id = 1

    def load_file(self, path: Path) -> None:
        self._push_undo()
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            width = float(pixmap.width())
            height = float(pixmap.height())
        elif path.suffix.lower() == ".pdf":
            width, height = 595.0, 842.0
        else:
            width, height = 520.0, 360.0
        scale = min(max(180.0, self.width() * 0.62) / width, max(160.0, self.height() * 0.74) / height, 1.0)
        width *= scale
        height *= scale
        rect = QRectF((self.width() - width) / 2, (self.height() - height) / 2, width, height)
        self.objects.append(CanvasObject(path=path, pixmap=pixmap, rect=rect, name=path.stem or f"Object {len(self.objects) + 1}"))
        self._select_only(len(self.objects) - 1)
        self._last_action = "open"
        self._emit_object_changes()
        self.update()

    def copy_selection(self) -> bool:
        selected = self._selected_objects()
        if not selected:
            return False
        self._clipboard = [obj.clone() for _index, obj in selected]
        self._last_action = "copy"
        return True

    def cut_selection(self) -> bool:
        if not self.copy_selection():
            return False
        self._push_undo()
        self._delete_selected_objects()
        self._last_action = "cut"
        return True

    def paste_selection(self) -> bool:
        if not self._clipboard:
            return False
        self._push_undo()
        start = len(self.objects)
        for obj in self._clipboard:
            clone = obj.clone(QPointF(24, 24))
            clone.name = self._next_object_name(obj.name)
            clone.group_id = None
            self.objects.append(clone)
        self.selected_indices = set(range(start, len(self.objects)))
        self._last_action = "paste"
        self._emit_object_changes()
        self.update()
        return True

    def repeat_last_action(self) -> bool:
        if self._last_action in {"copy", "paste", "open"}:
            return self.paste_selection()
        if not self.selected_indices:
            return False
        self._push_undo()
        for index in self.selected_indices:
            self.objects[index].rect.translate(12, 12)
        self._last_action = "repeat"
        self.update()
        return True

    def select_all(self) -> bool:
        if not self.objects:
            return False
        self.selected_indices = {index for index, obj in enumerate(self.objects) if obj.visible}
        self._emit_selection_changes()
        self.update()
        return True

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append(self._snapshot())
        self._restore_snapshot(self._undo_stack.pop())
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append(self._snapshot())
        self._restore_snapshot(self._redo_stack.pop())
        return True

    def bring_to_front(self) -> bool:
        if not self.selected_indices:
            return False
        self._push_undo()
        selected = [self.objects[index] for index in sorted(self.selected_indices)]
        remaining = [obj for index, obj in enumerate(self.objects) if index not in self.selected_indices]
        self.objects = remaining + selected
        self.selected_indices = set(range(len(remaining), len(self.objects)))
        self._emit_object_changes()
        self.update()
        return True

    def send_to_back(self) -> bool:
        if not self.selected_indices:
            return False
        self._push_undo()
        selected = [self.objects[index] for index in sorted(self.selected_indices)]
        remaining = [obj for index, obj in enumerate(self.objects) if index not in self.selected_indices]
        self.objects = selected + remaining
        self.selected_indices = set(range(len(selected)))
        self._emit_object_changes()
        self.update()
        return True

    def group_selection(self) -> bool:
        if len(self.selected_indices) < 2:
            return False
        self._push_undo()
        group_id = self._next_group_id
        self._next_group_id += 1
        for index in self.selected_indices:
            self.objects[index].group_id = group_id
        self._emit_object_changes()
        self.update()
        return True

    def ungroup_selection(self) -> bool:
        group_ids = {self.objects[index].group_id for index in self.selected_indices if self.objects[index].group_id is not None}
        if not group_ids:
            return False
        self._push_undo()
        for obj in self.objects:
            if obj.group_id in group_ids:
                obj.group_id = None
        self._emit_object_changes()
        self.update()
        return True

    def toggle_rotation_handles(self) -> bool:
        if not self.selected_indices:
            return False
        self._push_undo()
        first = self.objects[min(self.selected_indices)].rotation_handle_visible
        for index in self.selected_indices:
            self.objects[index].rotation_handle_visible = not first
        self._emit_object_changes()
        self.update()
        return True

    def _emit_object_changes(self) -> None:
        if hasattr(self, "objects_changed"):
            self.objects_changed.emit()
        self._emit_selection_changes()

    def _emit_selection_changes(self) -> None:
        if hasattr(self, "selection_changed"):
            self.selection_changed.emit()

    def _selected_objects(self) -> list[tuple[int, CanvasObject]]:
        return [(index, self.objects[index]) for index in sorted(self.selected_indices) if 0 <= index < len(self.objects)]

    def _select_only(self, index: int) -> None:
        self.selected_indices = {index}
        self._emit_selection_changes()

    def _delete_selected_objects(self) -> None:
        self.objects = [obj for index, obj in enumerate(self.objects) if index not in self.selected_indices]
        self.selected_indices = set()
        self._emit_object_changes()
        self.update()

    def _snapshot(self) -> list[CanvasObject]:
        return [obj.clone() for obj in self.objects]

    def _restore_snapshot(self, snapshot: list[CanvasObject]) -> None:
        self.objects = [obj.clone() for obj in snapshot]
        self.selected_indices = set()
        self._emit_object_changes()
        self.update()

    def _push_undo(self) -> None:
        self._undo_stack.append(self._snapshot())
        if len(self._undo_stack) > 80:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _next_object_name(self, base: str) -> str:
        existing = {obj.name for obj in self.objects}
        clean = base or "Object"
        if clean not in existing:
            return clean
        counter = 1
        while f"{clean}-{counter}" in existing:
            counter += 1
        return f"{clean}-{counter}"

    def _to_canvas_point(self, point: QPointF) -> QPointF:
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        zoom = max(self._zoom, 0.01)
        return QPointF(((point.x() - center_x) / zoom) + center_x, ((point.y() - center_y) / zoom) + center_y)

    def _scene_to_object_local(self, obj: CanvasObject, point: QPointF) -> QPointF:
        return _rotate_vector(point - obj.rect.center(), -obj.rotation)

    def _object_local_to_scene(self, obj: CanvasObject, point: QPointF) -> QPointF:
        return obj.rect.center() + _rotate_vector(point, obj.rotation)

    def _hit_test_object(self, point: QPointF) -> tuple[int | None, str | None]:
        for index in range(len(self.objects) - 1, -1, -1):
            obj = self.objects[index]
            if obj.visible:
                action = self._hit_test_single_object(obj, point)
                if action is not None:
                    return index, action
        return None, None

    def _hit_test_single_object(self, obj: CanvasObject, point: QPointF) -> str | None:
        local = self._scene_to_object_local(obj, point)
        half_w = obj.rect.width() / 2
        half_h = obj.rect.height() / 2
        if obj.rotation_handle_visible and math.hypot(local.x(), local.y() + half_h + 34) <= 15:
            return "rotate"
        handles = {
            "resize_nw": QPointF(-half_w, -half_h), "resize_n": QPointF(0, -half_h), "resize_ne": QPointF(half_w, -half_h),
            "resize_e": QPointF(half_w, 0), "resize_se": QPointF(half_w, half_h), "resize_s": QPointF(0, half_h),
            "resize_sw": QPointF(-half_w, half_h), "resize_w": QPointF(-half_w, 0),
        }
        for action, handle in handles.items():
            if abs(local.x() - handle.x()) <= 9.0 and abs(local.y() - handle.y()) <= 9.0:
                return action
        if -half_w + 7 <= local.x() <= half_w - 7 and -half_h + 7 <= local.y() <= half_h - 7:
            return "move"
        return None

    def _group_bounds(self) -> QRectF:
        points: list[QPointF] = []
        for index in self.selected_indices:
            obj = self.objects[index]
            half_w = obj.rect.width() / 2
            half_h = obj.rect.height() / 2
            for point in (QPointF(-half_w, -half_h), QPointF(half_w, -half_h), QPointF(half_w, half_h), QPointF(-half_w, half_h)):
                points.append(self._object_local_to_scene(obj, point))
        if not points:
            return QRectF()
        return QRectF(QPointF(min(point.x() for point in points), min(point.y() for point in points)), QPointF(max(point.x() for point in points), max(point.y() for point in points)))

    def _apply_drag(self, point: QPointF) -> None:
        if self._drag_action is None:
            return
        if self._drag_action == "move":
            delta = point - self._drag_start
            for index in self.selected_indices:
                self.objects[index].rect = QRectF(self._drag_start_rects[index]).translated(delta)
            self.update()
            return
        if self._drag_action == "rotate":
            start_angle = math.degrees(math.atan2(self._drag_start.y() - self._drag_group_center.y(), self._drag_start.x() - self._drag_group_center.x()))
            current_angle = math.degrees(math.atan2(point.y() - self._drag_group_center.y(), point.x() - self._drag_group_center.x()))
            delta_angle = current_angle - start_angle
            for index in self.selected_indices:
                start_rect = self._drag_start_rects[index]
                new_center = self._drag_group_center + _rotate_vector(start_rect.center() - self._drag_group_center, delta_angle)
                self.objects[index].rect = QRectF(new_center.x() - start_rect.width() / 2, new_center.y() - start_rect.height() / 2, start_rect.width(), start_rect.height())
                self.objects[index].rotation = self._drag_start_rotations[index] + delta_angle
            self.update()
            return
        if len(self.selected_indices) != 1 or not self._drag_action.startswith("resize"):
            return
        index = next(iter(self.selected_indices))
        obj = self.objects[index]
        start_rect = self._drag_start_rects[index]
        start_rotation = self._drag_start_rotations[index]
        delta_local = _rotate_vector(point - self._drag_start, -start_rotation)
        width = start_rect.width()
        height = start_rect.height()
        center_shift = QPointF(0, 0)
        if "w" in self._drag_action:
            width = max(35.0, width - delta_local.x())
            center_shift.setX(delta_local.x() / 2)
        if "e" in self._drag_action:
            width = max(35.0, width + delta_local.x())
            center_shift.setX(delta_local.x() / 2)
        if "n" in self._drag_action:
            height = max(35.0, height - delta_local.y())
            center_shift.setY(delta_local.y() / 2)
        if "s" in self._drag_action:
            height = max(35.0, height + delta_local.y())
            center_shift.setY(delta_local.y() / 2)
        new_center = start_rect.center() + _rotate_vector(center_shift, start_rotation)
        obj.rect = QRectF(new_center.x() - width / 2, new_center.y() - height / 2, width, height)
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            point = self._to_canvas_point(event.position())
            index, action = self._hit_test_object(point)
            ctrl = bool(event.modifiers() & Qt.ControlModifier)
            if index is None:
                if not ctrl:
                    self.selected_indices = set()
                    self._emit_selection_changes()
                self._selection_origin = point
                self._selection_rect = QRectF(point, point)
                self._drag_action = None
                self.update()
                event.accept()
                return
            if ctrl:
                if index in self.selected_indices:
                    self.selected_indices.remove(index)
                else:
                    self.selected_indices.add(index)
                self._emit_selection_changes()
            elif index not in self.selected_indices:
                self._select_only(index)
            obj = self.objects[index]
            if action is not None and not obj.locked:
                self._push_undo()
                self._drag_action = action
                self._drag_start = point
                self._drag_start_rects = {selected: QRectF(self.objects[selected].rect) for selected in self.selected_indices}
                self._drag_start_rotations = {selected: self.objects[selected].rotation for selected in self.selected_indices}
                self._drag_group_center = self._group_bounds().center() if len(self.selected_indices) > 1 else obj.rect.center()
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        point = self._to_canvas_point(event.position())
        self.mouse_position_changed.emit(point.x(), point.y())
        if self._drag_action is not None:
            self._apply_drag(point)
            event.accept()
            return
        if self._selection_origin is not None and event.buttons() & Qt.LeftButton:
            self._selection_rect = QRectF(self._selection_origin, point).normalized()
            self.update()
            event.accept()
            return
        _index, hover = self._hit_test_object(point)
        if hover == "move":
            self.setCursor(Qt.SizeAllCursor)
        elif hover == "rotate":
            self.setCursor(Qt.OpenHandCursor)
        elif hover in {"resize_n", "resize_s"}:
            self.setCursor(Qt.SizeVerCursor)
        elif hover in {"resize_e", "resize_w"}:
            self.setCursor(Qt.SizeHorCursor)
        elif hover in {"resize_ne", "resize_sw"}:
            self.setCursor(Qt.SizeBDiagCursor)
        elif hover in {"resize_nw", "resize_se"}:
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.unsetCursor()
        event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self._selection_origin is not None:
            if self._selection_rect is not None and self._selection_rect.width() > 6 and self._selection_rect.height() > 6:
                self.selected_indices = {index for index, obj in enumerate(self.objects) if obj.visible and self._selection_rect.intersects(self._object_scene_bounds(obj))}
                self._emit_selection_changes()
            self._selection_origin = None
            self._selection_rect = None
            self.update()
        self._drag_action = None
        event.accept()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        ctrl = bool(event.modifiers() & Qt.ControlModifier)
        shift = bool(event.modifiers() & Qt.ShiftModifier)
        if ctrl and event.key() == Qt.Key_A:
            self.select_all()
        elif ctrl and event.key() == Qt.Key_C:
            self.copy_selection()
        elif ctrl and event.key() == Qt.Key_X:
            self.cut_selection()
        elif ctrl and event.key() == Qt.Key_V:
            self.paste_selection()
        elif ctrl and event.key() == Qt.Key_Z and not shift:
            self.undo()
        elif (ctrl and event.key() == Qt.Key_Y) or (ctrl and shift and event.key() == Qt.Key_Z):
            self.redo()
        else:
            super().keyPressEvent(event)
            return
        event.accept()

    def paintEvent(self, event) -> None:  # noqa: N802
        QWidget.paintEvent(self, event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#fbfdff"))
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._zoom, self._zoom)
        painter.translate(-self.width() / 2, -self.height() / 2)
        self._paint_grid(painter)
        for index, obj in enumerate(self.objects):
            if obj.visible:
                self._paint_object(painter, obj)
                if index in self.selected_indices and len(self.selected_indices) == 1:
                    self._paint_selection_frame(painter, obj)
        if len(self.selected_indices) > 1:
            self._paint_group_selection(painter)
        if self._selection_rect is not None:
            fill = QColor("#2f7df6")
            fill.setAlpha(28)
            painter.fillRect(self._selection_rect, fill)
            painter.setPen(QPen(QColor("#2f7df6"), 1.2, Qt.DashLine))
            painter.drawRect(self._selection_rect)

    def _object_scene_bounds(self, obj: CanvasObject) -> QRectF:
        half_w = obj.rect.width() / 2
        half_h = obj.rect.height() / 2
        points = [self._object_local_to_scene(obj, point) for point in (QPointF(-half_w, -half_h), QPointF(half_w, -half_h), QPointF(half_w, half_h), QPointF(-half_w, half_h))]
        return QRectF(QPointF(min(point.x() for point in points), min(point.y() for point in points)), QPointF(max(point.x() for point in points), max(point.y() for point in points)))

    def _paint_object(self, painter: QPainter, obj: CanvasObject) -> None:
        rect = obj.rect
        painter.save()
        painter.translate(rect.center())
        painter.rotate(obj.rotation)
        local = QRectF(-rect.width() / 2, -rect.height() / 2, rect.width(), rect.height())
        painter.setPen(QPen(QColor("#d6e2f0"), 1.2))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(local)
        if not obj.pixmap.isNull():
            painter.drawPixmap(local.toRect(), obj.pixmap)
        else:
            painter.setPen(QPen(QColor("#465d78"), 1.2))
            painter.drawText(local.adjusted(10, 10, -10, -10), Qt.AlignCenter, obj.path.name)
        painter.restore()

    def _paint_selection_frame(self, painter: QPainter, obj: CanvasObject) -> None:
        rect = obj.rect
        half_w = rect.width() / 2
        half_h = rect.height() / 2
        select = QColor("#2f7df6")
        painter.save()
        painter.translate(rect.center())
        painter.rotate(obj.rotation)
        local = QRectF(-half_w, -half_h, rect.width(), rect.height())
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(select, 1.5, Qt.DashLine))
        painter.drawRect(local.adjusted(-5, -5, 5, 5))
        handles = (QPointF(-half_w, -half_h), QPointF(0, -half_h), QPointF(half_w, -half_h), QPointF(half_w, 0), QPointF(half_w, half_h), QPointF(0, half_h), QPointF(-half_w, half_h), QPointF(-half_w, 0))
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        painter.setBrush(select)
        for handle in handles:
            painter.drawRoundedRect(QRectF(handle.x() - 4, handle.y() - 4, 8, 8), 2, 2)
        if obj.rotation_handle_visible:
            rotate_center = QPointF(0, -half_h - 34)
            painter.setPen(QPen(select, 1.2, Qt.DashLine))
            painter.drawLine(QPointF(0, -half_h - 5), QPointF(0, rotate_center.y() + 13))
            painter.setBrush(QColor("#fff9de"))
            painter.setPen(QPen(QColor("#7e5b10"), 1.4))
            painter.drawEllipse(rotate_center, 13, 13)
            _paint_rotation_arc(painter, rotate_center, 7.2, QColor("#ff8a35"))
        painter.restore()

    def _paint_group_selection(self, painter: QPainter) -> None:
        rect = self._group_bounds().adjusted(-6, -6, 6, 6)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#2f7df6"), 1.5, Qt.DashLine))
        painter.drawRoundedRect(rect, 4, 4)
        rotate_center = QPointF(rect.center().x(), rect.top() - 34)
        painter.setPen(QPen(QColor("#2f7df6"), 1.2, Qt.DashLine))
        painter.drawLine(QPointF(rect.center().x(), rect.top()), QPointF(rotate_center.x(), rotate_center.y() + 13))
        painter.setBrush(QColor("#fff9de"))
        painter.setPen(QPen(QColor("#7e5b10"), 1.4))
        painter.drawEllipse(rotate_center, 13, 13)
        _paint_rotation_arc(painter, rotate_center, 7.2, QColor("#ff8a35"))


class EngineeringDesignWorkspace(ModuleWindow):
    def __init__(self, module: LauncherModule) -> None:
        self._start_bar_tool_state: dict[str, bool] = {}
        self._layer_list_layout: QVBoxLayout | None = None
        super().__init__(module)
        self._layers = []
        self._refresh_layers()

    def _build_workspace(self) -> QWidget:
        area = QWidget()
        area.setObjectName("WorkspaceArea")
        layout = QHBoxLayout(area)
        layout.setContentsMargins(14, 14, 14, 10)
        layout.setSpacing(12)
        layers = self._build_layers_panel()
        layers.setFixedWidth(236)
        layout.addWidget(layers)
        canvas_shell = QWidget()
        canvas_shell.setObjectName("CanvasShell")
        canvas_layout = QVBoxLayout(canvas_shell)
        canvas_layout.setContentsMargins(12, 12, 12, 12)
        self._canvas = EngineeringCanvas()
        self._canvas.setObjectName("GridCanvas")
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._canvas.mouse_position_changed.connect(self._update_canvas_coordinates)
        self._canvas.context_actions_requested.connect(self._show_canvas_context_menu)
        canvas_layout.addWidget(self._canvas, 1)
        layout.addWidget(canvas_shell, 1)
        properties = self._build_side_panel("Properties", ("Selection", "Coordinates", "Size", "Style", "Behavior"))
        properties.setFixedWidth(220)
        layout.addWidget(properties)
        return area

    def _build_layers_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("SidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        title = QLabel("Layers")
        title.setObjectName("PanelTitle")
        layout.addWidget(title)
        self._layer_list_layout = QVBoxLayout()
        self._layer_list_layout.setSpacing(5)
        layout.addLayout(self._layer_list_layout)
        layout.addStretch(1)
        return panel

    def _refresh_layers(self) -> None:
        if self._layer_list_layout is None:
            return
        while self._layer_list_layout.count():
            item = self._layer_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        canvas = self._canvas if isinstance(getattr(self, "_canvas", None), EngineeringCanvas) else None
        if canvas is None or not canvas.objects:
            empty = QLabel("No layers")
            empty.setObjectName("PanelItem")
            empty.setFixedHeight(28)
            self._layer_list_layout.addWidget(empty)
            return
        for index, obj in enumerate(canvas.objects):
            row = QLabel(("[G] " if obj.group_id is not None else "") + obj.name)
            row.setObjectName("PanelItem")
            row.setFixedHeight(28)
            if index in canvas.selected_indices:
                row.setStyleSheet("border:1px solid #2f7df6; border-radius:6px; padding-left:6px; background:#eef6ff;")
            self._layer_list_layout.addWidget(row)

    def _build_start_bar(self) -> QWidget:
        bar = super()._build_start_bar()
        self._start_bar_tool_state = {tool.key: True for tool in self.get_start_bar_tools()}
        return bar

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(34)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)
        self._status_items = []
        for text in ("Tool Select: Ready", "X: 0  Y: 0", "Unit: mm"):
            item = QLabel(text)
            item.setObjectName("StatusItem")
            layout.addWidget(item)
            self._status_items.append(item)
        layout.addStretch(1)
        zoom_label = QLabel("Zoom:")
        zoom_label.setObjectName("StatusItem")
        layout.addWidget(zoom_label)
        layout.addWidget(self._build_zoom_control())
        return bar

    def _copy(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.copy_selection():
            self._set_status("Copy")
            return
        super()._copy()

    def _cut(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.cut_selection():
            self._set_status("Cut")
            return
        super()._cut()

    def _paste(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.paste_selection():
            self._set_status("Paste")
            return
        super()._paste()

    def _repeat_last_tools(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.repeat_last_action():
            self._set_status("Repeat")
            return
        super()._repeat_last_tools()

    def _select_all(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.select_all():
            self._set_status("Select All")
            return
        super()._select_all()

    def _undo(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.undo():
            self._set_status("Undo")
            return
        self._set_status("Nothing to undo")

    def _redo(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.redo():
            self._set_status("Redo")
            return
        self._set_status("Nothing to redo")

    def _bring_to_front(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.bring_to_front():
            self._set_status("Bring to Front")
            return
        self._set_status("No selected object")

    def _send_to_back(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.send_to_back():
            self._set_status("Send to Back")
            return
        self._set_status("No selected object")

    def _group_selection(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.group_selection():
            self._set_status("Group")
            return
        self._set_status("Select at least two objects to group")

    def _ungroup_selection(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.ungroup_selection():
            self._set_status("Ungroup")
            return
        self._set_status("No selected group")

    def _rotate_selection(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.toggle_rotation_handles():
            self._set_status("Rotate handle toggled")
            return
        self._set_status("No selected object")

    def _build_zoom_control(self) -> QWidget:
        control = QWidget()
        control.setObjectName("ZoomControl")
        control.setFixedSize(126, 28)
        control_layout = QHBoxLayout(control)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(2)
        self._zoom_input = QDoubleSpinBox()
        self._zoom_input.setObjectName("ZoomInput")
        self._zoom_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._zoom_input.setRange(5.0, 3200.0)
        self._zoom_input.setDecimals(2)
        self._zoom_input.setSingleStep(5.0)
        self._zoom_input.setValue(100.0)
        self._zoom_input.setSuffix(" %")
        self._zoom_input.setFixedSize(92, 26)
        self._zoom_input.setStyleSheet(
            "QDoubleSpinBox#ZoomInput {background:#fff9de; border:1px solid #b38621; border-radius:8px;"
            "color:#132238; font-size:11px; font-style:normal; font-weight:700; padding:2px 6px; selection-background-color:#43d3bd; }"
        )
        self._zoom_input.valueChanged.connect(self._set_zoom)
        control_layout.addWidget(self._zoom_input)
        arrows = QWidget()
        arrows.setObjectName("ZoomArrowStack")
        arrows_layout = QVBoxLayout(arrows)
        arrows_layout.setContentsMargins(0, 0, 0, 0)
        arrows_layout.setSpacing(2)
        up_button = self._build_zoom_arrow_button("up")
        down_button = self._build_zoom_arrow_button("down")
        up_button.clicked.connect(lambda: self._zoom_input.stepUp())
        down_button.clicked.connect(lambda: self._zoom_input.stepDown())
        arrows_layout.addWidget(up_button)
        arrows_layout.addWidget(down_button)
        control_layout.addWidget(arrows)
        return control

    def _build_zoom_arrow_button(self, direction: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName("ZoomArrowButton")
        button.setFixedSize(28, 12)
        button.setIcon(self._build_zoom_arrow_icon(direction))
        button.setIconSize(QSize(22, 10))
        button.setToolTip("Zoom in" if direction == "up" else "Zoom out")
        button.setStyleSheet(
            "QPushButton#ZoomArrowButton {background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fff9de, stop:1 #ffc35a);"
            "border:1px solid #7e5b10; border-radius:4px; padding:0px; }"
            "QPushButton#ZoomArrowButton:hover { background:#ff8a35; border-color:#ffffff; }"
            "QPushButton#ZoomArrowButton:pressed { background:#d46a16; padding-top:1px; }"
        )
        return button

    def _build_zoom_arrow_icon(self, direction: str) -> QIcon:
        pixmap = QPixmap(22, 10)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#ffffff"), 0.9))
        painter.setBrush(QColor("#132238"))
        if direction == "up":
            points = QPolygonF([QPointF(11, 1), QPointF(20, 9), QPointF(2, 9)])
        else:
            points = QPolygonF([QPointF(2, 1), QPointF(20, 1), QPointF(11, 9)])
        painter.drawPolygon(points)
        painter.end()
        return QIcon(pixmap)

    def _show_view_menu(self, anchor: QWidget) -> None:
        items: list[MenuItemSpec] = [MenuItemSpec("Start Bar", self._toggle_start_bar, checkable=True, checked=self._view_state["start_bar"])]
        for tool in self.get_start_bar_tools():
            items.append(MenuItemSpec(tool.label, lambda key=tool.key: self._toggle_start_bar_tool(key), checkable=True, checked=self._start_bar_tool_state.get(tool.key, True)))
        self._show_menu("View", tuple(items), anchor)

    def _toggle_start_bar_tool(self, key: str) -> None:
        visible = not self._start_bar_tool_state.get(key, True)
        self._start_bar_tool_state[key] = visible
        if self._start_bar_widget is not None and hasattr(self._start_bar_widget, "set_tool_visible"):
            self._start_bar_widget.set_tool_visible(key, visible)
        label = next((tool.label for tool in self.get_start_bar_tools() if tool.key == key), key)
        self._set_status(f"{label} {'shown on' if visible else 'removed from'} Start Bar")

"""Engineering Design Tools workspace.

Shared engineering workspace for the Engineer Design Tools module. This file is
kept as the canonical module-specific implementation that connects the common
ModuleWindow shell to engineering canvas behavior, object selection, layers,
shortcuts, zoom, save/export, and repeat actions.
"""

from __future__ import annotations

import base64
import math
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Signal, Qt
from PySide6.QtGui import QColor, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QShortcut
from PySide6.QtWidgets import QAbstractSpinBox, QCheckBox, QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from src.engineers_tools.app.module_window import GridCanvas, MenuItemSpec, ModuleWindow, _layer_icon
from src.engineers_tools.app.modules import LauncherModule
from src.engineers_tools.app.project_file_dialog import ProjectFileDialog

ENGINEERING_WORKSPACE_UI_MARKER = "ENGINEERING_WORKSPACE_VIEW_STARTBAR_2026_06_27_G"


def _rotate_vector(vector: QPointF, degrees: float) -> QPointF:
    radians = math.radians(degrees)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)
    return QPointF(vector.x() * cos_a - vector.y() * sin_a, vector.x() * sin_a + vector.y() * cos_a)


def _draw_arc_arrow(painter: QPainter, center: QPointF, radius: float, color: QColor, reverse: bool = False) -> None:
    """Draw a clean half-arc rotation glyph with a real stroked arrow head."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(color, 2.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
    if reverse:
        painter.drawArc(rect, 140 * 16, -265 * 16)
        end_angle = math.radians(-125)
        direction = -1.0
    else:
        painter.drawArc(rect, 35 * 16, 265 * 16)
        end_angle = math.radians(-95)
        direction = 1.0
    tip = QPointF(center.x() + radius * math.cos(end_angle), center.y() + radius * math.sin(end_angle))
    tangent = QPointF(-math.sin(end_angle) * direction, math.cos(end_angle) * direction)
    normal = QPointF(math.cos(end_angle), math.sin(end_angle))
    p1 = QPointF(tip.x() - tangent.x() * 7.0 + normal.x() * 3.0, tip.y() - tangent.y() * 7.0 + normal.y() * 3.0)
    p2 = QPointF(tip.x() - tangent.x() * 7.0 - normal.x() * 3.0, tip.y() - tangent.y() * 7.0 - normal.y() * 3.0)
    painter.drawLine(tip, p1)
    painter.drawLine(tip, p2)
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
    objects_changed = Signal()
    selection_changed = Signal()

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
        self._drag_start_group_bounds = QRectF()
        self._selection_origin: QPointF | None = None
        self._selection_rect: QRectF | None = None
        self._undo_stack: list[list[CanvasObject]] = []
        self._redo_stack: list[list[CanvasObject]] = []
        self._next_group_id = 1
        self._active_group_edit: int | None = None

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
        obj = CanvasObject(path=path, pixmap=pixmap, rect=rect, name=path.stem or f"Object {len(self.objects) + 1}")
        self.objects.append(obj)
        self._select_only(len(self.objects) - 1)
        self._clipboard = [obj.clone()]
        self._last_action = "open"
        self._active_group_edit = None
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
        self._paste_objects(self._clipboard, QPointF(24, 24), "paste")
        return True

    def repeat_last_action(self) -> bool:
        source = self._clipboard or [obj.clone() for _index, obj in self._selected_objects()]
        if not source:
            return False
        self._push_undo()
        self._paste_objects(source, QPointF(28, 28), "repeat")
        return True

    def _paste_objects(self, source: list[CanvasObject], offset: QPointF, action: str) -> None:
        start = len(self.objects)
        for obj in source:
            clone = obj.clone(offset)
            clone.name = self._next_object_name(obj.name)
            clone.group_id = None
            self.objects.append(clone)
        self.selected_indices = set(range(start, len(self.objects)))
        self._active_group_edit = None
        self._last_action = action
        self._emit_object_changes()
        self.update()

    def select_all(self) -> bool:
        selected = {index for index, obj in enumerate(self.objects) if obj.visible}
        if not selected:
            return False
        self.selected_indices = selected
        self._active_group_edit = None
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
        self.selected_indices = {index for index, obj in enumerate(self.objects) if obj.group_id == group_id and obj.visible}
        self._active_group_edit = None
        self._last_action = "group"
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
        self._active_group_edit = None
        self._last_action = "ungroup"
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

    def toggle_object_visible(self, index: int) -> None:
        if 0 <= index < len(self.objects):
            self._push_undo()
            self.objects[index].visible = not self.objects[index].visible
            if not self.objects[index].visible:
                self.selected_indices.discard(index)
            self._emit_object_changes()
            self.update()

    def toggle_object_locked(self, index: int) -> None:
        if 0 <= index < len(self.objects):
            self._push_undo()
            self.objects[index].locked = not self.objects[index].locked
            self._emit_object_changes()
            self.update()

    def toggle_object_rotation_handle(self, index: int) -> None:
        if 0 <= index < len(self.objects):
            self._push_undo()
            self.objects[index].rotation_handle_visible = not self.objects[index].rotation_handle_visible
            self._emit_object_changes()
            self.update()

    def toggle_group_visible(self, group_id: int) -> None:
        self._push_undo()
        members = [obj for obj in self.objects if obj.group_id == group_id]
        next_state = not any(obj.visible for obj in members)
        for obj in members:
            obj.visible = next_state
        if not next_state:
            self.selected_indices = {index for index in self.selected_indices if self.objects[index].group_id != group_id}
        self._emit_object_changes()
        self.update()

    def toggle_group_locked(self, group_id: int) -> None:
        self._push_undo()
        members = [obj for obj in self.objects if obj.group_id == group_id]
        next_state = not all(obj.locked for obj in members)
        for obj in members:
            obj.locked = next_state
        self._emit_object_changes()
        self.update()

    def toggle_group_rotation_handle(self, group_id: int) -> None:
        self._push_undo()
        members = [obj for obj in self.objects if obj.group_id == group_id]
        next_state = not any(obj.rotation_handle_visible for obj in members)
        for obj in members:
            obj.rotation_handle_visible = next_state
        self._emit_object_changes()
        self.update()

    def rename_object(self, index: int, name: str) -> None:
        if 0 <= index < len(self.objects):
            self.objects[index].name = name.strip() or self.objects[index].name
            self._emit_object_changes()

    def select_group(self, group_id: int) -> None:
        self.selected_indices = {index for index, obj in enumerate(self.objects) if obj.group_id == group_id and obj.visible}
        self._active_group_edit = None
        self._emit_selection_changes()
        self.update()

    def _emit_object_changes(self) -> None:
        self.objects_changed.emit()
        self._emit_selection_changes()

    def _emit_selection_changes(self) -> None:
        self.selection_changed.emit()

    def _selected_objects(self) -> list[tuple[int, CanvasObject]]:
        return [(index, self.objects[index]) for index in sorted(self.selected_indices) if 0 <= index < len(self.objects)]

    def _select_only(self, index: int) -> None:
        if not 0 <= index < len(self.objects):
            return
        group_id = self.objects[index].group_id
        if group_id is not None and self._active_group_edit != group_id:
            self.selected_indices = {i for i, obj in enumerate(self.objects) if obj.group_id == group_id and obj.visible}
        else:
            self.selected_indices = {index}
        self._emit_selection_changes()

    def _selection_group_id(self) -> int | None:
        if not self.selected_indices:
            return None
        group_ids = {self.objects[index].group_id for index in self.selected_indices}
        if len(group_ids) != 1:
            return None
        group_id = next(iter(group_ids))
        if group_id is None:
            return None
        group_members = {index for index, obj in enumerate(self.objects) if obj.group_id == group_id and obj.visible}
        return group_id if group_members == self.selected_indices else None

    def _delete_selected_objects(self) -> None:
        self.objects = [obj for index, obj in enumerate(self.objects) if index not in self.selected_indices]
        self.selected_indices = set()
        self._active_group_edit = None
        self._emit_object_changes()
        self.update()

    def _snapshot(self) -> list[CanvasObject]:
        return [obj.clone() for obj in self.objects]

    def _restore_snapshot(self, snapshot: list[CanvasObject]) -> None:
        self.objects = [obj.clone() for obj in snapshot]
        self.selected_indices = set()
        self._active_group_edit = None
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

    def _object_scene_bounds(self, obj: CanvasObject) -> QRectF:
        half_w = obj.rect.width() / 2
        half_h = obj.rect.height() / 2
        points = [self._object_local_to_scene(obj, point) for point in (QPointF(-half_w, -half_h), QPointF(half_w, -half_h), QPointF(half_w, half_h), QPointF(-half_w, half_h))]
        return QRectF(QPointF(min(point.x() for point in points), min(point.y() for point in points)), QPointF(max(point.x() for point in points), max(point.y() for point in points)))

    def _hit_test_group_selection(self, point: QPointF) -> str | None:
        if self._selection_group_id() is None:
            return None
        rect = self._group_bounds().adjusted(-6, -6, 6, 6)
        rotate_center = QPointF(rect.center().x(), rect.top() - 34)
        if math.hypot(point.x() - rotate_center.x(), point.y() - rotate_center.y()) <= 15:
            return "rotate"
        handles = {
            "resize_nw": rect.topLeft(), "resize_n": QPointF(rect.center().x(), rect.top()), "resize_ne": rect.topRight(),
            "resize_e": QPointF(rect.right(), rect.center().y()), "resize_se": rect.bottomRight(), "resize_s": QPointF(rect.center().x(), rect.bottom()),
            "resize_sw": rect.bottomLeft(), "resize_w": QPointF(rect.left(), rect.center().y()),
        }
        for action, handle in handles.items():
            if abs(point.x() - handle.x()) <= 10.0 and abs(point.y() - handle.y()) <= 10.0:
                return action
        if rect.contains(point):
            return "move"
        return None

    def _hit_test_object(self, point: QPointF) -> tuple[int | None, str | None]:
        group_action = self._hit_test_group_selection(point)
        if group_action is not None and self.selected_indices:
            return next(iter(self.selected_indices)), group_action
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
        if self._drag_action.startswith("resize_"):
            if len(self.selected_indices) == 1:
                self._apply_single_resize(point, self._drag_action.removeprefix("resize_"))
            else:
                self._apply_group_resize(point, self._drag_action.removeprefix("resize_"))
            self.update()

    def _apply_single_resize(self, point: QPointF, handle: str) -> None:
        index = next(iter(self.selected_indices))
        obj = self.objects[index]
        start_rect = self._drag_start_rects[index]
        start_rotation = self._drag_start_rotations[index]
        delta_local = _rotate_vector(point - self._drag_start, -start_rotation)
        width = start_rect.width()
        height = start_rect.height()
        center_shift = QPointF(0, 0)
        if "w" in handle:
            width = max(35.0, width - delta_local.x())
            center_shift.setX(delta_local.x() / 2)
        if "e" in handle:
            width = max(35.0, width + delta_local.x())
            center_shift.setX(delta_local.x() / 2)
        if "n" in handle:
            height = max(35.0, height - delta_local.y())
            center_shift.setY(delta_local.y() / 2)
        if "s" in handle:
            height = max(35.0, height + delta_local.y())
            center_shift.setY(delta_local.y() / 2)
        new_center = start_rect.center() + _rotate_vector(center_shift, start_rotation)
        obj.rect = QRectF(new_center.x() - width / 2, new_center.y() - height / 2, width, height)

    def _apply_group_resize(self, point: QPointF, handle: str) -> None:
        start = QRectF(self._drag_start_group_bounds)
        if start.width() <= 1 or start.height() <= 1:
            return
        dx = point.x() - self._drag_start.x()
        dy = point.y() - self._drag_start.y()
        left, right, top, bottom = start.left(), start.right(), start.top(), start.bottom()
        if "w" in handle:
            left += dx
        if "e" in handle:
            right += dx
        if "n" in handle:
            top += dy
        if "s" in handle:
            bottom += dy
        if right - left < 40:
            right = left + 40
        if bottom - top < 40:
            bottom = top + 40
        new_bounds = QRectF(QPointF(left, top), QPointF(right, bottom)).normalized()
        sx = new_bounds.width() / start.width()
        sy = new_bounds.height() / start.height()
        for index in self.selected_indices:
            sr = self._drag_start_rects[index]
            rel = sr.center() - start.center()
            new_center = QPointF(new_bounds.center().x() + rel.x() * sx, new_bounds.center().y() + rel.y() * sy)
            width = max(35.0, sr.width() * sx)
            height = max(35.0, sr.height() * sy)
            self.objects[index].rect = QRectF(new_center.x() - width / 2, new_center.y() - height / 2, width, height)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            point = self._to_canvas_point(event.position())
            index, action = self._hit_test_object(point)
            ctrl = bool(event.modifiers() & Qt.ControlModifier)
            if index is None:
                if not ctrl:
                    self.selected_indices = set()
                    self._active_group_edit = None
                    self._emit_selection_changes()
                self._selection_origin = point
                self._selection_rect = QRectF(point, point)
                self._drag_action = None
                self.update()
                event.accept()
                return
            hit_group = self.objects[index].group_id
            if ctrl:
                if hit_group is not None and self._active_group_edit != hit_group:
                    members = {i for i, obj in enumerate(self.objects) if obj.group_id == hit_group and obj.visible}
                    self.selected_indices.symmetric_difference_update(members)
                elif index in self.selected_indices:
                    self.selected_indices.remove(index)
                else:
                    self.selected_indices.add(index)
                self._emit_selection_changes()
                self.update()
                event.accept()
                return
            if index not in self.selected_indices:
                self._select_only(index)
            if action is not None and not any(self.objects[selected].locked for selected in self.selected_indices):
                self._push_undo()
                self._drag_action = action
                self._drag_start = point
                self._drag_start_rects = {selected: QRectF(self.objects[selected].rect) for selected in self.selected_indices}
                self._drag_start_rotations = {selected: self.objects[selected].rotation for selected in self.selected_indices}
                self._drag_start_group_bounds = self._group_bounds()
                self._drag_group_center = self._drag_start_group_bounds.center() if len(self.selected_indices) > 1 else self.objects[index].rect.center()
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            point = self._to_canvas_point(event.position())
            index, _action = self._hit_test_object(point)
            if index is not None:
                group_id = self.objects[index].group_id
                if group_id is not None:
                    self._active_group_edit = group_id
                    self.selected_indices = {index}
                    self._emit_selection_changes()
                    self.update()
                    event.accept()
                    return
        super().mouseDoubleClickEvent(event)

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
                selected = {index for index, obj in enumerate(self.objects) if obj.visible and self._selection_rect.intersects(self._object_scene_bounds(obj))}
                expanded: set[int] = set()
                for index in selected:
                    group_id = self.objects[index].group_id
                    if group_id is not None and self._active_group_edit != group_id:
                        expanded.update(i for i, obj in enumerate(self.objects) if obj.group_id == group_id and obj.visible)
                    else:
                        expanded.add(index)
                self.selected_indices = expanded
                self._emit_selection_changes()
            self._selection_origin = None
            self._selection_rect = None
            self.update()
        self._drag_action = None
        self.unsetCursor()
        event.accept()

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        self.context_actions_requested.emit(event.globalPos())
        event.accept()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        ctrl = bool(event.modifiers() & Qt.ControlModifier)
        shift = bool(event.modifiers() & Qt.ShiftModifier)
        handled = True
        if ctrl and event.key() == Qt.Key_A:
            self.select_all()
        elif ctrl and event.key() == Qt.Key_C:
            self.copy_selection()
        elif ctrl and event.key() == Qt.Key_X:
            self.cut_selection()
        elif ctrl and event.key() == Qt.Key_V:
            self.paste_selection()
        elif ctrl and event.key() == Qt.Key_G and not shift:
            self.group_selection()
        elif ctrl and shift and event.key() == Qt.Key_G:
            self.ungroup_selection()
        elif ctrl and event.key() == Qt.Key_R:
            self.repeat_last_action()
        elif ctrl and event.key() == Qt.Key_Z and not shift:
            self.undo()
        elif (ctrl and event.key() == Qt.Key_Y) or (ctrl and shift and event.key() == Qt.Key_Z):
            self.redo()
        else:
            handled = False
        if handled:
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        QWidget.paintEvent(self, event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#fbfdff"))
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._zoom, self._zoom)
        painter.translate(-self.width() / 2, -self.height() / 2)
        self._paint_grid(painter)
        group_id = self._selection_group_id()
        for index, obj in enumerate(self.objects):
            if obj.visible:
                self._paint_object(painter, obj)
                if index in self.selected_indices and group_id is None:
                    self._paint_selection_frame(painter, obj)
        if group_id is not None:
            self._paint_group_selection(painter)
        if self._selection_rect is not None:
            fill = QColor("#2f7df6")
            fill.setAlpha(28)
            painter.fillRect(self._selection_rect, fill)
            painter.setPen(QPen(QColor("#2f7df6"), 1.2, Qt.DashLine))
            painter.drawRect(self._selection_rect)

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
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(select, 1.5, Qt.DashLine))
        painter.drawRect(QRectF(-half_w - 5, -half_h - 5, rect.width() + 10, rect.height() + 10))
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
            _draw_arc_arrow(painter, rotate_center, 7.2, QColor("#ff8a35"))
        painter.restore()

    def _paint_group_selection(self, painter: QPainter) -> None:
        rect = self._group_bounds().adjusted(-6, -6, 6, 6)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#2f7df6"), 1.5, Qt.DashLine))
        painter.drawRoundedRect(rect, 4, 4)
        handles = (rect.topLeft(), QPointF(rect.center().x(), rect.top()), rect.topRight(), QPointF(rect.right(), rect.center().y()), rect.bottomRight(), QPointF(rect.center().x(), rect.bottom()), rect.bottomLeft(), QPointF(rect.left(), rect.center().y()))
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        painter.setBrush(QColor("#2f7df6"))
        for handle in handles:
            painter.drawRoundedRect(QRectF(handle.x() - 4, handle.y() - 4, 8, 8), 2, 2)
        rotate_center = QPointF(rect.center().x(), rect.top() - 34)
        painter.setPen(QPen(QColor("#2f7df6"), 1.2, Qt.DashLine))
        painter.drawLine(QPointF(rect.center().x(), rect.top()), QPointF(rotate_center.x(), rotate_center.y() + 13))
        painter.setBrush(QColor("#fff9de"))
        painter.setPen(QPen(QColor("#7e5b10"), 1.4))
        painter.drawEllipse(rotate_center, 13, 13)
        _draw_arc_arrow(painter, rotate_center, 7.2, QColor("#ff8a35"))


class EngineeringDesignWorkspace(ModuleWindow):
    def __init__(self, module: LauncherModule) -> None:
        self._start_bar_tool_state: dict[str, bool] = {}
        self._layer_list_layout: QVBoxLayout | None = None
        self._save_options = {"save_grid": False, "remove_white_background": False}
        self._collapsed_groups: set[int] = set()
        self._engineering_shortcuts_installed = False
        self._engineering_shortcuts: list[QShortcut] = []
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
        self._canvas.objects_changed.connect(self._refresh_layers)
        self._canvas.selection_changed.connect(self._refresh_layers)
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
        grouped: dict[int, list[int]] = {}
        loose: list[int] = []
        for index, obj in enumerate(canvas.objects):
            if obj.group_id is None:
                loose.append(index)
            else:
                grouped.setdefault(obj.group_id, []).append(index)
        for group_id in sorted(grouped):
            indices = grouped[group_id]
            self._layer_list_layout.addWidget(self._build_group_layer_row(canvas, group_id, indices))
            if group_id not in self._collapsed_groups:
                for index in indices:
                    self._layer_list_layout.addWidget(self._build_object_layer_row(canvas, index, child=True))
        for index in loose:
            self._layer_list_layout.addWidget(self._build_object_layer_row(canvas, index, child=False))

    def _build_group_layer_row(self, canvas: EngineeringCanvas, group_id: int, indices: list[int]) -> QWidget:
        row = QWidget()
        row.setObjectName("LayerRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(3, 2, 3, 2)
        row_layout.setSpacing(3)
        expander = QPushButton("v" if group_id not in self._collapsed_groups else ">")
        expander.setObjectName("LayerExpandButton")
        expander.setToolTip("Collapse group" if group_id not in self._collapsed_groups else "Expand group")
        expander.setFixedSize(18, 24)
        expander.clicked.connect(lambda checked=False, gid=group_id: self._toggle_group_collapse(gid))
        members = [canvas.objects[index] for index in indices]
        visible = any(obj.visible for obj in members)
        locked = all(obj.locked for obj in members)
        rotate = any(obj.rotation_handle_visible for obj in members)
        row_layout.addWidget(expander)
        row_layout.addWidget(self._layer_button("eye", visible, "Show", lambda checked=False, gid=group_id: canvas.toggle_group_visible(gid)))
        row_layout.addWidget(self._layer_button("lock", locked, "Lock", lambda checked=False, gid=group_id: canvas.toggle_group_locked(gid)))
        row_layout.addWidget(self._layer_button("rotation", rotate, "Rotate Handle", lambda checked=False, gid=group_id: canvas.toggle_group_rotation_handle(gid)))
        name = QPushButton(f"Group {group_id}")
        name.setObjectName("MenuButton")
        name.clicked.connect(lambda checked=False, gid=group_id: canvas.select_group(gid))
        row_layout.addWidget(name, 1)
        return row

    def _build_object_layer_row(self, canvas: EngineeringCanvas, index: int, child: bool) -> QWidget:
        obj = canvas.objects[index]
        row = QWidget()
        row.setObjectName("LayerRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(24 if child else 3, 2, 3, 2)
        row_layout.setSpacing(3)
        row_layout.addWidget(self._layer_button("eye", obj.visible, "Show", lambda checked=False, i=index: canvas.toggle_object_visible(i)))
        row_layout.addWidget(self._layer_button("lock", obj.locked, "Lock", lambda checked=False, i=index: canvas.toggle_object_locked(i)))
        row_layout.addWidget(self._layer_button("rotation", obj.rotation_handle_visible, "Rotate Handle", lambda checked=False, i=index: canvas.toggle_object_rotation_handle(i)))
        name = QLineEdit(obj.name)
        name.setObjectName("LayerNameInput")
        name.setMinimumHeight(24)
        name.editingFinished.connect(lambda i=index, source=name: canvas.rename_object(i, source.text()))
        if index in canvas.selected_indices:
            name.setStyleSheet("border:1px solid #2f7df6; border-radius:6px; background:#eef6ff;")
        row_layout.addWidget(name, 1)
        return row

    def _toggle_group_collapse(self, group_id: int) -> None:
        if group_id in self._collapsed_groups:
            self._collapsed_groups.remove(group_id)
        else:
            self._collapsed_groups.add(group_id)
        self._refresh_layers()

    def _layer_button(self, kind: str, active: bool, tooltip: str, callback) -> QPushButton:
        button = QPushButton()
        button.setObjectName("LayerIconButton")
        button.setToolTip(tooltip)
        button.setFixedSize(26, 24)
        button.setIcon(_layer_icon(kind, active))
        button.setIconSize(QSize(23, 23))
        button.clicked.connect(callback)
        return button

    def _build_start_bar(self) -> QWidget:
        bar = super()._build_start_bar()
        layout = bar.layout()
        if layout is not None:
            select_index = 0
            for index in range(layout.count()):
                widget = layout.itemAt(index).widget()
                if widget is not None and widget.property("toolKey") == "select":
                    select_index = index
                    break
            layout.insertWidget(select_index, self._start_bar_action_button("Undo", self._build_history_icon("undo"), self._undo))
            layout.insertWidget(select_index + 1, self._start_bar_action_button("Redo", self._build_history_icon("redo"), self._redo))
        self._start_bar_tool_state = {tool.key: True for tool in self.get_start_bar_tools()}
        return bar

    def _start_bar_action_button(self, tooltip: str, icon: QIcon, callback) -> QPushButton:
        button = QPushButton()
        button.setObjectName("ToolIconButton")
        button.setToolTip(tooltip)
        button.setIcon(icon)
        button.setIconSize(QSize(26, 26))
        button.setFixedSize(42, 32)
        button.setStyleSheet(
            "QPushButton#ToolIconButton {border-radius:11px; border:1px solid #8ca8c5;"
            "background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ffffff, stop:0.42 #eaf6ff, stop:1 #b6cde7); padding:1px;}"
            "QPushButton#ToolIconButton:hover {border-color:#2f7df6; background:#eef6ff;}"
            "QPushButton#ToolIconButton:pressed {padding-top:2px; background:#c7d8ec;}"
        )
        button.clicked.connect(callback)
        return button

    def _build_history_icon(self, direction: str) -> QIcon:
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        badge = QPainterPath()
        badge.addRoundedRect(QRectF(5, 6, 38, 36), 12, 12)
        gradient = QLinearGradient(5, 6, 43, 42)
        gradient.setColorAt(0.0, QColor("#ffffff"))
        gradient.setColorAt(0.52, QColor("#dff2ff"))
        gradient.setColorAt(1.0, QColor("#57b8d9" if direction == "undo" else "#43d3bd"))
        painter.fillPath(badge, gradient)
        painter.setPen(QPen(QColor("#5d7898"), 1.2))
        painter.drawPath(badge)
        stroke = QColor("#12345a") if direction == "undo" else QColor("#0f766e")
        _draw_arc_arrow(painter, QPointF(24, 24), 10.5, stroke, reverse=(direction == "redo"))
        painter.end()
        return QIcon(pixmap)

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(34)
        bar.setStyleSheet("QWidget#StatusBar { background:#102238; } QLabel#StatusItem { color:#ffffff; font-size:11px; font-weight:600; }")
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

    def _install_shortcuts(self) -> None:
        self._install_engineering_shortcuts()

    def _install_engineering_shortcuts(self) -> None:
        if getattr(self, "_engineering_shortcuts_installed", False):
            return
        self._engineering_shortcuts_installed = True
        self._engineering_shortcuts = []
        for sequence, callback in (
            ("Ctrl+N", self._new_file), ("Ctrl+O", self._open_file), ("Ctrl+S", self._save_file), ("Ctrl+Shift+S", self._save_as_file),
            ("Ctrl+Z", self._undo), ("Ctrl+Y", self._redo), ("Ctrl+Shift+Z", self._redo),
            ("Ctrl+C", self._copy), ("Ctrl+X", self._cut), ("Ctrl+V", self._paste), ("Ctrl+A", self._select_all),
            ("Ctrl+R", self._repeat_last_tools), ("Ctrl+G", self._group_selection), ("Ctrl+Shift+G", self._ungroup_selection),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.WindowShortcut)
            shortcut.activated.connect(callback)
            shortcut.activatedAmbiguously.connect(callback)
            self._engineering_shortcuts.append(shortcut)

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

    def _group(self) -> None:
        self._group_selection()

    def _ungroup(self) -> None:
        self._ungroup_selection()

    def _rotate_selection(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.toggle_rotation_handles():
            self._set_status("Rotate handle toggled")
            return
        self._set_status("No selected object")

    def _rotation(self) -> None:
        self._rotate_selection()

    def _save_file(self):
        if self._current_file_path is None:
            return self._save_as_file()
        self._write_document(self._current_file_path)
        self._set_status(f"Saved {self._current_file_path.name}")
        return True

    def _save(self):
        return self._save_file()

    def _save_as_file(self):
        result = ProjectFileDialog.get_save_file(self, self._last_file_dir)
        if result is None:
            self._set_status("Save As canceled")
            return False
        if result.options is not None:
            self._save_options = result.options
        self._write_document(result.path)
        self._current_file_path = result.path
        self._last_file_dir = result.path.parent
        self._set_status(f"Saved As {result.path.name}")
        return True

    def _save_as(self):
        return self._save_as_file()

    def _save_file_as(self):
        return self._save_as_file()

    def _export_file(self) -> None:
        result = ProjectFileDialog.get_export_file(self, self._last_file_dir)
        if result is None:
            self._set_status("Export canceled")
            return
        if result.options is not None:
            self._save_options = result.options
        self._write_document(result.path)
        self._last_file_dir = result.path.parent
        self._set_status(f"Exported {result.path.name}")

    def _import_file(self) -> None:
        result = ProjectFileDialog.get_import_file(self, self._last_file_dir)
        if result and self._canvas is not None:
            self._canvas.load_file(result.path)
            self._last_file_dir = result.path.parent
            self._set_status(f"Imported {result.path.name}")
        else:
            self._set_status("Import canceled")

    def _write_document(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            path.write_bytes(self._blank_pdf_bytes())
        elif suffix == ".svg":
            path.write_text(self._build_svg_document(), encoding="utf-8")
        elif suffix == ".png":
            path.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="))
        elif suffix == ".docx":
            self._write_docx(path)
        elif suffix == ".pptx":
            self._write_pptx(path)
        elif suffix == ".xlsx":
            self._write_xlsx(path)
        elif suffix == ".csv":
            path.write_text("Engineer Tools Export\n", encoding="utf-8")
        else:
            path.write_text(self._build_project_text(), encoding="utf-8")

    def _build_project_text(self) -> str:
        return f"Engineer Tools document\nSave Grid: {self._save_options.get('save_grid', False)}\nRemove White Background: {self._save_options.get('remove_white_background', False)}\n"

    def _build_svg_document(self) -> str:
        grid = ""
        if self._save_options.get("save_grid", False):
            lines = []
            for x in range(0, 801, 50):
                lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="600" stroke="#d8e3ef" stroke-width="1"/>')
            for y in range(0, 601, 50):
                lines.append(f'<line x1="0" y1="{y}" x2="800" y2="{y}" stroke="#d8e3ef" stroke-width="1"/>')
            grid = "\n".join(lines)
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><rect width="800" height="600" fill="white"/>{grid}</svg>\n'

    def _blank_pdf_bytes(self) -> bytes:
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000053 00000 n \n0000000102 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n169\n%%EOF\n"

    def _write_zip(self, path: Path, files: dict[str, str]) -> None:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)

    def _write_docx(self, path: Path) -> None:
        self._write_zip(path, {
            "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
            "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
            "word/document.xml": '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Engineer Tools Export</w:t></w:r></w:p></w:body></w:document>',
        })

    def _write_pptx(self, path: Path) -> None:
        self._write_zip(path, {
            "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>',
            "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>',
            "ppt/presentation.xml": '<?xml version="1.0" encoding="UTF-8"?><p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst></p:presentation>',
            "ppt/_rels/presentation.xml.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>',
            "ppt/slides/slide1.xml": '<?xml version="1.0" encoding="UTF-8"?><p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr/><p:grpSpPr/></p:spTree></p:cSld></p:sld>',
        })

    def _write_xlsx(self, path: Path) -> None:
        self._write_zip(path, {
            "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
            "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
            "xl/workbook.xml": '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="EngineerTools" sheetId="1" r:id="rId1"/></sheets></workbook>',
            "xl/_rels/workbook.xml.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
            "xl/worksheets/sheet1.xml": '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Engineer Tools Export</t></is></c></row></sheetData></worksheet>',
        })

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
        self._zoom_input.setStyleSheet("QDoubleSpinBox#ZoomInput {background:#fff9de; border:1px solid #b38621; border-radius:8px; color:#132238; font-size:11px; font-style:normal; font-weight:700; padding:2px 6px; selection-background-color:#43d3bd; }")
        self._zoom_input.valueChanged.connect(self._set_zoom)
        control_layout.addWidget(self._zoom_input)
        arrows = QWidget()
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
        button.setStyleSheet("QPushButton#ZoomArrowButton {background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fff9de, stop:1 #ffc35a); border:1px solid #7e5b10; border-radius:4px; padding:0px; } QPushButton#ZoomArrowButton:hover { background:#ff8a35; border-color:#ffffff; } QPushButton#ZoomArrowButton:pressed { background:#d46a16; padding-top:1px; }")
        return button

    def _build_zoom_arrow_icon(self, direction: str) -> QIcon:
        pixmap = QPixmap(22, 10)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#ffffff"), 0.9))
        painter.setBrush(QColor("#132238"))
        points = QPolygonF([QPointF(11, 1), QPointF(20, 9), QPointF(2, 9)]) if direction == "up" else QPolygonF([QPointF(2, 1), QPointF(20, 1), QPointF(11, 9)])
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

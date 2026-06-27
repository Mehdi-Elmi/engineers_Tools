"""Engineering Design Tools workspace.

This file is the active workspace for mechanics, dynamics, statics, robotics,
and vector design. Future changes for this module must continue this class.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from src.engineers_tools.app.module_window import GridCanvas, MenuItemSpec, ModuleWindow, _paint_rotation_glyph
from src.engineers_tools.app.modules import LauncherModule

ENGINEERING_WORKSPACE_UI_MARKER = "ENGINEERING_WORKSPACE_VIEW_STARTBAR_2026_06_27_D"


@dataclass
class CanvasObject:
    path: Path
    pixmap: QPixmap
    rect: QRectF
    rotation: float = 0.0


class EngineeringCanvas(GridCanvas):
    def __init__(self) -> None:
        super().__init__()
        self.objects: list[CanvasObject] = []
        self.selected_index: int | None = None
        self._clipboard: CanvasObject | None = None
        self._last_action: str | None = None
        self._drag_action: str | None = None
        self._drag_start = QPointF()
        self._drag_start_rect = QRectF()
        self._drag_start_rotation = 0.0

    def load_file(self, path: Path) -> None:
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            width = float(pixmap.width())
            height = float(pixmap.height())
        elif path.suffix.lower() == ".pdf":
            width, height = 595.0, 842.0
        else:
            width, height = 520.0, 360.0
        max_width = max(180.0, self.width() * 0.62)
        max_height = max(160.0, self.height() * 0.74)
        scale = min(max_width / width, max_height / height, 1.0)
        width *= scale
        height *= scale
        rect = QRectF((self.width() - width) / 2, (self.height() - height) / 2, width, height)
        self.objects.append(CanvasObject(path=path, pixmap=pixmap, rect=rect))
        self.selected_index = len(self.objects) - 1
        self.update()

    def copy_selection(self) -> bool:
        obj = self._selected_object()
        if obj is None:
            return False
        self._clipboard = CanvasObject(obj.path, obj.pixmap, QRectF(obj.rect), obj.rotation)
        self._last_action = "copy"
        return True

    def cut_selection(self) -> bool:
        if not self.copy_selection() or self.selected_index is None:
            return False
        self.objects.pop(self.selected_index)
        self.selected_index = None
        self._last_action = "cut"
        self.update()
        return True

    def paste_selection(self) -> bool:
        if self._clipboard is None:
            return False
        clone = CanvasObject(self._clipboard.path, self._clipboard.pixmap, QRectF(self._clipboard.rect).translated(24, 24), self._clipboard.rotation)
        self.objects.append(clone)
        self.selected_index = len(self.objects) - 1
        self._last_action = "paste"
        self.update()
        return True

    def repeat_last_action(self) -> bool:
        if self._last_action in {"copy", "paste"}:
            return self.paste_selection()
        obj = self._selected_object()
        if obj is None:
            return False
        obj.rect.translate(12, 12)
        self.update()
        return True

    def select_all(self) -> bool:
        if not self.objects:
            return False
        self.selected_index = len(self.objects) - 1
        self.update()
        return True

    def bring_to_front(self) -> bool:
        if self.selected_index is None:
            return False
        obj = self.objects.pop(self.selected_index)
        self.objects.append(obj)
        self.selected_index = len(self.objects) - 1
        self.update()
        return True

    def send_to_back(self) -> bool:
        if self.selected_index is None:
            return False
        obj = self.objects.pop(self.selected_index)
        self.objects.insert(0, obj)
        self.selected_index = 0
        self.update()
        return True

    def _selected_object(self) -> CanvasObject | None:
        if self.selected_index is None or self.selected_index < 0 or self.selected_index >= len(self.objects):
            return None
        return self.objects[self.selected_index]

    def _to_canvas_point(self, point: QPointF) -> QPointF:
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        return QPointF(((point.x() - center_x) / self._zoom) + center_x, ((point.y() - center_y) / self._zoom) + center_y)

    def _hit_test_object(self, point: QPointF) -> tuple[int | None, str | None]:
        for index in range(len(self.objects) - 1, -1, -1):
            rect = self.objects[index].rect
            action = self._hit_test_rect(rect, point)
            if action is not None:
                return index, action
        return None, None

    def _hit_test_rect(self, rect: QRectF, point: QPointF) -> str | None:
        rotate_center = QPointF(rect.center().x(), rect.top() - 34)
        if math.hypot(point.x() - rotate_center.x(), point.y() - rotate_center.y()) <= 15:
            return "rotate"
        tolerance = 8.0
        handles = {
            "resize_nw": rect.topLeft(), "resize_n": QPointF(rect.center().x(), rect.top()), "resize_ne": rect.topRight(),
            "resize_e": QPointF(rect.right(), rect.center().y()), "resize_se": rect.bottomRight(), "resize_s": QPointF(rect.center().x(), rect.bottom()),
            "resize_sw": rect.bottomLeft(), "resize_w": QPointF(rect.left(), rect.center().y()),
        }
        for action, handle in handles.items():
            if abs(point.x() - handle.x()) <= tolerance and abs(point.y() - handle.y()) <= tolerance:
                return action
        inner = rect.adjusted(7, 7, -7, -7)
        if inner.contains(point):
            return "move"
        return None

    def _apply_drag(self, point: QPointF) -> None:
        obj = self._selected_object()
        if obj is None or self._drag_action is None:
            return
        dx = point.x() - self._drag_start.x()
        dy = point.y() - self._drag_start.y()
        rect = QRectF(self._drag_start_rect)
        if self._drag_action == "move":
            obj.rect = rect.translated(dx, dy)
        elif self._drag_action == "rotate":
            center = rect.center()
            start_angle = math.degrees(math.atan2(self._drag_start.y() - center.y(), self._drag_start.x() - center.x()))
            current_angle = math.degrees(math.atan2(point.y() - center.y(), point.x() - center.x()))
            obj.rotation = self._drag_start_rotation + current_angle - start_angle
        elif self._drag_action.startswith("resize"):
            if self._drag_action == "resize_w":
                rect.setLeft(rect.left() + dx)
            elif self._drag_action == "resize_e":
                rect.setRight(rect.right() + dx)
            elif self._drag_action == "resize_n":
                rect.setTop(rect.top() + dy)
            elif self._drag_action == "resize_s":
                rect.setBottom(rect.bottom() + dy)
            else:
                if "w" in self._drag_action:
                    rect.setLeft(rect.left() + dx)
                if "e" in self._drag_action:
                    rect.setRight(rect.right() + dx)
                if "n" in self._drag_action:
                    rect.setTop(rect.top() + dy)
                if "s" in self._drag_action:
                    rect.setBottom(rect.bottom() + dy)
            if rect.width() < 35:
                if "w" in self._drag_action:
                    rect.setLeft(rect.right() - 35)
                else:
                    rect.setRight(rect.left() + 35)
            if rect.height() < 35:
                if "n" in self._drag_action:
                    rect.setTop(rect.bottom() - 35)
                else:
                    rect.setBottom(rect.top() + 35)
            obj.rect = rect.normalized()
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            point = self._to_canvas_point(event.position())
            index, action = self._hit_test_object(point)
            if index is None:
                self.selected_index = None
                self._drag_action = None
                self.update()
                event.accept()
                return
            self.selected_index = index
            if action is not None:
                obj = self.objects[index]
                self._drag_action = action
                self._drag_start = point
                self._drag_start_rect = QRectF(obj.rect)
                self._drag_start_rotation = obj.rotation
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
        self._drag_action = None
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
            self._paint_object(painter, obj)
            if index == self.selected_index:
                self._paint_selection_frame(painter, obj.rect)

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

    def _paint_selection_frame(self, painter: QPainter, rect: QRectF) -> None:
        select = QColor("#2f7df6")
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(select, 1.5, Qt.DashLine))
        painter.drawRect(rect.adjusted(-5, -5, 5, 5))
        handles = (
            rect.topLeft(), QPointF(rect.center().x(), rect.top()), rect.topRight(),
            QPointF(rect.right(), rect.center().y()), rect.bottomRight(), QPointF(rect.center().x(), rect.bottom()),
            rect.bottomLeft(), QPointF(rect.left(), rect.center().y()),
        )
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        painter.setBrush(select)
        for handle in handles:
            painter.drawRoundedRect(QRectF(handle.x() - 4, handle.y() - 4, 8, 8), 2, 2)
        rotate_center = QPointF(rect.center().x(), rect.top() - 34)
        painter.setPen(QPen(select, 1.2, Qt.DashLine))
        painter.drawLine(QPointF(rect.center().x(), rect.top() - 5), QPointF(rotate_center.x(), rotate_center.y() + 13))
        painter.setBrush(QColor("#fff9de"))
        painter.setPen(QPen(QColor("#7e5b10"), 1.4))
        painter.drawEllipse(rotate_center, 13, 13)
        _paint_rotation_glyph(painter, rotate_center, 7.4, QColor("#ff8a35"))


class EngineeringDesignWorkspace(ModuleWindow):
    def __init__(self, module: LauncherModule) -> None:
        self._start_bar_tool_state: dict[str, bool] = {}
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
            self._add_layer("Pasted Object")
            self._set_status("Paste")
            return
        super()._paste()

    def _repeat_last_tools(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.repeat_last_action():
            self._add_layer("Repeated Object")
            self._set_status("Repeat")
            return
        super()._repeat_last_tools()

    def _select_all(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas) and self._canvas.select_all():
            self._set_status("Select All")
            return
        super()._select_all()

    def _bring_to_front(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas):
            self._canvas.bring_to_front()
        self._set_status("Bring to Front")

    def _send_to_back(self) -> None:
        if isinstance(self._canvas, EngineeringCanvas):
            self._canvas.send_to_back()
        self._set_status("Send to Back")

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

        tool_item = QLabel("Tool Select: Ready")
        tool_item.setObjectName("StatusItem")
        layout.addWidget(tool_item)
        self._status_items.append(tool_item)

        coordinate_item = QLabel("X: 0  Y: 0")
        coordinate_item.setObjectName("StatusItem")
        layout.addWidget(coordinate_item)
        self._status_items.append(coordinate_item)

        unit_item = QLabel("Unit: mm")
        unit_item.setObjectName("StatusItem")
        layout.addWidget(unit_item)
        self._status_items.append(unit_item)

        layout.addStretch(1)
        zoom_label = QLabel("Zoom:")
        zoom_label.setObjectName("StatusItem")
        layout.addWidget(zoom_label)
        layout.addWidget(self._build_zoom_control())
        return bar

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
        pixmap.fill(Qt.GlobalColor.transparent)
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

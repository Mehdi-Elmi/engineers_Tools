"""Current interaction cleanup for the Engineering Design Tools shell.

Applied last: keep one rotation angle badge, use the project Rotate dialog, and
make ruler-origin dragging follow the mouse directly.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap, QPolygonF, QShortcut
from PySide6.QtWidgets import QAbstractSpinBox, QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

PATCH_VERSION = "engineering-current-interaction-cleanup-2026-06-30-c"


def _angle_delta(a: float, b: float) -> float:
    return (a - b + 180.0) % 360.0 - 180.0


def _nearest_axis_angle(angle: float) -> float:
    return (round(angle / 90.0) * 90.0) % 360.0


def _selection_angle(canvas) -> float:
    selected = getattr(canvas, "selected_indices", set())
    objects = getattr(canvas, "objects", [])
    angles = [float(getattr(objects[index], "rotation", 0.0)) for index in selected if 0 <= index < len(objects)]
    if angles:
        return sum(angles) / len(angles)
    return float(getattr(canvas, "_rotation_degrees", 0.0))


def _can_rotate_selection(canvas) -> bool:
    selected = getattr(canvas, "selected_indices", set())
    objects = getattr(canvas, "objects", [])
    return any(0 <= index < len(objects) for index in selected) or getattr(canvas, "_object_rect", None) is not None


def _rotate_selection_by(canvas, degrees: float) -> bool:
    selected = getattr(canvas, "selected_indices", set())
    objects = getattr(canvas, "objects", [])
    valid = [index for index in sorted(selected) if 0 <= index < len(objects)]
    if valid:
        push_undo = getattr(canvas, "_push_undo", None)
        if callable(push_undo):
            push_undo()
        for index in valid:
            obj = objects[index]
            if not getattr(obj, "locked", False):
                obj.rotation = (float(getattr(obj, "rotation", 0.0)) + float(degrees)) % 360.0
        canvas._last_rotation_degrees = float(degrees)
        emit = getattr(canvas, "_emit_object_changes", None)
        if callable(emit):
            emit()
        canvas.update()
        return True
    if getattr(canvas, "_object_rect", None) is not None:
        canvas._rotation_degrees = (float(getattr(canvas, "_rotation_degrees", 0.0)) + float(degrees)) % 360.0
        canvas._last_rotation_degrees = float(degrees)
        canvas.update()
        return True
    return False


def _snap_rotation_to_axis(canvas) -> bool:
    selected = getattr(canvas, "selected_indices", set())
    objects = getattr(canvas, "objects", [])
    valid = [index for index in sorted(selected) if 0 <= index < len(objects)]
    if valid:
        push_undo = getattr(canvas, "_push_undo", None)
        if callable(push_undo):
            push_undo()
        changed = False
        for index in valid:
            obj = objects[index]
            if getattr(obj, "locked", False):
                continue
            current = float(getattr(obj, "rotation", 0.0))
            target = _nearest_axis_angle(current)
            if abs(_angle_delta(current, target)) > 0.01:
                obj.rotation = target
                changed = True
        if changed:
            emit = getattr(canvas, "_emit_object_changes", None)
            if callable(emit):
                emit()
            canvas.update()
        return changed
    if getattr(canvas, "_object_rect", None) is not None:
        current = float(getattr(canvas, "_rotation_degrees", 0.0))
        target = _nearest_axis_angle(current)
        if abs(_angle_delta(current, target)) <= 0.01:
            return False
        canvas._rotation_degrees = target
        canvas.update()
        return True
    return False


def _arrow_icon(direction: str) -> QIcon:
    pixmap = QPixmap(18, 8)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor("#ffffff"), 0.8))
    painter.setBrush(QColor("#132238"))
    points = QPolygonF([QPointF(9, 1), QPointF(16, 7), QPointF(2, 7)]) if direction == "up" else QPolygonF([QPointF(2, 1), QPointF(16, 1), QPointF(9, 7)])
    painter.drawPolygon(points)
    painter.end()
    return QIcon(pixmap)


def _arrow_button(direction: str) -> QPushButton:
    button = QPushButton()
    button.setObjectName("RotateArrowButton")
    button.setFixedSize(24, 10)
    button.setIcon(_arrow_icon(direction))
    button.setIconSize(QSize(18, 8))
    button.setStyleSheet(
        "QPushButton#RotateArrowButton {background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fff9de, stop:1 #ffc35a); border:1px solid #7e5b10; border-radius:3px; padding:0px;}"
        "QPushButton#RotateArrowButton:hover {background:#ff8a35; border-color:#ffffff;}"
        "QPushButton#RotateArrowButton:pressed {background:#d46a16; padding-top:1px;}"
    )
    return button


class _DialogDragFilter(QObject):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self._dialog = dialog
        self._dragging = False
        self._offset = QPoint()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._offset = event.globalPosition().toPoint() - self._dialog.frameGeometry().topLeft()
            event.accept()
            return True
        if event.type() == QEvent.Type.MouseMove and self._dragging:
            self._dialog.move(event.globalPosition().toPoint() - self._offset)
            event.accept()
            return True
        if event.type() == QEvent.Type.MouseButtonRelease and self._dragging:
            self._dragging = False
            event.accept()
            return True
        return False


def _ask_rotation_degrees(parent, default_value: float = 10.0) -> tuple[bool, float]:
    dialog = QDialog(parent)
    dialog.setObjectName("ProjectHelpDialog")
    dialog.setWindowTitle("Rotate")
    dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    dialog.setModal(True)
    dialog.resize(352, 184)

    shell = QWidget(dialog)
    shell.setObjectName("ProjectHelpShell")
    root = QVBoxLayout(dialog)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(shell)

    layout = QVBoxLayout(shell)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    header = QWidget()
    header.setObjectName("TopBar")
    header.setFixedHeight(44)
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(12, 0, 10, 0)
    if hasattr(parent, "_build_logo_mark"):
        header_layout.addWidget(parent._build_logo_mark())
    title = QLabel("Rotate")
    title.setObjectName("WindowTitle")
    title_font = title.font()
    title_font.setItalic(False)
    title.setFont(title_font)
    header_layout.addWidget(title, 1)
    layout.addWidget(header)

    drag_filter = _DialogDragFilter(dialog)
    header.installEventFilter(drag_filter)
    title.installEventFilter(drag_filter)
    dialog._engineering_drag_filter = drag_filter

    body = QWidget()
    body.setObjectName("WorkspaceArea")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(16, 14, 16, 14)
    body_layout.setSpacing(26)

    row = QHBoxLayout()
    row.setSpacing(6)
    label = QLabel("Degree")
    label.setObjectName("PanelTitle")
    label_font = label.font()
    label_font.setItalic(False)
    label.setFont(label_font)
    row.addWidget(label)

    degree_box = QWidget()
    degree_box.setObjectName("RotateDegreeBox")
    degree_box.setFixedSize(124, 28)
    degree_box.setStyleSheet(
        "QWidget#RotateDegreeBox {background:#fff9de; border:1px solid #b38621; border-radius:8px;}"
    )
    degree_layout = QHBoxLayout(degree_box)
    degree_layout.setContentsMargins(6, 2, 3, 2)
    degree_layout.setSpacing(3)

    spin = QDoubleSpinBox()
    spin.setObjectName("RotateDegreeInput")
    spin.setRange(-3600.0, 3600.0)
    spin.setDecimals(2)
    spin.setSingleStep(1.0)
    spin.setSuffix(" °")
    spin.setValue(default_value)
    spin.setFixedSize(86, 22)
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    spin_font = spin.font()
    spin_font.setItalic(False)
    spin_font.setBold(True)
    spin.setFont(spin_font)
    if spin.lineEdit() is not None:
        spin.lineEdit().setFont(spin_font)
    spin.setStyleSheet(
        "QDoubleSpinBox#RotateDegreeInput {background:transparent; border:none; color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:1px 2px; selection-background-color:#43d3bd;}"
    )
    degree_layout.addWidget(spin)

    arrows = QWidget()
    arrows.setFixedSize(26, 22)
    arrows_layout = QVBoxLayout(arrows)
    arrows_layout.setContentsMargins(0, 0, 0, 0)
    arrows_layout.setSpacing(1)
    up_button = _arrow_button("up")
    down_button = _arrow_button("down")
    up_button.clicked.connect(spin.stepUp)
    down_button.clicked.connect(spin.stepDown)
    arrows_layout.addWidget(up_button)
    arrows_layout.addWidget(down_button)
    degree_layout.addWidget(arrows)

    row.addWidget(degree_box)
    row.addStretch(1)
    body_layout.addLayout(row)

    buttons = QHBoxLayout()
    buttons.addStretch(1)
    apply_button = QPushButton("Apply")
    apply_button.setObjectName("PrimaryDialogButton")
    cancel_button = QPushButton("Cancel")
    cancel_button.setObjectName("SecondaryDialogButton")
    apply_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    buttons.addWidget(apply_button)
    buttons.addWidget(cancel_button)
    body_layout.addLayout(buttons)
    layout.addWidget(body)

    return (dialog.exec() == QDialog.DialogCode.Accepted, float(spin.value()))


def _install_rotation_cleanup() -> None:
    from . import workspace as edw

    def paint_event(self, event) -> None:
        QWidget.paintEvent(self, event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#fbfdff"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(getattr(self, "_zoom", 1.0), getattr(self, "_zoom", 1.0))
        painter.translate(-self.width() / 2, -self.height() / 2)
        self._paint_grid(painter)
        group_id = self._selection_group_id()
        for index, obj in enumerate(getattr(self, "objects", [])):
            if obj.visible:
                self._paint_object(painter, obj)
                if index in self.selected_indices and group_id is None:
                    self._paint_selection_frame(painter, obj)
        if group_id is not None:
            self._paint_group_selection(painter)
        if getattr(self, "_selection_rect", None) is not None:
            fill = QColor("#2f7df6")
            fill.setAlpha(28)
            painter.fillRect(self._selection_rect, fill)
            painter.setPen(QPen(QColor("#2f7df6"), 1.2, Qt.PenStyle.DashLine))
            painter.drawRect(self._selection_rect)
        painter.end()

    def rotation(self) -> None:
        canvas = getattr(self, "_canvas", None)
        if canvas is None or not _can_rotate_selection(canvas):
            self._set_status("Rotate disabled")
            return
        accepted, degrees = _ask_rotation_degrees(self, float(getattr(canvas, "_last_rotation_degrees", 10.0)))
        if not accepted:
            self._set_status("Rotate canceled")
            return
        self._set_status(f"Rotate {degrees:.2f}°" if _rotate_selection_by(canvas, degrees) else "Rotate disabled")

    def snap_rotation(self) -> None:
        canvas = getattr(self, "_canvas", None)
        if canvas is not None and _snap_rotation_to_axis(canvas):
            self._set_status(f"F8 Rotate snap {_selection_angle(canvas):.2f}°")
        else:
            self._set_status("F8 Rotate snap disabled")

    original_shortcuts = edw.EngineeringDesignWorkspace._install_engineering_shortcuts

    def install_shortcuts(self) -> None:
        original_shortcuts(self)
        if getattr(self, "_cleanup_f8_rotate_snap_installed", False):
            return
        shortcut = QShortcut(QKeySequence("F8"), self)
        shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        shortcut.activated.connect(lambda: self._snap_rotation_to_axis())
        shortcut.activatedAmbiguously.connect(lambda: self._snap_rotation_to_axis())
        if not hasattr(self, "_engineering_shortcuts") or self._engineering_shortcuts is None:
            self._engineering_shortcuts = []
        self._engineering_shortcuts.append(shortcut)
        self._cleanup_f8_rotate_snap_installed = True

    edw.EngineeringCanvas.paintEvent = paint_event
    edw.EngineeringCanvas.rotate_selection_by = _rotate_selection_by
    edw.EngineeringCanvas.snap_rotation_to_axis = _snap_rotation_to_axis
    edw.EngineeringDesignWorkspace._rotation = rotation
    edw.EngineeringDesignWorkspace._snap_rotation_to_axis = snap_rotation
    edw.EngineeringDesignWorkspace._install_engineering_shortcuts = install_shortcuts


def _install_ruler_origin_drag_cleanup() -> None:
    from src.engineers_tools.ui import start_bar as sb
    from . import cursor_unification_fixes as cursors

    def mouse_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._pressed = True
            self._press_pos = event.position()
            self._origin_drag_start_global = event.globalPosition().toPoint()
            self.grabMouse()
            self.setCursor(cursors.project_cursor("origin"))
            self.update()
            event.accept()
            return
        event.ignore()

    def mouse_move(self, event) -> None:
        if self._dragging and self.parentWidget() is not None:
            start = getattr(self, "_origin_drag_start_global", event.globalPosition().toPoint())
            moved = (event.globalPosition().toPoint() - start).manhattanLength()
            if moved >= 2:
                self._pressed = False
                self._preview_origin(event.globalPosition().toPoint())
                self.update()
            event.accept()
            return
        event.ignore()

    def mouse_release(self, event) -> None:
        if self._dragging:
            self._dragging = False
            try:
                self.releaseMouse()
            except RuntimeError:
                pass
            canvas = self.parentWidget()
            start = getattr(self, "_origin_drag_start_global", event.globalPosition().toPoint())
            moved = (event.globalPosition().toPoint() - start).manhattanLength()
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
            self._clear_origin_preview()
            self._press_pos = None
            self._origin_drag_start_global = None
            self.setCursor(cursors.project_cursor("origin"))
            self.update()
            event.accept()
            return
        event.ignore()

    sb._RulerCorner.mousePressEvent = mouse_press
    sb._RulerCorner.mouseMoveEvent = mouse_move
    sb._RulerCorner.mouseReleaseEvent = mouse_release


def apply_current_interaction_cleanup_fixes() -> None:
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_current_interaction_cleanup_patch", "") == PATCH_VERSION:
        return

    _install_rotation_cleanup()
    _install_ruler_origin_drag_cleanup()
    edw.EngineeringDesignWorkspace._engineering_current_interaction_cleanup_patch = PATCH_VERSION

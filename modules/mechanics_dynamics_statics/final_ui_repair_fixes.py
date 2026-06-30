"""Final UI repair layer for page setup, canvas cursors, and properties blocks."""

from __future__ import annotations

import math
import os
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QCursor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-final-ui-repair-2026-06-30-a"


def _runtime_log_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "EngineerTools" / "logs" / "runtime.log"
    return Path.home() / ".engineer_tools" / "logs" / "runtime.log"


def _log_error(operation: str, error: BaseException) -> None:
    try:
        path = _runtime_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"\n[{timestamp}] final_ui_repair.{operation} failed\n")
            log_file.write("".join(traceback.format_exception(type(error), error, error.__traceback__)))
    except OSError:
        return


def _arrow_head(painter: QPainter, tip: QPointF, tail: QPointF, size: float = 5.0) -> None:
    direction = tip - tail
    length = max(0.01, math.hypot(direction.x(), direction.y()))
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    base = QPointF(tip.x() - unit.x() * size, tip.y() - unit.y() * size)
    painter.drawPolygon(QPolygonF([
        tip,
        QPointF(base.x() + normal.x() * size * 0.48, base.y() + normal.y() * size * 0.48),
        QPointF(base.x() - normal.x() * size * 0.48, base.y() - normal.y() * size * 0.48),
    ]))


def _stroke_line(painter: QPainter, start: QPointF, end: QPointF, ink: QColor) -> None:
    painter.setPen(QPen(QColor("#ffffff"), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawLine(start, end)
    painter.setPen(QPen(ink, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawLine(start, end)


def _paint_hand(painter: QPainter, closed: bool) -> None:
    ink = QColor("#102238")
    fill = QLinearGradient(7, 4, 25, 29)
    fill.setColorAt(0.0, QColor("#ffffff"))
    fill.setColorAt(0.50, QColor("#fff1c2" if closed else "#e2f7ff"))
    fill.setColorAt(1.0, QColor("#ff8a35" if closed else "#55baf5"))
    path = QPainterPath()
    if closed:
        path.addRoundedRect(QRectF(7.8, 10.8, 17.6, 15.4), 6.0, 6.0)
        path.addRoundedRect(QRectF(8.5, 7.0, 4.5, 9.4), 2.1, 2.1)
        path.addRoundedRect(QRectF(12.9, 5.6, 4.5, 10.9), 2.1, 2.1)
        path.addRoundedRect(QRectF(17.2, 6.8, 4.5, 9.6), 2.1, 2.1)
        path.addRoundedRect(QRectF(21.3, 9.6, 4.2, 8.3), 2.0, 2.0)
    else:
        path.addRoundedRect(QRectF(8.0, 12.0, 15.8, 15.0), 6.0, 6.0)
        path.addRoundedRect(QRectF(7.6, 5.0, 4.2, 13.4), 2.0, 2.0)
        path.addRoundedRect(QRectF(11.8, 3.8, 4.2, 14.7), 2.0, 2.0)
        path.addRoundedRect(QRectF(16.0, 4.9, 4.2, 13.6), 2.0, 2.0)
        path.addRoundedRect(QRectF(20.0, 7.8, 4.2, 11.2), 2.0, 2.0)
    painter.fillPath(path, fill)
    painter.setPen(QPen(QColor("#ffffff"), 3.1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawPath(path)
    painter.setPen(QPen(ink, 1.35, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawPath(path)


def _repair_cursor(kind: str) -> QCursor:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    ink = QColor("#0f4f7c")
    if kind == "move":
        for tip, tail in (
            (QPointF(16, 4), QPointF(16, 15)),
            (QPointF(28, 16), QPointF(17, 16)),
            (QPointF(16, 28), QPointF(16, 17)),
            (QPointF(4, 16), QPointF(15, 16)),
        ):
            _stroke_line(painter, tail, tip, ink)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(ink)
            _arrow_head(painter, tip, tail, 5.0)
        painter.setBrush(QColor("#ffc35a"))
        painter.setPen(QPen(QColor("#102238"), 1.0))
        painter.drawEllipse(QPointF(16, 16), 3.0, 3.0)
    elif kind in {"hand_open", "rotate"}:
        _paint_hand(painter, closed=False)
    elif kind == "hand_closed":
        _paint_hand(painter, closed=True)
    elif kind in {"resize_h", "resize_v", "resize_fdiag", "resize_bdiag", "guide_h", "guide_v"}:
        points = {
            "resize_h": (QPointF(5, 16), QPointF(27, 16)),
            "guide_v": (QPointF(5, 16), QPointF(27, 16)),
            "resize_v": (QPointF(16, 5), QPointF(16, 27)),
            "guide_h": (QPointF(16, 5), QPointF(16, 27)),
            "resize_fdiag": (QPointF(7, 7), QPointF(25, 25)),
            "resize_bdiag": (QPointF(25, 7), QPointF(7, 25)),
        }[kind]
        a, b = points
        center = QPointF((a.x() + b.x()) / 2.0, (a.y() + b.y()) / 2.0)
        direction = b - a
        length = max(0.01, math.hypot(direction.x(), direction.y()))
        unit = QPointF(direction.x() / length, direction.y() / length)
        gap = 5.0
        left_inner = QPointF(center.x() - unit.x() * gap, center.y() - unit.y() * gap)
        right_inner = QPointF(center.x() + unit.x() * gap, center.y() + unit.y() * gap)
        _stroke_line(painter, a, left_inner, QColor("#102238"))
        _stroke_line(painter, right_inner, b, QColor("#102238"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#102238"))
        _arrow_head(painter, a, left_inner, 5.8)
        _arrow_head(painter, b, right_inner, 5.8)
        painter.setBrush(QColor("#ffc35a"))
        painter.setPen(QPen(QColor("#102238"), 1.0))
        painter.drawEllipse(center, 3.3, 3.3)
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
        gradient = QLinearGradient(6, 5, 24, 28)
        gradient.setColorAt(0.0, QColor("#ffffff"))
        gradient.setColorAt(0.58, QColor("#dff4ff"))
        gradient.setColorAt(1.0, QColor("#8dc1ff"))
        painter.fillPath(path, gradient)
        painter.setPen(QPen(QColor("#102238"), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)
    painter.end()
    return QCursor(pixmap, 16, 16)


def _cursor_name(action: str | None, dragging: bool = False) -> str | None:
    if action == "move":
        return "move"
    if action == "rotate":
        return "hand_closed" if dragging else "hand_open"
    if action in {"resize_n", "resize_s"}:
        return "resize_v"
    if action in {"resize_e", "resize_w"}:
        return "resize_h"
    if action in {"resize_nw", "resize_se"}:
        return "resize_fdiag"
    if action in {"resize_ne", "resize_sw"}:
        return "resize_bdiag"
    return None


def _set_canvas_cursor(canvas, action: str | None, dragging: bool = False) -> None:
    name = _cursor_name(action, dragging)
    if name is None:
        return
    canvas.setCursor(_repair_cursor(name))


def _open_page_setup_dialog(workspace) -> None:
    from . import file_export_project_fixes as export_fixes

    try:
        state = export_fixes._apply_page_setup_to_canvas(workspace)
        unit = str(state["unit"])
        unit_to_mm = export_fixes.UNIT_TO_MM
        mm_to_unit = export_fixes.MM_TO_UNIT
        paper_sizes = export_fixes.PAPER_SIZES_MM
        dialog = QDialog(workspace)
        dialog.setObjectName("PageSetupDialog")
        dialog.setWindowTitle("Page Setup")
        dialog.setModal(True)
        dialog.setMinimumWidth(380)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(14, 12, 14, 14)
        root.setSpacing(10)
        title = QLabel("Page Setup")
        title.setObjectName("PanelTitle")
        title.setStyleSheet("font-size:15px; font-weight:900; font-style:normal; color:#102238;")
        root.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        paper = QComboBox()
        paper.addItems(tuple(paper_sizes.keys()))
        paper.setCurrentText(str(state["paper"]))
        orientation = QComboBox()
        orientation.addItems(("Portrait", "Landscape"))
        orientation.setCurrentText(str(state["orientation"]))
        unit_box = QComboBox()
        unit_box.addItems(tuple(unit_to_mm.keys()))
        unit_box.setCurrentText(unit)
        dpi = QDoubleSpinBox()
        dpi.setRange(72, 2400)
        dpi.setDecimals(0)
        dpi.setSingleStep(50)
        dpi.setValue(float(state["dpi"]))
        position = QComboBox()
        position.addItems(("Top Left", "Top", "Top Right", "Left", "Center", "Right", "Bottom Left", "Bottom", "Bottom Right"))
        position.setCurrentText(str(state["position"]))

        def spin(value_mm: float) -> QDoubleSpinBox:
            box = QDoubleSpinBox()
            box.setRange(0, 1000000)
            box.setDecimals(3)
            box.setSingleStep(1)
            box.setValue(value_mm * mm_to_unit[unit_box.currentText()])
            box.setSuffix(f" {unit_box.currentText()}")
            return box

        width = spin(float(state["width_mm"]))
        height = spin(float(state["height_mm"]))
        margins = state["margins_mm"]
        top = spin(float(margins["top"]))
        right = spin(float(margins["right"]))
        bottom = spin(float(margins["bottom"]))
        left = spin(float(margins["left"]))
        dialog._last_unit = unit

        def refresh_size() -> None:
            w_mm, h_mm = paper_sizes.get(paper.currentText(), paper_sizes["Workspace"])
            if orientation.currentText() == "Landscape" and h_mm > w_mm:
                w_mm, h_mm = h_mm, w_mm
            if orientation.currentText() == "Portrait" and w_mm > h_mm:
                w_mm, h_mm = h_mm, w_mm
            factor = mm_to_unit[unit_box.currentText()]
            width.setValue(w_mm * factor)
            height.setValue(h_mm * factor)

        def refresh_unit() -> None:
            old_unit = getattr(dialog, "_last_unit", "mm")
            old_factor = unit_to_mm.get(old_unit, 1.0)
            new_unit = unit_box.currentText()
            for box in (width, height, top, right, bottom, left):
                value_mm = box.value() * old_factor
                box.setSuffix(f" {new_unit}")
                box.setValue(value_mm * mm_to_unit[new_unit])
            dialog._last_unit = new_unit

        paper.currentTextChanged.connect(lambda _text: refresh_size())
        orientation.currentTextChanged.connect(lambda _text: refresh_size())
        unit_box.currentTextChanged.connect(lambda _text: refresh_unit())
        for label, widget in (
            ("Paper", paper), ("Orientation", orientation), ("Unit", unit_box),
            ("Width", width), ("Height", height), ("Quality DPI", dpi),
            ("Top", top), ("Right", right), ("Bottom", bottom), ("Left", left),
            ("Object Position", position),
        ):
            form.addRow(label, widget)
        root.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        apply_button = QPushButton("Apply")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(apply_button)
        buttons.addWidget(cancel_button)
        root.addLayout(buttons)
        cancel_button.clicked.connect(dialog.reject)

        def apply() -> None:
            selected_unit = unit_box.currentText()
            factor_to_mm = unit_to_mm[selected_unit]
            new_state = export_fixes._normalize_page_setup({
                "paper": paper.currentText(),
                "orientation": orientation.currentText(),
                "dpi": int(dpi.value()),
                "unit": selected_unit,
                "margins_mm": {
                    "top": top.value() * factor_to_mm,
                    "right": right.value() * factor_to_mm,
                    "bottom": bottom.value() * factor_to_mm,
                    "left": left.value() * factor_to_mm,
                },
                "position": position.currentText(),
            })
            workspace._page_setup = new_state
            export_fixes._apply_page_setup_to_canvas(workspace, new_state)
            workspace._set_status(f"Page Setup {new_state['paper']} {new_state['orientation']} | {new_state['dpi']} DPI")
            dialog.accept()

        apply_button.clicked.connect(apply)
        dialog.setStyleSheet(
            "QDialog#PageSetupDialog {background:#eaf4ff;}"
            "QLabel {font-style:normal; font-weight:800; color:#132238;}"
            "QComboBox, QDoubleSpinBox {background:#fff9de; border:1px solid #b38621; border-radius:7px; padding:4px 7px; font-style:normal; color:#132238;}"
            "QPushButton {background:#fff9de; border:1px solid #b38621; border-radius:9px; padding:6px 14px; font-style:normal; font-weight:900; color:#132238;}"
            "QPushButton:hover {background:#ffefb0; border-color:#ff8a35;}"
        )
        dialog.exec()
    except Exception as error:  # noqa: BLE001 - keep the GUI alive and log the real failure.
        _log_error("page_setup", error)
        workspace._set_status("Page Setup error - see runtime.log")


def _property_row(label: str, value: str) -> QWidget:
    row = QWidget()
    row.setObjectName("GeometryRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(8, 3, 8, 3)
    layout.setSpacing(6)
    left = QLabel(label)
    left.setObjectName("GeometryLabel")
    right = QLabel(value)
    right.setObjectName("GeometryValue")
    right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(left, 1)
    layout.addWidget(right)
    return row


def _build_geometry_block() -> QWidget:
    block = QFrame()
    block.setObjectName("GeometryBlock")
    block.setFrameShape(QFrame.Shape.NoFrame)
    layout = QVBoxLayout(block)
    layout.setContentsMargins(0, 0, 0, 8)
    layout.setSpacing(0)

    header = QPushButton("Geometry")
    header.setObjectName("GeometryHeader")
    header.setCheckable(True)
    header.setChecked(True)
    layout.addWidget(header)

    body = QWidget()
    body.setObjectName("GeometryBody")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(0, 6, 0, 0)
    body_layout.setSpacing(3)
    for label, value in (
        ("Position X", "0.00 mm"),
        ("Position Y", "0.00 mm"),
        ("Width", "--"),
        ("Height", "--"),
        ("Rotation", "0.00 deg"),
    ):
        body_layout.addWidget(_property_row(label, value))
    layout.addWidget(body)

    def toggle(checked: bool) -> None:
        body.setVisible(checked)
        header.setText("Geometry" if checked else "Geometry  +")

    header.toggled.connect(toggle)
    block.setStyleSheet(
        "QFrame#GeometryBlock {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.58 #eef8ff, stop:1 #fff3d4); border:1px solid #9fb3ca; border-radius:8px;}"
        "QPushButton#GeometryHeader {background:#102238; color:#ffffff; border:0; border-top-left-radius:8px; border-top-right-radius:8px; padding:7px 10px; text-align:left; font-size:12px; font-style:normal; font-weight:900;}"
        "QWidget#GeometryBody {background:transparent;}"
        "QWidget#GeometryRow {background:rgba(255,255,255,170); border:1px solid rgba(151,171,196,120); border-radius:6px;}"
        "QLabel#GeometryLabel {color:#243a55; font-size:11px; font-style:normal; font-weight:800;}"
        "QLabel#GeometryValue {color:#0f4f7c; font-size:11px; font-style:normal; font-weight:900;}"
    )
    return block


def apply_final_ui_repair_fixes() -> None:
    from . import cursor_unification_fixes as cursors
    from . import interaction_fixes
    from . import ui_refinement_fixes
    from . import window_resize_fixes
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_final_ui_repair_patch", "") == PATCH_VERSION:
        return

    cursors.project_cursor = _repair_cursor
    interaction_fixes.project_cursor = _repair_cursor
    ui_refinement_fixes._refined_project_cursor = _repair_cursor
    window_resize_fixes._window_cursor = _repair_cursor

    original_mouse_press = edw.EngineeringCanvas.mousePressEvent
    original_mouse_move = edw.EngineeringCanvas.mouseMoveEvent
    original_mouse_release = edw.EngineeringCanvas.mouseReleaseEvent
    original_build_side_panel = edw.EngineeringDesignWorkspace._build_side_panel

    def mouse_press(self, event) -> None:
        action_before = None
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                _index, action_before = self._hit_test_object(self._to_canvas_point(event.position()))
            except Exception:
                action_before = None
        original_mouse_press(self, event)
        _set_canvas_cursor(self, getattr(self, "_drag_action", None) or action_before, dragging=True)

    def mouse_move(self, event) -> None:
        original_mouse_move(self, event)
        drag_action = getattr(self, "_drag_action", None)
        if drag_action is not None:
            _set_canvas_cursor(self, drag_action, dragging=True)
            return
        try:
            _index, hover = self._hit_test_object(self._to_canvas_point(event.position()))
        except Exception:
            hover = None
        _set_canvas_cursor(self, hover, dragging=False)

    def mouse_release(self, event) -> None:
        original_mouse_release(self, event)
        try:
            _index, hover = self._hit_test_object(self._to_canvas_point(event.position()))
        except Exception:
            hover = None
        _set_canvas_cursor(self, hover, dragging=False)

    def page_setup(self) -> None:
        self._set_status("Opening Page Setup")
        QTimer.singleShot(0, lambda owner=self: _open_page_setup_dialog(owner))

    def build_side_panel(self, title, rows):
        if title != "Properties":
            return original_build_side_panel(self, title, rows)
        panel = QWidget()
        panel.setObjectName("SidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        heading = QLabel("Properties")
        heading.setObjectName("PanelTitle")
        layout.addWidget(heading)
        layout.addWidget(_build_geometry_block())
        layout.addStretch(1)
        return panel

    edw.EngineeringCanvas.mousePressEvent = mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    edw.EngineeringDesignWorkspace._page_setup = page_setup
    edw.EngineeringDesignWorkspace._build_side_panel = build_side_panel
    edw.EngineeringDesignWorkspace._engineering_final_ui_repair_patch = PATCH_VERSION

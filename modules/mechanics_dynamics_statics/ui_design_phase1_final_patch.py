"""Final phase-1 UI design fixes for cursors, controls, properties, shortcuts and text bar."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QKeySequence, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-ui-design-phase1-final-2026-07-01-a"
FONT_CHOICES = ("Times New Roman",)

_TOOL_ICON_ASSETS = {
    "select": "select_edit_object.svg",
    "line": "line.svg",
    "vector": "vector.svg",
    "angle": "angle_moment.svg",
    "text": "text.svg",
    "grid": "grid.svg",
    "snap": "snap.svg",
    "unit": "unit.svg",
    "ruler": "ruler.svg",
    "zoom": "zoom.svg",
    "zoom_in": "zoom_in.svg",
    "zoom_out": "zoom_out.svg",
    "zoom_fit": "zoom_fit.svg",
}

_CURSOR_MAP = {
    "default": ("mouse_cursor.svg", 3, 3, 24),
    "pointer": ("mouse_cursor.svg", 3, 3, 24),
    "hand_pointer": ("mouse_cursor.svg", 3, 3, 24),
    "hand_open": ("mouse_cursor.svg", 3, 3, 24),
    "hand_closed": ("mouse_cursor.svg", 3, 3, 24),
    "pan_open": ("mouse_cursor.svg", 3, 3, 24),
    "pan_closed": ("mouse_cursor.svg", 3, 3, 24),
    "move": ("move_cursor.svg", 12, 12, 24),
    "rotate": ("rotate.svg", 12, 12, 32),
    "rotate_drag": ("rotate.svg", 12, 12, 32),
    "resize_n": ("resize_vertical.svg", 12, 12, 24),
    "resize_s": ("resize_vertical.svg", 12, 12, 24),
    "resize_e": ("resize_horizontal.svg", 12, 12, 24),
    "resize_w": ("resize_horizontal.svg", 12, 12, 24),
    "resize_ne": ("corner_resize_b.svg", 12, 12, 24),
    "resize_sw": ("corner_resize_b.svg", 12, 12, 24),
    "resize_nw": ("corner_resize_a.svg", 12, 12, 24),
    "resize_se": ("corner_resize_a.svg", 12, 12, 24),
    "resize_horizontal": ("resize_horizontal.svg", 12, 12, 24),
    "resize_vertical": ("resize_vertical.svg", 12, 12, 24),
    "resize_diag_f": ("corner_resize_a.svg", 12, 12, 24),
    "resize_diag_b": ("corner_resize_b.svg", 12, 12, 24),
    "resize_fdiag": ("corner_resize_a.svg", 12, 12, 24),
    "resize_bdiag": ("corner_resize_b.svg", 12, 12, 24),
}


def _asset_url(svg, name: str) -> str:
    return svg._asset_url(name) if hasattr(svg, "_asset_url") else ""


def _font(widget, size: int = 10, *, bold: bool = True, italic: bool = False) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(bold)
    font.setItalic(italic)
    widget.setFont(font)


def _apply_system_font_tree(root: QWidget) -> None:
    for widget in [root, *root.findChildren(QWidget)]:
        if isinstance(widget, (QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QKeySequenceEdit)):
            _font(widget, 9 if not isinstance(widget, QLabel) else 10, bold=True, italic=False)


def _style_spin(svg, spin) -> None:
    up = _asset_url(svg, "spin_up.svg")
    down = _asset_url(svg, "spin_down.svg")
    spin.setFixedHeight(22)
    spin.setStyleSheet(
        "QSpinBox, QDoubleSpinBox {background:#fffdf0; border:1px solid #b78316; border-radius:7px; color:#132238; font-family:'Times New Roman'; font-size:9px; font-style:normal; font-weight:800; padding:0px 27px 0px 5px;}"
        "QSpinBox::up-button, QDoubleSpinBox::up-button {width:24px; border:0; subcontrol-origin:border; subcontrol-position:top right; background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fffdf0, stop:.55 #ffe894, stop:1 #ffc64f); border-top-right-radius:6px;}"
        "QSpinBox::down-button, QDoubleSpinBox::down-button {width:24px; border:0; subcontrol-origin:border; subcontrol-position:bottom right; background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fffdf0, stop:.55 #ffe894, stop:1 #ffc64f); border-bottom-right-radius:6px;}"
        f"QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{image:url({up}); width:17px; height:10px;}}"
        f"QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{image:url({down}); width:17px; height:10px;}}"
    )


def _style_combo(svg, combo: QComboBox) -> None:
    arrow = _asset_url(svg, "combo_down.svg")
    combo.setFixedHeight(22)
    combo.setStyleSheet(
        "QComboBox {background:#ffffff; border:1px solid #9fb0c5; border-radius:7px; color:#132238; font-family:'Times New Roman'; font-size:9px; font-style:normal; font-weight:800; padding:0px 28px 0px 6px;}"
        "QComboBox::drop-down {width:25px; border:0; subcontrol-origin:border; subcontrol-position:center right; background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fffdf0, stop:.55 #ffe894, stop:1 #ffc64f); border-top-right-radius:6px; border-bottom-right-radius:6px;}"
        f"QComboBox::down-arrow {{image:url({arrow}); width:17px; height:10px;}}"
    )


def _choice(text: str, checked: bool, callback, width: int = 64) -> QPushButton:
    button = QPushButton(("● " if checked else "○ ") + text)
    button.setCheckable(True)
    button.setChecked(checked)
    button.setFixedSize(width, 22)
    _font(button, 9, bold=True, italic=False)
    button.setStyleSheet(
        "QPushButton {background:#ffffff; border:1px solid #b9c6d6; border-radius:7px; color:#223a58; padding:0px 4px; text-align:left;}"
        "QPushButton:hover {background:#fff4cf; border-color:#ff8a35;}"
        "QPushButton:checked {background:#eaf6ff; border-color:#2f7df6; color:#132238;}"
    )
    button.clicked.connect(callback)
    return button


def _section(title: str, height: int | None = None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("CompactPropertiesSection")
    if height is not None:
        frame.setFixedHeight(height)
    frame.setStyleSheet(
        "QFrame#CompactPropertiesSection {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:.55 #eef8ff, stop:1 #fff5d8); border:1px solid #b9c6d6; border-radius:10px;}"
    )
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(8, 5, 8, 6)
    layout.setSpacing(3)
    label = QLabel(title)
    label.setObjectName("CompactSectionTitle")
    _font(label, 10, bold=True, italic=False)
    label.setStyleSheet("QLabel#CompactSectionTitle {background:transparent; color:#132238; padding:0px;}")
    layout.addWidget(label)
    return frame, layout


def _row(label_text: str, editor: QWidget, label_width: int = 78) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    label = QLabel(label_text)
    label.setFixedWidth(label_width)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    _font(label, 9, bold=True, italic=False)
    label.setStyleSheet("QLabel {background:transparent; color:#223a58;}")
    layout.addWidget(label)
    layout.addWidget(editor, 1)
    return row


def _patch_svg_cursors(svg) -> None:
    svg._CURSOR_ASSET_MAP.update(_CURSOR_MAP)
    for name in ("hand_open", "hand_closed", "hand_pointer", "pan_open", "pan_closed"):
        svg._CURSOR_ASSET_MAP[name] = ("mouse_cursor.svg", 3, 3, 24)
    svg._CURSOR_CACHE.clear()

    if not getattr(svg, "_phase1_asset_cursor_wrapped", False):
        original = svg.asset_cursor

        def asset_cursor(file_name: str, fallback, hot_x: int = 8, hot_y: int = 8, max_side: int = 24):
            mapped = {
                "hand_open.svg": "mouse_cursor.svg",
                "hand_closed.svg": "mouse_cursor.svg",
                "hand_pointer.svg": "mouse_cursor.svg",
                "rotate_cursor.svg": "rotate.svg",
            }.get(file_name, file_name)
            return original(mapped, fallback, hot_x, hot_y, max_side)

        svg.asset_cursor = asset_cursor
        svg._phase1_asset_cursor_wrapped = True

    def project_cursor(kind: str):
        file_name, hot_x, hot_y, side = svg._CURSOR_ASSET_MAP.get(kind, svg._CURSOR_ASSET_MAP.get("default", ("mouse_cursor.svg", 3, 3, 24)))
        fallback = getattr(svg, "_FALLBACKS", {}).get(kind, Qt.CursorShape.ArrowCursor)
        return svg.asset_cursor(file_name, fallback, hot_x, hot_y, side)

    svg.project_cursor = project_cursor


def _patch_startbar_icons(sb, svg) -> None:
    def tool_icon(key: str) -> QIcon:
        icon = svg.asset_icon(_TOOL_ICON_ASSETS.get(key, "mouse_cursor.svg"))
        return icon if not icon.isNull() else QIcon()

    def mini_zoom_icon(action: str) -> QIcon:
        icon = svg.asset_icon(_TOOL_ICON_ASSETS.get(action, "zoom.svg"))
        return icon if not icon.isNull() else QIcon()

    sb._tool_icon = tool_icon
    sb._mini_zoom_icon = mini_zoom_icon


def _install_canvas_handle_patch(edw, svg) -> None:
    def hit_test_single(self, obj, point):
        local = self._scene_to_object_local(obj, point)
        half_w = obj.rect.width() / 2
        half_h = obj.rect.height() / 2
        if obj.rotation_handle_visible and math.hypot(local.x(), local.y() + half_h + 34) <= 22:
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

    def hit_test_group(self, point):
        if self._selection_group_id() is None:
            return None
        rect = self._group_bounds().adjusted(-6, -6, 6, 6)
        rotate_center = QPointF(rect.center().x(), rect.top() - 34)
        if math.hypot(point.x() - rotate_center.x(), point.y() - rotate_center.y()) <= 22:
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

    def paint_selection_frame(self, painter, obj) -> None:
        rect = obj.rect
        half_w = rect.width() / 2
        half_h = rect.height() / 2
        select = QColor("#2f7df6")
        painter.save()
        painter.translate(rect.center())
        painter.rotate(obj.rotation)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(select, 1.5, Qt.PenStyle.DashLine))
        painter.drawRect(QRectF(-half_w - 5, -half_h - 5, rect.width() + 10, rect.height() + 10))
        handles = (QPointF(-half_w, -half_h), QPointF(0, -half_h), QPointF(half_w, -half_h), QPointF(half_w, 0), QPointF(half_w, half_h), QPointF(0, half_h), QPointF(-half_w, half_h), QPointF(-half_w, 0))
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        painter.setBrush(select)
        for handle in handles:
            painter.drawRoundedRect(QRectF(handle.x() - 4, handle.y() - 4, 8, 8), 2, 2)
        if obj.rotation_handle_visible:
            rotate_center = QPointF(0, -half_h - 34)
            painter.setPen(QPen(select, 1.2, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(0, -half_h - 5), QPointF(0, rotate_center.y() + 18))
            painter.setBrush(QColor("#fff8dc"))
            painter.setPen(QPen(QColor("#7e5b10"), 1.5))
            painter.drawEllipse(rotate_center, 19.5, 19.5)
            edw._draw_arc_arrow(painter, rotate_center, 10.8, QColor("#ff8a35"))
            painter.setBrush(QColor("#2f7df6"))
            painter.setPen(QPen(QColor("#15324d"), 1.2))
            painter.drawEllipse(rotate_center, 4.2, 4.2)
        painter.restore()

    def paint_group_selection(self, painter) -> None:
        rect = self._group_bounds().adjusted(-6, -6, 6, 6)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#2f7df6"), 1.5, Qt.PenStyle.DashLine))
        painter.drawRoundedRect(rect, 4, 4)
        handles = (rect.topLeft(), QPointF(rect.center().x(), rect.top()), rect.topRight(), QPointF(rect.right(), rect.center().y()), rect.bottomRight(), QPointF(rect.center().x(), rect.bottom()), rect.bottomLeft(), QPointF(rect.left(), rect.center().y()))
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        painter.setBrush(QColor("#2f7df6"))
        for handle in handles:
            painter.drawRoundedRect(QRectF(handle.x() - 4, handle.y() - 4, 8, 8), 2, 2)
        rotate_center = QPointF(rect.center().x(), rect.top() - 34)
        painter.setPen(QPen(QColor("#2f7df6"), 1.2, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(rect.center().x(), rect.top()), QPointF(rotate_center.x(), rotate_center.y() + 18))
        painter.setBrush(QColor("#fff8dc"))
        painter.setPen(QPen(QColor("#7e5b10"), 1.5))
        painter.drawEllipse(rotate_center, 19.5, 19.5)
        edw._draw_arc_arrow(painter, rotate_center, 10.8, QColor("#ff8a35"))
        painter.setBrush(QColor("#2f7df6"))
        painter.setPen(QPen(QColor("#15324d"), 1.2))
        painter.drawEllipse(rotate_center, 4.2, 4.2)

    edw.EngineeringCanvas._hit_test_single_object = hit_test_single
    edw.EngineeringCanvas._hit_test_group_selection = hit_test_group
    edw.EngineeringCanvas._paint_selection_frame = paint_selection_frame
    edw.EngineeringCanvas._paint_group_selection = paint_group_selection


def _patch_file_properties(epp, svg) -> None:
    def general_page(self) -> QWidget:
        page = QWidget()
        page.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        general = self._settings.get("general", {})

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["mm", "cm", "m", "px", "pt", "in"])
        self.unit_combo.setCurrentText(str(general.get("unit", "mm")) if str(general.get("unit", "mm")) in {"mm", "cm", "m", "px", "pt", "in"} else "mm")
        self.unit_combo.hide()
        self.grid_check = QCheckBox()
        self.grid_check.setChecked(bool(general.get("grid_enabled", True)))
        self.grid_check.hide()
        self.snap_check = QCheckBox()
        self.snap_check.setChecked(bool(general.get("snap_enabled", False)))
        self.snap_check.hide()

        hidden = QWidget()
        hidden_layout = QVBoxLayout(hidden)
        hidden_layout.setContentsMargins(0, 0, 0, 0)
        for widget in (self.unit_combo, self.grid_check, self.snap_check):
            hidden_layout.addWidget(widget)
        hidden.hide()
        layout.addWidget(hidden)

        unit_frame, unit_layout = _section("Unit", 76)
        unit_grid = QGridLayout()
        unit_grid.setContentsMargins(0, 0, 0, 0)
        unit_grid.setHorizontalSpacing(5)
        unit_grid.setVerticalSpacing(3)
        unit_buttons = {}

        def select_unit(unit: str) -> None:
            self.unit_combo.setCurrentText(unit)
            for key, button in unit_buttons.items():
                active = key == unit
                button.setChecked(active)
                button.setText(("● " if active else "○ ") + key)
            self.grid_spacing.setSuffix(f" {unit}")

        for index, unit in enumerate(("mm", "cm", "m", "px", "pt", "in")):
            active = self.unit_combo.currentText() == unit
            button = _choice(unit, active, lambda checked=False, selected=unit: select_unit(selected), width=58)
            unit_buttons[unit] = button
            unit_grid.addWidget(button, index // 3, index % 3)
        unit_layout.addLayout(unit_grid)
        layout.addWidget(unit_frame)

        grid_frame, grid_layout = _section("Grid", 74)
        self.grid_spacing = QDoubleSpinBox()
        self.grid_spacing.setRange(0.000001, 1000000.0)
        self.grid_spacing.setDecimals(6)
        self.grid_spacing.setSingleStep(0.5)
        self.grid_spacing.setValue(float(general.get("grid_spacing", 1.0) or 1.0))
        self.grid_spacing.setSuffix(f" {self.unit_combo.currentText()}")
        _style_spin(svg, self.grid_spacing)
        grid_button = _choice("Grid On" if self.grid_check.isChecked() else "Grid Off", self.grid_check.isChecked(), lambda checked=False: None, width=92)

        def toggle_grid() -> None:
            active = not self.grid_check.isChecked()
            self.grid_check.setChecked(active)
            grid_button.setChecked(active)
            grid_button.setText("● Grid On" if active else "○ Grid Off")

        grid_button.clicked.disconnect()
        grid_button.clicked.connect(toggle_grid)
        grid_layout.addWidget(grid_button)
        grid_layout.addWidget(_row("Spacing", self.grid_spacing, 64))
        layout.addWidget(grid_frame)

        text_frame, text_layout = _section("Text", 74)
        self.text_font = QComboBox()
        self.text_font.addItems(list(FONT_CHOICES))
        current_font = str(general.get("text_font", "Times New Roman"))
        self.text_font.setCurrentText(current_font if current_font in FONT_CHOICES else "Times New Roman")
        _style_combo(svg, self.text_font)
        self.text_size = QSpinBox()
        self.text_size.setRange(1, 300)
        self.text_size.setValue(int(general.get("text_size", 12) or 12))
        self.text_size.setSuffix(" pt")
        _style_spin(svg, self.text_size)
        text_layout.addWidget(_row("Font", self.text_font, 64))
        text_layout.addWidget(_row("Size", self.text_size, 64))
        layout.addWidget(text_frame)

        snap_frame, snap_layout = _section("Snap", 50)
        snap_button = _choice("Snap On" if self.snap_check.isChecked() else "Snap Off", self.snap_check.isChecked(), lambda checked=False: None, width=94)

        def toggle_snap() -> None:
            active = not self.snap_check.isChecked()
            self.snap_check.setChecked(active)
            snap_button.setChecked(active)
            snap_button.setText("● Snap On" if active else "○ Snap Off")

        snap_button.clicked.disconnect()
        snap_button.clicked.connect(toggle_snap)
        snap_layout.addWidget(snap_button)
        layout.addWidget(snap_frame)

        view_frame, view_layout = _section("View", 118)
        view_grid = QGridLayout()
        view_grid.setContentsMargins(0, 0, 0, 0)
        view_grid.setHorizontalSpacing(5)
        view_grid.setVerticalSpacing(3)
        startbar_state = self._settings.get("view", {}).get("startbar", {}) if isinstance(self._settings.get("view", {}), dict) else {}
        self._view_buttons = {}
        labels = [("undo", "Undo"), ("redo", "Redo"), ("select", "Select"), ("line", "Line"), ("vector", "Vector"), ("angle", "Angle"), ("text", "Text"), ("grid", "Grid"), ("snap", "Snap"), ("unit", "Unit"), ("ruler", "Ruler"), ("zoom", "Zoom")]
        for index, (key, label) in enumerate(labels):
            checked = bool(startbar_state.get(key, True))
            button = _choice(label, checked, lambda checked=False: None, width=76)
            self._view_buttons[key] = button
            view_grid.addWidget(button, index // 4, index % 4)
        view_layout.addLayout(view_grid)
        layout.addWidget(view_frame)
        layout.addStretch(1)
        _apply_system_font_tree(page)
        return page

    def shortcut_page(self) -> QWidget:
        page = QWidget()
        page.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        hint = QLabel("Shortcut keys")
        _font(hint, 10, bold=True, italic=False)
        hint.setStyleSheet("QLabel {background:#ffffff; border:1px solid #b9c6d6; border-radius:9px; color:#132238; padding:5px 8px;}")
        layout.addWidget(hint)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(2, 2, 2, 2)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)
        shortcuts = self._settings.get("shortcuts", epp.DEFAULT_SHORTCUTS)
        self._shortcut_editors = {}
        for row, (key, label, default, _method) in enumerate(epp.SHORTCUT_SPECS):
            command = QLabel(label)
            _font(command, 9, bold=True, italic=False)
            command.setStyleSheet("QLabel {background:#ffffff; border:1px solid #c7d3e1; border-radius:7px; color:#223a58; padding:3px 6px;}")
            default_label = QLabel(default or "—")
            _font(default_label, 9, bold=True, italic=False)
            default_label.setStyleSheet("QLabel {background:#eef8ff; border:1px solid #c7d3e1; border-radius:7px; color:#39516f; padding:3px 6px;}")
            editor = QKeySequenceEdit()
            editor.setObjectName("ShortcutInput")
            editor.setKeySequence(QKeySequence(str(shortcuts.get(key, default) or "")))
            editor.setFixedHeight(24)
            editor.setStyleSheet("QKeySequenceEdit#ShortcutInput {background:#fffdf0; border:1px solid #b78316; border-radius:7px; color:#132238; font-family:'Times New Roman'; font-size:9px; font-weight:800; padding:1px 6px;}")
            self._shortcut_editors[key] = editor
            grid.addWidget(command, row, 0)
            grid.addWidget(default_label, row, 1)
            grid.addWidget(editor, row, 2)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        _apply_system_font_tree(page)
        return page

    old_init = epp.PropertiesDialog.__init__

    def dialog_init(self, workspace: QWidget) -> None:
        old_init(self, workspace)
        self.resize(720, 460)
        self.setMinimumSize(660, 420)
        _apply_system_font_tree(self)
        for combo in self.findChildren(QComboBox):
            _style_combo(svg, combo)
        for spin in [*self.findChildren(QSpinBox), *self.findChildren(QDoubleSpinBox)]:
            _style_spin(svg, spin)

    epp.PropertiesDialog._general_page = general_page
    epp.PropertiesDialog._shortcut_page = shortcut_page
    if not getattr(epp.PropertiesDialog, "_phase1_dialog_init_wrapped", False):
        epp.PropertiesDialog.__init__ = dialog_init
        epp.PropertiesDialog._phase1_dialog_init_wrapped = True


def _install_textbar(sb, svg) -> None:
    def find_command_bar(window) -> QWidget | None:
        bar = window.findChild(QWidget, "CommandBar")
        return bar if bar is not None and bar.layout() is not None else None

    def make_button(text: str, width: int = 28) -> QPushButton:
        button = QPushButton(text)
        button.setFixedSize(width, 22)
        _font(button, 9, bold=True, italic=False)
        button.setCursor(svg.project_cursor("default"))
        button.setStyleSheet(
            "QPushButton {background:#ffffff; border:1px solid #9fb0c5; border-radius:7px; color:#132238; padding:0px;}"
            "QPushButton:hover {background:#fff4cf; border-color:#ff8a35;}"
        )
        return button

    def ensure_bar(self):
        window = self.window()
        if window is None:
            return None
        command_bar = find_command_bar(window)
        if command_bar is None:
            return None
        existing = command_bar.findChild(QFrame, "InlineTextBar")
        if existing is not None:
            existing.show()
            self._text_toolbar_widget = existing
            self._text_toolbar_enabled = True
            return existing
        layout = command_bar.layout()
        bar = QFrame(command_bar)
        bar.setObjectName("InlineTextBar")
        bar.setFixedHeight(28)
        bar.setMinimumWidth(430)
        bar.setMaximumWidth(560)
        bar.setStyleSheet("QFrame#InlineTextBar {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:.55 #eef8ff, stop:1 #fff5d8); border:1px solid #8fa2bb; border-radius:10px;}")
        row = QHBoxLayout(bar)
        row.setContentsMargins(6, 2, 6, 2)
        row.setSpacing(4)
        combo = QComboBox()
        combo.addItems(list(FONT_CHOICES))
        combo.setFixedSize(140, 22)
        _style_combo(svg, combo)
        row.addWidget(combo)
        size = QSpinBox()
        size.setRange(1, 300)
        size.setValue(12)
        size.setSuffix(" pt")
        _style_spin(svg, size)
        size.setFixedSize(72, 22)
        row.addWidget(size)
        for text, width in (("B", 26), ("I", 26), ("•", 26), ("1.", 30), ("L", 26), ("C", 26), ("R", 26), ("RTL", 40), ("Σ", 28)):
            row.addWidget(make_button(text, width))
        insert_index = max(0, layout.count() - 1)
        layout.insertWidget(insert_index, bar, 0, Qt.AlignmentFlag.AlignVCenter)
        bar.show()
        self._text_toolbar_widget = bar
        self._text_toolbar_enabled = True
        return bar

    def set_visible(self, visible: bool = True, emit: bool = True) -> None:
        bar = ensure_bar(self)
        if bar is not None:
            bar.show()
        self._text_toolbar_enabled = True
        popup = getattr(self, "_popup", None)
        if popup is not None:
            popup.close()
        if emit:
            self.tool_requested.emit("text_on")
            self._set_host_status("Text bar ready")

    old_handle = sb.StartBar._handle_tool_click

    def handle_click(self, key: str) -> None:
        if key == "text":
            set_visible(self, True, True)
            return
        old_handle(self, key)

    sb.StartBar._ensure_text_toolbar = ensure_bar
    sb.StartBar._set_text_toolbar_visible = set_visible
    sb.StartBar._show_text_toolbar = lambda self, key: set_visible(self, True, True)
    sb.StartBar._handle_tool_click = handle_click


def apply_ui_design_phase1_final_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw
    from src.engineers_tools.app import engineering_properties_patch as epp
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_ui_design_phase1_final_patch", "") == PATCH_VERSION:
        return

    _patch_svg_cursors(svg)
    _patch_startbar_icons(sb, svg)
    _patch_file_properties(epp, svg)
    _install_textbar(sb, svg)
    _install_canvas_handle_patch(edw, svg)

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _apply_system_font_tree(self)
        for combo in self.findChildren(QComboBox):
            _style_combo(svg, combo)
        for spin in [*self.findChildren(QSpinBox), *self.findChildren(QDoubleSpinBox)]:
            _style_spin(svg, spin)
        start_bar = getattr(self, "_start_bar_widget", None)
        if start_bar is not None:
            QTimer.singleShot(0, lambda sb=start_bar: sb._set_text_toolbar_visible(True, emit=False))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_ui_design_phase1_final_patch = PATCH_VERSION

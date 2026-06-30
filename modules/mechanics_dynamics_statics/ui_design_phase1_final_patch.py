"""Final phase-1 UI design fixes for controls, Properties, Shortcut Key, Text Bar and SVG cursors."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import (
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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-ui-design-phase1-final-2026-07-01-b"
FONT_CHOICES = ("Times New Roman",)
UNITS = ("mm", "cm", "m", "px", "pt", "in")
VIEW_KEYS = (("undo", "Undo"), ("redo", "Redo"), ("select", "Select"), ("line", "Line"), ("vector", "Vector"), ("angle", "Angle"), ("text", "Text"), ("grid", "Grid"), ("snap", "Snap"), ("unit", "Unit"), ("ruler", "Ruler"), ("zoom", "Zoom"))

TOOL_ICONS = {
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

CURSORS = {
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


def _font(widget, size: int = 9) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(False)
    widget.setFont(font)


def _font_tree(root: QWidget) -> None:
    for widget in [root, *root.findChildren(QWidget)]:
        if isinstance(widget, (QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QKeySequenceEdit)):
            _font(widget, 9)


def _style_spin(svg, spin) -> None:
    up = _asset_url(svg, "spin_up.svg")
    down = _asset_url(svg, "spin_down.svg")
    spin.setFixedHeight(22)
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffdf0;border:1px solid #b78316;border-radius:7px;color:#132238;font-family:'Times New Roman';font-size:9px;font-weight:800;font-style:normal;padding:0 27px 0 5px;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{width:24px;border:0;subcontrol-origin:border;subcontrol-position:top right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffdf0,stop:.55 #ffe894,stop:1 #ffc64f);border-top-right-radius:6px;}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{width:24px;border:0;subcontrol-origin:border;subcontrol-position:bottom right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffdf0,stop:.55 #ffe894,stop:1 #ffc64f);border-bottom-right-radius:6px;}"
        f"QSpinBox::up-arrow,QDoubleSpinBox::up-arrow{{image:url({up});width:17px;height:10px;}}"
        f"QSpinBox::down-arrow,QDoubleSpinBox::down-arrow{{image:url({down});width:17px;height:10px;}}"
    )


def _style_combo(svg, combo: QComboBox) -> None:
    arrow = _asset_url(svg, "combo_down.svg")
    combo.setFixedHeight(22)
    combo.setStyleSheet(
        "QComboBox{background:#fff;border:1px solid #9fb0c5;border-radius:7px;color:#132238;font-family:'Times New Roman';font-size:9px;font-weight:800;font-style:normal;padding:0 28px 0 6px;}"
        "QComboBox::drop-down{width:25px;border:0;subcontrol-origin:border;subcontrol-position:center right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffdf0,stop:.55 #ffe894,stop:1 #ffc64f);border-top-right-radius:6px;border-bottom-right-radius:6px;}"
        f"QComboBox::down-arrow{{image:url({arrow});width:17px;height:10px;}}"
    )


def _button(text: str, checked: bool, width: int = 68) -> QPushButton:
    button = QPushButton(("● " if checked else "○ ") + text)
    button.setCheckable(True)
    button.setChecked(checked)
    button.setFixedSize(width, 22)
    _font(button)
    button.setStyleSheet("QPushButton{background:#fff;border:1px solid #b9c6d6;border-radius:7px;color:#223a58;padding:0 4px;text-align:left;}QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}QPushButton:checked{background:#eaf6ff;border-color:#2f7df6;color:#132238;}")
    return button


def _section(title: str, height: int) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("CompactPropertiesSection")
    frame.setFixedHeight(height)
    frame.setStyleSheet("QFrame#CompactPropertiesSection{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fff,stop:.55 #eef8ff,stop:1 #fff5d8);border:1px solid #b9c6d6;border-radius:10px;}")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(8, 5, 8, 6)
    layout.setSpacing(3)
    label = QLabel(title)
    label.setStyleSheet("QLabel{background:transparent;color:#132238;padding:0;}")
    _font(label, 10)
    layout.addWidget(label)
    return frame, layout


def _row(label_text: str, editor: QWidget, label_width: int = 64) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    label = QLabel(label_text)
    label.setFixedWidth(label_width)
    label.setStyleSheet("QLabel{background:transparent;color:#223a58;}")
    _font(label)
    layout.addWidget(label)
    layout.addWidget(editor, 1)
    return row


def _patch_cursors(svg) -> None:
    svg._CURSOR_ASSET_MAP.update(CURSORS)
    svg._CURSOR_CACHE.clear()
    if not getattr(svg, "_phase1_asset_cursor_wrapped", False):
        original = svg.asset_cursor

        def asset_cursor(file_name: str, fallback, hot_x: int = 8, hot_y: int = 8, max_side: int = 24):
            mapped = {"hand_open.svg": "mouse_cursor.svg", "hand_closed.svg": "mouse_cursor.svg", "hand_pointer.svg": "mouse_cursor.svg", "rotate_cursor.svg": "rotate.svg"}.get(file_name, file_name)
            return original(mapped, fallback, hot_x, hot_y, max_side)

        svg.asset_cursor = asset_cursor
        svg._phase1_asset_cursor_wrapped = True

    def project_cursor(kind: str):
        file_name, hot_x, hot_y, side = svg._CURSOR_ASSET_MAP.get(kind, svg._CURSOR_ASSET_MAP.get("default", ("mouse_cursor.svg", 3, 3, 24)))
        fallback = getattr(svg, "_FALLBACKS", {}).get(kind, Qt.CursorShape.ArrowCursor)
        return svg.asset_cursor(file_name, fallback, hot_x, hot_y, side)

    svg.project_cursor = project_cursor


def _patch_startbar_icons(sb, svg) -> None:
    sb._tool_icon = lambda key: svg.asset_icon(TOOL_ICONS.get(key, "mouse_cursor.svg"))
    sb._mini_zoom_icon = lambda action: svg.asset_icon(TOOL_ICONS.get(action, "zoom.svg"))


def _patch_textbar(sb, svg) -> None:
    def make_textbar(self):
        window = self.window()
        command_bar = window.findChild(QWidget, "CommandBar") if window is not None else None
        if command_bar is None or command_bar.layout() is None:
            return None
        existing = command_bar.findChild(QFrame, "InlineTextBar")
        if existing is not None:
            existing.show()
            return existing
        bar = QFrame(command_bar)
        bar.setObjectName("InlineTextBar")
        bar.setFixedHeight(28)
        bar.setMinimumWidth(430)
        bar.setMaximumWidth(560)
        bar.setStyleSheet("QFrame#InlineTextBar{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fff,stop:.55 #eef8ff,stop:1 #fff5d8);border:1px solid #8fa2bb;border-radius:10px;}")
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
        size.setFixedSize(72, 22)
        _style_spin(svg, size)
        row.addWidget(size)
        for text, width in (("B", 26), ("I", 26), ("•", 26), ("1.", 30), ("L", 26), ("C", 26), ("R", 26), ("RTL", 40), ("Σ", 28)):
            b = QPushButton(text)
            b.setFixedSize(width, 22)
            _font(b)
            b.setStyleSheet("QPushButton{background:#fff;border:1px solid #9fb0c5;border-radius:7px;color:#132238;padding:0;}QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}")
            row.addWidget(b)
        command_bar.layout().insertWidget(max(0, command_bar.layout().count() - 1), bar, 0, Qt.AlignmentFlag.AlignVCenter)
        bar.show()
        return bar

    def set_visible(self, visible: bool = True, emit: bool = True) -> None:
        bar = make_textbar(self)
        if bar is not None:
            bar.show()
        popup = getattr(self, "_popup", None)
        if popup is not None:
            popup.close()
        self._text_toolbar_enabled = True
        if emit:
            self.tool_requested.emit("text_on")
            self._set_host_status("Text bar ready")

    old_handle = sb.StartBar._handle_tool_click

    def handle(self, key: str) -> None:
        if key == "text":
            set_visible(self, True, True)
            return
        old_handle(self, key)

    sb.StartBar._ensure_text_toolbar = make_textbar
    sb.StartBar._set_text_toolbar_visible = set_visible
    sb.StartBar._show_text_toolbar = lambda self, key: set_visible(self, True, True)
    sb.StartBar._handle_tool_click = handle


def _patch_properties(epp, svg) -> None:
    def general_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        general = self._settings.get("general", {})
        self.unit_combo = QComboBox(); self.unit_combo.addItems(list(UNITS)); self.unit_combo.setCurrentText(str(general.get("unit", "mm")) if str(general.get("unit", "mm")) in UNITS else "mm"); self.unit_combo.hide()
        self.grid_check = QCheckBox(); self.grid_check.setChecked(bool(general.get("grid_enabled", True))); self.grid_check.hide()
        self.snap_check = QCheckBox(); self.snap_check.setChecked(bool(general.get("snap_enabled", False))); self.snap_check.hide()
        hidden = QWidget(); hidden_layout = QVBoxLayout(hidden); hidden_layout.setContentsMargins(0, 0, 0, 0)
        for w in (self.unit_combo, self.grid_check, self.snap_check): hidden_layout.addWidget(w)
        hidden.hide(); layout.addWidget(hidden)

        unit_frame, unit_layout = _section("Unit", 76); unit_grid = QGridLayout(); unit_grid.setContentsMargins(0, 0, 0, 0); unit_grid.setHorizontalSpacing(5); unit_grid.setVerticalSpacing(3); unit_buttons = {}
        def select_unit(unit: str) -> None:
            self.unit_combo.setCurrentText(unit)
            for k, b in unit_buttons.items(): b.setChecked(k == unit); b.setText(("● " if k == unit else "○ ") + k)
            self.grid_spacing.setSuffix(f" {unit}")
        for i, unit in enumerate(UNITS):
            b = _button(unit, self.unit_combo.currentText() == unit, 58); b.clicked.connect(lambda checked=False, u=unit: select_unit(u)); unit_buttons[unit] = b; unit_grid.addWidget(b, i // 3, i % 3)
        unit_layout.addLayout(unit_grid); layout.addWidget(unit_frame)

        grid_frame, grid_layout = _section("Grid", 74)
        self.grid_spacing = QDoubleSpinBox(); self.grid_spacing.setRange(0.000001, 1000000.0); self.grid_spacing.setDecimals(6); self.grid_spacing.setSingleStep(0.5); self.grid_spacing.setValue(float(general.get("grid_spacing", 1.0) or 1.0)); self.grid_spacing.setSuffix(f" {self.unit_combo.currentText()}"); _style_spin(svg, self.grid_spacing)
        grid_button = _button("Grid On" if self.grid_check.isChecked() else "Grid Off", self.grid_check.isChecked(), 92)
        def toggle_grid() -> None:
            active = not self.grid_check.isChecked(); self.grid_check.setChecked(active); grid_button.setChecked(active); grid_button.setText("● Grid On" if active else "○ Grid Off")
        grid_button.clicked.connect(toggle_grid); grid_layout.addWidget(grid_button); grid_layout.addWidget(_row("Spacing", self.grid_spacing)); layout.addWidget(grid_frame)

        text_frame, text_layout = _section("Text", 74)
        self.text_font = QComboBox(); self.text_font.addItems(list(FONT_CHOICES)); self.text_font.setCurrentText("Times New Roman"); _style_combo(svg, self.text_font)
        self.text_size = QSpinBox(); self.text_size.setRange(1, 300); self.text_size.setValue(int(general.get("text_size", 12) or 12)); self.text_size.setSuffix(" pt"); _style_spin(svg, self.text_size)
        text_layout.addWidget(_row("Font", self.text_font)); text_layout.addWidget(_row("Size", self.text_size)); layout.addWidget(text_frame)

        snap_frame, snap_layout = _section("Snap", 50); snap_button = _button("Snap On" if self.snap_check.isChecked() else "Snap Off", self.snap_check.isChecked(), 94)
        def toggle_snap() -> None:
            active = not self.snap_check.isChecked(); self.snap_check.setChecked(active); snap_button.setChecked(active); snap_button.setText("● Snap On" if active else "○ Snap Off")
        snap_button.clicked.connect(toggle_snap); snap_layout.addWidget(snap_button); layout.addWidget(snap_frame)

        view_frame, view_layout = _section("View", 118); view_grid = QGridLayout(); view_grid.setContentsMargins(0, 0, 0, 0); view_grid.setHorizontalSpacing(5); view_grid.setVerticalSpacing(3)
        self._view_buttons = {}; startbar_state = self._settings.get("view", {}).get("startbar", {}) if isinstance(self._settings.get("view", {}), dict) else {}
        for i, (key, label) in enumerate(VIEW_KEYS):
            b = _button(label, bool(startbar_state.get(key, True)), 76); self._view_buttons[key] = b; view_grid.addWidget(b, i // 4, i % 4)
        view_layout.addLayout(view_grid); layout.addWidget(view_frame); layout.addStretch(1); _font_tree(page); return page

    def shortcut_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(4)
        hint = QLabel("Shortcut keys"); _font(hint, 10); hint.setStyleSheet("QLabel{background:#fff;border:1px solid #b9c6d6;border-radius:9px;color:#132238;padding:5px 8px;}"); layout.addWidget(hint)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame); content = QWidget(); grid = QGridLayout(content); grid.setContentsMargins(2, 2, 2, 2); grid.setHorizontalSpacing(6); grid.setVerticalSpacing(4)
        shortcuts = self._settings.get("shortcuts", epp.DEFAULT_SHORTCUTS); self._shortcut_editors = {}
        for row, (key, label, default, _method) in enumerate(epp.SHORTCUT_SPECS):
            command = QLabel(label); _font(command); command.setStyleSheet("QLabel{background:#fff;border:1px solid #c7d3e1;border-radius:7px;color:#223a58;padding:3px 6px;}")
            default_label = QLabel(default or "—"); _font(default_label); default_label.setStyleSheet("QLabel{background:#eef8ff;border:1px solid #c7d3e1;border-radius:7px;color:#39516f;padding:3px 6px;}")
            editor = QKeySequenceEdit(); editor.setObjectName("ShortcutInput"); editor.setKeySequence(QKeySequence(str(shortcuts.get(key, default) or ""))); editor.setFixedHeight(24); editor.setStyleSheet("QKeySequenceEdit#ShortcutInput{background:#fffdf0;border:1px solid #b78316;border-radius:7px;color:#132238;font-family:'Times New Roman';font-size:9px;font-weight:800;padding:1px 6px;}")
            self._shortcut_editors[key] = editor; grid.addWidget(command, row, 0); grid.addWidget(default_label, row, 1); grid.addWidget(editor, row, 2)
        scroll.setWidget(content); layout.addWidget(scroll, 1); _font_tree(page); return page

    old_init = epp.PropertiesDialog.__init__
    def dialog_init(self, workspace: QWidget) -> None:
        old_init(self, workspace); self.resize(720, 460); self.setMinimumSize(660, 420); _font_tree(self)
        for c in self.findChildren(QComboBox): _style_combo(svg, c)
        for s in [*self.findChildren(QSpinBox), *self.findChildren(QDoubleSpinBox)]: _style_spin(svg, s)

    epp.PropertiesDialog._general_page = general_page
    epp.PropertiesDialog._shortcut_page = shortcut_page
    if not getattr(epp.PropertiesDialog, "_phase1_dialog_init_wrapped", False):
        epp.PropertiesDialog.__init__ = dialog_init
        epp.PropertiesDialog._phase1_dialog_init_wrapped = True


def apply_ui_design_phase1_final_patch() -> None:
    from . import final_cursor_properties_textbar_patch as fcp
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw
    from src.engineers_tools.app import engineering_properties_patch as epp
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_ui_design_phase1_final_patch", "") == PATCH_VERSION:
        return

    _patch_cursors(svg)
    fcp._style_spin = _style_spin
    fcp._style_combo = _style_combo
    fcp._install_inline_textbar = _patch_textbar
    _patch_startbar_icons(sb, svg)
    _patch_textbar(sb, svg)
    _patch_properties(epp, svg)

    old_init = edw.EngineeringDesignWorkspace.__init__
    def workspace_init(self, module) -> None:
        old_init(self, module); _font_tree(self)
        for c in self.findChildren(QComboBox): _style_combo(svg, c)
        for s in [*self.findChildren(QSpinBox), *self.findChildren(QDoubleSpinBox)]: _style_spin(svg, s)
        start_bar = getattr(self, "_start_bar_widget", None)
        if start_bar is not None:
            QTimer.singleShot(0, lambda sb=start_bar: sb._set_text_toolbar_visible(True, emit=False))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_ui_design_phase1_final_patch = PATCH_VERSION

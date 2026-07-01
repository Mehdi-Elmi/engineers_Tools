"""Phase-2 UI refinements requested after phase-1 visual test."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence
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
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-ui-design-phase2-refinement-2026-07-01-b"
FONT_CHOICES = ("Times New Roman",)
UNITS = ("mm", "cm", "m", "px", "pt", "in")
VIEW_KEYS = (("undo", "Undo"), ("redo", "Redo"), ("select", "Select"), ("line", "Line"), ("vector", "Vector"), ("angle", "Angle"), ("text", "Text"), ("grid", "Grid"), ("snap", "Snap"), ("unit", "Unit"), ("ruler", "Ruler"), ("zoom", "Zoom"))
CURSOR_OVERRIDES = {
    "rotate": ("rotate.svg", 24, 24, 54),
    "rotate_drag": ("rotate.svg", 24, 24, 54),
    "resize_n": ("resize_vertical.svg", 28, 28, 56),
    "resize_s": ("resize_vertical.svg", 28, 28, 56),
    "resize_e": ("resize_horizontal.svg", 28, 28, 56),
    "resize_w": ("resize_horizontal.svg", 28, 28, 56),
    "resize_ne": ("corner_resize_b.svg", 28, 28, 56),
    "resize_sw": ("corner_resize_b.svg", 28, 28, 56),
    "resize_nw": ("corner_resize_a.svg", 28, 28, 56),
    "resize_se": ("corner_resize_a.svg", 28, 28, 56),
    "resize_horizontal": ("resize_horizontal.svg", 28, 28, 56),
    "resize_vertical": ("resize_vertical.svg", 28, 28, 56),
    "resize_diag_f": ("corner_resize_a.svg", 28, 28, 56),
    "resize_diag_b": ("corner_resize_b.svg", 28, 28, 56),
    "resize_fdiag": ("corner_resize_a.svg", 28, 28, 56),
    "resize_bdiag": ("corner_resize_b.svg", 28, 28, 56),
}


def _asset_url(svg, name: str) -> str:
    return svg._asset_url(name) if hasattr(svg, "_asset_url") else ""


def _font(widget, size: int = 10) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(False)
    widget.setFont(font)


def _font_tree(root: QWidget) -> None:
    for widget in [root, *root.findChildren(QWidget)]:
        if isinstance(widget, (QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QKeySequenceEdit)):
            _font(widget, 10)


def _style_spin(svg, spin) -> None:
    up = _asset_url(svg, "spin_up.svg")
    down = _asset_url(svg, "spin_down.svg")
    spin.setFixedHeight(26)
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffdf6;border:1px solid #c29122;border-radius:8px;color:#132238;font-family:'Times New Roman';font-size:10px;font-weight:800;font-style:normal;padding:1px 31px 1px 7px;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{width:28px;border:0;subcontrol-origin:border;subcontrol-position:top right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);border-top-right-radius:7px;}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{width:28px;border:0;subcontrol-origin:border;subcontrol-position:bottom right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);border-bottom-right-radius:7px;}"
        f"QSpinBox::up-arrow,QDoubleSpinBox::up-arrow{{image:url({up});width:19px;height:12px;}}"
        f"QSpinBox::down-arrow,QDoubleSpinBox::down-arrow{{image:url({down});width:19px;height:12px;}}"
    )


def _style_combo(svg, combo: QComboBox) -> None:
    arrow = _asset_url(svg, "combo_down.svg")
    combo.setFixedHeight(26)
    combo.setStyleSheet(
        "QComboBox{background:#ffffff;border:1px solid #9fb0c5;border-radius:8px;color:#132238;font-family:'Times New Roman';font-size:10px;font-weight:800;font-style:normal;padding:1px 32px 1px 8px;}"
        "QComboBox::drop-down{width:29px;border:0;subcontrol-origin:border;subcontrol-position:center right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);border-top-right-radius:7px;border-bottom-right-radius:7px;}"
        f"QComboBox::down-arrow{{image:url({arrow});width:19px;height:12px;}}"
    )


def _button(text: str, checked: bool, width: int = 82) -> QPushButton:
    button = QPushButton(("● " if checked else "○ ") + text)
    button.setCheckable(True)
    button.setChecked(checked)
    button.setFixedSize(width, 26)
    _font(button, 10)
    button.setStyleSheet("QPushButton{background:#fff;border:1px solid #b9c6d6;border-radius:8px;color:#223a58;padding:0 5px;text-align:left;}QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}QPushButton:checked{background:#eaf6ff;border-color:#2f7df6;color:#132238;}")
    return button


def _clear_button(editor: QKeySequenceEdit) -> QPushButton:
    button = QPushButton("×")
    button.setFixedSize(28, 24)
    button.setToolTip("Remove shortcut")
    _font(button, 12)
    button.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffdf6,stop:.55 #ffdf79,stop:1 #ffb83d);border:1px solid #9b6d12;border-radius:8px;color:#132238;padding:0;}QPushButton:hover{background:#ffcf59;border-color:#ffffff;}QPushButton:pressed{background:#e39420;padding-top:1px;}")
    button.clicked.connect(lambda: editor.setKeySequence(QKeySequence()))
    return button


def _section(title: str, height: int) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("BalancedPropertiesSection")
    frame.setMinimumHeight(height)
    frame.setStyleSheet("QFrame#BalancedPropertiesSection{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fff,stop:.55 #eef8ff,stop:1 #fff5d8);border:1px solid #b9c6d6;border-radius:11px;}")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 7, 10, 8)
    layout.setSpacing(5)
    label = QLabel(title)
    label.setStyleSheet("QLabel{background:transparent;color:#132238;padding:0;}")
    _font(label, 11)
    layout.addWidget(label)
    return frame, layout


def _row(label_text: str, editor: QWidget, label_width: int = 82) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(7)
    label = QLabel(label_text)
    label.setFixedWidth(label_width)
    label.setStyleSheet("QLabel{background:transparent;color:#223a58;}")
    _font(label, 10)
    layout.addWidget(label)
    layout.addWidget(editor, 1)
    return row


def _remove_legacy_text_subbars(root: QWidget) -> None:
    for bar in root.findChildren(QFrame, "TextSubBar"):
        bar.hide()
        bar.setParent(None)
        bar.deleteLater()


def _install_textbar(sb, svg) -> None:
    def make_textbar(self):
        window = self.window()
        if window is None:
            return None
        _remove_legacy_text_subbars(window)
        command_bar = window.findChild(QWidget, "CommandBar")
        if command_bar is None or command_bar.layout() is None:
            return None
        existing = command_bar.findChild(QFrame, "InlineTextBar")
        if existing is not None:
            existing.setFixedHeight(36)
            existing.setMinimumWidth(660)
            existing.setMaximumWidth(880)
            existing.show()
            _remove_legacy_text_subbars(window)
            return existing
        bar = QFrame(command_bar)
        bar.setObjectName("InlineTextBar")
        bar.setFixedHeight(36)
        bar.setMinimumWidth(660)
        bar.setMaximumWidth(880)
        bar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bar.setStyleSheet("QFrame#InlineTextBar{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fff,stop:.52 #eef8ff,stop:1 #fff1c8);border:1px solid #8fa2bb;border-radius:12px;}")
        row = QHBoxLayout(bar)
        row.setContentsMargins(9, 4, 9, 4)
        row.setSpacing(6)
        combo = QComboBox(); combo.addItems(list(FONT_CHOICES)); combo.setCurrentText("Times New Roman"); combo.setFixedSize(176, 28); _style_combo(svg, combo); row.addWidget(combo)
        size = QSpinBox(); size.setRange(1, 300); size.setValue(12); size.setSuffix(" pt"); size.setFixedSize(90, 28); _style_spin(svg, size); row.addWidget(size)
        for text, width in (("B", 32), ("I", 32), ("•", 32), ("1.", 36), ("L", 32), ("C", 32), ("R", 32), ("J", 32), ("LS", 42), ("LTR", 48), ("RTL", 48), ("Σ", 34)):
            b = QPushButton(text); b.setFixedSize(width, 28); _font(b, 10); b.setStyleSheet("QPushButton{background:#fff;border:1px solid #9fb0c5;border-radius:8px;color:#132238;padding:0;}QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"); row.addWidget(b)
        command_bar.layout().insertWidget(max(0, command_bar.layout().count() - 1), bar, 0, Qt.AlignmentFlag.AlignVCenter)
        bar.show()
        _remove_legacy_text_subbars(window)
        return bar

    def set_visible(self, visible: bool = True, emit: bool = True) -> None:
        bar = make_textbar(self)
        if bar is not None:
            bar.show()
        popup = getattr(self, "_popup", None)
        if popup is not None:
            popup.close()
        _remove_legacy_text_subbars(self.window())
        self._text_toolbar_enabled = True
        if emit:
            self.tool_requested.emit("text_on")
            self._set_host_status("Text bar ready")

    old_handle = sb.StartBar._handle_tool_click
    old_show_event = sb.StartBar.showEvent

    def handle(self, key: str) -> None:
        if key == "text":
            set_visible(self, True, True)
            return
        old_handle(self, key)
        _remove_legacy_text_subbars(self.window())

    def show_event(self, event) -> None:
        old_show_event(self, event)
        QTimer.singleShot(0, lambda s=self: _remove_legacy_text_subbars(s.window()))
        QTimer.singleShot(0, lambda s=self: s._set_text_toolbar_visible(True, emit=False))

    sb.StartBar._ensure_text_toolbar = make_textbar
    sb.StartBar._set_text_toolbar_visible = set_visible
    sb.StartBar._show_text_toolbar = lambda self, key: set_visible(self, True, True)
    sb.StartBar._handle_tool_click = handle
    if not getattr(sb.StartBar, "_phase2_textbar_show_wrapped", False):
        sb.StartBar.showEvent = show_event
        sb.StartBar._phase2_textbar_show_wrapped = True


def _install_properties(epp, svg) -> None:
    def general_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(8)
        general = self._settings.get("general", {})
        self.unit_combo = QComboBox(); self.unit_combo.addItems(list(UNITS)); self.unit_combo.setCurrentText(str(general.get("unit", "mm")) if str(general.get("unit", "mm")) in UNITS else "mm"); self.unit_combo.hide()
        self.grid_check = QCheckBox(); self.grid_check.setChecked(bool(general.get("grid_enabled", True))); self.grid_check.hide()
        self.snap_check = QCheckBox(); self.snap_check.setChecked(bool(general.get("snap_enabled", False))); self.snap_check.hide()
        hidden = QWidget(); hidden_layout = QVBoxLayout(hidden); hidden_layout.setContentsMargins(0, 0, 0, 0)
        for w in (self.unit_combo, self.grid_check, self.snap_check): hidden_layout.addWidget(w)
        hidden.hide(); layout.addWidget(hidden)

        unit_frame, unit_layout = _section("Unit", 92); unit_grid = QGridLayout(); unit_grid.setContentsMargins(0, 0, 0, 0); unit_grid.setHorizontalSpacing(7); unit_grid.setVerticalSpacing(5); unit_buttons = {}
        def select_unit(unit: str) -> None:
            self.unit_combo.setCurrentText(unit)
            for k, b in unit_buttons.items(): b.setChecked(k == unit); b.setText(("● " if k == unit else "○ ") + k)
            self.grid_spacing.setSuffix(f" {unit}")
        for i, unit in enumerate(UNITS):
            b = _button(unit, self.unit_combo.currentText() == unit, 58); b.clicked.connect(lambda checked=False, u=unit: select_unit(u)); unit_buttons[unit] = b; unit_grid.addWidget(b, i // 3, i % 3)
        unit_layout.addLayout(unit_grid); layout.addWidget(unit_frame)

        grid_frame, grid_layout = _section("Grid", 92)
        self.grid_spacing = QDoubleSpinBox(); self.grid_spacing.setRange(0.000001, 1000000.0); self.grid_spacing.setDecimals(6); self.grid_spacing.setSingleStep(0.5); self.grid_spacing.setValue(float(general.get("grid_spacing", 1.0) or 1.0)); self.grid_spacing.setSuffix(f" {self.unit_combo.currentText()}"); _style_spin(svg, self.grid_spacing)
        grid_button = _button("Grid On" if self.grid_check.isChecked() else "Grid Off", self.grid_check.isChecked(), 102)
        def toggle_grid() -> None:
            active = not self.grid_check.isChecked(); self.grid_check.setChecked(active); grid_button.setChecked(active); grid_button.setText("● Grid On" if active else "○ Grid Off")
        grid_button.clicked.connect(toggle_grid); grid_layout.addWidget(grid_button); grid_layout.addWidget(_row("Spacing", self.grid_spacing, 76)); layout.addWidget(grid_frame)

        text_frame, text_layout = _section("Text", 92)
        self.text_font = QComboBox(); self.text_font.addItems(list(FONT_CHOICES)); self.text_font.setCurrentText("Times New Roman"); _style_combo(svg, self.text_font)
        self.text_size = QSpinBox(); self.text_size.setRange(1, 300); self.text_size.setValue(int(general.get("text_size", 12) or 12)); self.text_size.setSuffix(" pt"); _style_spin(svg, self.text_size)
        text_layout.addWidget(_row("Font", self.text_font, 76)); text_layout.addWidget(_row("Size", self.text_size, 76)); layout.addWidget(text_frame)

        snap_frame, snap_layout = _section("Snap", 64); snap_button = _button("Snap On" if self.snap_check.isChecked() else "Snap Off", self.snap_check.isChecked(), 102)
        def toggle_snap() -> None:
            active = not self.snap_check.isChecked(); self.snap_check.setChecked(active); snap_button.setChecked(active); snap_button.setText("● Snap On" if active else "○ Snap Off")
        snap_button.clicked.connect(toggle_snap); snap_layout.addWidget(snap_button); layout.addWidget(snap_frame)

        view_frame, view_layout = _section("View", 154); view_grid = QGridLayout(); view_grid.setContentsMargins(0, 0, 0, 0); view_grid.setHorizontalSpacing(7); view_grid.setVerticalSpacing(5)
        self._view_buttons = {}; startbar_state = self._settings.get("view", {}).get("startbar", {}) if isinstance(self._settings.get("view", {}), dict) else {}
        for i, (key, label) in enumerate(VIEW_KEYS):
            b = _button(label, bool(startbar_state.get(key, True)), 78); self._view_buttons[key] = b; view_grid.addWidget(b, i // 3, i % 3)
        view_layout.addLayout(view_grid); layout.addWidget(view_frame); layout.addStretch(1); _font_tree(page); return page

    def shortcut_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(7)
        hint = QLabel("Shortcut keys"); _font(hint, 11); hint.setStyleSheet("QLabel{background:#fff;border:1px solid #b9c6d6;border-radius:10px;color:#132238;padding:7px 9px;}"); layout.addWidget(hint)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame); content = QWidget(); grid = QGridLayout(content); grid.setContentsMargins(2, 2, 2, 2); grid.setHorizontalSpacing(7); grid.setVerticalSpacing(5)
        shortcuts = self._settings.get("shortcuts", epp.DEFAULT_SHORTCUTS); self._shortcut_editors = {}
        for row, (key, label, default, _method) in enumerate(epp.SHORTCUT_SPECS):
            command = QLabel(label); _font(command, 10); command.setStyleSheet("QLabel{background:#fff;border:1px solid #c7d3e1;border-radius:8px;color:#223a58;padding:4px 7px;}")
            default_label = QLabel(default or "—"); _font(default_label, 10); default_label.setStyleSheet("QLabel{background:#eef8ff;border:1px solid #c7d3e1;border-radius:8px;color:#39516f;padding:4px 7px;}")
            editor = QKeySequenceEdit(); editor.setObjectName("ShortcutInput"); editor.setKeySequence(QKeySequence(str(shortcuts.get(key, default) or ""))); editor.setFixedHeight(26); editor.setStyleSheet("QKeySequenceEdit#ShortcutInput{background:#fffdf6;border:1px solid #c29122;border-radius:8px;color:#132238;font-family:'Times New Roman';font-size:10px;font-weight:800;padding:1px 7px;}")
            self._shortcut_editors[key] = editor; grid.addWidget(command, row, 0); grid.addWidget(default_label, row, 1); grid.addWidget(editor, row, 2); grid.addWidget(_clear_button(editor), row, 3)
        scroll.setWidget(content); layout.addWidget(scroll, 1); _font_tree(page); return page

    old_init = epp.PropertiesDialog.__init__
    def dialog_init(self, workspace: QWidget) -> None:
        old_init(self, workspace); self.resize(600, 540); self.setMinimumSize(580, 500); _font_tree(self)
        for c in self.findChildren(QComboBox): _style_combo(svg, c)
        for s in [*self.findChildren(QSpinBox), *self.findChildren(QDoubleSpinBox)]: _style_spin(svg, s)

    epp.PropertiesDialog._general_page = general_page
    epp.PropertiesDialog._shortcut_page = shortcut_page
    if not getattr(epp.PropertiesDialog, "_phase2_dialog_init_wrapped", False):
        epp.PropertiesDialog.__init__ = dialog_init
        epp.PropertiesDialog._phase2_dialog_init_wrapped = True


def apply_ui_design_phase2_refinement_patch() -> None:
    from . import final_cursor_properties_textbar_patch as fcp
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw
    from src.engineers_tools.app import engineering_properties_patch as epp
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_ui_design_phase2_refinement_patch", "") == PATCH_VERSION:
        return

    svg._CURSOR_ASSET_MAP.update(CURSOR_OVERRIDES)
    svg._CURSOR_CACHE.clear()
    fcp._CURSOR_ASSET_OVERRIDES.update(CURSOR_OVERRIDES)
    fcp._style_spin = _style_spin
    fcp._style_combo = _style_combo
    _install_textbar(sb, svg)
    _install_properties(epp, svg)

    old_init = edw.EngineeringDesignWorkspace.__init__
    def workspace_init(self, module) -> None:
        old_init(self, module); _font_tree(self); _remove_legacy_text_subbars(self)
        for c in self.findChildren(QComboBox): _style_combo(svg, c)
        for s in [*self.findChildren(QSpinBox), *self.findChildren(QDoubleSpinBox)]: _style_spin(svg, s)
        start_bar = getattr(self, "_start_bar_widget", None)
        if start_bar is not None:
            QTimer.singleShot(0, lambda sb=start_bar: sb._set_text_toolbar_visible(True, emit=False))
            QTimer.singleShot(0, lambda root=self: _remove_legacy_text_subbars(root))
            QTimer.singleShot(120, lambda root=self: _remove_legacy_text_subbars(root))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_ui_design_phase2_refinement_patch = PATCH_VERSION
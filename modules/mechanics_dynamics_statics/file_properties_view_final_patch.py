"""Final File Properties > General layout: Unit, Grid, Text, Snap, View."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QPushButton, QSpinBox, QVBoxLayout, QWidget

PATCH_VERSION = "engineering-file-properties-view-final-2026-06-30-a"


def apply_file_properties_view_final_patch() -> None:
    from . import file_properties_general_patch as fpg
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw
    from src.engineers_tools.app import engineering_properties_patch as epp

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_file_properties_view_final_patch", "") == PATCH_VERSION:
        return

    old_apply = epp._apply_settings

    def no_collapse(self, event) -> None:
        QFrame.mousePressEvent(self, event)

    def style_spin(spin) -> None:
        styler = getattr(svg, "_style_spin", None)
        if callable(styler):
            styler(spin)
        else:
            spin.setStyleSheet("QSpinBox,QDoubleSpinBox{background:#fff9de;border:1px solid #b38621;border-radius:7px;color:#132238;font-weight:800;padding-right:22px;}")

    def text_block(dialog, general: dict):
        section = fpg._WaveSection("Text", dialog, collapsed=False, open_height=88)
        dialog.text_font = QComboBox()
        dialog.text_font.addItems(list(getattr(svg, "FONT_CHOICES", ("Times New Roman", "Arial", "Cambria Math"))))
        current = str(general.get("text_font", "Times New Roman"))
        dialog.text_font.setCurrentText(current if dialog.text_font.findText(current) >= 0 else "Times New Roman")
        dialog.text_font.setFixedHeight(25)
        dialog.text_size = QSpinBox()
        dialog.text_size.setRange(1, 300)
        dialog.text_size.setValue(int(general.get("text_size", 12) or 12))
        dialog.text_size.setSuffix(" pt")
        dialog.text_size.setFixedHeight(25)
        style_spin(dialog.text_size)
        section.add_body_widget(fpg._row("Font", dialog.text_font))
        section.add_body_widget(fpg._row("Size", dialog.text_size))
        return section

    def snap_block(dialog, general: dict):
        section = fpg._WaveSection("Snap", dialog, collapsed=False, open_height=60)
        current = bool(general.get("snap_enabled", False))
        dialog.snap_check.setChecked(current)
        button = fpg._choice_button("Snap On" if current else "Snap Off", current, lambda checked=False: None, width=104)
        def toggle() -> None:
            active = not dialog.snap_check.isChecked()
            dialog.snap_check.setChecked(active)
            button.setChecked(active)
            button.setIcon(fpg._radio_icon(active))
            button.setText("Snap On" if active else "Snap Off")
        button.clicked.connect(toggle)
        section.add_body_widget(button)
        return section

    def view_block(dialog, settings: dict):
        section = fpg._WaveSection("View", dialog, collapsed=False, open_height=126)
        content = QWidget()
        content.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        grid = QGridLayout(content)
        grid.setContentsMargins(2, 0, 2, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(2)
        view = settings.get("view", {}) if isinstance(settings, dict) else {}
        state = view.get("startbar", {}) if isinstance(view, dict) else {}
        dialog._view_buttons = {}
        items = [("text_toolbar", "Text Bar")]
        try:
            items.extend(fpg._view_items(dialog.workspace))
        except Exception:
            pass
        seen = set()
        row = 0
        for key, label in items:
            if key in seen:
                continue
            seen.add(key)
            default = bool(getattr(getattr(dialog.workspace, "_start_bar_widget", None), "_text_toolbar_enabled", False)) if key == "text_toolbar" else True
            checked = bool(state.get(key, default))
            def toggle(_checked=False, selected=key):
                button = dialog._view_buttons[selected]
                button.setIcon(fpg._radio_icon(button.isChecked()))
            button = fpg._choice_button(label, checked, toggle, width=92)
            dialog._view_buttons[key] = button
            grid.addWidget(button, row // 3, row % 3)
            row += 1
        section.add_body_widget(content)
        return section

    def general_page(self) -> QWidget:
        page = QWidget()
        page.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        general = self._settings.get("general", {})
        self.unit_combo = QComboBox(); self.unit_combo.addItems(list(fpg.UNITS)); self.unit_combo.setCurrentText(str(general.get("unit", "mm")) if str(general.get("unit", "mm")) in fpg.UNITS else "mm"); self.unit_combo.hide()
        self.grid_check = QCheckBox(); self.grid_check.setChecked(bool(general.get("grid_enabled", True))); self.grid_check.hide()
        self.snap_check = QCheckBox(); self.snap_check.setChecked(bool(general.get("snap_enabled", False))); self.snap_check.hide()
        self.grid_spacing = QDoubleSpinBox(); self.grid_spacing.setRange(0.000001, 1000000.0); self.grid_spacing.setDecimals(6); self.grid_spacing.setSingleStep(0.5); self.grid_spacing.setValue(float(general.get("grid_spacing", 1.0) or 1.0)); style_spin(self.grid_spacing)
        hidden = QWidget(); hidden_layout = QVBoxLayout(hidden); hidden_layout.setContentsMargins(0, 0, 0, 0)
        for widget in (self.unit_combo, self.grid_check, self.snap_check):
            hidden_layout.addWidget(widget)
        hidden.hide(); layout.addWidget(hidden)
        layout.addWidget(fpg._unit_block(self, general))
        layout.addWidget(fpg._grid_block(self, general))
        layout.addWidget(text_block(self, general))
        layout.addWidget(snap_block(self, general))
        layout.addWidget(view_block(self, self._settings))
        layout.addStretch(1)
        return page

    def apply_settings(workspace, settings: dict, reinstall_shortcuts: bool = True) -> None:
        old_apply(workspace, settings, reinstall_shortcuts=reinstall_shortcuts)
        start_bar = getattr(workspace, "_start_bar_widget", None)
        if start_bar is None:
            return
        view = settings.get("view", {}) if isinstance(settings, dict) else {}
        state = view.get("startbar", {}) if isinstance(view, dict) else {}
        setter = getattr(start_bar, "_set_text_toolbar_visible", None)
        if callable(setter) and "text_toolbar" in state:
            setter(bool(state.get("text_toolbar")), False)

    fpg._WaveSection.mousePressEvent = no_collapse
    epp.PropertiesDialog._general_page = general_page
    epp._apply_settings = apply_settings
    edw.EngineeringDesignWorkspace._engineering_file_properties_view_final_patch = PATCH_VERSION

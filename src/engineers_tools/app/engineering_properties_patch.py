"""Properties dialog and settings patch for Engineering Design Tools."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFontComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
    QSpinBox,
)

VERSION = "properties-settings-1"
UNITS = ("mm", "cm", "m", "px", "pt", "in")
SHORTCUT_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("new_file", "New File", "Ctrl+N", "_new_file"),
    ("open_file", "Open File", "Ctrl+O", "_open_file"),
    ("save_file", "Save", "Ctrl+S", "_save_file"),
    ("save_as_file", "Save As", "Ctrl+Shift+S", "_save_as_file"),
    ("page_setup", "Page Setup", "", "_page_setup"),
    ("print_setup", "Print Setup", "Ctrl+P", "_print_setup"),
    ("properties", "Properties", "", "_file_properties"),
    ("undo", "Undo", "Ctrl+Z", "_undo"),
    ("redo", "Redo", "Ctrl+Y", "_redo"),
    ("redo_alt", "Redo Alt", "Ctrl+Shift+Z", "_redo"),
    ("copy", "Copy", "Ctrl+C", "_copy"),
    ("cut", "Cut", "Ctrl+X", "_cut"),
    ("paste", "Paste", "Ctrl+V", "_paste"),
    ("delete", "Delete", "Delete", "_delete"),
    ("delete_alt", "Delete Alt", "Backspace", "_delete"),
    ("select_all", "Select All", "Ctrl+A", "_select_all"),
    ("repeat_last", "Repeat Last Tool", "Ctrl+R", "_repeat_last_tools"),
    ("group", "Group", "Ctrl+G", "_group_selection"),
    ("ungroup", "Ungroup", "Ctrl+Shift+G", "_ungroup_selection"),
    ("bring_front", "Bring To Front", "", "_bring_to_front"),
    ("send_back", "Send To Back", "", "_send_to_back"),
    ("move", "Move", "", "_move"),
    ("rotate", "Rotate", "", "_rotation"),
)
DEFAULT_SHORTCUTS = {key: sequence for key, _label, sequence, _method in SHORTCUT_SPECS}


def _settings_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA")
    base = Path(root) if root else Path.home() / "AppData" / "Local"
    path = base / "EngineerTools" / "settings"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _auto_settings_path() -> Path:
    return _settings_dir() / "engineer_tools_properties.etprops"


def _default_settings(workspace=None) -> dict[str, Any]:
    start_bar = getattr(workspace, "_start_bar_widget", None)
    view_state = getattr(workspace, "_view_state", {}) if workspace is not None else {}
    return {
        "version": 1,
        "general": {
            "unit": getattr(start_bar, "_unit", "mm"),
            "grid_enabled": bool(getattr(start_bar, "_grid_enabled", view_state.get("grid", True))),
            "grid_spacing": float(getattr(start_bar, "_grid_spacing", 4.0)),
            "snap_enabled": bool(view_state.get("snap", False)),
            "text_font": str(getattr(workspace, "_default_text_font", "Times New Roman")),
            "text_size": int(getattr(workspace, "_default_text_size", 12)),
        },
        "shortcuts": dict(DEFAULT_SHORTCUTS),
        "page_setup": dict(getattr(workspace, "_page_setup_settings", {}) or {}),
        "print_setup": dict(getattr(workspace, "_print_settings", {}) or {}),
    }


def _merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def _read_settings(path: Path, workspace=None) -> dict[str, Any]:
    settings = _default_settings(workspace)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _merge(settings, data)
        except Exception as error:  # noqa: BLE001
            logging.exception("engineering_properties_patch: read failed %s: %s", path, error)
    return settings


def _write_settings(path: Path, settings: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def _collect_settings(workspace) -> dict[str, Any]:
    settings = _default_settings(workspace)
    existing = getattr(workspace, "_properties_settings", None)
    if isinstance(existing, dict):
        _merge(settings, existing)
    start_bar = getattr(workspace, "_start_bar_widget", None)
    view_state = getattr(workspace, "_view_state", {})
    settings["general"].update(
        {
            "unit": getattr(start_bar, "_unit", settings["general"]["unit"]),
            "grid_enabled": bool(getattr(start_bar, "_grid_enabled", view_state.get("grid", True))),
            "grid_spacing": float(getattr(start_bar, "_grid_spacing", settings["general"]["grid_spacing"])),
            "snap_enabled": bool(view_state.get("snap", settings["general"]["snap_enabled"])),
            "text_font": str(getattr(workspace, "_default_text_font", settings["general"]["text_font"])),
            "text_size": int(getattr(workspace, "_default_text_size", settings["general"]["text_size"])),
        }
    )
    settings["page_setup"] = dict(getattr(workspace, "_page_setup_settings", settings.get("page_setup", {})) or {})
    settings["print_setup"] = dict(getattr(workspace, "_print_settings", settings.get("print_setup", {})) or {})
    return settings


def _style_dialog(widget: QWidget) -> None:
    widget.setStyleSheet(
        "QWidget#PropertiesShell{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.50 #edf6ff,stop:1 #dbe6f4);border:1px solid #8fa2bb;border-radius:16px;}"
        "QWidget#PropertiesHeader{background:#132238;border-top-left-radius:16px;border-top-right-radius:16px;}"
        "QLabel#PropertiesTitle{background:transparent;color:#ffffff;font-size:15px;font-weight:800;padding:6px 2px;}"
        "QLabel#PropertiesSectionTitle{background:transparent;color:#1f3148;font-size:14px;font-weight:900;}"
        "QLabel#PropertiesFieldLabel{background:transparent;color:#1f3148;font-size:12px;font-style:normal;font-weight:800;}"
        "QLabel#PropertiesHint{background:rgba(255,255,255,130);border:1px solid #c3d0df;border-radius:9px;color:#39516f;font-size:11px;font-style:normal;padding:7px;}"
        "QPushButton#PropertiesNavButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba(255,255,255,220),stop:1 rgba(226,240,255,220));border:1px solid #b8c5d4;border-left:3px solid #43d3bd;border-radius:9px;color:#1f3148;font-size:12px;font-weight:900;padding:7px 9px;text-align:left;}"
        "QPushButton#PropertiesNavButton:hover{background:#fff4cf;border-color:#ff8a35;border-left-color:#ff8a35;}"
        "QPushButton#PropertiesNavButton:checked{background:#eaf6ff;border-color:#2f7df6;border-left-color:#2f7df6;}"
        "QWidget#PropertiesCard{background:rgba(255,255,255,185);border:1px solid #c3d0df;border-radius:12px;}"
        "QComboBox#PropertiesCombo,QFontComboBox#PropertiesCombo,QLineEdit#PropertiesInput,QSpinBox#PropertiesSpin,QDoubleSpinBox#PropertiesSpin,QKeySequenceEdit#ShortcutInput{background:#ffffff;border:1px solid #9fb0c5;border-radius:8px;color:#132238;font-size:12px;font-style:normal;font-weight:800;padding:5px 8px;}"
        "QCheckBox#RadioLikeOption{background:transparent;color:#132238;font-size:12px;font-style:normal;font-weight:800;spacing:7px;}"
        "QCheckBox#RadioLikeOption::indicator{width:16px;height:16px;border-radius:9px;border:2px solid #2d7eea;background:#ffffff;}"
        "QCheckBox#RadioLikeOption::indicator:checked{border:2px solid #2d7eea;background:qradialgradient(cx:.5,cy:.5,radius:.70,fx:.5,fy:.5,stop:0 #2d7eea,stop:.42 #2d7eea,stop:.46 #ffffff,stop:1 #ffffff);}"
        "QPushButton#PrimaryDialogButton,QPushButton#SecondaryDialogButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #d8e3f0);border:1px solid #95a9c1;border-bottom:2px solid #7188a5;border-radius:8px;color:#223650;font-size:12px;font-weight:800;padding:4px 10px;}"
        "QPushButton#PrimaryDialogButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.42 #fff1bf,stop:1 #ff8a35);border-color:#7e5b10;border-bottom-color:#7e5b10;}"
    )


def _card(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("PropertiesCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(12, 10, 12, 12)
    layout.setSpacing(8)
    label = QLabel(title)
    label.setObjectName("PropertiesSectionTitle")
    layout.addWidget(label)
    return frame, layout


def _field(label_text: str, editor: QWidget) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    label = QLabel(label_text)
    label.setObjectName("PropertiesFieldLabel")
    label.setFixedWidth(110)
    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(label)
    layout.addWidget(editor, 1)
    return row


def _combo(values: tuple[str, ...], current: str) -> QComboBox:
    combo = QComboBox()
    combo.setObjectName("PropertiesCombo")
    combo.addItems(list(values))
    index = combo.findText(current)
    combo.setCurrentIndex(index if index >= 0 else 0)
    return combo


def _radio(text: str, checked: bool) -> QCheckBox:
    check = QCheckBox(text)
    check.setObjectName("RadioLikeOption")
    check.setChecked(checked)
    return check


def _install_shortcuts(workspace, shortcuts: dict[str, str]) -> None:
    for shortcut in list(getattr(workspace, "_engineering_shortcuts", [])):
        try:
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        except Exception:
            pass
    workspace._engineering_shortcuts = []
    workspace._engineering_shortcut_bindings = dict(DEFAULT_SHORTCUTS)
    if isinstance(shortcuts, dict):
        workspace._engineering_shortcut_bindings.update({str(k): str(v) for k, v in shortcuts.items()})
    for key, _label, default, method_name in SHORTCUT_SPECS:
        sequence = str(workspace._engineering_shortcut_bindings.get(key, default) or "").strip()
        if not sequence:
            continue
        callback = getattr(workspace, method_name, None)
        if not callable(callback) and method_name == "_group_selection":
            callback = getattr(workspace, "_group", None)
        if not callable(callback) and method_name == "_ungroup_selection":
            callback = getattr(workspace, "_ungroup", None)
        if not callable(callback):
            continue
        shortcut = QShortcut(QKeySequence(sequence), workspace)
        shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        shortcut.activated.connect(callback)
        shortcut.activatedAmbiguously.connect(callback)
        workspace._engineering_shortcuts.append(shortcut)
    workspace._engineering_shortcuts_installed = True
    logging.info("engineering_properties_patch: shortcuts installed count=%s", len(workspace._engineering_shortcuts))


def _apply_settings(workspace, settings: dict[str, Any], reinstall_shortcuts: bool = True) -> None:
    workspace._properties_settings = settings
    general = settings.get("general", {})
    unit = str(general.get("unit", "mm")) if str(general.get("unit", "mm")) in UNITS else "mm"
    grid_enabled = bool(general.get("grid_enabled", True))
    grid_spacing = float(general.get("grid_spacing", 4.0) or 4.0)
    snap_enabled = bool(general.get("snap_enabled", False))
    workspace._default_text_font = str(general.get("text_font", "Times New Roman"))
    workspace._default_text_size = int(general.get("text_size", 12) or 12)
    view_state = getattr(workspace, "_view_state", None)
    if isinstance(view_state, dict):
        view_state["grid"] = grid_enabled
        view_state["snap"] = snap_enabled
    start_bar = getattr(workspace, "_start_bar_widget", None)
    if start_bar is not None:
        try:
            if getattr(start_bar, "_unit", "mm") != unit and hasattr(start_bar, "_set_unit"):
                start_bar._set_unit(unit)
            else:
                start_bar._unit = unit
            start_bar._grid_spacing = grid_spacing
            start_bar._grid_enabled = grid_enabled
            if hasattr(start_bar, "_apply_unit_to_host"):
                start_bar._apply_unit_to_host()
            if hasattr(start_bar, "_apply_grid_to_host"):
                start_bar._apply_grid_to_host()
        except Exception as error:  # noqa: BLE001
            logging.exception("engineering_properties_patch: start bar apply failed: %s", error)
    for item in getattr(workspace, "_status_items", []):
        if hasattr(item, "text") and item.text().startswith("Unit:"):
            item.setText(f"Unit: {unit}")
            break
    if reinstall_shortcuts:
        _install_shortcuts(workspace, settings.get("shortcuts", DEFAULT_SHORTCUTS))
    refresh = getattr(workspace, "_refresh_properties_summary_panel", None)
    if callable(refresh):
        refresh()


class PropertiesDialog(QDialog):
    def __init__(self, workspace: QWidget) -> None:
        super().__init__(workspace)
        self.workspace = workspace
        self.setObjectName("ProjectHelpDialog")
        self.setWindowTitle("Properties")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.resize(840, 560)
        self._settings = _collect_settings(workspace)
        self._shortcut_editors: dict[str, QKeySequenceEdit] = {}
        self._build_ui()
        _style_dialog(self)

    def _build_ui(self) -> None:
        shell = QWidget()
        shell.setObjectName("PropertiesShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 14)
        layout.setSpacing(10)
        layout.addWidget(self._header())
        body = QHBoxLayout()
        body.setContentsMargins(16, 8, 16, 0)
        body.setSpacing(12)
        nav = QVBoxLayout()
        nav.setSpacing(7)
        self.stack = QStackedWidget()
        self._nav_buttons: list[QPushButton] = []
        for index, (title, page) in enumerate((("General", self._general_page()), ("Shortcut Key", self._shortcut_page()), ("Save/Load", self._save_load_page()))):
            button = QPushButton(title)
            button.setObjectName("PropertiesNavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, selected=index: self._select(selected))
            self._nav_buttons.append(button)
            nav.addWidget(button)
            self.stack.addWidget(page)
        nav.addStretch(1)
        self._select(0)
        nav_widget = QWidget()
        nav_widget.setFixedWidth(180)
        nav_widget.setLayout(nav)
        body.addWidget(nav_widget)
        body.addWidget(self.stack, 1)
        layout.addLayout(body, 1)
        buttons = QHBoxLayout()
        buttons.setContentsMargins(16, 0, 16, 0)
        buttons.addStretch(1)
        save = QPushButton("Save")
        save.setObjectName("PrimaryDialogButton")
        save.clicked.connect(self._save_and_accept)
        buttons.addWidget(save)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryDialogButton")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

    def _header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("PropertiesHeader")
        header.setFixedHeight(44)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 8, 0)
        builder = getattr(self.workspace, "_build_window_mark", None)
        mark = builder() if callable(builder) else QLabel("AT")
        mark.setFixedSize(36, 32)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(mark)
        title = QLabel("Properties")
        title.setObjectName("PropertiesTitle")
        layout.addWidget(title, 1)
        close = QPushButton("×")
        close.setObjectName("MenuDialogClose")
        close.setFixedSize(28, 26)
        close.clicked.connect(self.reject)
        layout.addWidget(close)
        return header

    def _select(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self._nav_buttons):
            button.setChecked(i == index)

    def _general_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        card, card_layout = _card("General")
        general = self._settings["general"]
        self.unit_combo = _combo(UNITS, str(general.get("unit", "mm")))
        self.grid_check = _radio("Grid enabled", bool(general.get("grid_enabled", True)))
        self.snap_check = _radio("Snap enabled", bool(general.get("snap_enabled", False)))
        self.grid_spacing = QDoubleSpinBox()
        self.grid_spacing.setObjectName("PropertiesSpin")
        self.grid_spacing.setRange(0.000001, 1000000.0)
        self.grid_spacing.setDecimals(6)
        self.grid_spacing.setSingleStep(0.5)
        self.grid_spacing.setValue(float(general.get("grid_spacing", 4.0) or 4.0))
        self.text_font = QFontComboBox()
        self.text_font.setObjectName("PropertiesCombo")
        self.text_font.setCurrentText(str(general.get("text_font", "Times New Roman")))
        self.text_size = QSpinBox()
        self.text_size.setObjectName("PropertiesSpin")
        self.text_size.setRange(1, 300)
        self.text_size.setValue(int(general.get("text_size", 12) or 12))
        for label, editor in (("Unit", self.unit_combo), ("Grid spacing", self.grid_spacing), ("Text font", self.text_font), ("Text size", self.text_size)):
            card_layout.addWidget(_field(label, editor))
        card_layout.addWidget(self.grid_check)
        card_layout.addWidget(self.snap_check)
        hint = QLabel("Unit, Grid and Snap are connected to Start Bar and View state.")
        hint.setObjectName("PropertiesHint")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _shortcut_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        card, card_layout = _card("Shortcut Key")
        hint = QLabel("Every shortcut is editable. Empty shortcut means the command has no keyboard binding.")
        hint.setObjectName("PropertiesHint")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        shortcuts = self._settings.get("shortcuts", DEFAULT_SHORTCUTS)
        for row, (key, label, default, _method) in enumerate(SHORTCUT_SPECS):
            command = QLabel(label)
            command.setObjectName("PropertiesFieldLabel")
            editor = QKeySequenceEdit()
            editor.setObjectName("ShortcutInput")
            try:
                editor.setClearButtonEnabled(True)
            except Exception:
                pass
            editor.setKeySequence(QKeySequence(str(shortcuts.get(key, default) or "")))
            self._shortcut_editors[key] = editor
            grid.addWidget(command, row, 0)
            grid.addWidget(editor, row, 1)
        scroll.setWidget(content)
        card_layout.addWidget(scroll, 1)
        layout.addWidget(card, 1)
        return page

    def _save_load_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        card, card_layout = _card("Save/Load")
        hint = QLabel("This file stores Page Setup, Printer settings, General settings and Shortcut Keys. A loaded file becomes the automatic startup settings file.")
        hint.setObjectName("PropertiesHint")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)
        save_file = QPushButton("Save Settings File")
        save_file.setObjectName("PrimaryDialogButton")
        save_file.clicked.connect(self._save_file)
        load_file = QPushButton("Load Settings File")
        load_file.setObjectName("SecondaryDialogButton")
        load_file.clicked.connect(self._load_file)
        auto_path = QLineEdit(str(_auto_settings_path()))
        auto_path.setObjectName("PropertiesInput")
        auto_path.setReadOnly(True)
        card_layout.addWidget(save_file)
        card_layout.addWidget(load_file)
        card_layout.addWidget(_field("Auto load file", auto_path))
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _read_controls(self) -> dict[str, Any]:
        settings = _collect_settings(self.workspace)
        settings["general"] = {
            "unit": self.unit_combo.currentText(),
            "grid_enabled": self.grid_check.isChecked(),
            "grid_spacing": float(self.grid_spacing.value()),
            "snap_enabled": self.snap_check.isChecked(),
            "text_font": self.text_font.currentText(),
            "text_size": int(self.text_size.value()),
        }
        settings["shortcuts"] = {key: editor.keySequence().toString(QKeySequence.SequenceFormat.PortableText) for key, editor in self._shortcut_editors.items()}
        return settings

    def _save_and_accept(self) -> None:
        settings = self._read_controls()
        _apply_settings(self.workspace, settings, reinstall_shortcuts=True)
        _write_settings(_auto_settings_path(), settings)
        self.accept()

    def _save_file(self) -> None:
        settings = self._read_controls()
        path_text, _ = QFileDialog.getSaveFileName(self, "Save Properties Settings", str(_auto_settings_path()), "Engineer Tools Properties (*.etprops);;JSON (*.json)")
        if not path_text:
            return
        path = Path(path_text)
        if not path.suffix:
            path = path.with_suffix(".etprops")
        _write_settings(path, settings)
        _write_settings(_auto_settings_path(), settings)

    def _load_file(self) -> None:
        path_text, _ = QFileDialog.getOpenFileName(self, "Load Properties Settings", str(_settings_dir()), "Engineer Tools Properties (*.etprops *.json);;All Files (*)")
        if not path_text:
            return
        settings = _read_settings(Path(path_text), self.workspace)
        _write_settings(_auto_settings_path(), settings)
        _apply_settings(self.workspace, settings, reinstall_shortcuts=True)
        self.close()
        PropertiesDialog(self.workspace).exec()


def _build_properties_panel(workspace) -> QWidget:
    panel = QWidget()
    panel.setObjectName("SidePanel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)
    title = QLabel("Properties")
    title.setObjectName("PanelTitle")
    layout.addWidget(title)
    summary = QVBoxLayout()
    summary.setSpacing(6)
    layout.addLayout(summary)
    open_button = QPushButton("Open Full Properties")
    open_button.setObjectName("PrimaryDialogButton")
    open_button.clicked.connect(workspace._file_properties)
    layout.addWidget(open_button)
    layout.addStretch(1)

    def refresh() -> None:
        while summary.count():
            item = summary.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        settings = _collect_settings(workspace)
        general = settings["general"]
        rows = (
            ("General", f"Unit: {general['unit']} | Grid: {'On' if general['grid_enabled'] else 'Off'}"),
            ("Snap", "On" if general.get("snap_enabled") else "Off"),
            ("Text", f"{general.get('text_font', 'Times New Roman')} | {general.get('text_size', 12)} pt"),
            ("Shortcut Key", f"{sum(1 for value in settings.get('shortcuts', {}).values() if value)} active"),
            ("Save/Load", _auto_settings_path().name),
        )
        for heading, value in rows:
            box = QLabel(f"{heading}\n{value}")
            box.setObjectName("PanelItem")
            box.setWordWrap(True)
            box.setMinimumHeight(42)
            summary.addWidget(box)

    panel.refresh_properties_summary = refresh
    refresh()
    return panel


def _patch_print_setup_apply_button() -> None:
    try:
        from . import engineering_print_setup_final_patch as final_patch
    except Exception:
        logging.exception("engineering_properties_patch: print final patch import failed")
        return
    dialog_cls = getattr(final_patch, "FinalPrintSetupDialog", None)
    if dialog_cls is None or getattr(dialog_cls, "_properties_no_apply_patched", False):
        return
    original_build_ui = dialog_cls._build_ui

    def build_ui_without_apply(self):
        original_build_ui(self)
        for button in list(self.findChildren(QPushButton)):
            if button.text() == "Apply":
                button.hide()
                parent = button.parentWidget()
                layout = parent.layout() if parent is not None else None
                if layout is not None:
                    layout.removeWidget(button)
                button.setParent(None)
                button.deleteLater()
        status = getattr(self, "_status", None)
        if status is not None:
            status.setText("Select a printer, then print.")

    dialog_cls._build_ui = build_ui_without_apply
    dialog_cls._properties_no_apply_patched = True
    logging.info("engineering_properties_patch: print setup Apply button disabled")


def apply_engineering_properties_patch() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import module_window as mw
    except Exception:
        logging.exception("engineering_properties_patch: imports failed")
        return
    if getattr(edw.EngineeringDesignWorkspace, "_properties_patch_version", "") == VERSION:
        return
    _patch_print_setup_apply_button()
    original_init = edw.EngineeringDesignWorkspace.__init__
    original_build_side_panel = edw.EngineeringDesignWorkspace._build_side_panel

    def build_side_panel(self, title: str, rows: tuple[str, ...]) -> QWidget:
        if title == "Properties":
            panel = _build_properties_panel(self)
            self._properties_panel_widget = panel
            self._refresh_properties_summary_panel = panel.refresh_properties_summary
            return panel
        return original_build_side_panel(self, title, rows)

    def file_properties(self) -> None:
        dialog = PropertiesDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._set_status("Properties saved")
        else:
            self._set_status("Properties closed")

    def install_engineering_shortcuts(self) -> None:
        if getattr(self, "_engineering_shortcuts_installed", False):
            return
        settings = getattr(self, "_properties_settings", None)
        shortcuts = settings.get("shortcuts", DEFAULT_SHORTCUTS) if isinstance(settings, dict) else DEFAULT_SHORTCUTS
        _install_shortcuts(self, shortcuts)

    def init(self, module) -> None:
        self._properties_settings = _read_settings(_auto_settings_path(), self)
        original_init(self, module)
        settings = _read_settings(_auto_settings_path(), self)
        self._properties_settings = settings
        _apply_settings(self, settings, reinstall_shortcuts=True)
        logging.info("engineering_properties_patch: startup settings loaded path=%s", _auto_settings_path())

    edw.EngineeringDesignWorkspace._build_side_panel = build_side_panel
    edw.EngineeringDesignWorkspace._file_properties = file_properties
    edw.EngineeringDesignWorkspace._install_engineering_shortcuts = install_engineering_shortcuts
    edw.EngineeringDesignWorkspace.__init__ = init
    mw.ModuleWindow._file_properties = file_properties
    edw.EngineeringDesignWorkspace._properties_patch_version = VERSION
    logging.info("engineering_properties_patch: installed version=%s", VERSION)

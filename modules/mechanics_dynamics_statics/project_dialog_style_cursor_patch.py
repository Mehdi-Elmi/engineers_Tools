"""Project dialog and shared control styling for the engineering UI.

This patch is also the last shared owner for ComboBox and SpinBox arrow styling.
The arrows intentionally use generated dark-blue PNG assets instead of Qt CSS
triangles, because the triangle fallback was rendering as square blocks on the
Windows runtime.
"""

from __future__ import annotations

import importlib
import re
import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap, QPolygonF, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit, QListWidget, QPushButton, QSpinBox, QTextEdit, QWidget

PATCH_VERSION = "engineering-project-dialog-style-cursor-2026-07-02-g"
_ARROW_CACHE: dict[str, str] = {}
_PREFIX_RE = re.compile(r"^\s*(?:\d+[\.)]|[ivxlcdmIVXLCDM]+[\.)]|[A-Za-z]+[\.)]|[●○■◆➤✓•])\s+")
FONT_CHOICES = ("Times New Roman", "B Zar", "B Nazanin", "B Mitra", "B Lotus", "B Titr", "B Yekan", "B Koodak", "B Traffic")


def _arrow_path(direction: str = "down") -> str:
    cached = _ARROW_CACHE.get(direction)
    if cached:
        return cached
    size = 18
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(QColor("#173454"))
    painter.setPen(Qt.PenStyle.NoPen)
    if direction == "up":
        points = [QPointF(9, 4), QPointF(14, 12), QPointF(4, 12)]
    elif direction == "down":
        points = [QPointF(4, 6), QPointF(14, 6), QPointF(9, 14)]
    elif direction == "left":
        points = [QPointF(5, 9), QPointF(13, 4), QPointF(13, 14)]
    else:
        points = [QPointF(13, 9), QPointF(5, 4), QPointF(5, 14)]
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    path = Path(tempfile.gettempdir()) / f"engineering_shared_arrow_{direction}_20260702g.png"
    pixmap.save(path.as_posix(), "PNG")
    _ARROW_CACHE[direction] = path.as_posix()
    return path.as_posix()


def _style_combo_arrow(combo: QComboBox) -> None:
    combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    combo.setStyleSheet(
        "QComboBox{background:#fffefa;border:1px solid #b88718;border-radius:8px;color:#173454;"
        "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:2px 28px 2px 8px;outline:0;}"
        "QComboBox:hover{border-color:#173454;background:#ffffff;}"
        "QComboBox:focus{outline:0;border:1px solid #b88718;}"
        "QComboBox::drop-down{subcontrol-origin:padding;subcontrol-position:top right;width:24px;"
        "border-left:1px solid #b88718;border-top-right-radius:7px;border-bottom-right-radius:7px;"
        "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        f"QComboBox::down-arrow{{image:url({_arrow_path('down')});width:16px;height:16px;}}"
        "QComboBox QAbstractItemView{background:#ffffff;border:1px solid #9fb1c7;border-radius:8px;"
        "selection-background-color:#e7f1ff;selection-color:#173454;outline:0;}"
    )


def _style_numeric_spin(spin: QSpinBox | QDoubleSpinBox) -> None:
    spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
    spin.setKeyboardTracking(True)
    spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    try:
        edit = spin.lineEdit()
        edit.setReadOnly(False)
        edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        edit.setCursorPosition(0)
        edit.setStyleSheet(
            "QLineEdit{background:transparent;border:0;color:#173454;font-family:'Times New Roman';"
            "font-size:12px;font-weight:900;font-style:normal;padding:0;outline:0;}"
        )
    except Exception:
        pass
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffefa;border:1px solid #b88718;border-radius:8px;color:#173454;"
        "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:2px 26px 2px 8px;outline:0;}"
        "QSpinBox:focus,QDoubleSpinBox:focus{border:1px solid #173454;outline:0;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{subcontrol-origin:border;subcontrol-position:top right;width:23px;"
        "border-left:1px solid #b88718;border-top-right-radius:7px;"
        "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{subcontrol-origin:border;subcontrol-position:bottom right;width:23px;"
        "border-left:1px solid #b88718;border-bottom-right-radius:7px;"
        "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        f"QSpinBox::up-arrow,QDoubleSpinBox::up-arrow{{image:url({_arrow_path('up')});width:14px;height:14px;}}"
        f"QSpinBox::down-arrow,QDoubleSpinBox::down-arrow{{image:url({_arrow_path('down')});width:14px;height:14px;}}"
    )


def _polish_dialog(root: QWidget | None) -> None:
    if root is None:
        return
    for combo in root.findChildren(QComboBox):
        _style_combo_arrow(combo)
    for spin in root.findChildren(QSpinBox):
        _style_numeric_spin(spin)
    for spin in root.findChildren(QDoubleSpinBox):
        _style_numeric_spin(spin)
    for edit in root.findChildren(QLineEdit):
        edit.setStyleSheet(
            "QLineEdit{background:#fffefa;border:1px solid #b88718;border-radius:8px;color:#173454;"
            "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:3px 7px;outline:0;}"
            "QLineEdit:focus{border:1px solid #173454;}"
        )
    for view in root.findChildren(QListWidget):
        view.setStyleSheet(
            "QListWidget{background:#ffffff;border:1px solid #9fb1c7;border-radius:8px;color:#173454;"
            "font-family:'Times New Roman';font-weight:900;font-style:italic;outline:0;}"
            "QListWidget::item{padding:4px 6px;border-radius:5px;}"
            "QListWidget::item:selected{background:#e7f1ff;color:#173454;}"
        )
    for button in root.findChildren(QPushButton):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)


def _active_text_editor(root: QWidget | None) -> QTextEdit | None:
    canvas = getattr(root, "_canvas", None) if root is not None else None
    editor = getattr(canvas, "_active_text_editor", None) if canvas is not None else None
    return editor if isinstance(editor, QTextEdit) else None


def _active_canvas(root: QWidget | None):
    return getattr(root, "_canvas", None) if root is not None else None


def _save_active_text_editor(root: QWidget | None) -> None:
    canvas = _active_canvas(root)
    editor = _active_text_editor(root)
    if canvas is None or editor is None:
        return
    try:
        from . import ui_text_tool_final_patch as text_final
        text_final._save_editor_text(canvas, editor)
    except Exception:
        pass


def _save_text_direction(root: QWidget | None, rtl: bool, alignment: str) -> None:
    canvas = _active_canvas(root)
    if canvas is None:
        return
    index = getattr(canvas, "_active_text_editor_index", None)
    if index is None or not (0 <= index < len(getattr(canvas, "objects", []))):
        return
    obj = canvas.objects[index]
    obj.text_rtl = bool(rtl)
    obj.text_align = alignment
    try:
        canvas.update()
    except Exception:
        pass


def _merge_text_format(root: QWidget | None, fmt: QTextCharFormat) -> None:
    editor = _active_text_editor(root)
    if editor is None:
        return
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.mergeCharFormat(fmt)
    editor.mergeCurrentCharFormat(fmt)
    editor.setTextCursor(cursor)
    editor.setFocus()
    _save_active_text_editor(root)


def _apply_text_font(root: QWidget | None, family: str) -> None:
    fmt = QTextCharFormat()
    fmt.setFontFamily(family or "Times New Roman")
    _merge_text_format(root, fmt)


def _apply_text_size(root: QWidget | None, size: int | float) -> None:
    try:
        point_size = max(1.0, float(size))
    except Exception:
        point_size = 12.0
    fmt = QTextCharFormat()
    fmt.setFontPointSize(point_size)
    _merge_text_format(root, fmt)


def _apply_text_bold(root: QWidget | None, checked: bool) -> None:
    fmt = QTextCharFormat()
    fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
    _merge_text_format(root, fmt)


def _apply_text_italic(root: QWidget | None, checked: bool) -> None:
    fmt = QTextCharFormat()
    fmt.setFontItalic(bool(checked))
    _merge_text_format(root, fmt)


def _button_map(root: QWidget | None) -> dict:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


def _set_checked_silent(buttons: dict, name: str, checked: bool) -> None:
    button = buttons.get(name)
    if not isinstance(button, QPushButton):
        return
    blocked = button.blockSignals(True)
    button.setChecked(checked)
    button.blockSignals(blocked)


def _apply_text_direction(root: QWidget | None, *, rtl: bool) -> None:
    buttons = _button_map(root)
    _set_checked_silent(buttons, "Right to left", rtl)
    _set_checked_silent(buttons, "Left to right", not rtl)
    _set_checked_silent(buttons, "Align right", rtl)
    _set_checked_silent(buttons, "Align left", not rtl)
    _set_checked_silent(buttons, "Align center", False)
    _set_checked_silent(buttons, "Justify", False)
    editor = _active_text_editor(root)
    if editor is None:
        return
    editor.setLayoutDirection(Qt.LayoutDirection.RightToLeft if rtl else Qt.LayoutDirection.LeftToRight)
    editor.setAlignment(Qt.AlignmentFlag.AlignRight if rtl else Qt.AlignmentFlag.AlignLeft)
    editor.setFocus()
    _save_text_direction(root, rtl, "right" if rtl else "left")
    _save_active_text_editor(root)


def _apply_text_alignment(root: QWidget | None, alignment: str) -> None:
    buttons = _button_map(root)
    for name in ("Align left", "Align center", "Align right", "Justify"):
        _set_checked_silent(buttons, name, False)
    active = {"left": "Align left", "center": "Align center", "right": "Align right", "justify": "Justify"}.get(alignment, "Align left")
    _set_checked_silent(buttons, active, True)
    editor = _active_text_editor(root)
    if editor is None:
        return
    qt_alignment = {
        "left": Qt.AlignmentFlag.AlignLeft,
        "center": Qt.AlignmentFlag.AlignHCenter,
        "right": Qt.AlignmentFlag.AlignRight,
        "justify": Qt.AlignmentFlag.AlignJustify,
    }.get(alignment, Qt.AlignmentFlag.AlignLeft)
    editor.setAlignment(qt_alignment)
    if alignment in {"right", "justify"} and buttons.get("Right to left") and buttons["Right to left"].isChecked():
        editor.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        _save_text_direction(root, True, alignment)
    else:
        _save_text_direction(root, editor.layoutDirection() == Qt.LayoutDirection.RightToLeft, alignment)
    editor.setFocus()
    _save_active_text_editor(root)


def _normalize_font_combo(combo: QComboBox) -> None:
    current = combo.currentText()
    wanted = list(FONT_CHOICES)
    existing = [combo.itemText(i) for i in range(combo.count())]
    if existing == wanted:
        return
    blocked = combo.blockSignals(True)
    combo.clear()
    combo.addItems(wanted)
    combo.setCurrentText(current if current in wanted else "Times New Roman")
    combo.blockSignals(blocked)


def _wire_text_controls(root: QWidget | None) -> None:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    if not isinstance(controls, dict):
        return
    combo = controls.get("font")
    size = controls.get("size")
    buttons = controls.get("buttons", {}) if isinstance(controls.get("buttons", {}), dict) else {}
    if isinstance(combo, QComboBox):
        _normalize_font_combo(combo)
    if isinstance(combo, QComboBox) and combo.property("finalFontApplyWire") != PATCH_VERSION:
        combo.currentTextChanged.connect(lambda value, w=root: _apply_text_font(w, value))
        combo.setProperty("finalFontApplyWire", PATCH_VERSION)
    if isinstance(size, (QSpinBox, QDoubleSpinBox)) and size.property("finalSizeApplyWire") != PATCH_VERSION:
        size.valueChanged.connect(lambda value, w=root: _apply_text_size(w, value))
        size.setProperty("finalSizeApplyWire", PATCH_VERSION)
    bold = buttons.get("Bold")
    italic = buttons.get("Italic")
    if isinstance(bold, QPushButton) and bold.property("finalBoldApplyWire") != PATCH_VERSION:
        bold.toggled.connect(lambda checked, w=root: _apply_text_bold(w, checked))
        bold.setProperty("finalBoldApplyWire", PATCH_VERSION)
    if isinstance(italic, QPushButton):
        font = italic.font()
        font.setFamily("Times New Roman")
        font.setPointSize(15)
        font.setBold(True)
        font.setItalic(True)
        italic.setFont(font)
        italic.setText("I")
        if italic.property("finalItalicApplyWire") != PATCH_VERSION:
            italic.toggled.connect(lambda checked, w=root: _apply_text_italic(w, checked))
            italic.setProperty("finalItalicApplyWire", PATCH_VERSION)
    wiring = (
        ("Right to left", lambda w=root: _apply_text_direction(w, rtl=True)),
        ("Left to right", lambda w=root: _apply_text_direction(w, rtl=False)),
        ("Align left", lambda w=root: _apply_text_alignment(w, "left")),
        ("Align center", lambda w=root: _apply_text_alignment(w, "center")),
        ("Align right", lambda w=root: _apply_text_alignment(w, "right")),
        ("Justify", lambda w=root: _apply_text_alignment(w, "justify")),
    )
    for name, callback in wiring:
        button = buttons.get(name)
        if isinstance(button, QPushButton) and button.property("finalDirectionWire") != PATCH_VERSION:
            button.clicked.connect(lambda checked=False, cb=callback: cb())
            button.setProperty("finalDirectionWire", PATCH_VERSION)


def _remove_current_list_prefix(root: QWidget | None) -> None:
    editor = _active_text_editor(root)
    if editor is None:
        return
    cursor = editor.textCursor()
    block = cursor.block()
    match = _PREFIX_RE.match(block.text() or "")
    if match is None:
        return
    cursor.setPosition(block.position())
    cursor.setPosition(block.position() + match.end(), QTextCursor.MoveMode.KeepAnchor)
    cursor.removeSelectedText()
    editor.setTextCursor(cursor)
    _save_active_text_editor(root)


def _install_text_list_none_behavior() -> None:
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return
    if getattr(line_patch, "_project_none_behavior_patch", "") == PATCH_VERSION:
        return

    def deactivate_list_style(root: QWidget | None) -> None:
        try:
            line_patch._set_list_button_state(root, None)
        except Exception:
            pass
        if root is not None:
            setattr(root, "_last_text_list_settings", {})
            setattr(root, "_text_numbering_next", 1)
        _remove_current_list_prefix(root)

    line_patch._deactivate_list_style = deactivate_list_style
    line_patch._project_none_behavior_patch = PATCH_VERSION


def _install_text_backspace_behavior() -> None:
    try:
        from . import text_toolbar_final_event_safety_patch as final_event
    except Exception:
        return
    if getattr(final_event, "_project_backspace_behavior_patch", "") == PATCH_VERSION:
        return

    def delete_previous_char(editor: QTextEdit) -> None:
        cursor = editor.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        else:
            cursor.deletePreviousChar()
        editor.setTextCursor(cursor)
        final_event._save_editor(editor)

    def delete_next_char(editor: QTextEdit) -> None:
        cursor = editor.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        else:
            cursor.deleteChar()
        editor.setTextCursor(cursor)
        final_event._save_editor(editor)

    final_event._delete_previous_char = delete_previous_char
    final_event._delete_next_char = delete_next_char
    final_event._project_backspace_behavior_patch = PATCH_VERSION


def _install_shared_arrow_styles() -> None:
    try:
        from src.engineers_tools.app import interaction_ui_patch as interaction
        interaction._control_arrow_path = _arrow_path
        interaction._style_numeric_spin = _style_numeric_spin
        interaction._style_combo_arrow = _style_combo_arrow
    except Exception:
        pass
    try:
        from . import text_line_math_symbols_patch as line_patch
        line_patch._combo_style = _style_combo_arrow
        line_patch._spin_style = _style_numeric_spin
    except Exception:
        pass
    _install_text_list_none_behavior()
    _install_text_backspace_behavior()


def _patch_dialog_class(cls) -> None:
    if getattr(cls, "_engineering_shared_arrow_patch", "") == PATCH_VERSION:
        return
    old_init = cls.__init__

    def dialog_init(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        _polish_dialog(self)
        QTimer.singleShot(0, lambda root=self: _polish_dialog(root))
        QTimer.singleShot(120, lambda root=self: _polish_dialog(root))

    cls.__init__ = dialog_init
    cls._engineering_shared_arrow_patch = PATCH_VERSION


def _patch_known_dialogs() -> None:
    module_names = (
        "modules.mechanics_dynamics_statics.project_file_dialog",
        "modules.mechanics_dynamics_statics.project_dialogs_patch",
        "modules.mechanics_dynamics_statics.file_dialog_patch",
        "src.engineers_tools.app.engineering_properties_patch",
    )
    class_names = (
        "ProjectFileDialog",
        "EngineeringFileDialog",
        "FilePropertiesDialog",
        "PropertiesDialog",
        "PageSetupDialog",
        "PrintSetupDialog",
    )
    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        for class_name in class_names:
            cls = getattr(module, class_name, None)
            if cls is not None:
                _patch_dialog_class(cls)


def _patch_workspace_text_controls() -> None:
    try:
        from . import workspace as edw
    except Exception:
        return
    if getattr(edw.EngineeringDesignWorkspace, "_engineering_project_text_controls_patch", "") == PATCH_VERSION:
        return
    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _install_shared_arrow_styles()
        _wire_text_controls(self)
        for delay in (0, 120, 350, 900):
            QTimer.singleShot(delay, lambda root=self: (_install_shared_arrow_styles(), _wire_text_controls(root)))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_project_text_controls_patch = PATCH_VERSION


def apply_project_dialog_style_cursor_patch() -> None:
    _install_shared_arrow_styles()
    _patch_known_dialogs()
    _patch_workspace_text_controls()

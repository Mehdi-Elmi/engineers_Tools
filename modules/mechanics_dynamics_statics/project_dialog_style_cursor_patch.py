"""Project dialog and final text-input ownership for the engineering UI.

This patch runs at the end of the engineering module patch chain. It owns the
shared ComboBox/SpinBox arrows, Text toolbar wiring, TextBox Backspace/Delete
behavior, math auto-conversion, and the shortcut entry for converting selected
text to math.
"""

from __future__ import annotations

import importlib
import re
import tempfile
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainter, QPixmap, QPolygonF, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QApplication, QComboBox, QDoubleSpinBox, QLineEdit, QListWidget, QPushButton, QSpinBox, QTextEdit, QWidget

PATCH_VERSION = "engineering-project-dialog-style-cursor-2026-07-02-j"
_ARROW_CACHE: dict[str, str] = {}
_PREFIX_RE = re.compile(r"^\s*(?:\d+[\.)]|[ivxlcdmIVXLCDM]+[\.)]|[A-Za-z]+[\.)]|[●○■◆➤✓•])\s+")
_MATH_TOKEN_RE = re.compile(r"([A-Za-z0-9]+)([\^_/])([A-Za-z0-9]+)$")
FONT_CHOICES = ("Times New Roman", "B Zar", "B Nazanin", "B Mitra", "B Lotus", "B Titr", "B Yekan", "B Koodak", "B Traffic")


def _arrow_path(direction: str = "down") -> str:
    cached = _ARROW_CACHE.get(direction)
    if cached:
        return cached
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(QColor("#173454"))
    painter.setPen(Qt.PenStyle.NoPen)
    if direction == "up":
        points = [QPointF(9, 4), QPointF(14, 12), QPointF(4, 12)]
    elif direction == "left":
        points = [QPointF(5, 9), QPointF(13, 4), QPointF(13, 14)]
    elif direction == "right":
        points = [QPointF(13, 9), QPointF(5, 4), QPointF(5, 14)]
    else:
        points = [QPointF(4, 6), QPointF(14, 6), QPointF(9, 14)]
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    path = Path(tempfile.gettempdir()) / f"engineering_shared_arrow_{direction}_20260702j.png"
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


def _workspace_from_widget(widget: QWidget | None) -> QWidget | None:
    current = widget
    while current is not None:
        if hasattr(current, "_start_bar_widget") or current.objectName() == "EngineeringDesignWorkspace":
            return current
        current = current.parentWidget()
    return None


def _workspace_from_editor(editor: QTextEdit) -> QWidget | None:
    root = _workspace_from_widget(editor)
    if root is not None:
        return root
    owner = getattr(editor, "_canvas_owner", None)
    root = _workspace_from_widget(owner) if owner is not None else None
    if root is not None:
        return root
    app = QApplication.instance()
    if app is not None:
        for widget in app.topLevelWidgets():
            root = _workspace_from_widget(widget)
            canvas = getattr(root, "_canvas", None) if root is not None else None
            if getattr(canvas, "_active_text_editor", None) is editor:
                editor._canvas_owner = canvas
                return root
    return None


def _active_canvas(root: QWidget | None):
    return getattr(root, "_canvas", None) if root is not None else None


def _active_text_editor(root: QWidget | None) -> QTextEdit | None:
    canvas = _active_canvas(root)
    editor = getattr(canvas, "_active_text_editor", None) if canvas is not None else None
    return editor if isinstance(editor, QTextEdit) else None


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


def _buttons(root: QWidget | None) -> dict:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


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
    fmt = QTextCharFormat()
    fmt.setFontPointSize(max(1.0, float(size or 12)))
    _merge_text_format(root, fmt)


def _apply_text_bold(root: QWidget | None, checked: bool) -> None:
    fmt = QTextCharFormat()
    fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
    _merge_text_format(root, fmt)


def _apply_text_italic(root: QWidget | None, checked: bool) -> None:
    fmt = QTextCharFormat()
    fmt.setFontItalic(bool(checked))
    _merge_text_format(root, fmt)


def _normalize_font_combo(combo: QComboBox) -> None:
    current = combo.currentText()
    wanted = list(FONT_CHOICES)
    if [combo.itemText(i) for i in range(combo.count())] == wanted:
        return
    blocked = combo.blockSignals(True)
    combo.clear()
    combo.addItems(wanted)
    combo.setCurrentText(current if current in wanted else "Times New Roman")
    combo.blockSignals(blocked)


def _set_checked_silent(buttons: dict, name: str, checked: bool) -> None:
    button = buttons.get(name)
    if isinstance(button, QPushButton):
        blocked = button.blockSignals(True)
        button.setChecked(checked)
        button.blockSignals(blocked)


def _apply_text_direction(root: QWidget | None, *, rtl: bool) -> None:
    buttons = _buttons(root)
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
    _save_active_text_editor(root)


def _apply_text_alignment(root: QWidget | None, alignment: str) -> None:
    buttons = _buttons(root)
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
    editor.setFocus()
    _save_active_text_editor(root)


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
        if combo.property("finalFontApplyWire") != PATCH_VERSION:
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


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _normal_char_format(editor: QTextEdit) -> QTextCharFormat:
    fmt = QTextCharFormat(editor.currentCharFormat())
    fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
    return fmt


def _reset_math_format(editor: QTextEdit, cursor: QTextCursor) -> None:
    normal = _normal_char_format(editor)
    normal.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
    cursor.setCharFormat(normal)
    editor.setCurrentCharFormat(normal)
    editor.setTextCursor(cursor)


def _fraction_html(top: str, bottom: str) -> str:
    return (
        "<table cellspacing='0' cellpadding='0' style='display:inline;vertical-align:middle;'>"
        f"<tr><td align='center' style='padding:0 2px;'>{_escape_html(top)}</td></tr>"
        f"<tr><td align='center' style='border-top:1px solid #132238;padding:0 2px;'>{_escape_html(bottom)}</td></tr>"
        "</table>"
    )


def _auto_convert_math_token(editor: QTextEdit) -> bool:
    cursor = editor.textCursor()
    block = cursor.block()
    block_start = block.position()
    rel_pos = max(0, cursor.position() - block_start)
    prefix = (block.text() or "")[:rel_pos].rstrip()
    match = _MATH_TOKEN_RE.search(prefix)
    if match is None:
        return False
    left, operator, right = match.group(1), match.group(2), match.group(3)
    replace = editor.textCursor()
    replace.setPosition(block_start + match.start())
    replace.setPosition(block_start + match.end(), QTextCursor.MoveMode.KeepAnchor)
    normal = _normal_char_format(editor)
    replace.removeSelectedText()
    if operator == "/":
        replace.insertHtml(_fraction_html(left, right))
        _reset_math_format(editor, replace)
        return True
    elevated = QTextCharFormat(normal)
    elevated.setVerticalAlignment(
        QTextCharFormat.VerticalAlignment.AlignSuperScript if operator == "^" else QTextCharFormat.VerticalAlignment.AlignSubScript
    )
    replace.insertText(left, normal)
    replace.insertText(right, elevated)
    _reset_math_format(editor, replace)
    return True


def _save_editor(editor: QTextEdit) -> None:
    root = _workspace_from_editor(editor)
    if root is not None:
        _save_active_text_editor(root)


def _delete_previous_char(editor: QTextEdit) -> None:
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.removeSelectedText()
    else:
        cursor.deletePreviousChar()
    editor.setTextCursor(cursor)
    _save_editor(editor)


def _delete_next_char(editor: QTextEdit) -> None:
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.removeSelectedText()
    else:
        cursor.deleteChar()
    editor.setTextCursor(cursor)
    _save_editor(editor)


def _matches(event, standard_key: QKeySequence.StandardKey) -> bool:
    try:
        return bool(event.matches(standard_key))
    except Exception:
        return False


def _install_text_list_none_behavior() -> None:
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return

    def deactivate_list_style(root: QWidget | None) -> None:
        try:
            line_patch._set_list_button_state(root, None)
        except Exception:
            pass
        if root is not None:
            setattr(root, "_last_text_list_settings", {})
        _remove_current_list_prefix(root)

    line_patch._deactivate_list_style = deactivate_list_style
    line_patch._project_none_behavior_patch = PATCH_VERSION


def _insert_active_list_after_enter(editor: QTextEdit) -> bool:
    root = _workspace_from_editor(editor)
    if root is None:
        return False
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return False
    settings = line_patch._text_settings_for_active_list(root)
    if settings is None:
        return False
    cursor = editor.textCursor()
    cursor.insertBlock()
    line_patch._insert_list_prefix_with_cursor(root, cursor, settings, advance_number=True)
    editor.setTextCursor(cursor)
    _save_editor(editor)
    return True


def _final_text_key_handler(editor: QTextEdit, event) -> bool:
    if event.type() == QEvent.Type.ShortcutOverride:
        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            event.accept()
            return True
        if any(_matches(event, key) for key in (QKeySequence.StandardKey.Copy, QKeySequence.StandardKey.Cut, QKeySequence.StandardKey.Paste, QKeySequence.StandardKey.SelectAll)):
            event.accept()
            return True
        return False
    if event.type() != QEvent.Type.KeyPress:
        return False
    if _matches(event, QKeySequence.StandardKey.Copy):
        editor.copy(); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.Cut):
        editor.cut(); _save_editor(editor); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.Paste):
        editor.paste(); _save_editor(editor); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.SelectAll):
        editor.selectAll(); event.accept(); return True
    if event.key() == Qt.Key.Key_Backspace:
        _delete_previous_char(editor); event.accept(); return True
    if event.key() == Qt.Key.Key_Delete:
        _delete_next_char(editor); event.accept(); return True
    if event.key() == Qt.Key.Key_Space:
        QTextEdit.keyPressEvent(editor, event)
        _auto_convert_math_token(editor)
        _save_editor(editor)
        event.accept()
        return True
    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        if _insert_active_list_after_enter(editor):
            event.accept()
            return True
        _auto_convert_math_token(editor)
        QTextEdit.keyPressEvent(editor, event)
        _save_editor(editor)
        event.accept()
        return True
    return False


class _ProjectTextKeyFilter(QObject):
    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if isinstance(watched, QTextEdit) and _final_text_key_handler(watched, event):
            return True
        return super().eventFilter(watched, event)


def _install_application_text_filter() -> None:
    app = QApplication.instance()
    if app is None:
        return
    old_filter = getattr(app, "_engineering_project_text_key_filter", None)
    if old_filter is not None:
        try:
            app.removeEventFilter(old_filter)
        except Exception:
            pass
    filter_obj = _ProjectTextKeyFilter(app)
    filter_obj._project_version = PATCH_VERSION
    app.installEventFilter(filter_obj)
    app._engineering_project_text_key_filter = filter_obj


def _install_text_backspace_behavior() -> None:
    for module_name in ("text_toolbar_final_event_safety_patch", "text_line_math_symbols_patch", "ui_text_tool_final_patch", "final_focus_editing_icons_patch"):
        try:
            module = __import__(f"modules.mechanics_dynamics_statics.{module_name}", fromlist=[module_name])
            module._handle_editor_event = _final_text_key_handler
            module._handle_editor_key = _final_text_key_handler
            module._handle_text_editor_key = _final_text_key_handler
            module._delete_previous_char = _delete_previous_char
            module._delete_next_char = _delete_next_char
            module._auto_convert_math_token = _auto_convert_math_token
        except Exception:
            pass
    _install_application_text_filter()


def _install_shortcut_policy() -> None:
    try:
        from . import text_line_math_symbols_patch as line_patch
        from . import workspace as edw
        from src.engineers_tools.app import engineering_properties_patch as epp
    except Exception:
        return
    if getattr(epp, "_project_text_shortcut_policy", "") == PATCH_VERSION:
        return
    cleaned = []
    has_math = False
    for key, label, default, method in epp.SHORTCUT_SPECS:
        if key == "delete_alt":
            default = ""
        if key == "convert_selected_math":
            has_math = True
        cleaned.append((key, label, default, method))
    if not has_math:
        cleaned.append(("convert_selected_math", "Convert Selected Text To Math", "Ctrl+M", "_convert_selected_text_to_math"))
    epp.SHORTCUT_SPECS = tuple(cleaned)
    epp.DEFAULT_SHORTCUTS = {key: sequence for key, _label, sequence, _method in epp.SHORTCUT_SPECS}
    old_install = epp._install_shortcuts

    def install_shortcuts(workspace, shortcuts: dict[str, str]) -> None:
        filtered = dict(shortcuts or {})
        filtered["delete_alt"] = ""
        old_install(workspace, filtered)

    def convert_selected_text_to_math(self) -> None:
        line_patch._convert_selection_to_math(self)

    epp._install_shortcuts = install_shortcuts
    edw.EngineeringDesignWorkspace._convert_selected_text_to_math = convert_selected_text_to_math
    epp._project_text_shortcut_policy = PATCH_VERSION


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
    _install_shortcut_policy()
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
        _install_application_text_filter()
        _wire_text_controls(self)
        for delay in (0, 120, 350, 900):
            QTimer.singleShot(delay, lambda root=self: (_install_shared_arrow_styles(), _install_application_text_filter(), _wire_text_controls(root)))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_project_text_controls_patch = PATCH_VERSION


def apply_project_dialog_style_cursor_patch() -> None:
    _install_shared_arrow_styles()
    _install_application_text_filter()
    _patch_known_dialogs()
    _patch_workspace_text_controls()

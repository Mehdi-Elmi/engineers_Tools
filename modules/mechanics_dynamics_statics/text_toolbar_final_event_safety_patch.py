"""Final safety layer for Text toolbar event behavior.

This patch fixes exclusive toolbar state, line spacing enum safety, and the real
QTextEdit event path. Runtime creates a plain QTextEdit for TextBox editing, so
Canvas key handlers do not receive Enter/Backspace while the editor has focus.
The event filter installed here owns that editor path directly.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QEvent, QTimer, Qt
from PySide6.QtGui import QFont, QKeySequence, QTextBlockFormat
from PySide6.QtWidgets import QButtonGroup, QPushButton, QTextEdit, QWidget

PATCH_VERSION = "engineering-text-toolbar-final-event-safety-2026-07-02-e"


class _FinalEditorEventFilter(QObject):
    def eventFilter(self, watched, event) -> bool:
        if not isinstance(watched, QTextEdit):
            return False
        if event.type() == QEvent.Type.ShortcutOverride and _is_text_shortcut(event):
            event.accept()
            return True
        if event.type() == QEvent.Type.KeyPress and _handle_editor_event(watched, event):
            return True
        return False


def _workspace_from_widget(widget: QWidget | None) -> QWidget | None:
    current = widget
    while current is not None:
        if hasattr(current, "_start_bar_widget") and hasattr(current, "_canvas"):
            return current
        current = current.parentWidget()
    return None


def _workspace_from_editor(editor: QTextEdit | None) -> QWidget | None:
    canvas = getattr(editor, "_canvas_owner", None) if editor is not None else None
    if canvas is not None:
        root = _workspace_from_widget(canvas)
        if root is not None:
            return root
    return _workspace_from_widget(editor)


def _buttons(root: QWidget | None) -> dict:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


def _plain_font(editor: QTextEdit) -> None:
    font = QFont("Times New Roman", max(1, editor.currentFont().pointSize() if editor.currentFont().pointSize() > 0 else 12))
    font.setBold(False)
    font.setItalic(False)
    editor.setFont(font)
    editor.setCurrentFont(font)


def _reset_style_buttons(root: QWidget | None) -> None:
    buttons = _buttons(root)
    bold = buttons.get("Bold")
    italic = buttons.get("Italic")
    if bold is not None:
        bold.setChecked(False)
    if italic is not None:
        italic.setChecked(False)
        font = italic.font()
        font.setItalic(True)
        italic.setFont(font)


def _matches(event, standard) -> bool:
    try:
        return bool(event.matches(standard))
    except Exception:
        return False


def _is_text_shortcut(event) -> bool:
    return any(
        _matches(event, key)
        for key in (
            QKeySequence.StandardKey.Copy,
            QKeySequence.StandardKey.Cut,
            QKeySequence.StandardKey.Paste,
            QKeySequence.StandardKey.SelectAll,
        )
    ) or event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace)


def _save_editor(editor: QTextEdit | None) -> None:
    canvas = getattr(editor, "_canvas_owner", None) if editor is not None else None
    if canvas is None:
        return
    try:
        from . import ui_text_tool_final_patch as final_text
        final_text._save_editor_text(canvas, editor)
    except Exception:
        pass
    try:
        from . import text_toolbar_word_behavior_patch as word
        word._save_active_editor(canvas)
    except Exception:
        pass


def _patch_text_defaults(final_text) -> None:
    if getattr(final_text, "_final_event_plain_defaults", "") == PATCH_VERSION:
        return
    old_settings = final_text._current_text_settings

    def current_text_settings(window: QWidget | None) -> dict[str, object]:
        settings = dict(old_settings(window))
        settings["font"] = settings.get("font") or "Times New Roman"
        settings["bold"] = False
        settings["italic"] = False
        return settings

    final_text._current_text_settings = current_text_settings
    final_text._final_event_plain_defaults = PATCH_VERSION


def _activate_list_mode(root: QWidget | None, mode: str, style: str | None = None) -> None:
    if root is None:
        return
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return
    settings = dict(line_patch._default_list_settings(mode, style))
    settings["mode"] = mode
    if style:
        settings["style"] = style
    settings["bold"] = True
    settings["italic"] = False
    setattr(root, "_last_text_list_settings", settings)
    line_patch._set_list_button_state(root, mode)
    if mode == "numbering":
        setattr(root, "_text_numbering_next", int(settings.get("start_numbering", 1)))


def _wire_list_buttons(root: QWidget | None) -> None:
    buttons = _buttons(root)
    for name, mode, style in (("Bullet", "bullet", "●"), ("Numbering", "numbering", "1.")):
        button = buttons.get(name)
        if button is None:
            continue
        button.setCheckable(True)
        if button.property("finalEventListWire") == PATCH_VERSION:
            continue
        button.pressed.connect(lambda w=root, m=mode, s=style: _activate_list_mode(w, m, s))
        button.clicked.connect(lambda checked=False, w=root, m=mode, s=style: _activate_list_mode(w, m, s))
        button.setProperty("finalEventListWire", PATCH_VERSION)


def _insert_active_list_after_enter(editor: QTextEdit) -> bool:
    root = _workspace_from_editor(editor)
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


def _handle_editor_event(editor: QTextEdit, event) -> bool:
    if _matches(event, QKeySequence.StandardKey.Copy):
        editor.copy(); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.Cut):
        editor.cut(); _save_editor(editor); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.Paste):
        editor.paste(); _save_editor(editor); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.SelectAll):
        editor.selectAll(); event.accept(); return True
    if event.key() == Qt.Key.Key_Backspace:
        cursor = editor.textCursor(); cursor.deletePreviousChar(); editor.setTextCursor(cursor); _save_editor(editor); event.accept(); return True
    if event.key() == Qt.Key.Key_Delete:
        cursor = editor.textCursor(); cursor.deleteChar(); editor.setTextCursor(cursor); _save_editor(editor); event.accept(); return True
    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        if _insert_active_list_after_enter(editor):
            event.accept(); return True
    return False


def _install_editor_filter(editor: QTextEdit | None) -> None:
    if not isinstance(editor, QTextEdit):
        return
    canvas = editor.parentWidget()
    if canvas is not None and getattr(editor, "_canvas_owner", None) is None:
        editor._canvas_owner = canvas
    root = _workspace_from_editor(editor)
    _wire_list_buttons(root)
    if editor.property("finalPlainDefaults") != PATCH_VERSION and not editor.toPlainText().strip():
        _plain_font(editor)
        editor.setProperty("finalPlainDefaults", PATCH_VERSION)
    if editor.property("finalEventFilter") == PATCH_VERSION:
        return
    filter_obj = _FinalEditorEventFilter(editor)
    editor.installEventFilter(filter_obj)
    editor._final_event_filter = filter_obj
    editor.setProperty("finalEventFilter", PATCH_VERSION)


def _patch_rich_editor_show(runtime, final_text) -> None:
    if getattr(runtime, "_final_event_editor_show_patch", "") == PATCH_VERSION:
        return
    old_show = runtime._show_rich_text_editor

    def show_rich_text_editor(canvas, index: int) -> None:
        old_show(canvas, index)
        editor = getattr(canvas, "_active_text_editor", None)
        _install_editor_filter(editor)
        root = _workspace_from_widget(canvas)
        _wire_list_buttons(root)
        _reset_style_buttons(root)
        if isinstance(editor, QTextEdit) and not editor.toPlainText().strip():
            _plain_font(editor)

    runtime._show_rich_text_editor = show_rich_text_editor
    final_text._show_text_editor = show_rich_text_editor
    runtime._final_event_editor_show_patch = PATCH_VERSION


def _patch_color_dialog(text_lag) -> None:
    if getattr(text_lag, "_final_event_color_dialog_patch", "") == PATCH_VERSION:
        return

    def open_standard_color_dialog(parent: QWidget, current: str) -> str | None:
        try:
            from . import standard_color_dialog
            return standard_color_dialog.get_custom_color(parent, current, "Add Custom Color")
        except Exception:
            return None

    text_lag._open_standard_color_dialog = open_standard_color_dialog
    text_lag._final_event_color_dialog_patch = PATCH_VERSION


def _stable_build_exclusive_group(bar: QWidget, root: QWidget | None, names: tuple[str, ...], attr: str, default: str, callback) -> None:
    from . import text_toolbar_word_behavior_patch as word

    old = getattr(bar, attr, None)
    buttons = word._buttons(root)
    if isinstance(old, QButtonGroup):
        if not any(buttons.get(name) is not None and buttons[name].isChecked() for name in names):
            button = buttons.get(default)
            if button is not None:
                button.setChecked(True)
        return

    group = QButtonGroup(bar)
    group.setExclusive(True)
    for name in names:
        button = buttons.get(name)
        if button is None:
            continue
        button.setCheckable(True)
        button.setChecked(name == default)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setProperty("wordExclusiveGroup", attr)
        word._set_no_focus(button)
        group.addButton(button)
    group.buttonClicked.connect(lambda button, w=root: callback(w, button.toolTip()))
    setattr(bar, attr, group)


def _safe_apply_line_spacing(root: QWidget | None, value: float) -> None:
    from . import text_toolbar_word_behavior_patch as word

    editor = word._active_editor(root)
    if editor is None:
        return
    cursor = editor.textCursor()
    block = cursor.blockFormat()
    height_type = getattr(QTextBlockFormat.LineHeightTypes, "ProportionalHeight", 1)
    height_type = getattr(height_type, "value", height_type)
    block.setLineHeight(float(value) * 100.0, int(height_type))
    cursor.mergeBlockFormat(block)
    editor.setTextCursor(cursor)
    canvas = word._canvas(root)
    if canvas is not None:
        word._save_active_editor(canvas)


def _patch_canvas_key_handler(edw) -> None:
    if getattr(edw.EngineeringCanvas, "_text_toolbar_final_event_safety_key_patch", "") == PATCH_VERSION:
        return
    old_key = edw.EngineeringCanvas.keyPressEvent

    def key_press(self, event) -> None:
        editor = getattr(self, "_active_text_editor", None)
        _install_editor_filter(editor)
        if isinstance(editor, QTextEdit) and editor.hasFocus():
            if _handle_editor_event(editor, event):
                return
            QTextEdit.keyPressEvent(editor, event)
            _save_editor(editor)
            return
        old_key(self, event)

    edw.EngineeringCanvas.keyPressEvent = key_press
    edw.EngineeringCanvas._text_toolbar_final_event_safety_key_patch = PATCH_VERSION


def apply_text_toolbar_final_event_safety_patch() -> None:
    from . import text_lag_final_patch as text_lag
    from . import text_toolbar_word_behavior_patch as word
    from . import ui_text_tool_final_patch as final_text
    from . import ui_text_tool_runtime_fix_patch as runtime
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_final_event_safety_patch", "") == PATCH_VERSION:
        return

    _patch_text_defaults(final_text)
    word._build_exclusive_group = _stable_build_exclusive_group
    word._apply_line_spacing = _safe_apply_line_spacing
    _patch_rich_editor_show(runtime, final_text)
    _patch_color_dialog(text_lag)
    _patch_canvas_key_handler(edw)

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _patch_text_defaults(final_text)
        word._build_exclusive_group = _stable_build_exclusive_group
        word._apply_line_spacing = _safe_apply_line_spacing
        _patch_rich_editor_show(runtime, final_text)
        _patch_color_dialog(text_lag)
        _patch_canvas_key_handler(edw)
        _wire_list_buttons(self)
        _reset_style_buttons(self)
        editor = getattr(getattr(self, "_canvas", None), "_active_text_editor", None)
        _install_editor_filter(editor)
        for delay in (0, 120, 400):
            QTimer.singleShot(delay, lambda root=self: (word._apply_word_toolbar(root), _wire_list_buttons(root), _reset_style_buttons(root)))
        logging.info("text_toolbar_final_event_safety_patch: installed version=%s", PATCH_VERSION)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_final_event_safety_patch = PATCH_VERSION

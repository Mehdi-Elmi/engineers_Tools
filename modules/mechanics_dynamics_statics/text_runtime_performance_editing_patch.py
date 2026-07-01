"""Performance and editing fixes for the final Text workflow.

This patch runs after the Text toolbar safety layers. It prevents expensive
rebuilds of color palettes and menu trees, fixes Bold/Italic by applying real
QTextCharFormat changes, keeps Text Box painting from drawing duplicate text
behind the active QTextEdit, and adds basic automatic bullet/number continuation.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QKeySequence, QTextCharFormat
from PySide6.QtWidgets import QHBoxLayout, QMenu, QPushButton, QTextEdit, QWidget

PATCH_VERSION = "engineering-text-runtime-performance-editing-2026-07-02-b"

_BULLET_PREFIX = {
    "filled": "• ",
    "hollow": "○ ",
    "square": "■ ",
    "diamond": "◆ ",
    "arrow": "➤ ",
    "check": "✓ ",
}
_NUMBER_PREFIX = {
    "decimal_dot": lambda n: f"{n}. ",
    "decimal_paren": lambda n: f"{n}) ",
    "roman": lambda n: ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][min(max(n, 1), 10) - 1] + ". ",
    "alpha_upper": lambda n: f"{chr(64 + ((n - 1) % 26) + 1)}. ",
    "alpha_lower": lambda n: f"{chr(96 + ((n - 1) % 26) + 1)}. ",
    "roman_lower": lambda n: ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"][min(max(n, 1), 10) - 1] + ". ",
}


def _root_from_canvas(canvas) -> QWidget | None:
    return canvas.window() if hasattr(canvas, "window") else None


def _active_editor(root: QWidget | None) -> QTextEdit | None:
    canvas = getattr(root, "_canvas", None) if root is not None else None
    editor = getattr(canvas, "_active_text_editor", None) if canvas is not None else None
    return editor if isinstance(editor, QTextEdit) else None


def _buttons(root: QWidget | None) -> dict[str, QPushButton]:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


def _save(root: QWidget | None) -> None:
    canvas = getattr(root, "_canvas", None) if root is not None else None
    if canvas is None:
        return
    try:
        from . import text_toolbar_word_behavior_patch as word
        word._save_active_editor(canvas)
    except Exception:
        pass


def _patch_save_state(word) -> None:
    if getattr(word, "_performance_save_state_patch", "") == PATCH_VERSION:
        return
    old_save = word._save_active_editor

    def save_active_editor(canvas) -> None:
        old_save(canvas)
        root = _root_from_canvas(canvas)
        buttons = _buttons(root)
        index = getattr(canvas, "_active_text_editor_index", None)
        if not isinstance(index, int) or not (0 <= index < len(getattr(canvas, "objects", []))):
            return
        obj = canvas.objects[index]
        bold = buttons.get("Bold")
        italic = buttons.get("Italic")
        obj.text_bold = bool(bold.isChecked()) if bold is not None else False
        obj.text_italic = bool(italic.isChecked()) if italic is not None else False

    word._save_active_editor = save_active_editor
    word._performance_save_state_patch = PATCH_VERSION


def _merge_format(editor: QTextEdit, *, bold: bool | None = None, italic: bool | None = None) -> None:
    fmt = QTextCharFormat()
    if bold is not None:
        fmt.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
    if italic is not None:
        fmt.setFontItalic(bool(italic))
    cursor = editor.textCursor()
    cursor.mergeCharFormat(fmt)
    editor.mergeCurrentCharFormat(fmt)


def _patch_bold_italic(word) -> None:
    def set_bold(root: QWidget | None, active: bool) -> None:
        editor = word._active_editor(root)
        if editor is None:
            return
        _merge_format(editor, bold=bool(active))
        _save(root)

    def set_italic(root: QWidget | None, active: bool) -> None:
        editor = word._active_editor(root)
        if editor is None:
            return
        _merge_format(editor, italic=bool(active))
        _save(root)

    word._set_editor_bold = set_bold
    word._set_editor_italic = set_italic


def _patch_runtime_palette(runtime) -> None:
    if getattr(runtime, "_performance_palette_patch", "") == PATCH_VERSION:
        return
    old_install = runtime._install_text_color_palette
    old_style = runtime._style_inline_text_bar

    def install_palette(bar: QWidget, root: QWidget | None) -> None:
        holder = bar.findChild(QWidget, "RuntimeTextColorPaletteHolder")
        if holder is not None and holder.property("performancePalette") == PATCH_VERSION:
            return
        old_install(bar, root)
        holder = bar.findChild(QWidget, "RuntimeTextColorPaletteHolder")
        if holder is not None:
            holder.setProperty("performancePalette", PATCH_VERSION)

    def style_inline_text_bar(bar: QWidget | None) -> None:
        if bar is None:
            return
        if bar.property("performanceStyled") == PATCH_VERSION:
            return
        old_style(bar)
        bar.setProperty("performanceStyled", PATCH_VERSION)
        command_bar = bar.parentWidget()
        if command_bar is not None and command_bar.objectName() == "CommandBar":
            command_bar.setMinimumHeight(max(command_bar.minimumHeight(), 60))
            command_bar.setFixedHeight(max(command_bar.height(), 60))
        bar.setFixedHeight(max(bar.height(), 50))
        layout = bar.layout()
        if isinstance(layout, QHBoxLayout):
            layout.setContentsMargins(12, 7, 12, 7)
            layout.setSpacing(7)

    runtime._install_text_color_palette = install_palette
    runtime._style_inline_text_bar = style_inline_text_bar
    runtime._performance_palette_patch = PATCH_VERSION


def _set_list_mode(root: QWidget | None, mode: str | None, value: str | None) -> None:
    if root is None:
        return
    if not mode or value == "none":
        setattr(root, "_text_active_list_mode", None)
        return
    counter = 1
    if mode == "numbering":
        previous = getattr(root, "_text_active_list_mode", None)
        if isinstance(previous, dict) and previous.get("mode") == "numbering" and previous.get("value") == value:
            counter = int(previous.get("counter", 1))
    setattr(root, "_text_active_list_mode", {"mode": mode, "value": value, "counter": counter})


def _insert_prefix(root: QWidget | None, mode: str, value: str) -> None:
    editor = _active_editor(root)
    if editor is None:
        return
    if value == "none":
        _set_list_mode(root, None, None)
        return
    if mode == "bullet":
        prefix = _BULLET_PREFIX.get(value, "")
        if prefix:
            editor.textCursor().insertText(prefix)
            _set_list_mode(root, "bullet", value)
    else:
        state = getattr(root, "_text_active_list_mode", None)
        counter = int(state.get("counter", 1)) if isinstance(state, dict) and state.get("mode") == "numbering" and state.get("value") == value else 1
        maker = _NUMBER_PREFIX.get(value)
        if maker is not None:
            editor.textCursor().insertText(maker(counter))
            _set_list_mode(root, "numbering", value)
    _save(root)


def _continue_list(root: QWidget | None) -> None:
    editor = _active_editor(root)
    state = getattr(root, "_text_active_list_mode", None) if root is not None else None
    if editor is None or not isinstance(state, dict):
        return
    mode = state.get("mode")
    value = state.get("value")
    if mode == "bullet":
        prefix = _BULLET_PREFIX.get(str(value), "")
        if prefix:
            editor.textCursor().insertText(prefix)
    elif mode == "numbering":
        counter = int(state.get("counter", 1)) + 1
        maker = _NUMBER_PREFIX.get(str(value))
        if maker is not None:
            state["counter"] = counter
            editor.textCursor().insertText(maker(counter))
    _save(root)


def _menu_action(menu: QMenu, text: str, callback) -> None:
    action = menu.addAction(text)
    action.triggered.connect(lambda checked=False: callback())


def _patch_word_menus(word) -> None:
    def rebuild_text_menus(root: QWidget | None) -> None:
        bar = root.findChild(QWidget, "InlineTextBar") if root is not None else None
        if bar is not None and bar.property("performanceMenus") == PATCH_VERSION:
            return
        buttons = word._buttons(root)
        try:
            from . import text_color_inline_palette_patch as list_settings
        except Exception:
            list_settings = None

        bullet = buttons.get("Bullet")
        if bullet is not None:
            menu = QMenu(bullet)
            _menu_action(menu, "None", lambda w=root: _set_list_mode(w, None, None))
            for text, value in (("●", "filled"), ("○", "hollow"), ("■", "square"), ("◆", "diamond"), ("➤", "arrow"), ("✓", "check")):
                _menu_action(menu, text, lambda w=root, v=value: _insert_prefix(w, "bullet", v))
            menu.addSeparator()
            _menu_action(menu, "Custom bullet settings...", lambda w=root: list_settings._open_settings(w, "bullet") if list_settings is not None else None)
            bullet.setMenu(menu)
            word._set_no_focus(bullet)

        numbering = buttons.get("Numbering")
        if numbering is not None:
            menu = QMenu(numbering)
            _menu_action(menu, "None", lambda w=root: _set_list_mode(w, None, None))
            for text, value in (("1. 2. 3.", "decimal_dot"), ("1) 2) 3)", "decimal_paren"), ("I. II. III.", "roman"), ("A. B. C.", "alpha_upper"), ("a. b. c.", "alpha_lower"), ("i. ii. iii.", "roman_lower")):
                _menu_action(menu, text, lambda w=root, v=value: _insert_prefix(w, "numbering", v))
            menu.addSeparator()
            _menu_action(menu, "Custom numbering settings...", lambda w=root: list_settings._open_settings(w, "numbering") if list_settings is not None else None)
            numbering.setMenu(menu)
            word._set_no_focus(numbering)

        if bar is not None:
            bar.setProperty("performanceMenus", PATCH_VERSION)

    word._rebuild_text_menus = rebuild_text_menus


def _patch_canvas_key(edw) -> None:
    if getattr(edw.EngineeringCanvas, "_performance_text_key_patch", "") == PATCH_VERSION:
        return
    old_key = edw.EngineeringCanvas.keyPressEvent

    def key_press(self, event) -> None:
        editor = getattr(self, "_active_text_editor", None)
        if isinstance(editor, QTextEdit) and editor.hasFocus():
            root = _root_from_canvas(self)
            if event.matches(QKeySequence.StandardKey.SelectAll):
                editor.selectAll()
                event.accept()
                return
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                editor.keyPressEvent(event)
                _continue_list(root)
                _save(root)
                return
            editor.keyPressEvent(event)
            _save(root)
            return
        old_key(self, event)

    edw.EngineeringCanvas.keyPressEvent = key_press
    edw.EngineeringCanvas._performance_text_key_patch = PATCH_VERSION


def _patch_text_paint(runtime) -> None:
    if getattr(runtime, "_performance_text_paint_patch", "") == PATCH_VERSION:
        return
    old_paint_text_object = runtime._paint_text_object

    def paint_text_object(canvas, painter, obj) -> None:
        editor = getattr(canvas, "_active_text_editor", None)
        index = getattr(canvas, "_active_text_editor_index", None)
        if isinstance(editor, QTextEdit) and editor.isVisible() and isinstance(index, int):
            try:
                if 0 <= index < len(canvas.objects) and canvas.objects[index] is obj:
                    # The live QTextEdit is already visible. Painting the stored
                    # text behind it creates the shadow/double-text artifact.
                    return
            except Exception:
                pass
        old_paint_text_object(canvas, painter, obj)

    runtime._paint_text_object = paint_text_object
    runtime._performance_text_paint_patch = PATCH_VERSION


def _normalize_toolbar_once(root: QWidget | None) -> None:
    if root is None:
        return
    bar = root.findChild(QWidget, "InlineTextBar")
    if bar is None:
        return
    if bar.property("performanceGeometry") == PATCH_VERSION:
        return
    command_bar = bar.parentWidget()
    if command_bar is not None and command_bar.objectName() == "CommandBar":
        command_bar.setMinimumHeight(max(command_bar.minimumHeight(), 60))
        command_bar.setFixedHeight(max(command_bar.height(), 60))
    bar.setFixedHeight(max(bar.height(), 50))
    bar.setProperty("performanceGeometry", PATCH_VERSION)


def apply_text_runtime_performance_editing_patch() -> None:
    from . import text_toolbar_word_behavior_patch as word
    from . import ui_text_tool_runtime_fix_patch as runtime
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_runtime_performance_editing_patch", "") == PATCH_VERSION:
        return

    _patch_save_state(word)
    _patch_bold_italic(word)
    _patch_runtime_palette(runtime)
    _patch_word_menus(word)
    _patch_canvas_key(edw)
    _patch_text_paint(runtime)

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _patch_save_state(word)
        _patch_bold_italic(word)
        _patch_runtime_palette(runtime)
        _patch_word_menus(word)
        _patch_canvas_key(edw)
        _patch_text_paint(runtime)
        _normalize_toolbar_once(self)
        QTimer.singleShot(0, lambda root=self: _normalize_toolbar_once(root))
        logging.info("text_runtime_performance_editing_patch: installed version=%s", PATCH_VERSION)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_runtime_performance_editing_patch = PATCH_VERSION

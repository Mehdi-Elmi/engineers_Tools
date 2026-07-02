"""Final lag reduction, Text color toolbar, and editor key ownership patch.

This patch intentionally runs last. It makes the Text toolbar normalization
idempotent, creates the color swatch strip only when missing, prevents old
repeated timers from doing expensive work during maximize/minimize, and owns the
final QTextEdit key behavior so text editing is never routed to object actions.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QKeySequence, QTextCharFormat
from PySide6.QtWidgets import QColorDialog, QGridLayout, QHBoxLayout, QPushButton, QSizePolicy, QTextEdit, QWidget

PATCH_VERSION = "engineering-text-lag-final-2026-07-02-b"

_COLOR_NAMES = {
    "#132238": "Navy",
    "#2f7df6": "Blue",
    "#0f2a44": "Dark blue",
    "#f18a2a": "Orange",
    "#c9342b": "Red",
    "#168a50": "Green",
    "#6e4ad6": "Purple",
    "#536271": "Gray",
}


def _buttons(root: QWidget | None) -> dict[str, QPushButton]:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


def _active_editor(root: QWidget | None):
    canvas = getattr(root, "_canvas", None) if root is not None else None
    return getattr(canvas, "_active_text_editor", None) if canvas is not None else None


def _text_window_from_editor(editor: QTextEdit | None) -> QWidget | None:
    canvas = getattr(editor, "_canvas_owner", None) if editor is not None else None
    return canvas.window() if canvas is not None and hasattr(canvas, "window") else None


def _save_editor(editor: QTextEdit | None) -> None:
    canvas = getattr(editor, "_canvas_owner", None) if editor is not None else None
    if canvas is None:
        return
    try:
        from . import ui_text_tool_final_patch as text_final
        text_final._save_editor_text(canvas, editor)
    except Exception:
        pass
    try:
        from . import text_toolbar_word_behavior_patch as word
        word._save_active_editor(canvas)
    except Exception:
        pass


def _matches(event, standard) -> bool:
    try:
        return bool(event.matches(standard))
    except Exception:
        return False


def _insert_active_list_after_enter(editor: QTextEdit) -> bool:
    root = _text_window_from_editor(editor)
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


def _handle_text_editor_key(editor: QTextEdit, event) -> bool:
    if _matches(event, QKeySequence.StandardKey.Copy):
        editor.copy()
        event.accept()
        return True
    if _matches(event, QKeySequence.StandardKey.Cut):
        editor.cut()
        _save_editor(editor)
        event.accept()
        return True
    if _matches(event, QKeySequence.StandardKey.Paste):
        editor.paste()
        _save_editor(editor)
        event.accept()
        return True
    if _matches(event, QKeySequence.StandardKey.SelectAll):
        editor.selectAll()
        event.accept()
        return True
    if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
        QTextEdit.keyPressEvent(editor, event)
        _save_editor(editor)
        event.accept()
        return True
    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        if _insert_active_list_after_enter(editor):
            event.accept()
            return True
    return False


def _is_text_shortcut(event) -> bool:
    return any(
        _matches(event, standard)
        for standard in (
            QKeySequence.StandardKey.Copy,
            QKeySequence.StandardKey.Cut,
            QKeySequence.StandardKey.Paste,
            QKeySequence.StandardKey.SelectAll,
        )
    ) or event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace)


def _patch_text_key_ownership(edw) -> None:
    try:
        from . import ui_text_tool_final_patch as text_final
        text_final._handle_editor_key = _handle_text_editor_key
    except Exception:
        pass
    try:
        from . import final_focus_editing_icons_patch as focus_patch
        focus_patch._handle_editor_key = _handle_text_editor_key
        focus_patch._is_text_shortcut = _is_text_shortcut
    except Exception:
        pass

    if getattr(edw.EngineeringCanvas, "_lag_final_text_key_owner", "") == PATCH_VERSION:
        return
    old_key = edw.EngineeringCanvas.keyPressEvent

    def key_press(self, event) -> None:
        editor = getattr(self, "_active_text_editor", None)
        if isinstance(editor, QTextEdit) and editor.hasFocus():
            if _handle_text_editor_key(editor, event):
                return
            QTextEdit.keyPressEvent(editor, event)
            _save_editor(editor)
            return
        old_key(self, event)

    edw.EngineeringCanvas.keyPressEvent = key_press
    edw.EngineeringCanvas._lag_final_text_key_owner = PATCH_VERSION


def _apply_text_color(root: QWidget | None, value: str) -> None:
    try:
        from . import ui_text_tool_runtime_fix_patch as runtime
        runtime._apply_text_action(root, "text_color", value)
    except Exception:
        editor = _active_editor(root)
        if editor is not None:
            editor.setTextColor(QColor(value))


def _swatch_style(color: str) -> str:
    return (
        f"QPushButton{{background:{color};border:1px solid #243d58;border-radius:2px;padding:0;margin:0;outline:0;}}"
        "QPushButton:hover{border:2px solid #ff8a35;}"
        "QPushButton:focus{outline:0;border:1px solid #243d58;}"
    )


def _make_swatch(parent: QWidget, root: QWidget | None, color: str) -> QPushButton:
    button = QPushButton(parent)
    button.setObjectName("RuntimeTextColorSwatch")
    button.setProperty("runtimeTextColorControl", True)
    button.setFixedSize(16, 16)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setProperty("colorValue", color)
    button.setToolTip(_COLOR_NAMES.get(color.lower(), color))
    button.setStyleSheet(_swatch_style(color))

    def choose_custom() -> None:
        current = QColor(str(button.property("colorValue") or color))
        picked = QColorDialog.getColor(current, button, "Custom Color")
        if picked.isValid():
            value = picked.name()
            button.setProperty("colorValue", value)
            button.setToolTip(_COLOR_NAMES.get(value.lower(), value))
            button.setStyleSheet(_swatch_style(value))
            _apply_text_color(root, value)

    button.clicked.connect(lambda checked=False, b=button, w=root: _apply_text_color(w, str(b.property("colorValue") or color)))
    button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    button.customContextMenuRequested.connect(lambda _pos: choose_custom())
    return button


def _custom_colors(root: QWidget | None) -> list[str]:
    if root is None:
        return []
    values = getattr(root, "_runtime_text_custom_colors", None)
    if not isinstance(values, list):
        values = []
        setattr(root, "_runtime_text_custom_colors", values)
    return values


def _ensure_color_strip(bar: QWidget | None, root: QWidget | None) -> None:
    if bar is None:
        return
    holder = bar.findChild(QWidget, "RuntimeTextColorPaletteHolder")
    if holder is not None:
        holder.show()
        return

    try:
        from . import ui_text_tool_runtime_fix_patch as runtime
        base_colors = list(getattr(runtime, "_TEXT_COLOR_PALETTE", ()))
    except Exception:
        base_colors = []
    if not base_colors:
        base_colors = list(_COLOR_NAMES.keys())
    colors = base_colors + _custom_colors(root)
    swatch = 16
    gap = 2
    columns = max(4, (len(colors) + 1) // 2)
    palette_width = columns * swatch + max(0, columns - 1) * gap
    palette_height = 2 * swatch + gap

    palette = QWidget(bar)
    palette.setObjectName("RuntimeTextColorPalette")
    palette.setProperty("runtimeTextColorControl", True)
    palette.setFixedSize(palette_width, palette_height)
    grid = QGridLayout(palette)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(gap)
    grid.setVerticalSpacing(gap)
    for index, color in enumerate(colors):
        grid.addWidget(_make_swatch(palette, root, color), index % 2, index // 2)

    add = QPushButton("＋", bar)
    add.setObjectName("RuntimeTextAddColorButton")
    add.setProperty("runtimeTextColorControl", True)
    add.setFixedSize(18, palette_height)
    add.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    add.setToolTip("Add custom color")
    add.setStyleSheet(
        "QPushButton#RuntimeTextAddColorButton{background:#fff2be;border:1px solid #b98920;border-radius:4px;"
        "color:#132238;font-family:'Times New Roman';font-size:11px;font-weight:900;padding:0;margin:0;outline:0;}"
        "QPushButton#RuntimeTextAddColorButton:hover{background:#ffd36d;border-color:#ff8a35;}"
        "QPushButton#RuntimeTextAddColorButton:pressed{background:#f18a2a;color:#ffffff;padding-top:1px;}"
        "QPushButton#RuntimeTextAddColorButton:focus{outline:0;}"
    )

    def add_color() -> None:
        picked = QColorDialog.getColor(QColor("#2f7df6"), add, "Add Custom Color")
        if not picked.isValid():
            return
        value = picked.name()
        values = _custom_colors(root)
        if value not in values and len(values) < 20:
            values.append(value)
        _apply_text_color(root, value)
        holder = bar.findChild(QWidget, "RuntimeTextColorPaletteHolder")
        if holder is not None:
            holder.hide()
            holder.setParent(None)
            holder.deleteLater()
        _ensure_color_strip(bar, root)

    add.clicked.connect(add_color)

    holder = QWidget(bar)
    holder.setObjectName("RuntimeTextColorPaletteHolder")
    holder.setProperty("runtimeTextColorControl", True)
    holder.setFixedSize(palette_width + 20, palette_height)
    row = QHBoxLayout(holder)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(2)
    row.addWidget(palette)
    row.addWidget(add)
    layout = bar.layout()
    if isinstance(layout, QHBoxLayout):
        layout.addWidget(holder)


def _reset_text_defaults(root: QWidget | None) -> None:
    buttons = _buttons(root)
    for name in ("Bold", "Italic"):
        button = buttons.get(name)
        if button is not None and not button.property("userChangedTextStyle"):
            button.setChecked(False)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)


def _patch_bold_italic_user_flags(word) -> None:
    if getattr(word, "_lag_user_style_flags", "") == PATCH_VERSION:
        return
    old_wire = word._wire_toggle_button

    def wire_toggle_button(root: QWidget | None, button: QPushButton, kind: str) -> None:
        old_wire(root, button, kind)
        if not button.property("lagUserFlagWire"):
            button.clicked.connect(lambda checked=False, b=button: b.setProperty("userChangedTextStyle", True))
            button.setProperty("lagUserFlagWire", True)

    word._wire_toggle_button = wire_toggle_button
    word._lag_user_style_flags = PATCH_VERSION


def _patch_word_apply_toolbar(word) -> None:
    if getattr(word, "_lag_fast_apply_patch", "") == PATCH_VERSION:
        return
    old_apply = word._apply_word_toolbar

    def fast_apply_word_toolbar(root: QWidget | None) -> None:
        if root is None:
            return
        bar = root.findChild(QWidget, "InlineTextBar")
        if bar is None:
            return
        if bar.property("lagFastApplied") != PATCH_VERSION:
            old_apply(root)
            bar.setProperty("lagFastApplied", PATCH_VERSION)
            command_bar = bar.parentWidget()
            if command_bar is not None and command_bar.objectName() == "CommandBar":
                command_bar.setMinimumHeight(60)
                command_bar.setFixedHeight(60)
            bar.setFixedHeight(50)
            bar.setMinimumWidth(760)
            bar.setMaximumWidth(980)
            bar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            layout = bar.layout()
            if isinstance(layout, QHBoxLayout):
                layout.setContentsMargins(10, 6, 10, 6)
                layout.setSpacing(5)
            _reset_text_defaults(root)
        _ensure_color_strip(bar, root)
        editor = word._active_editor(root)
        if editor is not None and not editor.property("lagEditorNormalized"):
            word._normalize_editor(root)
            editor.setProperty("lagEditorNormalized", PATCH_VERSION)

    word._apply_word_toolbar = fast_apply_word_toolbar
    word._lag_fast_apply_patch = PATCH_VERSION


def _patch_runtime_style(runtime) -> None:
    if getattr(runtime, "_lag_runtime_style_patch", "") == PATCH_VERSION:
        return
    old_style = runtime._style_inline_text_bar
    old_install = runtime._install_text_color_palette

    def install_text_color_palette(bar: QWidget, root: QWidget | None) -> None:
        _ensure_color_strip(bar, root)

    def style_inline_text_bar(bar: QWidget | None) -> None:
        if bar is None:
            return
        if bar.property("lagRuntimeStyled") != PATCH_VERSION:
            old_style(bar)
            bar.setProperty("lagRuntimeStyled", PATCH_VERSION)
            bar.setFixedHeight(50)
            bar.setMinimumWidth(760)
            bar.setMaximumWidth(980)
            bar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            layout = bar.layout()
            if isinstance(layout, QHBoxLayout):
                layout.setContentsMargins(10, 6, 10, 6)
                layout.setSpacing(5)
        _ensure_color_strip(bar, bar.window())

    runtime._install_text_color_palette = install_text_color_palette
    runtime._style_inline_text_bar = style_inline_text_bar
    runtime._lag_original_install_palette = old_install
    runtime._lag_runtime_style_patch = PATCH_VERSION


def _patch_canvas_defaults(edw) -> None:
    if getattr(edw.EngineeringCanvas, "_lag_text_default_patch", "") == PATCH_VERSION:
        return
    old_release = edw.EngineeringCanvas.mouseReleaseEvent

    def mouse_release(self, event) -> None:
        old_release(self, event)
        root = self.window() if hasattr(self, "window") else None
        _reset_text_defaults(root)
        index = getattr(self, "_active_text_editor_index", None)
        if isinstance(index, int) and 0 <= index < len(getattr(self, "objects", [])):
            buttons = _buttons(root)
            bold = buttons.get("Bold")
            italic = buttons.get("Italic")
            obj = self.objects[index]
            obj.text_bold = bool(bold.isChecked()) if bold is not None else False
            obj.text_italic = bool(italic.isChecked()) if italic is not None else False
            editor = getattr(self, "_active_text_editor", None)
            if editor is not None:
                fmt = QTextCharFormat()
                fmt.setFontWeight(75 if obj.text_bold else 50)
                fmt.setFontItalic(bool(obj.text_italic))
                editor.mergeCurrentCharFormat(fmt)

    edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    edw.EngineeringCanvas._lag_text_default_patch = PATCH_VERSION


def apply_text_lag_final_patch() -> None:
    from . import text_toolbar_word_behavior_patch as word
    from . import ui_text_tool_runtime_fix_patch as runtime
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_lag_final_patch", "") == PATCH_VERSION:
        return

    _patch_bold_italic_user_flags(word)
    _patch_runtime_style(runtime)
    _patch_word_apply_toolbar(word)
    _patch_canvas_defaults(edw)
    _patch_text_key_ownership(edw)

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _patch_bold_italic_user_flags(word)
        _patch_runtime_style(runtime)
        _patch_word_apply_toolbar(word)
        _patch_canvas_defaults(edw)
        _patch_text_key_ownership(edw)
        root = self
        start_bar = getattr(root, "_start_bar_widget", None)
        if start_bar is not None:
            ensure = getattr(start_bar, "_ensure_text_toolbar", None)
            if callable(ensure):
                bar = ensure()
                _ensure_color_strip(bar, root)
        _reset_text_defaults(root)
        QTimer.singleShot(0, lambda r=root: word._apply_word_toolbar(r))
        QTimer.singleShot(0, lambda: _patch_text_key_ownership(edw))
        logging.info("text_lag_final_patch: installed version=%s", PATCH_VERSION)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_lag_final_patch = PATCH_VERSION

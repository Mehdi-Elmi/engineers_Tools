"""Word-like behavior layer for the Engineering Text toolbar.

This patch runs last. It does not create a new toolbar; it normalizes the
already-created InlineTextBar, removes focus rectangles, keeps Bold/Italic off by
default, makes alignment and direction exclusive, forces text editors to save
before closing, and prevents old canvas handlers from leaving hand cursors during
Move/Rotate/Resize drags.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QTextBlockFormat, QTextCursor
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QMenu, QPushButton, QTextEdit, QWidget

PATCH_VERSION = "engineering-text-toolbar-word-behavior-2026-07-02-a"

_ALIGN_TOOLTIPS = ("Align left", "Align center", "Align right", "Justify")
_DIRECTION_TOOLTIPS = ("Left to right", "Right to left")
_ALIGN_TEXT = {
    "Align left": "☰",
    "Align center": "≡",
    "Align right": "☷",
    "Justify": "▤",
}
_DIRECTION_TEXT = {
    "Left to right": "¶→",
    "Right to left": "←¶",
}
_LINE_SPACING_TEXT = "↕"
_ACTION_TO_CURSOR = {
    "move": "move_drag",
    "rotate": "rotate_drag",
    "resize_n": "resize_n",
    "resize_s": "resize_s",
    "resize_e": "resize_e",
    "resize_w": "resize_w",
    "resize_ne": "resize_ne",
    "resize_sw": "resize_sw",
    "resize_nw": "resize_nw",
    "resize_se": "resize_se",
}


def _controls(root: QWidget | None) -> dict:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    return controls if isinstance(controls, dict) else {}


def _buttons(root: QWidget | None) -> dict[str, QPushButton]:
    controls = _controls(root)
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


def _canvas(root: QWidget | None):
    return getattr(root, "_canvas", None) if root is not None else None


def _active_editor(root: QWidget | None) -> QTextEdit | None:
    canvas = _canvas(root)
    editor = getattr(canvas, "_active_text_editor", None) if canvas is not None else None
    return editor if isinstance(editor, QTextEdit) else None


def _set_no_focus(button: QPushButton) -> None:
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setAutoDefault(False)
    button.setDefault(False)
    button.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
    style = button.styleSheet() or ""
    if "word-no-focus" not in style:
        button.setStyleSheet(
            style
            + "\n/* word-no-focus */"
            + "\nQPushButton{outline:0;}"
            + "\nQPushButton:focus{outline:0;border:1px solid #9fb0c5;}"
            + "\nQPushButton:checked:focus{outline:0;border:1px solid #7e5b10;}"
        )
    if not button.property("wordNoFocusClear"):
        button.pressed.connect(button.clearFocus)
        button.released.connect(button.clearFocus)
        button.setProperty("wordNoFocusClear", True)


def _move_cursor_to_end(editor: QTextEdit) -> None:
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)


def _save_active_editor(canvas) -> None:
    editor = getattr(canvas, "_active_text_editor", None)
    if not isinstance(editor, QTextEdit):
        return
    index = getattr(canvas, "_active_text_editor_index", None)
    if not isinstance(index, int) or not (0 <= index < len(getattr(canvas, "objects", []))):
        return
    obj = canvas.objects[index]
    obj.text = editor.toPlainText()
    obj.text_html = editor.toHtml()
    font = editor.currentFont()
    obj.text_font = font.family() or getattr(obj, "text_font", "Times New Roman")
    obj.text_size = int(font.pointSize() if font.pointSize() > 0 else getattr(obj, "text_size", 12))
    obj.text_bold = bool(font.bold())
    obj.text_italic = bool(font.italic())
    obj.text_rtl = editor.layoutDirection() == Qt.LayoutDirection.RightToLeft
    canvas.update()


def _selected_align(root: QWidget | None) -> str:
    buttons = _buttons(root)
    if buttons.get("Align center") is not None and buttons["Align center"].isChecked():
        return "center"
    if buttons.get("Align right") is not None and buttons["Align right"].isChecked():
        return "right"
    if buttons.get("Justify") is not None and buttons["Justify"].isChecked():
        return "justify"
    return "left"


def _selected_direction(root: QWidget | None) -> str:
    buttons = _buttons(root)
    rtl = buttons.get("Right to left")
    return "rtl" if rtl is not None and rtl.isChecked() else "ltr"


def _set_editor_bold(root: QWidget | None, active: bool) -> None:
    editor = _active_editor(root)
    if editor is None:
        return
    font = editor.currentFont()
    font.setBold(active)
    editor.setCurrentFont(font)
    canvas = _canvas(root)
    if canvas is not None:
        _save_active_editor(canvas)


def _set_editor_italic(root: QWidget | None, active: bool) -> None:
    editor = _active_editor(root)
    if editor is None:
        return
    font = editor.currentFont()
    font.setItalic(active)
    editor.setCurrentFont(font)
    canvas = _canvas(root)
    if canvas is not None:
        _save_active_editor(canvas)


def _apply_line_spacing(root: QWidget | None, value: float) -> None:
    editor = _active_editor(root)
    if editor is None:
        return
    cursor = editor.textCursor()
    block = cursor.blockFormat()
    block.setLineHeight(float(value) * 100.0, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
    cursor.mergeBlockFormat(block)
    editor.setTextCursor(cursor)
    _move_cursor_to_end(editor)
    canvas = _canvas(root)
    if canvas is not None:
        _save_active_editor(canvas)


def _apply_align(root: QWidget | None, value: str) -> None:
    editor = _active_editor(root)
    if editor is None:
        return
    mapping = {
        "left": Qt.AlignmentFlag.AlignLeft,
        "center": Qt.AlignmentFlag.AlignCenter,
        "right": Qt.AlignmentFlag.AlignRight,
        "justify": Qt.AlignmentFlag.AlignJustify,
    }
    editor.setAlignment(mapping.get(value, Qt.AlignmentFlag.AlignLeft))
    _move_cursor_to_end(editor)
    canvas = _canvas(root)
    if canvas is not None:
        _save_active_editor(canvas)


def _apply_direction(root: QWidget | None, value: str) -> None:
    editor = _active_editor(root)
    buttons = _buttons(root)
    rtl = value == "rtl"
    if editor is not None:
        direction = Qt.LayoutDirection.RightToLeft if rtl else Qt.LayoutDirection.LeftToRight
        editor.setLayoutDirection(direction)
        editor.viewport().setLayoutDirection(direction)
        align = Qt.AlignmentFlag.AlignRight if rtl else Qt.AlignmentFlag.AlignLeft
        editor.setAlignment(align)
        _move_cursor_to_end(editor)
    target = "Align right" if rtl else "Align left"
    for name in _ALIGN_TOOLTIPS:
        button = buttons.get(name)
        if button is not None:
            button.setChecked(name == target)
    canvas = _canvas(root)
    if canvas is not None:
        _save_active_editor(canvas)


def _install_editor_tail_guard(root: QWidget | None, editor: QTextEdit) -> None:
    if editor.property("wordTailGuard"):
        return

    def keep_saved_and_at_end() -> None:
        # This project currently expects typing to append at the visible end,
        # especially for mixed Persian/English/math input.
        _move_cursor_to_end(editor)
        canvas = _canvas(root)
        if canvas is not None:
            _save_active_editor(canvas)

    editor.textChanged.connect(keep_saved_and_at_end)
    editor.setProperty("wordTailGuard", True)


def _normalize_editor(root: QWidget | None) -> None:
    editor = _active_editor(root)
    if editor is None:
        return
    buttons = _buttons(root)
    font = editor.currentFont() if editor.currentFont() is not None else QFont("Times New Roman", 12)
    font.setBold(bool(buttons.get("Bold").isChecked()) if buttons.get("Bold") is not None else False)
    font.setItalic(bool(buttons.get("Italic").isChecked()) if buttons.get("Italic") is not None else False)
    editor.setCurrentFont(font)
    direction = _selected_direction(root)
    rtl = direction == "rtl"
    layout_direction = Qt.LayoutDirection.RightToLeft if rtl else Qt.LayoutDirection.LeftToRight
    editor.setLayoutDirection(layout_direction)
    editor.viewport().setLayoutDirection(layout_direction)
    align = _selected_align(root)
    if rtl and align == "left":
        align = "right"
    mapping = {
        "left": Qt.AlignmentFlag.AlignLeft,
        "center": Qt.AlignmentFlag.AlignCenter,
        "right": Qt.AlignmentFlag.AlignRight,
        "justify": Qt.AlignmentFlag.AlignJustify,
    }
    editor.setAlignment(mapping.get(align, Qt.AlignmentFlag.AlignLeft))
    _install_editor_tail_guard(root, editor)
    _move_cursor_to_end(editor)
    canvas = _canvas(root)
    if canvas is not None:
        _save_active_editor(canvas)


def _wire_toggle_button(root: QWidget | None, button: QPushButton, kind: str) -> None:
    if button.property("wordBehaviorWired"):
        return
    button.setCheckable(True)
    button.setChecked(False)
    _set_no_focus(button)
    if kind == "bold":
        button.clicked.connect(lambda checked=False, w=root: _set_editor_bold(w, bool(checked)))
    elif kind == "italic":
        button.clicked.connect(lambda checked=False, w=root: _set_editor_italic(w, bool(checked)))
    button.setProperty("wordBehaviorWired", True)


def _build_exclusive_group(bar: QWidget, root: QWidget | None, names: tuple[str, ...], attr: str, default: str, callback) -> None:
    old = getattr(bar, attr, None)
    buttons = _buttons(root)
    if isinstance(old, QButtonGroup):
        for name in names:
            button = buttons.get(name)
            if button is not None:
                button.setChecked(name == default and not any(buttons.get(n) is not None and buttons[n].isChecked() for n in names))
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
        _set_no_focus(button)
        group.addButton(button)
    group.buttonClicked.connect(lambda button, w=root: callback(w, button.toolTip()))
    setattr(bar, attr, group)


def _menu_action(menu: QMenu, text: str, callback) -> None:
    action = menu.addAction(text)
    action.triggered.connect(lambda checked=False: callback())


def _rebuild_text_menus(root: QWidget | None) -> None:
    buttons = _buttons(root)
    try:
        from . import text_color_inline_palette_patch as list_settings
    except Exception:
        list_settings = None

    bullet = buttons.get("Bullet")
    if bullet is not None:
        menu = QMenu(bullet)
        _menu_action(menu, "None", lambda w=root: None)
        for text, value in (("●", "filled"), ("○", "hollow"), ("■", "square"), ("◆", "diamond"), ("➤", "arrow"), ("✓", "check")):
            _menu_action(menu, text, lambda w=root, v=value: _insert_prefix(w, "bullet", v))
        menu.addSeparator()
        _menu_action(menu, "Custom bullet settings...", lambda w=root: list_settings._open_settings(w, "bullet") if list_settings is not None else None)
        bullet.setMenu(menu)
        _set_no_focus(bullet)

    numbering = buttons.get("Numbering")
    if numbering is not None:
        menu = QMenu(numbering)
        _menu_action(menu, "None", lambda w=root: None)
        for text, value in (("1. 2. 3.", "decimal_dot"), ("1) 2) 3)", "decimal_paren"), ("I. II. III.", "roman"), ("A. B. C.", "alpha_upper"), ("a. b. c.", "alpha_lower"), ("i. ii. iii.", "roman_lower")):
            _menu_action(menu, text, lambda w=root, v=value: _insert_prefix(w, "numbering", v))
        menu.addSeparator()
        _menu_action(menu, "Custom numbering settings...", lambda w=root: list_settings._open_settings(w, "numbering") if list_settings is not None else None)
        numbering.setMenu(menu)
        _set_no_focus(numbering)

    line = buttons.get("Line spacing")
    if line is not None:
        menu = QMenu(line)
        for label, value in (("1.0", 1.0), ("1.15", 1.15), ("1.5", 1.5), ("2.0", 2.0)):
            _menu_action(menu, label, lambda w=root, v=value: _apply_line_spacing(w, v))
        menu.addSeparator()
        _menu_action(menu, "Line and paragraph settings...", lambda w=root: _apply_line_spacing(w, 1.15))
        line.setMenu(menu)
        _set_no_focus(line)


def _insert_prefix(root: QWidget | None, command: str, value: str) -> None:
    editor = _active_editor(root)
    if editor is None:
        return
    bullet_values = {
        "filled": "• ",
        "hollow": "○ ",
        "square": "■ ",
        "diamond": "◆ ",
        "arrow": "➤ ",
        "check": "✓ ",
    }
    numbering_values = {
        "decimal_dot": "1. ",
        "decimal_paren": "1) ",
        "roman": "I. ",
        "alpha_upper": "A. ",
        "alpha_lower": "a. ",
        "roman_lower": "i. ",
    }
    prefix = bullet_values.get(value, "") if command == "bullet" else numbering_values.get(value, "")
    if not prefix:
        return
    editor.textCursor().insertText(prefix)
    _move_cursor_to_end(editor)
    canvas = _canvas(root)
    if canvas is not None:
        _save_active_editor(canvas)


def _apply_word_toolbar(root: QWidget | None) -> None:
    if root is None:
        return
    bar = root.findChild(QWidget, "InlineTextBar")
    if bar is None:
        return
    bar.setProperty("wordBehavior", PATCH_VERSION)
    bar.setMinimumWidth(max(bar.minimumWidth(), 1080))
    bar.setMaximumWidth(max(bar.maximumWidth(), 1320))
    bar.setFixedHeight(max(bar.height(), 56))
    layout = bar.layout()
    if isinstance(layout, QHBoxLayout):
        layout.setSpacing(max(layout.spacing(), 7))
        layout.setContentsMargins(12, 7, 12, 7)

    controls = _controls(root)
    for field in (controls.get("font"), controls.get("size")):
        if isinstance(field, QWidget):
            field.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    buttons = _buttons(root)
    for button in buttons.values():
        if isinstance(button, QPushButton):
            _set_no_focus(button)

    bold = buttons.get("Bold")
    italic = buttons.get("Italic")
    if bold is not None:
        bold.setText("B")
        _wire_toggle_button(root, bold, "bold")
    if italic is not None:
        italic.setText("I")
        font = italic.font()
        font.setItalic(True)
        italic.setFont(font)
        _wire_toggle_button(root, italic, "italic")

    for name, label in _ALIGN_TEXT.items():
        button = buttons.get(name)
        if button is not None:
            button.setText(label)
            button.setFixedSize(34, 32)
            _set_no_focus(button)
    for name, label in _DIRECTION_TEXT.items():
        button = buttons.get(name)
        if button is not None:
            button.setText(label)
            button.setFixedSize(42, 32)
            _set_no_focus(button)
    line = buttons.get("Line spacing")
    if line is not None:
        line.setText(_LINE_SPACING_TEXT)
        line.setFixedSize(34, 32)
        _set_no_focus(line)

    _build_exclusive_group(
        bar,
        root,
        _ALIGN_TOOLTIPS,
        "_word_align_group",
        "Align left",
        lambda w, tooltip: _apply_align(w, {
            "Align left": "left",
            "Align center": "center",
            "Align right": "right",
            "Justify": "justify",
        }.get(tooltip, "left")),
    )
    _build_exclusive_group(
        bar,
        root,
        _DIRECTION_TOOLTIPS,
        "_word_direction_group",
        "Left to right",
        lambda w, tooltip: _apply_direction(w, "rtl" if tooltip == "Right to left" else "ltr"),
    )
    _rebuild_text_menus(root)
    _normalize_editor(root)


def _patch_runtime_constants() -> None:
    try:
        from . import ui_text_tool_runtime_fix_patch as runtime
    except Exception:
        return
    runtime._TEXT_SWATCH_SIZE = 16
    runtime._TEXT_SWATCH_GAP = 2
    runtime._TEXT_ADD_BUTTON_WIDTH = 14
    runtime._TEXT_ADD_BUTTON_GAP = 8


def _patch_editor_show_functions() -> None:
    try:
        from . import ui_text_tool_runtime_fix_patch as runtime
        from . import ui_text_tool_final_patch as final_text
    except Exception:
        return
    if getattr(runtime, "_word_behavior_editor_hooks", "") == PATCH_VERSION:
        return

    old_runtime_show = getattr(runtime, "_show_rich_text_editor", None)
    if callable(old_runtime_show):
        def show_rich_text_editor(canvas, index: int) -> None:
            old_runtime_show(canvas, index)
            root = canvas.window() if hasattr(canvas, "window") else None
            _normalize_editor(root)
        runtime._show_rich_text_editor = show_rich_text_editor
        final_text._show_text_editor = show_rich_text_editor

    old_runtime_hide = getattr(runtime, "_hide_rich_text_editor", None)
    if callable(old_runtime_hide):
        def hide_rich_text_editor(canvas) -> None:
            _save_active_editor(canvas)
            old_runtime_hide(canvas)
            canvas.update()
        runtime._hide_rich_text_editor = hide_rich_text_editor
        final_text._hide_text_editor = hide_rich_text_editor

    runtime._word_behavior_editor_hooks = PATCH_VERSION


def _set_project_cursor(canvas, svg, kind: str) -> None:
    try:
        setter = getattr(svg, "_set_cursor_kind", None)
        if callable(setter):
            setter(canvas, kind)
            return
        canvas.setCursor(svg.project_cursor(kind))
    except Exception:
        if kind.startswith("rotate"):
            canvas.setCursor(Qt.CursorShape.CrossCursor)
        elif kind.startswith("resize") or kind.startswith("move"):
            canvas.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            canvas.setCursor(Qt.CursorShape.ArrowCursor)


def _hover_kind(canvas, event) -> str | None:
    try:
        point = canvas._to_canvas_point(event.position())
        _index, action = canvas._hit_test_object(point)
    except Exception:
        return None
    return _ACTION_TO_CURSOR.get(str(action))


def _apply_drag_cursor(canvas, svg, event=None) -> None:
    action = getattr(canvas, "_drag_action", None)
    kind = _ACTION_TO_CURSOR.get(str(action))
    if kind is None and event is not None:
        kind = _hover_kind(canvas, event)
    if kind is not None:
        _set_project_cursor(canvas, svg, kind)


def _patch_canvas_interaction() -> None:
    try:
        from . import svg_cursor_assets_activation_patch as svg
        from . import workspace as edw
    except Exception:
        return
    if getattr(edw.EngineeringCanvas, "_word_canvas_interaction_patch", "") == PATCH_VERSION:
        return

    old_press = edw.EngineeringCanvas.mousePressEvent
    old_move = edw.EngineeringCanvas.mouseMoveEvent
    old_release = edw.EngineeringCanvas.mouseReleaseEvent
    old_key = edw.EngineeringCanvas.keyPressEvent

    def mouse_press(self, event) -> None:
        _save_active_editor(self)
        old_press(self, event)
        _apply_drag_cursor(self, svg, event)

    def mouse_move(self, event) -> None:
        old_move(self, event)
        _apply_drag_cursor(self, svg, event)

    def mouse_release(self, event) -> None:
        old_release(self, event)
        _save_active_editor(self)
        _apply_drag_cursor(self, svg, event)

    def key_press(self, event) -> None:
        editor = getattr(self, "_active_text_editor", None)
        if isinstance(editor, QTextEdit) and editor.hasFocus():
            editor.event(event)
            _save_active_editor(self)
            return
        old_key(self, event)

    edw.EngineeringCanvas.mousePressEvent = mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    edw.EngineeringCanvas.keyPressEvent = key_press
    edw.EngineeringCanvas._word_canvas_interaction_patch = PATCH_VERSION


def apply_text_toolbar_word_behavior_patch() -> None:
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_word_behavior_patch", "") == PATCH_VERSION:
        return

    _patch_runtime_constants()
    _patch_editor_show_functions()
    _patch_canvas_interaction()
    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _patch_runtime_constants()
        _patch_editor_show_functions()
        _patch_canvas_interaction()
        _apply_word_toolbar(self)
        for delay in (0, 80, 250, 700, 1500):
            QTimer.singleShot(delay, lambda root=self: _apply_word_toolbar(root))
        logging.info("text_toolbar_word_behavior_patch: installed version=%s", PATCH_VERSION)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_word_behavior_patch = PATCH_VERSION

"""Word-like behavior layer for the Engineering Text toolbar.

This patch does not create a new toolbar. It normalizes the already-created
InlineTextBar so focus rectangles disappear, Bold/Italic are off by default,
alignment and direction are exclusive, and the color palette uses one owner.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QTextEdit, QWidget

PATCH_VERSION = "engineering-text-toolbar-word-behavior-2026-07-01-a"

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


def _controls(root: QWidget | None) -> dict:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    return controls if isinstance(controls, dict) else {}


def _buttons(root: QWidget | None) -> dict[str, QPushButton]:
    controls = _controls(root)
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


def _active_editor(root: QWidget | None) -> QTextEdit | None:
    canvas = getattr(root, "_canvas", None) if root is not None else None
    editor = getattr(canvas, "_active_text_editor", None) if canvas is not None else None
    return editor if isinstance(editor, QTextEdit) else None


def _set_no_focus(button: QPushButton) -> None:
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setAutoDefault(False)
    button.setDefault(False)
    style = button.styleSheet() or ""
    if "QPushButton:focus" not in style:
        button.setStyleSheet(
            style
            + "\nQPushButton{outline:0;}"
            + "\nQPushButton:focus{border:1px solid #9fb0c5;}"
            + "\nQPushButton:checked:focus{border:1px solid #7e5b10;}"
        )


def _set_editor_bold(root: QWidget | None, active: bool) -> None:
    editor = _active_editor(root)
    if editor is None:
        return
    font = editor.currentFont()
    font.setBold(active)
    editor.setCurrentFont(font)


def _set_editor_italic(root: QWidget | None, active: bool) -> None:
    editor = _active_editor(root)
    if editor is None:
        return
    font = editor.currentFont()
    font.setItalic(active)
    editor.setCurrentFont(font)


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
    target = "Align right" if rtl else "Align left"
    for name in _ALIGN_TOOLTIPS:
        button = buttons.get(name)
        if button is not None:
            button.setChecked(name == target)


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
    if isinstance(old, QButtonGroup):
        return
    buttons = _buttons(root)
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


def _apply_word_toolbar(root: QWidget | None) -> None:
    if root is None:
        return
    bar = root.findChild(QWidget, "InlineTextBar")
    if bar is None:
        return
    bar.setProperty("wordBehavior", PATCH_VERSION)
    bar.setMinimumWidth(max(bar.minimumWidth(), 1040))
    bar.setMaximumWidth(max(bar.maximumWidth(), 1280))
    bar.setFixedHeight(max(bar.height(), 54))
    layout = bar.layout()
    if isinstance(layout, QHBoxLayout):
        layout.setSpacing(max(layout.spacing(), 6))
        layout.setContentsMargins(11, 7, 11, 7)

    controls = _controls(root)
    for field in (controls.get("font"), controls.get("size")):
        if isinstance(field, QWidget):
            field.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    buttons = _buttons(root)
    bold = buttons.get("Bold")
    italic = buttons.get("Italic")
    if bold is not None:
        _wire_toggle_button(root, bold, "bold")
    if italic is not None:
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


def _patch_runtime_constants() -> None:
    try:
        from . import ui_text_tool_runtime_fix_patch as runtime
    except Exception:
        return
    runtime._TEXT_SWATCH_SIZE = 16
    runtime._TEXT_SWATCH_GAP = 2
    runtime._TEXT_ADD_BUTTON_WIDTH = 14
    runtime._TEXT_ADD_BUTTON_GAP = 8


def apply_text_toolbar_word_behavior_patch() -> None:
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_word_behavior_patch", "") == PATCH_VERSION:
        return

    _patch_runtime_constants()
    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _patch_runtime_constants()
        _apply_word_toolbar(self)
        for delay in (0, 80, 250, 700, 1500):
            QTimer.singleShot(delay, lambda root=self: _apply_word_toolbar(root))
        logging.info("text_toolbar_word_behavior_patch: installed version=%s", PATCH_VERSION)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_word_behavior_patch = PATCH_VERSION

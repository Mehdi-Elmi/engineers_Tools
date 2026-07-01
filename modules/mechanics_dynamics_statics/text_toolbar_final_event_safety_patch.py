"""Final safety layer for Text toolbar event behavior.

This runs immediately after text_toolbar_word_behavior_patch. It fixes two
runtime risks without creating any new UI: exclusive button groups must keep the
current checked button during repeated toolbar normalization, and line spacing
must use a safe enum value across PySide6 builds.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence, QTextBlockFormat
from PySide6.QtWidgets import QButtonGroup, QTextEdit, QWidget

PATCH_VERSION = "engineering-text-toolbar-final-event-safety-2026-07-02-a"


def _stable_build_exclusive_group(bar: QWidget, root: QWidget | None, names: tuple[str, ...], attr: str, default: str, callback) -> None:
    from . import text_toolbar_word_behavior_patch as word

    old = getattr(bar, attr, None)
    buttons = word._buttons(root)
    if isinstance(old, QButtonGroup):
        # Repeated toolbar passes must not clear the user's current choice.
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
    word._move_cursor_to_end(editor)
    canvas = word._canvas(root)
    if canvas is not None:
        word._save_active_editor(canvas)


def _patch_canvas_key_handler(edw) -> None:
    if getattr(edw.EngineeringCanvas, "_text_toolbar_final_event_safety_key_patch", "") == PATCH_VERSION:
        return
    old_key = edw.EngineeringCanvas.keyPressEvent

    def key_press(self, event) -> None:
        editor = getattr(self, "_active_text_editor", None)
        if isinstance(editor, QTextEdit) and editor.hasFocus():
            if event.matches(QKeySequence.StandardKey.SelectAll):
                editor.selectAll()
                event.accept()
                return
            event.ignore()
            return
        old_key(self, event)

    edw.EngineeringCanvas.keyPressEvent = key_press
    edw.EngineeringCanvas._text_toolbar_final_event_safety_key_patch = PATCH_VERSION


def apply_text_toolbar_final_event_safety_patch() -> None:
    from . import text_toolbar_word_behavior_patch as word
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_final_event_safety_patch", "") == PATCH_VERSION:
        return

    word._build_exclusive_group = _stable_build_exclusive_group
    word._apply_line_spacing = _safe_apply_line_spacing
    _patch_canvas_key_handler(edw)

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        word._build_exclusive_group = _stable_build_exclusive_group
        word._apply_line_spacing = _safe_apply_line_spacing
        _patch_canvas_key_handler(edw)
        for delay in (0, 120, 400):
            QTimer.singleShot(delay, lambda root=self: word._apply_word_toolbar(root))
        logging.info("text_toolbar_final_event_safety_patch: installed version=%s", PATCH_VERSION)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_final_event_safety_patch = PATCH_VERSION

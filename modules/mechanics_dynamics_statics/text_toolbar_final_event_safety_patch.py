"""Safe final guard for Text editor keyboard priority.

This module runs near the end of the Engineering Design Tools patch chain. It
must stay small: its job is only to protect live text editing from window/canvas
shortcuts. It does not render math, does not repaint text objects, and does not
replace the Text tool architecture.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QTextEdit, QWidget

PATCH_VERSION = "engineering-text-toolbar-final-event-safety-safe-shim-2026-07-02-b"
_TEXT_PRIORITY_FILTER: QObject | None = None


def _editor_from_widget(widget) -> QWidget | None:
    current = widget
    depth = 0
    while isinstance(current, QWidget) and depth < 12:
        if isinstance(current, (QTextEdit, QPlainTextEdit, QLineEdit)):
            return current
        current = current.parentWidget()
        depth += 1
    return None


def _matches(event, standard_key: QKeySequence.StandardKey) -> bool:
    try:
        return bool(event.matches(standard_key))
    except Exception:
        return False


def _save_editor(editor) -> None:
    canvas = getattr(editor, "_canvas_owner", None)
    if canvas is None:
        return
    try:
        from . import ui_text_tool_final_patch as text_final
        text_final._save_editor_text(canvas, editor)
    except Exception:
        logging.exception("text final safety: failed to save active text editor")


def _native_key_press(editor, event) -> None:
    if isinstance(editor, QTextEdit):
        QTextEdit.keyPressEvent(editor, event)
    elif isinstance(editor, QPlainTextEdit):
        QPlainTextEdit.keyPressEvent(editor, event)
    elif isinstance(editor, QLineEdit):
        QLineEdit.keyPressEvent(editor, event)


def _is_protected_text_key(event) -> bool:
    if any(_matches(event, key) for key in (
        QKeySequence.StandardKey.Copy,
        QKeySequence.StandardKey.Cut,
        QKeySequence.StandardKey.Paste,
        QKeySequence.StandardKey.SelectAll,
    )):
        return True
    return event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete)


def _handle_text_editor_key(editor, event) -> bool:
    if _matches(event, QKeySequence.StandardKey.Copy):
        editor.copy(); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.Cut):
        editor.cut(); _save_editor(editor); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.Paste):
        editor.paste(); _save_editor(editor); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.SelectAll):
        editor.selectAll(); event.accept(); return True
    if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
        _native_key_press(editor, event)
        _save_editor(editor)
        event.accept()
        return True
    return False


class _TextPriorityFilter(QObject):
    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        editor = _editor_from_widget(watched)
        if editor is None:
            return False
        if event.type() == QEvent.Type.ShortcutOverride and _is_protected_text_key(event):
            event.accept()
            return True
        if event.type() == QEvent.Type.KeyPress:
            return _handle_text_editor_key(editor, event)
        return False


def _install_text_priority_filter() -> None:
    global _TEXT_PRIORITY_FILTER
    app = QApplication.instance()
    if app is None:
        return
    if _TEXT_PRIORITY_FILTER is not None:
        try:
            app.removeEventFilter(_TEXT_PRIORITY_FILTER)
        except Exception:
            pass
    _TEXT_PRIORITY_FILTER = _TextPriorityFilter(app)
    app.installEventFilter(_TEXT_PRIORITY_FILTER)


def _patch_text_tool_handler() -> None:
    try:
        from . import ui_text_tool_final_patch as text_final
        text_final._handle_editor_key = _handle_text_editor_key
    except Exception:
        logging.exception("text final safety: failed to patch text tool key handler")


def apply_text_toolbar_final_event_safety_patch() -> None:
    """Protect active text editing without changing rendering or math behavior."""
    try:
        from . import workspace as edw
    except Exception:
        logging.exception("text_toolbar_final_event_safety_patch: workspace import failed")
        return

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_final_event_safety_patch", "") == PATCH_VERSION:
        return

    _patch_text_tool_handler()
    _install_text_priority_filter()
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_final_event_safety_patch = PATCH_VERSION
    logging.info("text_toolbar_final_event_safety_patch: text priority guard installed version=%s", PATCH_VERSION)

"""Final text stability guard for Engineering Design Tools.

This patch is intentionally narrow. It protects Text Box objects and text-editor
keyboard behavior without changing file/menu/object commands.
"""

from __future__ import annotations

import copy
import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QTextEdit

PATCH_VERSION = "engineering-text-stability-guard-2026-07-02-a"

_TEXT_ATTR_DEFAULTS: dict[str, object] = {
    "is_text_box": False,
    "text": "",
    "text_html": "",
    "text_font": "Times New Roman",
    "text_size": 12,
    "text_bold": False,
    "text_italic": False,
    "text_rtl": False,
    "text_color": "#132238",
    "text_align": "left",
    "text_line_spacing": 1.0,
}


def _safe_copy_value(value):
    try:
        return copy.deepcopy(value)
    except Exception:
        return value


def _install_canvas_object_clone_guard(edw) -> None:
    cls = edw.CanvasObject
    if getattr(cls, "_text_stability_clone_guard", "") == PATCH_VERSION:
        return
    old_clone = cls.clone
    dataclass_fields = set(getattr(cls, "__dataclass_fields__", {}) or {})

    def clone_with_runtime_attrs(self, offset=None):
        copied = old_clone(self, offset)
        for name, value in vars(self).items():
            if name in dataclass_fields:
                continue
            try:
                setattr(copied, name, _safe_copy_value(value))
            except Exception:
                logging.exception("text_stability_guard: failed copying runtime attr %s", name)
        if bool(getattr(self, "is_text_box", False)):
            for name, default in _TEXT_ATTR_DEFAULTS.items():
                if not hasattr(copied, name):
                    setattr(copied, name, _safe_copy_value(getattr(self, name, default)))
        return copied

    cls.clone = clone_with_runtime_attrs
    cls._text_stability_clone_guard = PATCH_VERSION


def _matches(event, standard) -> bool:
    try:
        return bool(event.matches(standard))
    except Exception:
        return False


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


def _insert_active_list_after_enter(editor: QTextEdit) -> bool:
    try:
        from . import text_lag_final_patch as lag
        return bool(lag._insert_active_list_after_enter(editor))
    except Exception:
        return False


def _delete_from_editor(editor: QTextEdit, *, previous: bool) -> None:
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.removeSelectedText()
    elif previous:
        cursor.deletePreviousChar()
    else:
        cursor.deleteChar()
    editor.setTextCursor(cursor)
    _save_editor(editor)


def _safe_text_editor_key_handler(editor: QTextEdit, event) -> bool:
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
    if event.key() == Qt.Key.Key_Backspace:
        _delete_from_editor(editor, previous=True)
        event.accept()
        return True
    if event.key() == Qt.Key.Key_Delete:
        _delete_from_editor(editor, previous=False)
        event.accept()
        return True
    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        if _insert_active_list_after_enter(editor):
            event.accept()
            return True
    return False


def _safe_is_text_shortcut(event) -> bool:
    return any(
        _matches(event, standard)
        for standard in (
            QKeySequence.StandardKey.Copy,
            QKeySequence.StandardKey.Cut,
            QKeySequence.StandardKey.Paste,
            QKeySequence.StandardKey.SelectAll,
        )
    ) or event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace)


def _install_text_key_guard(edw) -> None:
    try:
        from . import ui_text_tool_final_patch as text_final
        text_final._handle_editor_key = _safe_text_editor_key_handler
    except Exception:
        pass
    try:
        from . import text_lag_final_patch as lag
        lag._handle_text_editor_key = _safe_text_editor_key_handler
        lag._is_text_shortcut = _safe_is_text_shortcut
    except Exception:
        pass
    try:
        from . import text_line_math_symbols_patch as line_patch
        # This module patches the final handlers earlier; keep its final reference safe too.
        line_patch._safe_text_editor_key_handler = _safe_text_editor_key_handler
    except Exception:
        pass
    try:
        from . import final_focus_editing_icons_patch as focus_patch
        focus_patch._handle_editor_key = _safe_text_editor_key_handler
        focus_patch._is_text_shortcut = _safe_is_text_shortcut
    except Exception:
        pass

    if getattr(edw.EngineeringCanvas, "_text_stability_key_guard", "") == PATCH_VERSION:
        return
    old_key_press = edw.EngineeringCanvas.keyPressEvent

    def key_press(self, event) -> None:
        editor = getattr(self, "_active_text_editor", None)
        if isinstance(editor, QTextEdit) and editor.isVisible() and editor.hasFocus():
            if _safe_text_editor_key_handler(editor, event):
                return
            QTextEdit.keyPressEvent(editor, event)
            _save_editor(editor)
            return
        old_key_press(self, event)

    edw.EngineeringCanvas.keyPressEvent = key_press
    edw.EngineeringCanvas._text_stability_key_guard = PATCH_VERSION


def _install_text_defaults_guard(edw) -> None:
    if getattr(edw.EngineeringCanvas, "_text_stability_defaults_guard", "") == PATCH_VERSION:
        return
    old_emit = edw.EngineeringCanvas._emit_object_changes

    def emit_object_changes(self) -> None:
        for obj in getattr(self, "objects", []):
            if bool(getattr(obj, "is_text_box", False)):
                for name, default in _TEXT_ATTR_DEFAULTS.items():
                    if not hasattr(obj, name):
                        setattr(obj, name, _safe_copy_value(default))
        old_emit(self)

    edw.EngineeringCanvas._emit_object_changes = emit_object_changes
    edw.EngineeringCanvas._text_stability_defaults_guard = PATCH_VERSION


def apply_text_stability_guard_patch() -> None:
    try:
        from . import workspace as edw
    except Exception:
        logging.exception("text_stability_guard: workspace import failed")
        return
    _install_canvas_object_clone_guard(edw)
    _install_text_defaults_guard(edw)
    _install_text_key_guard(edw)
    logging.info("text_stability_guard: installed version=%s", PATCH_VERSION)

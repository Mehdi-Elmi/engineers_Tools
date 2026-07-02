"""Safe final guard for Text editor keyboard priority and TextBox copying.

This module runs near the end of the Engineering Design Tools patch chain. It
must stay small: it protects live text editing from window/canvas shortcuts and
keeps TextBox metadata alive during canvas copy/paste. It does not render math,
does not repaint text objects, and does not replace the Text tool architecture.
"""

from __future__ import annotations

import copy
import logging

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QTextEdit, QWidget

PATCH_VERSION = "engineering-text-toolbar-final-event-safety-safe-shim-2026-07-02-c"
_TEXT_PRIORITY_FILTER: QObject | None = None
_TEXTBOX_EXTRA_FIELDS = (
    "is_text_box",
    "text",
    "text_html",
    "text_font",
    "text_size",
    "text_bold",
    "text_italic",
    "text_rtl",
    "text_align",
    "text_color",
    "line_spacing",
    "bullet_settings",
    "numbering_settings",
    "list_mode",
    "list_prefix",
)
_CANVAS_BASE_FIELDS = {"path", "pixmap", "rect", "rotation", "name", "visible", "locked", "rotation_handle_visible", "group_id"}


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


def _copy_extra_metadata(source, target) -> None:
    for key, value in getattr(source, "__dict__", {}).items():
        if key in _CANVAS_BASE_FIELDS:
            continue
        try:
            setattr(target, key, copy.deepcopy(value))
        except Exception:
            setattr(target, key, value)


def _patch_canvas_clone(edw) -> None:
    cls = getattr(edw, "CanvasObject", None)
    if cls is None or getattr(cls, "_text_metadata_clone_patch", "") == PATCH_VERSION:
        return
    original_clone = cls.clone

    def clone(self, offset=None):
        copied = original_clone(self, offset)
        _copy_extra_metadata(self, copied)
        return copied

    cls.clone = clone
    cls._text_metadata_clone_patch = PATCH_VERSION


def _patch_project_clipboard_metadata() -> None:
    try:
        from . import file_export_project_fixes as export_patch
    except Exception:
        return
    if getattr(export_patch, "_text_metadata_clipboard_patch", "") == PATCH_VERSION:
        return
    original_to_data = export_patch._object_to_data
    original_to_object = export_patch._data_to_object

    def object_to_data(obj):
        data = original_to_data(obj)
        extras = {}
        for field in _TEXTBOX_EXTRA_FIELDS:
            if hasattr(obj, field):
                value = getattr(obj, field)
                if isinstance(value, (str, int, float, bool, type(None), list, tuple, dict)):
                    extras[field] = value
        if extras:
            data["extras"] = extras
        return data

    def data_to_object(edw, item):
        obj = original_to_object(edw, item)
        extras = item.get("extras")
        if isinstance(extras, dict):
            for key, value in extras.items():
                setattr(obj, str(key), value)
        return obj

    export_patch._object_to_data = object_to_data
    export_patch._data_to_object = data_to_object
    export_patch._text_metadata_clipboard_patch = PATCH_VERSION


def apply_text_toolbar_final_event_safety_patch() -> None:
    """Protect active text editing and preserve TextBox metadata on copy/paste."""
    try:
        from . import workspace as edw
    except Exception:
        logging.exception("text_toolbar_final_event_safety_patch: workspace import failed")
        return

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_final_event_safety_patch", "") == PATCH_VERSION:
        return

    _patch_text_tool_handler()
    _install_text_priority_filter()
    _patch_canvas_clone(edw)
    _patch_project_clipboard_metadata()
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_final_event_safety_patch = PATCH_VERSION
    logging.info("text_toolbar_final_event_safety_patch: text priority and metadata guard installed version=%s", PATCH_VERSION)

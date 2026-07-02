"""Focused Text Box copy and key handling fixes.

This single patch directly fixes three tested areas: QTextEdit undo/delete keys,
saving active Text Box content before canvas copy/cut, and preserving Text Box
attributes during clone/paste.
"""

from __future__ import annotations

import copy
import logging

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QTextEdit, QWidget

PATCH_VERSION = "engineering-text-stability-guard-2026-07-02-d"

_TEXT_ATTRS = (
    "is_text_box",
    "text",
    "text_html",
    "text_font",
    "text_size",
    "text_bold",
    "text_italic",
    "text_rtl",
    "text_color",
    "text_align",
    "text_line_spacing",
)

_TEXT_DEFAULTS = {
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


def _copy_value(value):
    try:
        return copy.deepcopy(value)
    except Exception:
        return value


def _copy_text_attrs(source, target) -> None:
    if not bool(getattr(source, "is_text_box", False)):
        return
    for name in _TEXT_ATTRS:
        setattr(target, name, _copy_value(getattr(source, name, _TEXT_DEFAULTS.get(name))))


def _normalize_text_box(obj) -> None:
    if not bool(getattr(obj, "is_text_box", False)):
        return
    for name, default in _TEXT_DEFAULTS.items():
        if not hasattr(obj, name):
            setattr(obj, name, _copy_value(default))


def _canvas_from_editor(editor: QWidget | None):
    current = editor
    depth = 0
    while isinstance(current, QWidget) and depth < 12:
        if hasattr(current, "objects") and hasattr(current, "selected_indices"):
            return current
        current = current.parentWidget()
        depth += 1
    return getattr(editor, "_canvas_owner", None) if editor is not None else None


def _save_editor(editor: QTextEdit | None) -> None:
    if not isinstance(editor, QTextEdit):
        return
    canvas = _canvas_from_editor(editor)
    if canvas is None:
        return
    try:
        from . import ui_text_tool_final_patch as text_final
        text_final._save_editor_text(canvas, editor)
    except Exception:
        pass
    try:
        index = getattr(canvas, "_active_text_editor_index", None)
        if isinstance(index, int) and 0 <= index < len(getattr(canvas, "objects", [])):
            obj = canvas.objects[index]
            obj.text = editor.toPlainText()
            obj.text_html = editor.toHtml()
            _normalize_text_box(obj)
    except Exception:
        logging.exception("text_stability_guard: save editor failed")


def _shortcut(event, standard) -> bool:
    try:
        return bool(event.matches(standard))
    except Exception:
        return False


def _handle_text_key(editor: QTextEdit, event) -> bool:
    if _shortcut(event, QKeySequence.StandardKey.Undo):
        editor.undo()
        _save_editor(editor)
        event.accept()
        return True
    if _shortcut(event, QKeySequence.StandardKey.Redo):
        editor.redo()
        _save_editor(editor)
        event.accept()
        return True
    if _shortcut(event, QKeySequence.StandardKey.Copy):
        editor.copy()
        event.accept()
        return True
    if _shortcut(event, QKeySequence.StandardKey.Cut):
        editor.cut()
        _save_editor(editor)
        event.accept()
        return True
    if _shortcut(event, QKeySequence.StandardKey.Paste):
        editor.paste()
        _save_editor(editor)
        event.accept()
        return True
    if _shortcut(event, QKeySequence.StandardKey.SelectAll):
        editor.selectAll()
        event.accept()
        return True
    if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
        QTextEdit.keyPressEvent(editor, event)
        _save_editor(editor)
        event.accept()
        return True
    return False


def _is_text_shortcut(event) -> bool:
    return any(
        _shortcut(event, standard)
        for standard in (
            QKeySequence.StandardKey.Undo,
            QKeySequence.StandardKey.Redo,
            QKeySequence.StandardKey.Copy,
            QKeySequence.StandardKey.Cut,
            QKeySequence.StandardKey.Paste,
            QKeySequence.StandardKey.SelectAll,
        )
    ) or event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete)


def _patch_canvas_text_editor() -> None:
    try:
        from . import ui_text_tool_final_patch as text_final
        editor_cls = text_final._CanvasTextEdit
    except Exception:
        return
    if getattr(editor_cls, "_text_stability_editor_guard", "") == PATCH_VERSION:
        return
    old_event = editor_cls.event

    def event(self, event) -> bool:
        if event.type() == QEvent.Type.ShortcutOverride and _is_text_shortcut(event):
            event.accept()
            return True
        return old_event(self, event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if _handle_text_key(self, event):
            return
        QTextEdit.keyPressEvent(self, event)
        _save_editor(self)

    editor_cls.event = event
    editor_cls.keyPressEvent = keyPressEvent
    editor_cls._text_stability_editor_guard = PATCH_VERSION

    try:
        text_final._handle_editor_key = _handle_text_key
    except Exception:
        pass


def _patch_app_text_filter() -> None:
    try:
        from src.engineers_tools.app import engineering_text_editor_patch as app_text
        filter_cls = app_text._TextEditorPriorityFilter
    except Exception:
        return
    if getattr(filter_cls, "_text_stability_filter_guard", "") == PATCH_VERSION:
        return
    old_event_filter = filter_cls.eventFilter

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.KeyPress:
            editor = watched if isinstance(watched, QTextEdit) else None
            if editor is not None and editor.isVisible() and editor.isEnabled() and editor.hasFocus():
                if _handle_text_key(editor, event):
                    return True
        return old_event_filter(self, watched, event)

    filter_cls.eventFilter = eventFilter
    filter_cls._text_stability_filter_guard = PATCH_VERSION


def _patch_clone(edw) -> None:
    cls = edw.CanvasObject
    if getattr(cls, "_text_stability_clone_guard", "") == PATCH_VERSION:
        return
    old_clone = cls.clone

    def clone(self, offset=None):
        copied = old_clone(self, offset)
        _copy_text_attrs(self, copied)
        return copied

    cls.clone = clone
    cls._text_stability_clone_guard = PATCH_VERSION


def _patch_canvas_copy(edw) -> None:
    canvas_cls = edw.EngineeringCanvas
    if getattr(canvas_cls, "_text_stability_copy_guard", "") == PATCH_VERSION:
        return
    old_copy = canvas_cls.copy_selection
    old_cut = canvas_cls.cut_selection
    old_paste = canvas_cls.paste_selection

    def sync(self) -> None:
        editor = getattr(self, "_active_text_editor", None)
        if isinstance(editor, QTextEdit):
            _save_editor(editor)
        for obj in getattr(self, "objects", []):
            _normalize_text_box(obj)

    def copy_selection(self) -> None:
        sync(self)
        old_copy(self)
        for obj in getattr(self, "_clipboard", []):
            _normalize_text_box(obj)

    def cut_selection(self) -> None:
        sync(self)
        old_cut(self)
        for obj in getattr(self, "_clipboard", []):
            _normalize_text_box(obj)

    def paste_selection(self) -> None:
        for obj in getattr(self, "_clipboard", []):
            _normalize_text_box(obj)
        old_paste(self)
        for obj in getattr(self, "objects", []):
            _normalize_text_box(obj)

    canvas_cls.copy_selection = copy_selection
    canvas_cls.cut_selection = cut_selection
    canvas_cls.paste_selection = paste_selection
    canvas_cls._text_stability_copy_guard = PATCH_VERSION


def apply_text_stability_guard_patch() -> None:
    try:
        from . import workspace as edw
    except Exception:
        logging.exception("text_stability_guard: workspace import failed")
        return
    _patch_canvas_text_editor()
    _patch_app_text_filter()
    _patch_clone(edw)
    _patch_canvas_copy(edw)
    logging.info("text_stability_guard: installed version=%s", PATCH_VERSION)

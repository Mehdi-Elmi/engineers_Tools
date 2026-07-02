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

PATCH_VERSION = "engineering-text-stability-guard-2026-07-02-e"

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


def _text_editor_from_widget(widget) -> QTextEdit | None:
    current = widget
    depth = 0
    while isinstance(current, QWidget) and depth < 10:
        if isinstance(current, QTextEdit):
            return current
        current = current.parentWidget()
        depth += 1
    return None


def _widget_inside(widget: QWidget | None, parent: QWidget | None) -> bool:
    current = widget
    depth = 0
    while isinstance(current, QWidget) and depth < 12:
        if current is parent:
            return True
        current = current.parentWidget()
        depth += 1
    return False


def _focused_text_editor() -> QTextEdit | None:
    app = QApplication.instance()
    focus = app.focusWidget() if app is not None else None
    editor = _text_editor_from_widget(focus)
    if editor is not None and editor.isVisible() and editor.isEnabled() and _widget_inside(focus, editor):
        return editor
    return None


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


def _explicit_shortcut(event, key, *, ctrl=False, shift=False) -> bool:
    modifiers = event.modifiers()
    has_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
    has_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
    return event.key() == key and has_ctrl == ctrl and has_shift == shift


def _delete_text(editor: QTextEdit, *, previous: bool) -> None:
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.removeSelectedText()
    elif previous:
        cursor.deletePreviousChar()
    else:
        cursor.deleteChar()
    editor.setTextCursor(cursor)
    _save_editor(editor)


def _handle_text_key(editor: QTextEdit, event) -> bool:
    if _shortcut(event, QKeySequence.StandardKey.Undo) or _explicit_shortcut(event, Qt.Key.Key_Z, ctrl=True):
        editor.undo()
        _save_editor(editor)
        event.accept()
        return True
    if _shortcut(event, QKeySequence.StandardKey.Redo) or _explicit_shortcut(event, Qt.Key.Key_Y, ctrl=True) or _explicit_shortcut(event, Qt.Key.Key_Z, ctrl=True, shift=True):
        editor.redo()
        _save_editor(editor)
        event.accept()
        return True
    if _shortcut(event, QKeySequence.StandardKey.Copy) or _explicit_shortcut(event, Qt.Key.Key_C, ctrl=True):
        editor.copy()
        event.accept()
        return True
    if _shortcut(event, QKeySequence.StandardKey.Cut) or _explicit_shortcut(event, Qt.Key.Key_X, ctrl=True):
        editor.cut()
        _save_editor(editor)
        event.accept()
        return True
    if _shortcut(event, QKeySequence.StandardKey.Paste) or _explicit_shortcut(event, Qt.Key.Key_V, ctrl=True):
        editor.paste()
        _save_editor(editor)
        event.accept()
        return True
    if _shortcut(event, QKeySequence.StandardKey.SelectAll) or _explicit_shortcut(event, Qt.Key.Key_A, ctrl=True):
        editor.selectAll()
        event.accept()
        return True
    if event.key() == Qt.Key.Key_Backspace:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            QTextEdit.keyPressEvent(editor, event)
            _save_editor(editor)
        else:
            _delete_text(editor, previous=True)
        event.accept()
        return True
    if event.key() == Qt.Key.Key_Delete:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            QTextEdit.keyPressEvent(editor, event)
            _save_editor(editor)
        else:
            _delete_text(editor, previous=False)
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
    ) or event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete, Qt.Key.Key_Z, Qt.Key.Key_Y)


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


def _run_strict_text_action(action: str) -> bool:
    editor = _focused_text_editor()
    if editor is None:
        return False
    if action == "copy":
        editor.copy()
        return True
    if action == "cut":
        editor.cut()
        _save_editor(editor)
        return True
    if action == "paste":
        editor.paste()
        _save_editor(editor)
        return True
    if action == "delete":
        _delete_text(editor, previous=False)
        return True
    if action == "select_all":
        editor.selectAll()
        return True
    return False


def _patch_app_text_filter() -> None:
    try:
        from src.engineers_tools.app import engineering_text_editor_patch as app_text
        filter_cls = app_text._TextEditorPriorityFilter
    except Exception:
        return

    app_text._active_editor = _focused_text_editor
    app_text._run_text_action = _run_strict_text_action

    if getattr(filter_cls, "_text_stability_filter_guard", "") == PATCH_VERSION:
        return
    old_event_filter = filter_cls.eventFilter

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.ShortcutOverride):
            editor = _text_editor_from_widget(watched)
            if editor is not None and editor.isVisible() and editor.isEnabled() and _widget_inside(QApplication.focusWidget(), editor):
                if event.type() == QEvent.Type.ShortcutOverride and _is_text_shortcut(event):
                    event.accept()
                    return True
                if event.type() == QEvent.Type.KeyPress and _handle_text_key(editor, event):
                    return True
        return old_event_filter(self, watched, event)

    filter_cls.eventFilter = eventFilter
    filter_cls._text_stability_filter_guard = PATCH_VERSION


def _patch_workspace_shortcuts(edw) -> None:
    workspace_cls = edw.EngineeringDesignWorkspace
    if getattr(workspace_cls, "_text_stability_workspace_shortcut_guard", "") == PATCH_VERSION:
        return

    def selected_canvas(self):
        canvas = getattr(self, "_canvas", None)
        if isinstance(canvas, edw.EngineeringCanvas) and getattr(canvas, "selected_indices", None):
            return canvas
        return None

    def copy_action(self):
        canvas = selected_canvas(self)
        if canvas is not None and canvas.copy_selection():
            self._set_status("Copy")
            return
        super(workspace_cls, self)._copy()

    def cut_action(self):
        canvas = selected_canvas(self)
        if canvas is not None and canvas.cut_selection():
            self._set_status("Cut")
            return
        super(workspace_cls, self)._cut()

    def paste_action(self):
        canvas = getattr(self, "_canvas", None)
        if isinstance(canvas, edw.EngineeringCanvas) and canvas.paste_selection():
            self._set_status("Paste")
            return
        super(workspace_cls, self)._paste()

    workspace_cls._copy = copy_action
    workspace_cls._cut = cut_action
    workspace_cls._paste = paste_action
    workspace_cls._text_stability_workspace_shortcut_guard = PATCH_VERSION


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

    def copy_selection(self) -> bool:
        sync(self)
        result = bool(old_copy(self))
        for obj in getattr(self, "_clipboard", []):
            _normalize_text_box(obj)
        return result

    def cut_selection(self) -> bool:
        sync(self)
        result = bool(old_cut(self))
        for obj in getattr(self, "_clipboard", []):
            _normalize_text_box(obj)
        return result

    def paste_selection(self) -> bool:
        for obj in getattr(self, "_clipboard", []):
            _normalize_text_box(obj)
        result = bool(old_paste(self))
        for obj in getattr(self, "objects", []):
            _normalize_text_box(obj)
        return result

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
    _patch_workspace_shortcuts(edw)
    _patch_clone(edw)
    _patch_canvas_copy(edw)
    logging.info("text_stability_guard: installed version=%s", PATCH_VERSION)

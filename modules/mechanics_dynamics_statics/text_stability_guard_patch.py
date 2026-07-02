"""Final text stability guard for Engineering Design Tools.

This patch is intentionally narrow. It protects Text Box objects and text-editor
keyboard behavior without changing file/menu/object commands.
"""

from __future__ import annotations

import copy
import logging

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QTextEdit, QWidget

PATCH_VERSION = "engineering-text-stability-guard-2026-07-02-b"
_TEXT_STABILITY_FILTER: QObject | None = None

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


def _is_text_editor(widget) -> bool:
    return isinstance(widget, (QTextEdit, QPlainTextEdit, QLineEdit))


def _editor_from_widget(widget) -> QWidget | None:
    current = widget
    depth = 0
    while isinstance(current, QWidget) and depth < 10:
        if _is_text_editor(current):
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


def _focused_text_editor() -> QWidget | None:
    app = QApplication.instance()
    focus = app.focusWidget() if app is not None else None
    editor = _editor_from_widget(focus)
    if editor is not None and editor.isVisible() and editor.isEnabled() and _widget_inside(focus, editor):
        return editor
    return None


def _canvas_from_editor(editor: QWidget | None):
    if editor is None:
        return None
    canvas = getattr(editor, "_canvas_owner", None)
    if canvas is not None:
        return canvas
    current = editor.parentWidget()
    depth = 0
    while isinstance(current, QWidget) and depth < 12:
        if hasattr(current, "objects") and hasattr(current, "selected_indices"):
            return current
        current = current.parentWidget()
        depth += 1
    return None


def _save_editor(editor: QWidget | None) -> None:
    canvas = _canvas_from_editor(editor)
    if canvas is None or not isinstance(editor, QTextEdit):
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


def _native_text_key(editor: QWidget, event) -> bool:
    try:
        if isinstance(editor, QTextEdit):
            QTextEdit.keyPressEvent(editor, event)
        elif isinstance(editor, QPlainTextEdit):
            QPlainTextEdit.keyPressEvent(editor, event)
        elif isinstance(editor, QLineEdit):
            QLineEdit.keyPressEvent(editor, event)
        else:
            return False
        _save_editor(editor)
        event.accept()
        return True
    except Exception:
        logging.exception("text_stability_guard: native text key failed")
        return False


def _safe_text_editor_key_handler(editor: QTextEdit, event) -> bool:
    if _matches(event, QKeySequence.StandardKey.Undo):
        editor.undo()
        _save_editor(editor)
        event.accept()
        return True
    if _matches(event, QKeySequence.StandardKey.Redo):
        editor.redo()
        _save_editor(editor)
        event.accept()
        return True
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
        # Let Qt handle normal deletion and Ctrl+Backspace/Ctrl+Delete so the
        # operation stays on the QTextEdit undo stack and word-wise deletion works.
        return _native_text_key(editor, event)
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
            QKeySequence.StandardKey.Undo,
            QKeySequence.StandardKey.Redo,
        )
    ) or event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace)


def _run_focused_text_action(action: str) -> bool:
    editor = _focused_text_editor()
    if editor is None:
        return False
    if action == "copy" and hasattr(editor, "copy"):
        editor.copy()
        return True
    if action == "cut" and hasattr(editor, "cut"):
        editor.cut()
        _save_editor(editor)
        return True
    if action == "paste" and hasattr(editor, "paste"):
        editor.paste()
        _save_editor(editor)
        return True
    if action == "delete":
        if isinstance(editor, QTextEdit):
            cursor = editor.textCursor()
            if cursor.hasSelection():
                cursor.removeSelectedText()
            else:
                cursor.deleteChar()
            editor.setTextCursor(cursor)
            _save_editor(editor)
            return True
        if hasattr(editor, "del_"):
            editor.del_()
            return True
    if action == "select_all" and hasattr(editor, "selectAll"):
        editor.selectAll()
        return True
    return False


def _install_external_text_priority_guard() -> None:
    try:
        from src.engineers_tools.app import engineering_text_editor_patch as app_text
    except Exception:
        return

    app_text._active_editor = _focused_text_editor
    app_text._run_text_action = _run_focused_text_action


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
        if isinstance(editor, QTextEdit) and editor.isVisible() and _widget_inside(QApplication.focusWidget(), editor):
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


class _FinalTextEditorEventFilter(QObject):
    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if event.type() != QEvent.Type.KeyPress:
            return False
        editor = _editor_from_widget(watched)
        if not isinstance(editor, QTextEdit):
            return False
        if not editor.isVisible() or not editor.isEnabled() or not _widget_inside(QApplication.focusWidget(), editor):
            return False
        if _safe_text_editor_key_handler(editor, event):
            return True
        return False


def _install_final_text_event_filter() -> None:
    global _TEXT_STABILITY_FILTER
    app = QApplication.instance()
    if app is None or _TEXT_STABILITY_FILTER is not None:
        return
    _TEXT_STABILITY_FILTER = _FinalTextEditorEventFilter()
    app.installEventFilter(_TEXT_STABILITY_FILTER)


def apply_text_stability_guard_patch() -> None:
    try:
        from . import workspace as edw
    except Exception:
        logging.exception("text_stability_guard: workspace import failed")
        return
    _install_canvas_object_clone_guard(edw)
    _install_text_defaults_guard(edw)
    _install_external_text_priority_guard()
    _install_text_key_guard(edw)
    _install_final_text_event_filter()
    logging.info("text_stability_guard: installed version=%s", PATCH_VERSION)

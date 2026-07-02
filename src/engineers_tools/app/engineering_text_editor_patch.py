"""Text-editor priority fixes for Engineering Design Tools."""

from __future__ import annotations

import logging

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication, QLineEdit, QMenu, QPlainTextEdit, QTextEdit, QWidget


VERSION = "text-editor-priority-1"
_TEXT_FILTER: QObject | None = None
_LAST_TEXT_EDITOR: QWidget | None = None
_ORIGINAL_ACTIONS: dict[tuple[type, str], object] = {}


def _is_text_editor(widget) -> bool:
    return isinstance(widget, (QTextEdit, QPlainTextEdit, QLineEdit))


def _editor_from(widget) -> QWidget | None:
    current = widget
    depth = 0
    while isinstance(current, QWidget) and depth < 8:
        if _is_text_editor(current):
            return current
        current = current.parentWidget()
        depth += 1
    return None


def _active_editor() -> QWidget | None:
    global _LAST_TEXT_EDITOR
    app = QApplication.instance()
    focus = app.focusWidget() if app is not None else None
    editor = _editor_from(focus)
    if editor is not None and editor.isVisible() and editor.isEnabled():
        _LAST_TEXT_EDITOR = editor
        return editor
    if _LAST_TEXT_EDITOR is not None and _LAST_TEXT_EDITOR.isVisible() and _LAST_TEXT_EDITOR.isEnabled() and _LAST_TEXT_EDITOR.hasFocus():
        return _LAST_TEXT_EDITOR
    return None


def _text_cursor(editor) -> QTextCursor | None:
    if isinstance(editor, (QTextEdit, QPlainTextEdit)):
        return editor.textCursor()
    return None


def _delete_text(editor, backwards: bool = False) -> bool:
    if isinstance(editor, QLineEdit):
        if editor.hasSelectedText():
            editor.insert("")
        elif backwards:
            editor.backspace()
        else:
            editor.del_()
        return True
    cursor = _text_cursor(editor)
    if cursor is None:
        return False
    if cursor.hasSelection():
        cursor.removeSelectedText()
    elif backwards:
        cursor.deletePreviousChar()
    else:
        cursor.deleteChar()
    editor.setTextCursor(cursor)
    return True


def _copy_text(editor) -> bool:
    if hasattr(editor, "copy"):
        editor.copy()
        return True
    return False


def _cut_text(editor) -> bool:
    if hasattr(editor, "cut"):
        editor.cut()
        return True
    return False


def _paste_text(editor) -> bool:
    if hasattr(editor, "paste"):
        editor.paste()
        return True
    return False


def _select_all_text(editor) -> bool:
    if hasattr(editor, "selectAll"):
        editor.selectAll()
        return True
    return False


def _style_text_menu(menu: QMenu) -> None:
    menu.setStyleSheet(
        "QMenu {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.55 #edf8ff, stop:1 #fff1d3); border:1px solid #8fa2bb; border-radius:10px; padding:6px;}"
        "QMenu::item {color:#1f3148; padding:6px 24px 6px 12px; border-radius:7px; font-size:12px; font-style:italic; font-weight:800;}"
        "QMenu::item:selected {background:#fff4cf; color:#132238;}"
    )


def _show_text_menu(editor, global_pos: QPoint) -> bool:
    menu = QMenu(editor)
    _style_text_menu(menu)
    copy_action = menu.addAction("Copy")
    cut_action = menu.addAction("Cut")
    paste_action = menu.addAction("Paste")
    delete_action = menu.addAction("Delete")
    menu.addSeparator()
    select_all_action = menu.addAction("Select All")
    chosen = menu.exec(global_pos)
    if chosen == copy_action:
        return _copy_text(editor)
    if chosen == cut_action:
        return _cut_text(editor)
    if chosen == paste_action:
        return _paste_text(editor)
    if chosen == delete_action:
        return _delete_text(editor, backwards=False)
    if chosen == select_all_action:
        return _select_all_text(editor)
    return True


class _TextEditorPriorityFilter(QObject):
    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        global _LAST_TEXT_EDITOR
        editor = _editor_from(watched)
        if editor is None:
            return False
        if event.type() == QEvent.Type.FocusIn:
            _LAST_TEXT_EDITOR = editor
            return False
        if event.type() == QEvent.Type.ContextMenu:
            point_getter = getattr(event, "globalPos", None)
            global_pos = point_getter() if callable(point_getter) else editor.mapToGlobal(QPoint(8, 8))
            event.accept()
            return _show_text_menu(editor, global_pos)
        if event.type() != QEvent.Type.KeyPress:
            return False
        modifiers = event.modifiers()
        ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        key = event.key()
        if ctrl and key == Qt.Key.Key_C:
            event.accept()
            return _copy_text(editor)
        if ctrl and key == Qt.Key.Key_X:
            event.accept()
            return _cut_text(editor)
        if ctrl and key == Qt.Key.Key_V:
            event.accept()
            return _paste_text(editor)
        if ctrl and key == Qt.Key.Key_A:
            event.accept()
            return _select_all_text(editor)
        if not ctrl and not shift and key == Qt.Key.Key_Delete:
            event.accept()
            return _delete_text(editor, backwards=False)
        if not ctrl and not shift and key == Qt.Key.Key_Backspace:
            event.accept()
            return _delete_text(editor, backwards=True)
        return False


def _run_text_action(action: str) -> bool:
    editor = _active_editor()
    if editor is None:
        return False
    if action == "copy":
        return _copy_text(editor)
    if action == "cut":
        return _cut_text(editor)
    if action == "paste":
        return _paste_text(editor)
    if action == "delete":
        return _delete_text(editor, backwards=False)
    if action == "select_all":
        return _select_all_text(editor)
    return False


def _wrap_workspace_action(cls, method_name: str, action: str) -> None:
    key = (cls, method_name)
    if key in _ORIGINAL_ACTIONS or not hasattr(cls, method_name):
        return
    original = getattr(cls, method_name)
    _ORIGINAL_ACTIONS[key] = original

    def wrapper(self, *args, **kwargs):
        if _run_text_action(action):
            setter = getattr(self, "_set_status", None)
            if callable(setter):
                setter(f"Text {action.replace('_', ' ').title()}")
            return None
        return original(self, *args, **kwargs)

    setattr(cls, method_name, wrapper)


def _insert_text_symbol(self, symbol: str) -> None:
    editor = _active_editor()
    if editor is not None:
        if isinstance(editor, QLineEdit):
            editor.insert(symbol)
        else:
            cursor = editor.textCursor()
            cursor.insertText(symbol)
            editor.setTextCursor(cursor)
        return
    canvas = getattr(self, "_canvas", None)
    editor = getattr(canvas, "_active_text_editor", None)
    if editor is not None:
        if isinstance(editor, QLineEdit):
            editor.insert(symbol)
        else:
            cursor = editor.textCursor()
            cursor.insertText(symbol)
            editor.setTextCursor(cursor)


def _install_workspace_wrappers() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_text_editor_patch: workspace import failed")
        return
    workspace_cls = edw.EngineeringDesignWorkspace
    for name, action in (
        ("_copy", "copy"),
        ("_cut", "cut"),
        ("_paste", "paste"),
        ("_delete", "delete"),
        ("_select_all", "select_all"),
        ("_copy_selection", "copy"),
        ("_cut_selection", "cut"),
        ("_paste_from_clipboard", "paste"),
        ("_delete_selection", "delete"),
    ):
        _wrap_workspace_action(workspace_cls, name, action)
    workspace_cls._insert_text_symbol = _insert_text_symbol


def apply_engineering_text_editor_patch() -> None:
    global _TEXT_FILTER
    app = QApplication.instance()
    if app is not None and _TEXT_FILTER is None:
        _TEXT_FILTER = _TextEditorPriorityFilter()
        app.installEventFilter(_TEXT_FILTER)
    _install_workspace_wrappers()
    logging.info("engineering_text_editor_patch: installed version=%s", VERSION)

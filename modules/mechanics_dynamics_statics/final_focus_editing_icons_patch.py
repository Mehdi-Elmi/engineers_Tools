"""Final focus, editing shortcut, and Text toolbar icon cleanup.

This patch removes Qt focus rectangles globally, standardizes Text editing
shortcuts, and replaces text-based align labels with drawn toolbar icons.
"""

from __future__ import annotations

import copy
import logging

from PySide6.QtCore import QEvent, QObject, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPen, QPixmap, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication,
    QAbstractButton,
    QHBoxLayout,
    QMenuBar,
    QProxyStyle,
    QPushButton,
    QStyle,
    QTextEdit,
    QWidget,
)

PATCH_VERSION = "engineering-final-focus-editing-icons-2026-07-02-b"

_ALIGN_MODES = ("left", "center", "right", "justify")


class _NoFocusRectStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):  # noqa: N802
        if element == QStyle.PrimitiveElement.PE_FrameFocusRect:
            return
        super().drawPrimitive(element, option, painter, widget)


class _TextEditShortcutFilter(QObject):
    def eventFilter(self, watched, event):  # noqa: N802
        if not isinstance(watched, QTextEdit):
            return False
        if event.type() == QEvent.Type.ShortcutOverride and _is_text_shortcut(event):
            event.accept()
            return True
        if event.type() == QEvent.Type.KeyPress and _handle_editor_key(watched, event):
            return True
        return False


def _is_text_shortcut(event) -> bool:
    if event.matches(QKeySequence.StandardKey.Copy):
        return True
    if event.matches(QKeySequence.StandardKey.Cut):
        return True
    if event.matches(QKeySequence.StandardKey.Paste):
        return True
    if event.matches(QKeySequence.StandardKey.SelectAll):
        return True
    return event.key() in {Qt.Key.Key_Delete, Qt.Key.Key_Backspace}


def _canvas_for_editor(editor: QTextEdit):
    parent = editor.parentWidget()
    while parent is not None:
        if hasattr(parent, "_active_text_editor") or parent.__class__.__name__ == "EngineeringCanvas":
            return parent
        parent = parent.parentWidget()
    return None


def _handle_editor_key(editor: QTextEdit, event) -> bool:
    canvas = _canvas_for_editor(editor)
    if event.matches(QKeySequence.StandardKey.Copy):
        editor.copy(); event.accept(); return True
    if event.matches(QKeySequence.StandardKey.Cut):
        editor.cut();
        if canvas is not None:
            _save_editor(canvas)
        event.accept(); return True
    if event.matches(QKeySequence.StandardKey.Paste):
        editor.paste();
        if canvas is not None:
            _save_editor(canvas)
        event.accept(); return True
    if event.matches(QKeySequence.StandardKey.SelectAll):
        editor.selectAll(); event.accept(); return True
    if event.key() == Qt.Key.Key_Delete:
        _delete_editor_selection(editor)
        if canvas is not None:
            _save_editor(canvas)
        event.accept(); return True
    if event.key() == Qt.Key.Key_Backspace:
        cursor = editor.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        else:
            cursor.deletePreviousChar()
        editor.setTextCursor(cursor)
        if canvas is not None:
            _save_editor(canvas)
        event.accept(); return True
    return False


def _install_text_shortcut_filter(root: QWidget | None = None) -> None:
    app = QApplication.instance()
    if app is None:
        return
    filter_obj = getattr(app, "_engineering_text_edit_shortcut_filter", None)
    if filter_obj is None:
        filter_obj = _TextEditShortcutFilter(app)
        app._engineering_text_edit_shortcut_filter = filter_obj

        def on_focus_changed(_old, now) -> None:
            if isinstance(now, QTextEdit):
                _install_filter_on_editor(now, filter_obj)

        app.focusChanged.connect(on_focus_changed)
    if root is not None:
        for editor in root.findChildren(QTextEdit):
            _install_filter_on_editor(editor, filter_obj)


def _install_filter_on_editor(editor: QTextEdit, filter_obj: QObject) -> None:
    if editor.property("engineeringTextShortcutFilter") == PATCH_VERSION:
        return
    editor.installEventFilter(filter_obj)
    editor.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
    editor.setProperty("engineeringTextShortcutFilter", PATCH_VERSION)


def _install_no_focus_style() -> None:
    app = QApplication.instance()
    if app is None or getattr(app, "_engineering_no_focus_rect_style", "") == PATCH_VERSION:
        return
    style = _NoFocusRectStyle(app.style())
    app.setStyle(style)
    app._engineering_no_focus_rect_style = PATCH_VERSION
    app._engineering_no_focus_rect_style_object = style
    app.setStyleSheet(
        (app.styleSheet() or "")
        + "\nQWidget{outline:0;}"
        + "\nQPushButton:focus,QToolButton:focus,QMenuBar:focus,QMenuBar::item:focus{outline:0;border:inherit;}"
    )
    _install_text_shortcut_filter()


def _remove_focus_from_widgets(root: QWidget | None) -> None:
    if root is None:
        return
    for button in root.findChildren(QAbstractButton):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        style = button.styleSheet() or ""
        if "final-focus-clean" not in style:
            button.setStyleSheet(
                style
                + "\n/* final-focus-clean */"
                + "\nQPushButton:focus,QToolButton:focus{outline:0;}"
            )
    for menubar in root.findChildren(QMenuBar):
        menubar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        menubar.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
    _install_text_shortcut_filter(root)


def _align_icon(mode: str, *, selected: bool = False) -> QIcon:
    pixmap = QPixmap(28, 28)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    if selected:
        painter.setPen(QPen(QColor("#9fb0c5"), 1.0))
        painter.setBrush(QColor("#edf3f9"))
        painter.drawRoundedRect(2, 2, 24, 24, 5, 5)
    pen = QPen(QColor("#132238"), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    rows = [8, 12, 16, 20]
    widths = [15, 11, 17, 13] if mode != "justify" else [17, 17, 17, 17]
    for y, width in zip(rows, widths):
        if mode == "center":
            x = (28 - width) / 2
        elif mode == "right":
            x = 21 - width
        else:
            x = 7
        painter.drawLine(int(x), y, int(x + width), y)
    painter.end()
    return QIcon(pixmap)


def _set_italic_button(button: QPushButton) -> None:
    button.setText("I")
    button.setIcon(QIcon())
    font = button.font()
    font.setFamily("Times New Roman")
    font.setPointSize(max(font.pointSize(), 12))
    font.setBold(True)
    font.setItalic(True)
    button.setFont(font)
    button.setFixedSize(max(button.width(), 34), max(button.height(), 32))


def _merge_italic(editor: QTextEdit, active: bool) -> None:
    fmt = QTextCharFormat()
    fmt.setFontItalic(bool(active))
    cursor = editor.textCursor()
    cursor.mergeCharFormat(fmt)
    editor.mergeCurrentCharFormat(fmt)


def _set_align_icon(button: QPushButton, mode: str) -> None:
    button.setText("")
    button.setIcon(_align_icon(mode, selected=False))
    button.setIconSize(button.size() if button.width() > 0 else pixmap_size())
    button.setFixedSize(34, 32)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)


def pixmap_size():
    from PySide6.QtCore import QSize
    return QSize(28, 28)


def _apply_toolbar_icons(root: QWidget | None) -> None:
    if root is None:
        return
    start_bar = getattr(root, "_start_bar_widget", None)
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    if not isinstance(buttons, dict):
        return
    italic = buttons.get("Italic")
    if isinstance(italic, QPushButton):
        _set_italic_button(italic)
    mapping = {
        "Align left": "left",
        "Align center": "center",
        "Align right": "right",
        "Justify": "justify",
    }
    for name, mode in mapping.items():
        button = buttons.get(name)
        if isinstance(button, QPushButton):
            _set_align_icon(button, mode)
    bar = root.findChild(QWidget, "InlineTextBar")
    if bar is not None and isinstance(bar.layout(), QHBoxLayout):
        bar.layout().setSpacing(5)


def _active_editor(canvas) -> QTextEdit | None:
    editor = getattr(canvas, "_active_text_editor", None)
    return editor if isinstance(editor, QTextEdit) else None


def _save_editor(canvas) -> None:
    try:
        from . import text_toolbar_word_behavior_patch as word
        word._save_active_editor(canvas)
    except Exception:
        pass


def _delete_editor_selection(editor: QTextEdit) -> None:
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.removeSelectedText()
    else:
        cursor.deleteChar()
    editor.setTextCursor(cursor)


def _copy_canvas_selection(canvas) -> bool:
    if hasattr(canvas, "copy_selected_objects") and canvas.copy_selected_objects():
        return True
    window = canvas.window() if hasattr(canvas, "window") else None
    copier = getattr(window, "_copy_selection", None)
    if callable(copier):
        copier()
        return True
    selected = sorted(getattr(canvas, "selected_indices", set()))
    objects = getattr(canvas, "objects", [])
    if selected and objects:
        canvas._engineering_clipboard_objects = [copy.deepcopy(objects[i]) for i in selected if 0 <= i < len(objects)]
        return True
    return False


def _paste_canvas_selection(canvas) -> bool:
    if hasattr(canvas, "paste_copied_objects") and canvas.paste_copied_objects():
        return True
    window = canvas.window() if hasattr(canvas, "window") else None
    paster = getattr(window, "_paste_from_clipboard", None)
    if callable(paster):
        paster()
        return True
    objects = getattr(canvas, "_engineering_clipboard_objects", None)
    if isinstance(objects, list) and objects:
        if hasattr(canvas, "_push_undo"):
            canvas._push_undo()
        base = len(canvas.objects)
        clones = []
        for obj in objects:
            clone = copy.deepcopy(obj)
            if hasattr(clone, "rect"):
                clone.rect.translate(12.0, 12.0)
            clones.append(clone)
        canvas.objects.extend(clones)
        if hasattr(canvas, "_select_only") and clones:
            canvas.selected_indices = set(range(base, base + len(clones)))
        if hasattr(canvas, "_emit_object_changes"):
            canvas._emit_object_changes()
        canvas.update()
        return True
    return False


def _delete_canvas_selection(canvas) -> bool:
    if hasattr(canvas, "delete_selected_objects") and canvas.delete_selected_objects():
        return True
    window = canvas.window() if hasattr(canvas, "window") else None
    deleter = getattr(window, "_delete_selection", None)
    if callable(deleter):
        deleter()
        return True
    selected = sorted(getattr(canvas, "selected_indices", set()), reverse=True)
    if not selected:
        return False
    if hasattr(canvas, "_push_undo"):
        canvas._push_undo()
    for index in selected:
        if 0 <= index < len(canvas.objects):
            del canvas.objects[index]
    canvas.selected_indices = set()
    if hasattr(canvas, "_emit_object_changes"):
        canvas._emit_object_changes()
    canvas.update()
    return True


def _patch_canvas_keys(edw) -> None:
    if getattr(edw.EngineeringCanvas, "_final_focus_editing_key_patch", "") == PATCH_VERSION:
        return
    old_key = edw.EngineeringCanvas.keyPressEvent

    def key_press(self, event) -> None:
        editor = _active_editor(self)
        if editor is not None and editor.hasFocus():
            if _handle_editor_key(editor, event):
                return
            editor.keyPressEvent(event)
            _save_editor(self)
            return
        if event.matches(QKeySequence.StandardKey.Copy):
            if _copy_canvas_selection(self):
                event.accept(); return
        if event.matches(QKeySequence.StandardKey.Cut):
            copied = _copy_canvas_selection(self)
            deleted = _delete_canvas_selection(self) if copied else False
            if copied or deleted:
                event.accept(); return
        if event.matches(QKeySequence.StandardKey.Paste):
            if _paste_canvas_selection(self):
                event.accept(); return
        if event.key() == Qt.Key.Key_Delete:
            if _delete_canvas_selection(self):
                event.accept(); return
        old_key(self, event)

    edw.EngineeringCanvas.keyPressEvent = key_press
    edw.EngineeringCanvas._final_focus_editing_key_patch = PATCH_VERSION


def _patch_word_italic(word) -> None:
    def set_editor_italic(root: QWidget | None, active: bool) -> None:
        canvas = getattr(root, "_canvas", None) if root is not None else None
        editor = _active_editor(canvas) if canvas is not None else None
        if editor is None:
            return
        _merge_italic(editor, bool(active))
        _save_editor(canvas)

    word._set_editor_italic = set_editor_italic


def apply_final_focus_editing_icons_patch() -> None:
    from . import text_toolbar_word_behavior_patch as word
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_final_focus_editing_icons_patch", "") == PATCH_VERSION:
        return

    _install_no_focus_style()
    _patch_word_italic(word)
    _patch_canvas_keys(edw)

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _install_no_focus_style()
        _install_text_shortcut_filter(self)
        _patch_word_italic(word)
        _patch_canvas_keys(edw)
        _remove_focus_from_widgets(self)
        _apply_toolbar_icons(self)
        for delay in (0, 150, 500, 1200):
            QTimer.singleShot(delay, lambda root=self: (_remove_focus_from_widgets(root), _apply_toolbar_icons(root), _install_text_shortcut_filter(root)))
        logging.info("final_focus_editing_icons_patch: installed version=%s", PATCH_VERSION)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_final_focus_editing_icons_patch = PATCH_VERSION

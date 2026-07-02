"""Final runtime owner for Text editor keyboard, numbering, color and toolbar controls."""

from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QEvent, QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainter, QPixmap, QPolygonF, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QWidget,
)

PATCH_VERSION = "engineering-text-toolbar-final-event-safety-2026-07-02-i"
_ARROW_CACHE: dict[str, str] = {}


def _workspace_from_widget(widget: QWidget | None) -> QWidget | None:
    current = widget
    while current is not None:
        if hasattr(current, "_start_bar_widget") or current.objectName() == "EngineeringDesignWorkspace":
            return current
        current = current.parentWidget()
    return None


def _workspace_from_editor(editor: QTextEdit) -> QWidget | None:
    root = _workspace_from_widget(editor)
    if root is not None:
        return root
    item = getattr(editor, "_engineering_text_item", None) or getattr(editor, "_text_item", None)
    scene = item.scene() if item is not None and hasattr(item, "scene") else None
    views = scene.views() if scene is not None and hasattr(scene, "views") else []
    for view in views:
        root = _workspace_from_widget(view)
        if root is not None:
            return root
    owner = getattr(editor, "_canvas_owner", None)
    return _workspace_from_widget(owner) if owner is not None else None


def _buttons(root: QWidget | None) -> dict:
    if root is None:
        return {}
    return getattr(root, "_text_toolbar_buttons", {}) or getattr(root, "_text_buttons", {}) or {}


def _plain_font(editor: QTextEdit) -> None:
    current = editor.currentFont()
    size = current.pointSize() if current.pointSize() > 0 else 12
    font = QFont("Times New Roman", max(1, size))
    font.setBold(False)
    font.setItalic(False)
    editor.setFont(font)
    editor.setCurrentFont(font)
    editor.setFontWeight(QFont.Weight.Normal)
    editor.setFontItalic(False)


def _reset_style_buttons(root: QWidget | None) -> None:
    buttons = _buttons(root)
    bold = buttons.get("Bold") or buttons.get("bold")
    italic = buttons.get("Italic") or buttons.get("italic")
    if bold is not None and not bold.property("userChangedTextStyle"):
        bold.setChecked(False)
    if italic is not None:
        if not italic.property("userChangedTextStyle"):
            italic.setChecked(False)
        font = italic.font()
        font.setItalic(True)
        italic.setFont(font)
        italic.setText("I")


def _save_editor(editor: QTextEdit) -> None:
    for name in ("_save_to_item", "_commit_to_item", "_sync_to_item", "_commit_text_to_item"):
        callback = getattr(editor, name, None)
        if callable(callback):
            try:
                callback()
                return
            except TypeError:
                pass
            except Exception:
                logging.exception("text final safety: editor save callback failed")
                return
    item = getattr(editor, "_engineering_text_item", None) or getattr(editor, "_text_item", None)
    if item is not None:
        try:
            if hasattr(item, "setPlainText"):
                item.setPlainText(editor.toPlainText())
        except Exception:
            logging.exception("text final safety: direct item save failed")


def _matches(event, standard_key: QKeySequence.StandardKey) -> bool:
    try:
        return event.matches(standard_key)
    except Exception:
        return False


def _roman_to_int(text: str) -> int | None:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    previous = 0
    if not text:
        return None
    for char in reversed(text.upper()):
        value = values.get(char)
        if value is None:
            return None
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total if total > 0 else None


def _alpha_to_int(text: str) -> int | None:
    if not text or not text.isalpha():
        return None
    total = 0
    for char in text.upper():
        total = total * 26 + (ord(char) - ord("A") + 1)
    return total if total > 0 else None


def _next_number_from_line(settings: dict, text: str) -> int | None:
    style = str(settings.get("style", "1."))
    if style in {"1.", "1)"}:
        match = re.match(r"^\s*(\d+)\s*[\.)]\s*", text or "")
        return int(match.group(1)) + 1 if match else None
    if style in {"I.", "i."}:
        match = re.match(r"^\s*([ivxlcdmIVXLCDM]+)\s*[\.)]\s*", text or "")
        value = _roman_to_int(match.group(1)) if match else None
        return value + 1 if value is not None else None
    if style in {"A.", "a."}:
        match = re.match(r"^\s*([A-Za-z]+)\s*[\.)]\s*", text or "")
        value = _alpha_to_int(match.group(1)) if match else None
        return value + 1 if value is not None else None
    match = re.match(r"^\s*(\d+)\s*[\.)]\s*", text or "")
    return int(match.group(1)) + 1 if match else None


def _sync_numbering_next_from_current_line(root: QWidget | None, editor: QTextEdit, settings: dict) -> None:
    if root is None or settings.get("mode") != "numbering":
        return
    next_value = _next_number_from_line(settings, editor.textCursor().block().text())
    if next_value is not None:
        setattr(root, "_text_numbering_next", next_value)
        return
    if not hasattr(root, "_text_numbering_next"):
        try:
            setattr(root, "_text_numbering_next", int(settings.get("start_numbering", 1)))
        except Exception:
            setattr(root, "_text_numbering_next", 1)


def _insert_active_list_after_enter(editor: QTextEdit) -> bool:
    root = _workspace_from_editor(editor)
    if root is None:
        return False
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return False
    settings = line_patch._text_settings_for_active_list(root)
    if settings is None:
        return False
    _sync_numbering_next_from_current_line(root, editor, settings)
    cursor = editor.textCursor()
    cursor.insertBlock()
    line_patch._insert_list_prefix_with_cursor(root, cursor, settings, advance_number=True)
    editor.setTextCursor(cursor)
    _save_editor(editor)
    return True


def _delete_previous_char(editor: QTextEdit) -> None:
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.removeSelectedText()
    else:
        position = cursor.position()
        if position > 0:
            cursor.setPosition(position - 1, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
    editor.setTextCursor(cursor)
    _save_editor(editor)


def _delete_next_char(editor: QTextEdit) -> None:
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.removeSelectedText()
    else:
        position = cursor.position()
        cursor.setPosition(position + 1, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
    editor.setTextCursor(cursor)
    _save_editor(editor)


def _handle_editor_event(editor: QTextEdit, event) -> bool:
    if event.type() == QEvent.Type.ShortcutOverride and any(
        _matches(event, key)
        for key in (
            QKeySequence.StandardKey.Copy,
            QKeySequence.StandardKey.Cut,
            QKeySequence.StandardKey.Paste,
            QKeySequence.StandardKey.SelectAll,
        )
    ):
        event.accept()
        return True
    if event.type() != QEvent.Type.KeyPress:
        return False
    if _matches(event, QKeySequence.StandardKey.Copy):
        editor.copy(); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.Cut):
        editor.cut(); _save_editor(editor); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.Paste):
        editor.paste(); _save_editor(editor); event.accept(); return True
    if _matches(event, QKeySequence.StandardKey.SelectAll):
        editor.selectAll(); event.accept(); return True
    if event.key() == Qt.Key.Key_Backspace:
        _delete_previous_char(editor); event.accept(); return True
    if event.key() == Qt.Key.Key_Delete:
        _delete_next_char(editor); event.accept(); return True
    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        if _insert_active_list_after_enter(editor):
            event.accept(); return True
    return False


class _FinalEditorEventFilter(QObject):
    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if isinstance(watched, QTextEdit) and _handle_editor_event(watched, event):
            return True
        return super().eventFilter(watched, event)


def _install_editor_filter(editor: QTextEdit | None) -> None:
    if editor is None:
        return
    root = _workspace_from_editor(editor)
    if not editor.property("finalPlainDefaults"):
        _plain_font(editor)
        _reset_style_buttons(root)
        editor.setProperty("finalPlainDefaults", PATCH_VERSION)
    if editor.property("finalEventFilter") == PATCH_VERSION:
        return
    old_filter = getattr(editor, "_final_event_filter", None)
    if old_filter is not None:
        try:
            editor.removeEventFilter(old_filter)
        except Exception:
            pass
    filter_obj = _FinalEditorEventFilter(editor)
    editor.installEventFilter(filter_obj)
    editor._final_event_filter = filter_obj
    editor.setProperty("finalEventFilter", PATCH_VERSION)


def _arrow_url(direction: str) -> str:
    cached = _ARROW_CACHE.get(direction)
    if cached:
        return cached
    size = 18
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(QColor("#173454"))
    painter.setPen(Qt.PenStyle.NoPen)
    points = [QPointF(9, 4), QPointF(14, 12), QPointF(4, 12)] if direction == "up" else [QPointF(4, 6), QPointF(14, 6), QPointF(9, 14)]
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    path = Path(tempfile.gettempdir()) / f"engineering_arrow_{direction}_20260702i.png"
    pixmap.save(path.as_posix(), "PNG")
    _ARROW_CACHE[direction] = path.as_posix()
    return path.as_posix()


def _style_toolbar_combo(combo: QComboBox) -> None:
    combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    combo.setStyleSheet(
        "QComboBox{background:#fffefa;border:1px solid #b88718;border-radius:8px;color:#173454;"
        "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:2px 28px 2px 8px;outline:0;}"
        "QComboBox:hover{border-color:#173454;background:#ffffff;}"
        "QComboBox::drop-down{subcontrol-origin:padding;subcontrol-position:top right;width:24px;"
        "border-left:1px solid #b88718;border-top-right-radius:7px;border-bottom-right-radius:7px;"
        "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        f"QComboBox::down-arrow{{image:url({_arrow_url('down')});width:16px;height:16px;}}"
    )


def _style_toolbar_spin(spin: QSpinBox | QDoubleSpinBox) -> None:
    spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffefa;border:1px solid #b88718;border-radius:8px;color:#173454;"
        "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:2px 26px 2px 8px;outline:0;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{subcontrol-origin:border;subcontrol-position:top right;width:23px;"
        "border-left:1px solid #b88718;border-top-right-radius:7px;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{subcontrol-origin:border;subcontrol-position:bottom right;width:23px;"
        "border-left:1px solid #b88718;border-bottom-right-radius:7px;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        f"QSpinBox::up-arrow,QDoubleSpinBox::up-arrow{{image:url({_arrow_url('up')});width:14px;height:14px;}}"
        f"QSpinBox::down-arrow,QDoubleSpinBox::down-arrow{{image:url({_arrow_url('down')});width:14px;height:14px;}}"
    )


def _polish_textbar_controls(root: QWidget | None) -> None:
    if root is None:
        return
    for bar in root.findChildren(QWidget, "InlineTextBar"):
        bar.setMinimumHeight(max(bar.minimumHeight(), 44))
        for combo in bar.findChildren(QComboBox):
            _style_toolbar_combo(combo)
        for spin in bar.findChildren(QSpinBox):
            _style_toolbar_spin(spin)
        for spin in bar.findChildren(QDoubleSpinBox):
            _style_toolbar_spin(spin)
    _reset_style_buttons(root)


def _patch_show_editor(module) -> None:
    old_show = getattr(module, "_show_rich_text_editor", None)
    if not callable(old_show) or getattr(old_show, "_final_safety_wrapped", False):
        return

    def show_editor(*args, **kwargs):
        result = old_show(*args, **kwargs)
        for value in list(args) + list(kwargs.values()) + [result]:
            if isinstance(value, QTextEdit):
                _install_editor_filter(value)
            elif isinstance(value, QWidget):
                for editor in value.findChildren(QTextEdit):
                    _install_editor_filter(editor)
        return result

    show_editor._final_safety_wrapped = True
    module._show_rich_text_editor = show_editor


def _patch_color_dialog() -> None:
    try:
        from . import standard_color_dialog
    except Exception:
        return

    def open_standard_color_dialog(parent=None, current="#000000", *args, **kwargs):
        title = kwargs.get("title") or (args[0] if args else "Add Custom Color")
        return standard_color_dialog.get_custom_color(parent, current, title)

    for module_name in ("text_lag_final_patch", "text_line_math_symbols_patch"):
        try:
            module = __import__(f"modules.mechanics_dynamics_statics.{module_name}", fromlist=[module_name])
            module._open_custom_color_dialog = open_standard_color_dialog
        except Exception:
            logging.exception("text final safety: color dialog patch failed for %s", module_name)


def _current_unit(root: QWidget | None) -> str:
    start_bar = getattr(root, "_start_bar_widget", None)
    if start_bar is not None:
        for name in ("_unit", "unit", "current_unit"):
            value = getattr(start_bar, name, None)
            if isinstance(value, str) and value:
                return value
    return "mm"


def _patch_line_module_controls() -> None:
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return
    line_patch._combo_style = _style_toolbar_combo
    line_patch._spin_style = _style_toolbar_spin
    if getattr(line_patch, "_final_exact_start_number_patch", "") != PATCH_VERSION:
        old_format_prefix = line_patch._format_prefix

        def format_prefix(settings, root=None, advance_number=False):
            if isinstance(settings, dict) and settings.get("mode") == "numbering" and root is not None and not advance_number:
                try:
                    setattr(root, "_text_numbering_next", int(settings.get("start_numbering", 1)))
                except Exception:
                    setattr(root, "_text_numbering_next", 1)
            return old_format_prefix(settings, root, advance_number)

        line_patch._format_prefix = format_prefix
        line_patch._final_exact_start_number_patch = PATCH_VERSION


def _patch_line_spacing_dialog() -> None:
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return
    _patch_line_module_controls()

    def open_line_spacing_settings(root: QWidget | None) -> None:
        dialog, body, body_layout = line_patch._dialog_shell(root, "Line and Paragraph Settings", (380, 210))
        body.setStyleSheet("QWidget{background:#ffffff;border:0;}")
        unit = _current_unit(root)
        row = QHBoxLayout()
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(8)
        custom = QCheckBox("Custom", body)
        custom.setChecked(True)
        custom.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if hasattr(line_patch, "_choice_toggle_style"):
            custom.setStyleSheet(line_patch._choice_toggle_style())
        value = QDoubleSpinBox(body)
        value.setRange(0.1, 500.0)
        value.setDecimals(2)
        value.setSingleStep(0.5)
        value.setValue(float(getattr(root, "_text_line_spacing", 1.0) or 1.0))
        value.setSuffix(f" {unit}")
        value.setMinimumWidth(138)
        _style_toolbar_spin(value)
        row.addWidget(custom)
        row.addWidget(value)
        row.addStretch(1)
        body_layout.addLayout(row)
        hint = QLabel("Custom line spacing uses the active Unit setting.", body)
        hint.setStyleSheet("QLabel{font-family:'Times New Roman';font-size:11px;font-weight:900;font-style:italic;color:#173454;}")
        body_layout.addWidget(hint)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        ok = QPushButton("OK", body)
        cancel = QPushButton("Cancel", body)
        for button in (ok, cancel):
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setStyleSheet(line_patch._button_style("QPushButton"))
        ok.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        body_layout.addLayout(buttons)
        if hasattr(line_patch, "_prepare_dialog_masks"):
            line_patch._prepare_dialog_masks(dialog)
        if dialog.exec() == dialog.DialogCode.Accepted and custom.isChecked():
            try:
                line_patch._apply_line_spacing(root, float(value.value()))
            except Exception:
                setattr(root, "_text_line_spacing", float(value.value()))

    line_patch._open_line_spacing_settings = open_line_spacing_settings


def _install_existing_editors(root: QWidget | None) -> None:
    if root is None:
        return
    for editor in root.findChildren(QTextEdit):
        _install_editor_filter(editor)


def _patch_canvas_key_handler(edw) -> None:
    canvas_cls = getattr(edw, "EngineeringCanvas", None)
    if canvas_cls is None or getattr(canvas_cls, "_text_toolbar_final_event_safety_key_patch", "") == PATCH_VERSION:
        return
    old_key = canvas_cls.keyPressEvent

    def key_press(self, event) -> None:
        editor = getattr(self, "_active_text_editor", None)
        if isinstance(editor, QTextEdit):
            if getattr(editor, "_canvas_owner", None) is None:
                editor._canvas_owner = self
            _install_editor_filter(editor)
            if editor.hasFocus() and _handle_editor_event(editor, event):
                return
        old_key(self, event)

    canvas_cls.keyPressEvent = key_press
    canvas_cls._text_toolbar_final_event_safety_key_patch = PATCH_VERSION


def apply_text_toolbar_final_event_safety_patch() -> None:
    modules = []
    for module_name in ("text_lag_final_patch", "ui_text_tool_final_patch", "ui_text_tool_runtime_fix_patch"):
        try:
            modules.append(__import__(f"modules.mechanics_dynamics_statics.{module_name}", fromlist=[module_name]))
        except Exception:
            pass
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_final_event_safety_patch", "") == PATCH_VERSION:
        return

    _patch_color_dialog()
    _patch_line_spacing_dialog()
    _patch_line_module_controls()
    _patch_canvas_key_handler(edw)
    for module in modules:
        _patch_show_editor(module)

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _patch_color_dialog()
        _patch_line_spacing_dialog()
        _patch_line_module_controls()
        _patch_canvas_key_handler(edw)
        _install_existing_editors(self)
        _polish_textbar_controls(self)
        for delay in (0, 80, 250, 700, 1400):
            QTimer.singleShot(delay, lambda root=self: (_install_existing_editors(root), _polish_textbar_controls(root), _patch_line_module_controls()))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_final_event_safety_patch = PATCH_VERSION

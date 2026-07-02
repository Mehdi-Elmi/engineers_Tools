"""Final runtime owner for Text editor keyboard, color and line-spacing controls."""

from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QEvent, QPointF, QRectF, QTimer, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QImage, QKeySequence, QPainter, QPixmap, QPolygonF, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextImageFormat
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QHBoxLayout, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget

PATCH_VERSION = "engineering-text-toolbar-final-event-safety-2026-07-02-p"
_ARROW_CACHE: dict[str, str] = {}
_MATH_TOKEN_RE = re.compile(r"([A-Za-z0-9]+)([\^_/])([A-Za-z0-9]+)$")


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
    owner = getattr(editor, "_canvas_owner", None)
    root = _workspace_from_widget(owner) if owner is not None else None
    if root is not None:
        return root
    app = QApplication.instance()
    if app is not None:
        for widget in app.topLevelWidgets():
            root = _workspace_from_widget(widget)
            canvas = getattr(root, "_canvas", None) if root is not None else None
            if getattr(canvas, "_active_text_editor", None) is editor:
                editor._canvas_owner = canvas
                return root
    return None


def _buttons(root: QWidget | None) -> dict:
    if root is None:
        return {}
    start_bar = getattr(root, "_start_bar_widget", None)
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


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
    for name in ("Bold", "Italic"):
        button = buttons.get(name)
        if button is not None and not button.property("userChangedTextStyle"):
            button.setChecked(False)
    italic = buttons.get("Italic")
    if italic is not None:
        font = italic.font()
        font.setFamily("Times New Roman")
        font.setBold(True)
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
    root = _workspace_from_editor(editor)
    canvas = getattr(root, "_canvas", None) if root is not None else None
    if canvas is not None:
        try:
            from . import ui_text_tool_final_patch as text_final
            text_final._save_editor_text(canvas, editor)
        except Exception:
            pass


def _matches(event, standard_key: QKeySequence.StandardKey) -> bool:
    try:
        return bool(event.matches(standard_key))
    except Exception:
        return False


def _normal_char_format(editor: QTextEdit) -> QTextCharFormat:
    fmt = QTextCharFormat(editor.currentCharFormat())
    fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
    return fmt


def _math_part_format(base: QTextCharFormat, alignment: QTextCharFormat.VerticalAlignment) -> QTextCharFormat:
    fmt = QTextCharFormat(base)
    fmt.setVerticalAlignment(alignment)
    size = fmt.fontPointSize()
    if size > 0:
        fmt.setFontPointSize(max(6.0, size * 0.82))
    return fmt


def _reset_math_format(editor: QTextEdit, cursor: QTextCursor) -> None:
    normal = _normal_char_format(editor)
    normal.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
    cursor.setCharFormat(normal)
    editor.setCurrentCharFormat(normal)
    editor.setTextCursor(cursor)


def _fraction_image_format(editor: QTextEdit, top: str, bottom: str, base: QTextCharFormat) -> QTextImageFormat:
    font = QFont(editor.currentFont())
    size = base.fontPointSize() or font.pointSizeF() or 12.0
    font.setPointSizeF(max(6.0, size * 0.82))
    metrics = QFontMetricsF(font)
    width = int(max(metrics.horizontalAdvance(top), metrics.horizontalAdvance(bottom)) + 14)
    line_height = int(metrics.height() + 2)
    height = int(line_height * 2 + 5)
    image = QImage(max(18, width), max(20, height), QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setFont(font)
    painter.setPen(QColor("#132238"))
    painter.drawText(QRectF(0, 0, image.width(), line_height), Qt.AlignmentFlag.AlignCenter, top)
    line_y = line_height + 1
    painter.drawLine(QPointF(3, line_y), QPointF(image.width() - 3, line_y))
    painter.drawText(QRectF(0, line_y + 2, image.width(), line_height), Qt.AlignmentFlag.AlignCenter, bottom)
    painter.end()
    name = f"engineering-inline-fraction-{id(editor)}-{editor.textCursor().position()}-{top}-{bottom}"
    url = QUrl(name)
    editor.document().addResource(QTextDocument.ResourceType.ImageResource, url, image)
    fmt = QTextImageFormat()
    fmt.setName(name)
    fmt.setWidth(image.width())
    fmt.setHeight(image.height())
    fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignMiddle)
    return fmt


def _auto_convert_math_token(editor: QTextEdit) -> bool:
    cursor = editor.textCursor()
    block = cursor.block()
    block_start = block.position()
    rel_pos = max(0, cursor.position() - block_start)
    prefix = (block.text() or "")[:rel_pos].rstrip()
    match = _MATH_TOKEN_RE.search(prefix)
    if match is None:
        return False
    left, operator, right = match.group(1), match.group(2), match.group(3)
    replace = editor.textCursor()
    replace.setPosition(block_start + match.start())
    replace.setPosition(block_start + match.end(), QTextCursor.MoveMode.KeepAnchor)
    normal = _normal_char_format(editor)
    replace.removeSelectedText()
    if operator == "/":
        replace.insertImage(_fraction_image_format(editor, left, right, normal))
        _reset_math_format(editor, replace)
        return True
    elevated = _math_part_format(
        normal,
        QTextCharFormat.VerticalAlignment.AlignSuperScript if operator == "^" else QTextCharFormat.VerticalAlignment.AlignSubScript,
    )
    replace.insertText(left, normal)
    replace.insertText(right, elevated)
    _reset_math_format(editor, replace)
    return True


def _delete_previous_char(editor: QTextEdit) -> None:
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.removeSelectedText()
    else:
        cursor.deletePreviousChar()
    editor.setTextCursor(cursor)
    _save_editor(editor)


def _delete_next_char(editor: QTextEdit) -> None:
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.removeSelectedText()
    else:
        cursor.deleteChar()
    editor.setTextCursor(cursor)
    _save_editor(editor)


def _handle_editor_event(editor: QTextEdit, event) -> bool:
    if event.type() == QEvent.Type.ShortcutOverride:
        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete, Qt.Key.Key_Space):
            event.accept(); return True
        if any(_matches(event, key) for key in (QKeySequence.StandardKey.Copy, QKeySequence.StandardKey.Cut, QKeySequence.StandardKey.Paste, QKeySequence.StandardKey.SelectAll)):
            event.accept(); return True
        return False
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
    if event.key() == Qt.Key.Key_Space:
        QTextEdit.keyPressEvent(editor, event)
        _auto_convert_math_token(editor)
        _save_editor(editor)
        event.accept()
        return True
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
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(QColor("#173454"))
    painter.setPen(Qt.PenStyle.NoPen)
    points = [QPointF(9, 4), QPointF(14, 12), QPointF(4, 12)] if direction == "up" else [QPointF(4, 6), QPointF(14, 6), QPointF(9, 14)]
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    path = Path(tempfile.gettempdir()) / f"engineering_arrow_{direction}_20260702p.png"
    pixmap.save(path.as_posix(), "PNG")
    _ARROW_CACHE[direction] = path.as_posix()
    return path.as_posix()


def _style_toolbar_combo(combo: QComboBox) -> None:
    combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    combo.setStyleSheet(
        "QComboBox{background:#fffefa;border:1px solid #b88718;border-radius:8px;color:#173454;font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:2px 28px 2px 8px;outline:0;}"
        "QComboBox::drop-down{subcontrol-origin:padding;subcontrol-position:top right;width:24px;border-left:1px solid #b88718;border-top-right-radius:7px;border-bottom-right-radius:7px;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        f"QComboBox::down-arrow{{image:url({_arrow_url('down')});width:16px;height:16px;}}"
    )


def _style_toolbar_spin(spin: QSpinBox | QDoubleSpinBox) -> None:
    spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
    spin.setKeyboardTracking(True)
    try:
        spin.lineEdit().setReadOnly(False)
    except Exception:
        pass
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffefa;border:1px solid #b88718;border-radius:8px;color:#173454;font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:2px 26px 2px 8px;outline:0;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{subcontrol-origin:border;subcontrol-position:top right;width:23px;border-left:1px solid #b88718;border-top-right-radius:7px;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{subcontrol-origin:border;subcontrol-position:bottom right;width:23px;border-left:1px solid #b88718;border-bottom-right-radius:7px;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        f"QSpinBox::up-arrow,QDoubleSpinBox::up-arrow{{image:url({_arrow_url('up')});width:14px;height:14px;}} QSpinBox::down-arrow,QDoubleSpinBox::down-arrow{{image:url({_arrow_url('down')});width:14px;height:14px;}}"
    )


def _text_menu_button_style() -> str:
    return (
        "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ffffff,stop:0.58 #eef8ff,stop:1 #e5f1ff);"
        "border:1px solid #b8c5d4;border-left:3px solid #43d3bd;border-radius:7px;color:#102238;"
        "font-family:'Times New Roman';font-size:12px;font-style:italic;font-weight:900;padding:4px 8px 4px 10px;text-align:left;outline:0;}"
        "QPushButton[menuAccent='red']{border-left:3px solid #ff3565;}"
        "QPushButton[menuAccent='cyan']{border-left:3px solid #43d3bd;}"
        "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;color:#102238;}"
        "QPushButton:pressed{background:#f18a2a;color:#ffffff;padding-top:5px;}"
        "QPushButton:focus{outline:0;border:1px solid #b8c5d4;}"
    )


def _text_popup_shell(parent: QWidget | None, width: int):
    popup = QDialog(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
    popup.setObjectName("TextStandardMenuPopup")
    popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    popup.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
    popup.setStyleSheet("QDialog#TextStandardMenuPopup{background:transparent;border:0;} QWidget#TextStandardMenuShell{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:1 #eaf6ff);border:1px solid #9fb1c7;border-radius:11px;} QLabel{color:#173454;font-family:'Times New Roman';font-size:12px;font-style:italic;font-weight:900;}")
    outer = QVBoxLayout(popup)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)
    shell = QWidget(popup)
    shell.setObjectName("TextStandardMenuShell")
    shell.setMinimumWidth(width)
    outer.addWidget(shell)
    layout = QVBoxLayout(shell)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(3)
    return popup, shell, layout


def _text_menu_row(layout: QVBoxLayout, text: str, handler) -> QPushButton:
    button = QPushButton(text)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setMinimumHeight(25)
    button.setProperty("menuAccent", "red" if layout.count() == 0 else "cyan")
    button.setStyleSheet(_text_menu_button_style())
    font = button.font()
    font.setFamily("Times New Roman")
    font.setBold(True)
    font.setItalic(True)
    button.setFont(font)
    button.clicked.connect(lambda checked=False: handler())
    layout.addWidget(button)
    return button


def _patch_text_popup_menu_style() -> None:
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return
    line_patch._menu_button_style = _text_menu_button_style
    line_patch._popup_shell = _text_popup_shell
    line_patch._add_menu_row = _text_menu_row


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
            module._open_standard_color_dialog = open_standard_color_dialog
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


def _unit_to_points(value: float, unit: str) -> float:
    normalized = (unit or "mm").strip().lower()
    if normalized in {"cm", "centimeter", "centimeters"}:
        return value * 72.0 / 2.54
    if normalized in {"in", "inch", "inches"}:
        return value * 72.0
    if normalized in {"pt", "point", "points"}:
        return value
    return value * 72.0 / 25.4


def _fixed_line_height_type() -> int:
    value = QTextBlockFormat.LineHeightTypes.FixedHeight
    try:
        return int(value.value)
    except Exception:
        return int(value)


def _apply_custom_line_spacing(root: QWidget | None, value: float, unit: str) -> None:
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return
    _canvas, editor = line_patch._root_editor(root)
    if editor is None:
        return
    cursor = editor.textCursor()
    block = QTextBlockFormat(cursor.blockFormat())
    block.setLineHeight(max(1, int(round(_unit_to_points(value, unit)))), _fixed_line_height_type())
    cursor.mergeBlockFormat(block)
    editor.setTextCursor(cursor)
    editor.setFocus()
    try:
        line_patch._save(root)
    except Exception:
        pass


def _patch_line_module_controls() -> None:
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return
    line_patch._combo_style = _style_toolbar_combo
    line_patch._spin_style = _style_toolbar_spin
    line_patch._auto_convert_math_token = _auto_convert_math_token


def _patch_line_spacing_dialog() -> None:
    try:
        from . import text_line_math_symbols_patch as line_patch
    except Exception:
        return
    _patch_text_popup_menu_style()
    _patch_line_module_controls()

    def show_line_popup(root: QWidget | None, anchor: QPushButton) -> None:
        popup, _shell, layout = line_patch._popup_shell(anchor, 306)
        for label, value in (("1.0", 1.0), ("1.15", 1.15), ("1.5", 1.5), ("2.0", 2.0)):
            line_patch._add_menu_row(layout, label, lambda checked=False, v=value, p=popup, w=root: (p.accept(), line_patch._apply_line_spacing(w, v)))
        custom_holder = QWidget(popup)
        custom_holder.setMinimumHeight(42)
        row = QHBoxLayout(custom_holder)
        row.setContentsMargins(6, 4, 6, 4)
        row.setSpacing(7)
        custom = QCheckBox("Custom", custom_holder)
        custom.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        custom.setStyleSheet(line_patch._choice_toggle_style())
        unit = _current_unit(root)
        value = QDoubleSpinBox(custom_holder)
        value.setRange(0.1, 500.0)
        value.setDecimals(2)
        value.setSingleStep(0.5)
        value.setValue(float(getattr(root, "_text_line_spacing", 4.0) or 4.0))
        value.setSuffix(f" {unit}")
        value.setFixedWidth(132)
        _style_toolbar_spin(value)
        apply = QPushButton("Apply", custom_holder)
        apply.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        apply.setFixedHeight(30)
        apply.setFixedWidth(58)
        apply.setStyleSheet(line_patch._button_style("QPushButton"))
        value.setEnabled(False)
        apply.setEnabled(False)
        custom.toggled.connect(lambda checked: (value.setEnabled(checked), apply.setEnabled(checked)))
        apply.clicked.connect(lambda checked=False, p=popup, w=root, v=value, u=unit: (p.accept(), _apply_custom_line_spacing(w, float(v.value()), u)))
        row.addWidget(custom)
        row.addWidget(value)
        row.addWidget(apply)
        layout.addWidget(custom_holder)
        line_patch._show_popup_near(root, anchor, popup)

    line_patch._show_line_popup = show_line_popup
    line_patch._open_line_spacing_settings = lambda root: None


def _patch_key_handlers() -> None:
    for module_name in ("text_lag_final_patch", "text_line_math_symbols_patch", "ui_text_tool_final_patch", "final_focus_editing_icons_patch", "project_dialog_style_cursor_patch"):
        try:
            module = __import__(f"modules.mechanics_dynamics_statics.{module_name}", fromlist=[module_name])
            module._handle_text_editor_key = _handle_editor_event
            module._handle_editor_key = _handle_editor_event
            module._handle_editor_event = _handle_editor_event
            module._auto_convert_math_token = _auto_convert_math_token
        except Exception:
            pass


def _install_existing_editors(root: QWidget | None) -> None:
    if root is None:
        return
    canvas = getattr(root, "_canvas", None)
    editor = getattr(canvas, "_active_text_editor", None) if canvas is not None else None
    if isinstance(editor, QTextEdit):
        editor._canvas_owner = canvas
        _install_editor_filter(editor)
    for editor in root.findChildren(QTextEdit):
        if getattr(editor, "_canvas_owner", None) is None and canvas is not None:
            editor._canvas_owner = canvas
        _install_editor_filter(editor)


def _patch_canvas_key_handler(edw) -> None:
    canvas_cls = getattr(edw, "EngineeringCanvas", None)
    if canvas_cls is None or getattr(canvas_cls, "_text_toolbar_final_event_safety_key_patch", "") == PATCH_VERSION:
        return
    old_key = canvas_cls.keyPressEvent

    def key_press(self, event) -> None:
        editor = getattr(self, "_active_text_editor", None)
        if isinstance(editor, QTextEdit):
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

    already_wrapped = getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_final_event_safety_patch", "") == PATCH_VERSION

    _patch_color_dialog()
    _patch_text_popup_menu_style()
    _patch_line_spacing_dialog()
    _patch_line_module_controls()
    _patch_key_handlers()
    _patch_canvas_key_handler(edw)
    for module in modules:
        _patch_show_editor(module)

    if already_wrapped:
        return

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _patch_color_dialog()
        _patch_text_popup_menu_style()
        _patch_line_spacing_dialog()
        _patch_line_module_controls()
        _patch_key_handlers()
        _patch_canvas_key_handler(edw)
        _install_existing_editors(self)
        _polish_textbar_controls(self)
        for delay in (0, 80, 250, 700, 1400):
            QTimer.singleShot(delay, lambda root=self: (_patch_key_handlers(), _install_existing_editors(root), _polish_textbar_controls(root), _patch_text_popup_menu_style(), _patch_line_spacing_dialog(), _patch_line_module_controls()))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_final_event_safety_patch = PATCH_VERSION

"""Final Line Spacing, Math Symbols, and list settings patch."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from PySide6.QtCore import QPoint, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainterPath, QPixmap, QRegion, QTextBlockFormat, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-text-line-math-symbols-2026-07-02-d"

PALETTE = ["#000000", "#132238", "#2f7df6", "#36a9e1", "#f18a2a", "#ffbf36", "#c9342b", "#168a50"]
COLOR_NAMES = {
    "#000000": "Black",
    "#132238": "Navy",
    "#2f7df6": "Blue",
    "#36a9e1": "Sky blue",
    "#f18a2a": "Orange",
    "#ffbf36": "Yellow",
    "#c9342b": "Red",
    "#168a50": "Green",
}
GREEK = ("α", "β", "γ", "δ", "ε", "ζ", "η", "θ", "λ", "μ", "π", "ρ", "σ", "τ", "φ", "ω", "Γ", "Δ", "Θ", "Λ", "Π", "Σ", "Φ", "Ω")
OPERATORS = ("±", "×", "÷", "=", "≠", "≤", "≥", "≈", "≡", "∞", "√", "∛", "∑", "∏", "∫", "∂", "∇", "∈", "∉", "∩", "∪", "⊂", "⊆")
ARROWS = ("←", "→", "↑", "↓", "↔", "↕", "↦", "⇒", "⇐", "⇔", "↗", "↘", "↙", "↖")
BULLETS = ("●", "○", "■", "◆", "➤", "✓")
NUMBERING = ("1.", "1)", "I.", "A.", "a.", "i.")


def _font(widget: QWidget, size: int = 10, *, bold: bool = True, symbol: bool = False, italic: bool = False) -> None:
    font = widget.font()
    font.setFamily("Segoe UI Symbol" if symbol else "Times New Roman")
    font.setPointSize(size)
    font.setBold(bold)
    font.setItalic(italic)
    widget.setFont(font)


def _button_style(selector: str = "QPushButton") -> str:
    return (
        selector + "{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:.55 #fff6d6,stop:1 #ffc969);"
        "border:1px solid #b98920;border-radius:8px;color:#132238;font-family:'Times New Roman';"
        "font-weight:900;font-style:normal;padding:4px 12px;outline:0;}"
        + selector + ":hover{background:#fff4cf;border-color:#ff8a35;}"
        + selector + ":pressed{background:#f18a2a;color:#ffffff;padding-top:5px;}"
        + selector + ":focus{outline:0;border:1px solid #b98920;}"
    )


def _menu_button_style() -> str:
    return (
        "QPushButton{background:rgba(255,255,255,218);border:1px solid #b8c5d4;border-radius:8px;"
        "color:#1f3148;font-family:'Times New Roman';font-size:12px;font-style:italic;font-weight:900;"
        "padding:5px 10px;text-align:left;outline:0;}"
        "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"
        "QPushButton:pressed{background:#f18a2a;color:#ffffff;padding-top:6px;}"
        "QPushButton:focus{outline:0;border:1px solid #b8c5d4;}"
    )


def _symbol_button_style() -> str:
    return (
        "QPushButton{background:rgba(255,255,255,230);border:1px solid #b8c5d4;border-radius:7px;"
        "color:#132238;font-family:'Segoe UI Symbol';font-size:14px;font-weight:400;font-style:normal;"
        "padding:0;outline:0;}"
        "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"
        "QPushButton:pressed{background:#f18a2a;color:#ffffff;}"
        "QPushButton:focus{outline:0;border:1px solid #b8c5d4;}"
    )


def _close_button_style() -> str:
    return (
        "QPushButton{background:#f8fbff;border:1px solid #7fa6ca;border-radius:9px;color:#102238;"
        "font-family:'Times New Roman';font-size:14px;font-weight:900;font-style:normal;padding:0;outline:0;}"
        "QPushButton:hover{background:#c9342b;border-color:#9d241f;color:#ffffff;}"
        "QPushButton:pressed{background:#8f1f1a;color:#ffffff;}"
        "QPushButton:focus{outline:0;border:1px solid #7fa6ca;}"
    )


def _add_color_button_style() -> str:
    return (
        "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe9a6,stop:.55 #ffc35a,stop:1 #f18a2a);"
        "border:1px solid #8b5d13;border-radius:6px;color:#102238;font-family:'Times New Roman';font-size:16px;"
        "font-weight:900;font-style:normal;padding:0;margin:0;outline:0;}"
        "QPushButton:hover{background:#ffdc78;border-color:#ff8a35;}"
        "QPushButton:pressed{background:#d8781f;color:#ffffff;padding-top:1px;}"
        "QPushButton:focus{outline:0;border:1px solid #8b5d13;}"
    )


def _apply_rounded_mask(widget: QWidget | None, radius: int = 12) -> None:
    if widget is None or widget.width() <= 0 or widget.height() <= 0:
        return
    path = QPainterPath()
    path.addRoundedRect(QRectF(widget.rect()), radius, radius)
    widget.setMask(QRegion(path.toFillPolygon().toPolygon()))


def _prepare_dialog_masks(dialog: QDialog, radius: int = 16) -> None:
    dialog.adjustSize()
    _apply_rounded_mask(dialog, radius)
    root = dialog.findChild(QWidget, "DialogRoot")
    _apply_rounded_mask(root, radius)


def _combo_style(combo: QComboBox) -> None:
    combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    combo.setFixedHeight(30)
    combo.setStyleSheet(
        "QComboBox{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#132238;"
        "font-family:'Times New Roman';font-size:11px;font-weight:800;font-style:normal;padding:1px 35px 1px 9px;outline:0;}"
        "QComboBox::drop-down{width:32px;border:0;subcontrol-origin:border;subcontrol-position:center right;"
        "background:#fff0a8;border-top-right-radius:8px;border-bottom-right-radius:8px;}"
        "QComboBox::down-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:7px solid #102238;}"
    )
    _font(combo, 10)


def _spin_style(spin) -> None:
    spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    spin.setKeyboardTracking(True)
    spin.setFixedHeight(30)
    try:
        edit = spin.lineEdit()
        edit.setReadOnly(False)
        edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        edit.setStyleSheet(
            "QLineEdit{background:transparent;border:0;color:#132238;font-family:'Times New Roman';"
            "font-size:11px;font-weight:500;font-style:normal;padding:0;}"
        )
    except Exception:
        pass
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#132238;"
        "font-family:'Times New Roman';font-size:11px;font-weight:500;font-style:normal;padding:1px 34px 1px 8px;outline:0;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{width:31px;border:0;subcontrol-position:top right;background:#fff0a8;border-top-right-radius:8px;}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{width:31px;border:0;subcontrol-position:bottom right;background:#fff0a8;border-bottom-right-radius:8px;}"
        "QSpinBox::up-arrow,QDoubleSpinBox::up-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:7px solid #102238;}"
        "QSpinBox::down-arrow,QDoubleSpinBox::down-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:7px solid #102238;}"
    )
    _font(spin, 10, bold=False, italic=False)


def _logo_pixmap_from_app() -> QPixmap:
    app = QApplication.instance()
    if app is None:
        return QPixmap()
    for widget in app.topLevelWidgets():
        icon = widget.windowIcon()
        if icon is not None and not icon.isNull():
            pixmap = icon.pixmap(24, 24)
            if not pixmap.isNull():
                return pixmap
    return QPixmap()


def _logo_pixmap_from_files() -> QPixmap:
    names = {
        "logo.png", "app_logo.png", "atlas_logo.png", "engineer_tools_logo.png", "icon.png",
        "logo.jpg", "app_icon.png", "window_icon.png", "atlas.png", "atls.png",
    }
    for root in list(Path(__file__).resolve().parents[:7]):
        for folder_name in ("logo", "assets", "icons", "images", "resources"):
            candidate = root / folder_name
            if not candidate.exists():
                continue
            for path in candidate.rglob("*"):
                if path.name.lower() in names or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                    pixmap = QPixmap(str(path))
                    if not pixmap.isNull():
                        return pixmap
    return QPixmap()


def _make_logo_label(parent: QWidget) -> QLabel:
    logo = QLabel(parent)
    logo.setFixedSize(28, 28)
    logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pixmap = _logo_pixmap_from_app()
    if pixmap.isNull():
        pixmap = _logo_pixmap_from_files()
    if not pixmap.isNull():
        logo.setPixmap(pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo.setStyleSheet("QLabel{background:#ffffff;border:1px solid #7fa6ca;border-radius:5px;}")
    else:
        logo.setText("")
        logo.setStyleSheet("QLabel{background:#ffffff;border:1px solid #7fa6ca;border-radius:5px;}")
    return logo


def _root_editor(root: QWidget | None):
    canvas = getattr(root, "_canvas", None) if root is not None else None
    editor = getattr(canvas, "_active_text_editor", None) if canvas is not None else None
    return canvas, editor


def _save(root: QWidget | None) -> None:
    canvas, editor = _root_editor(root)
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


def _patch_text_edit_key_handlers() -> None:
    def _matches(event, standard) -> bool:
        try:
            return bool(event.matches(standard))
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
            pass

    def _text_edit_handler(editor, event) -> bool:
        if _matches(event, QKeySequence.StandardKey.Copy):
            editor.copy(); event.accept(); return True
        if _matches(event, QKeySequence.StandardKey.Cut):
            editor.cut(); _save_editor(editor); event.accept(); return True
        if _matches(event, QKeySequence.StandardKey.Paste):
            editor.paste(); _save_editor(editor); event.accept(); return True
        if _matches(event, QKeySequence.StandardKey.SelectAll):
            editor.selectAll(); event.accept(); return True
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            return False
        return False

    def _is_text_shortcut(event) -> bool:
        return any(
            _matches(event, key)
            for key in (
                QKeySequence.StandardKey.Copy,
                QKeySequence.StandardKey.Cut,
                QKeySequence.StandardKey.Paste,
                QKeySequence.StandardKey.SelectAll,
            )
        )

    try:
        from . import ui_text_tool_final_patch as text_final
        text_final._handle_editor_key = _text_edit_handler
    except Exception:
        pass
    try:
        from . import final_focus_editing_icons_patch as focus_patch
        focus_patch._handle_editor_key = _text_edit_handler
        focus_patch._is_text_shortcut = _is_text_shortcut
    except Exception:
        pass


def _insert_symbol(root: QWidget | None, symbol: str) -> None:
    _canvas, editor = _root_editor(root)
    if editor is None:
        return
    cursor = editor.textCursor()
    fmt = QTextCharFormat(editor.currentCharFormat())
    fmt.setFontFamily("Segoe UI Symbol")
    fmt.setFontWeight(QFont.Weight.Normal)
    fmt.setFontItalic(False)
    cursor.insertText(symbol, fmt)
    editor.setTextCursor(cursor)
    editor.setFocus()
    _save(root)


def _convert_selection_to_math(root: QWidget | None) -> None:
    _canvas, editor = _root_editor(root)
    if editor is None:
        return
    cursor = editor.textCursor()
    text = cursor.selectedText() or editor.toPlainText()
    if not text:
        return
    html = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = re.sub(r"_([A-Za-z0-9]+)", r"<sub>\1</sub>", html)
    html = re.sub(r"\^([A-Za-z0-9]+)", r"<sup>\1</sup>", html)
    html = html.replace("+-", "±").replace("!=", "≠").replace("<=", "≤").replace(">=", "≥")
    if cursor.hasSelection():
        cursor.insertHtml(html)
    else:
        editor.selectAll()
        cursor = editor.textCursor()
        cursor.insertHtml(html)
    editor.setFocus()
    _save(root)


def _line_height_type() -> int:
    value = QTextBlockFormat.LineHeightTypes.ProportionalHeight
    try:
        return int(value.value)
    except Exception:
        return int(value)


def _apply_line_spacing(root: QWidget | None, value: float) -> None:
    _canvas, editor = _root_editor(root)
    if editor is None:
        return
    cursor = editor.textCursor()
    block = QTextBlockFormat(cursor.blockFormat())
    block.setLineHeight(int(value * 100), _line_height_type())
    cursor.mergeBlockFormat(block)
    editor.setTextCursor(cursor)
    editor.setFocus()
    _save(root)


def _buttons(root: QWidget | None) -> dict:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


def _insert_list_prefix(root: QWidget | None, prefix: str) -> None:
    _canvas, editor = _root_editor(root)
    if editor is None:
        return
    cursor = editor.textCursor()
    cursor.insertText(prefix + " ")
    editor.setTextCursor(cursor)
    editor.setFocus()
    _save(root)


def _roman(value: int, lower: bool = False) -> str:
    pairs = ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
    number = max(1, min(int(value), 3999))
    result = ""
    for amount, symbol in pairs:
        while number >= amount:
            result += symbol
            number -= amount
    return result.lower() if lower else result


def _alpha(value: int, lower: bool = False) -> str:
    number = max(1, int(value))
    chars: list[str] = []
    while number:
        number -= 1
        chars.append(chr(ord("A") + number % 26))
        number //= 26
    text = "".join(reversed(chars))
    return text.lower() if lower else text


def _format_numbering_prefix(style: str, start: int) -> str:
    if style == "1.":
        return f"{start}."
    if style == "1)":
        return f"{start})"
    if style == "I.":
        return _roman(start) + "."
    if style == "i.":
        return _roman(start, lower=True) + "."
    if style == "A.":
        return _alpha(start) + "."
    if style == "a.":
        return _alpha(start, lower=True) + "."
    return style


def _points_from_mm(value: object) -> float:
    try:
        return max(0.0, float(value)) * 72.0 / 25.4
    except Exception:
        return 0.0


def _apply_custom_list_style(root: QWidget | None, settings: dict[str, object]) -> None:
    _canvas, editor = _root_editor(root)
    if editor is None:
        return
    cursor = editor.textCursor()
    block = QTextBlockFormat(cursor.blockFormat())
    block.setLeftMargin(_points_from_mm(settings.get("indent_mm", 0)))
    block.setTextIndent(_points_from_mm(settings.get("gap_mm", 0)))
    cursor.mergeBlockFormat(block)
    fmt = QTextCharFormat(editor.currentCharFormat())
    fmt.setFontFamily(str(settings.get("font", "Times New Roman")))
    fmt.setFontPointSize(float(settings.get("size", 12)))
    fmt.setForeground(QColor(str(settings.get("color", "#000000"))))
    fmt.setFontItalic(False)
    fmt.setFontWeight(QFont.Weight.Normal)
    mode = str(settings.get("mode", "bullet"))
    style = str(settings.get("style", "•"))
    prefix = _format_numbering_prefix(style, int(settings.get("start_numbering", 1))) if mode == "numbering" else style
    cursor.insertText(prefix + " ", fmt)
    editor.setTextCursor(cursor)
    editor.setFocus()
    _save(root)


def _popup_shell(parent: QWidget | None, width: int) -> tuple[QDialog, QWidget, QVBoxLayout]:
    popup = QDialog(parent)
    popup.setObjectName("TextStandardMenuPopup")
    popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
    popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    popup.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
    popup.setAutoFillBackground(False)
    popup.setStyleSheet("QDialog#TextStandardMenuPopup{background:transparent;border:0;}")
    shell = QWidget(popup)
    shell.setObjectName("TextStandardMenuShell")
    shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    shell.setMinimumWidth(width)
    shell.setStyleSheet(
        "QWidget#TextStandardMenuShell{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:0.55 #edf8ff,stop:1 #fff1d3);"
        "border:1px solid #8fa2bb;border-radius:12px;}"
        "QLabel{background:transparent;color:#1f3148;font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:italic;}"
    )
    root = QVBoxLayout(popup)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(shell)
    layout = QVBoxLayout(shell)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(5)
    return popup, shell, layout


def _show_popup_near(root: QWidget | None, button: QPushButton, popup: QDialog) -> None:
    if root is not None:
        old = getattr(root, "_text_standard_popup", None)
        if old is not None:
            old.close()
        setattr(root, "_text_standard_popup", popup)
    popup.adjustSize()
    shell = popup.findChild(QWidget, "TextStandardMenuShell")
    _apply_rounded_mask(shell, 12)
    _apply_rounded_mask(popup, 12)
    position = button.mapToGlobal(QPoint(0, button.height() + 3))
    popup.move(position)
    popup.exec()


def _add_menu_row(layout: QVBoxLayout, text: str, handler) -> None:
    button = QPushButton(text)
    button.setMinimumHeight(25)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setStyleSheet(_menu_button_style())
    _font(button, 10, italic=True)
    button.clicked.connect(handler)
    layout.addWidget(button)


def _show_line_popup(root: QWidget | None, anchor: QPushButton) -> None:
    popup, _shell, layout = _popup_shell(anchor, 186)
    for label, value in (("1.0", 1.0), ("1.15", 1.15), ("1.5", 1.5), ("2.0", 2.0)):
        _add_menu_row(layout, label, lambda checked=False, v=value, p=popup, w=root: (p.accept(), _apply_line_spacing(w, v)))
    _add_menu_row(layout, "Line and paragraph settings...", lambda checked=False, p=popup, w=root: (p.accept(), _open_line_spacing_settings(w)))
    _show_popup_near(root, anchor, popup)


def _show_math_popup(root: QWidget | None, anchor: QPushButton) -> None:
    popup, _shell, layout = _popup_shell(anchor, 278)
    for title, symbols in (("Greek letters", GREEK), ("Math operators", OPERATORS), ("Arrows", ARROWS)):
        label = QLabel(title)
        _font(label, 10, italic=True)
        layout.addWidget(label)
        grid_holder = QWidget(popup)
        grid = QGridLayout(grid_holder)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(3)
        grid.setVerticalSpacing(3)
        for index, symbol in enumerate(symbols):
            button = QPushButton(symbol)
            button.setFixedSize(28, 25)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setStyleSheet(_symbol_button_style())
            _font(button, 11, bold=False, symbol=True, italic=False)
            button.clicked.connect(lambda checked=False, s=symbol, p=popup, w=root: (p.accept(), _insert_symbol(w, s)))
            grid.addWidget(button, index // 8, index % 8)
        layout.addWidget(grid_holder)
    _add_menu_row(layout, "Convert selected text to math", lambda checked=False, p=popup, w=root: (p.accept(), _convert_selection_to_math(w)))
    _show_popup_near(root, anchor, popup)


def _show_list_popup(root: QWidget | None, anchor: QPushButton, mode: str) -> None:
    popup, _shell, layout = _popup_shell(anchor, 210)
    _add_menu_row(layout, "None", lambda checked=False, p=popup: p.accept())
    values = BULLETS if mode == "bullet" else NUMBERING
    grid_holder = QWidget(popup)
    grid = QGridLayout(grid_holder)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(4)
    grid.setVerticalSpacing(4)
    for index, value in enumerate(values):
        button = QPushButton(value)
        button.setFixedSize(42, 30)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(_symbol_button_style())
        _font(button, 11, bold=False, symbol=(mode == "bullet"), italic=False)
        button.clicked.connect(lambda checked=False, v=value, p=popup, w=root: (p.accept(), _insert_list_prefix(w, v)))
        grid.addWidget(button, index // 3, index % 3)
    layout.addWidget(grid_holder)
    settings_text = "Custom bullet settings..." if mode == "bullet" else "Custom numbering settings..."
    _add_menu_row(layout, settings_text, lambda checked=False, p=popup, w=root, m=mode: (p.accept(), _open_list_settings(w, m)))
    _show_popup_near(root, anchor, popup)


def _dialog_shell(parent: QWidget | None, title: str, minimum: tuple[int, int]) -> tuple[QDialog, QWidget, QVBoxLayout]:
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    dialog.setMinimumSize(*minimum)
    dialog.setStyleSheet(
        "QDialog{background:transparent;}"
        "QWidget#DialogRoot{background:#ffffff;border:1px solid #95aac5;border-radius:16px;}"
        "QWidget#DialogHeader{background:#102238;border-top-left-radius:16px;border-top-right-radius:16px;}"
        "QWidget#DialogBody{background:#ffffff;border-bottom-left-radius:16px;border-bottom-right-radius:16px;}"
        "QLabel{color:#173454;font-family:'Times New Roman';font-weight:900;font-style:normal;}"
    )
    outer = QVBoxLayout(dialog)
    outer.setContentsMargins(0, 0, 0, 0)
    shell = QWidget(dialog)
    shell.setObjectName("DialogRoot")
    shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    outer.addWidget(shell)
    root_layout = QVBoxLayout(shell)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)
    header = QWidget(shell)
    header.setObjectName("DialogHeader")
    header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    header.setFixedHeight(42)
    header_row = QHBoxLayout(header)
    header_row.setContentsMargins(12, 4, 10, 4)
    title_label = QLabel(title, header)
    _font(title_label, 12, italic=True)
    title_label.setStyleSheet("QLabel{color:#ffffff;font-style:italic;font-weight:900;}")
    close = QPushButton("×", header)
    close.setFixedSize(24, 24)
    close.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    close.setStyleSheet(_close_button_style())
    close.clicked.connect(dialog.reject)
    header_row.addWidget(_make_logo_label(header))
    header_row.addWidget(title_label, 1)
    header_row.addWidget(close)
    root_layout.addWidget(header)
    body = QWidget(shell)
    body.setObjectName("DialogBody")
    body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(16, 14, 16, 14)
    body_layout.setSpacing(9)
    root_layout.addWidget(body, 1)
    return dialog, body, body_layout


def _open_custom_color_dialog(parent: QWidget | None, initial: str) -> str | None:
    dialog, body, body_layout = _dialog_shell(parent, "Add Custom Color", (560, 430))
    picker = QColorDialog(QColor(initial), body)
    picker.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
    picker.setOption(QColorDialog.ColorDialogOption.NoButtons, True)
    picker.setStyleSheet("QColorDialog{background:#ffffff;border:0;} QPushButton{font-family:'Times New Roman';font-weight:900;}")
    body_layout.addWidget(picker, 1)
    actions = QHBoxLayout()
    actions.addStretch(1)
    ok = QPushButton("OK")
    cancel = QPushButton("Cancel")
    for button in (ok, cancel):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(_button_style("QPushButton"))
    ok.clicked.connect(dialog.accept)
    cancel.clicked.connect(dialog.reject)
    actions.addWidget(ok)
    actions.addWidget(cancel)
    body_layout.addLayout(actions)
    _prepare_dialog_masks(dialog)
    if dialog.exec() == QDialog.DialogCode.Accepted and picker.currentColor().isValid():
        return picker.currentColor().name()
    return None


def _open_line_spacing_settings(root: QWidget | None) -> None:
    dialog, _body, body_layout = _dialog_shell(root, "Line and Paragraph Settings", (420, 250))
    form = QFormLayout()
    value = QDoubleSpinBox()
    value.setRange(0.5, 6.0)
    value.setDecimals(2)
    value.setSingleStep(0.05)
    value.setValue(1.15)
    _spin_style(value)
    form.addRow("Line spacing", value)
    body_layout.addLayout(form)
    actions = QHBoxLayout()
    actions.addStretch(1)
    ok = QPushButton("OK")
    cancel = QPushButton("Cancel")
    for button in (ok, cancel):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(_button_style("QPushButton"))
    ok.clicked.connect(dialog.accept)
    cancel.clicked.connect(dialog.reject)
    actions.addWidget(ok)
    actions.addWidget(cancel)
    body_layout.addLayout(actions)
    _prepare_dialog_masks(dialog)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        _apply_line_spacing(root, value.value())


def _open_list_settings(root: QWidget | None, mode: str) -> None:
    try:
        from . import ui_text_runtime_guard_patch as guard
        font_choices = list(guard.FONT_CHOICES)
    except Exception:
        font_choices = ["Times New Roman", "B Zar", "Zar", "B Nazanin", "Nazanin", "Arial"]

    title = "Custom Bullet Settings" if mode == "bullet" else "Custom Numbering Settings"
    dialog, body, body_layout = _dialog_shell(root, title, (500, 410))
    form = QFormLayout()
    form.setHorizontalSpacing(10)
    form.setVerticalSpacing(7)
    style = QComboBox(); style.addItems(list(BULLETS if mode == "bullet" else NUMBERING)); _combo_style(style)
    size = QSpinBox(); size.setRange(4, 96); size.setValue(12); size.setSuffix(" pt"); _spin_style(size)
    start = QSpinBox(); start.setRange(1, 9999); start.setValue(1); _spin_style(start)
    indent = QDoubleSpinBox(); indent.setRange(0, 100); indent.setDecimals(2); indent.setValue(7.0); indent.setSuffix(" mm"); _spin_style(indent)
    gap = QDoubleSpinBox(); gap.setRange(0, 80); gap.setDecimals(2); gap.setValue(4.0); gap.setSuffix(" mm"); _spin_style(gap)
    font_box = QComboBox(); font_box.addItems(font_choices); _combo_style(font_box)
    selected = {"color": "#000000"}
    preview = QLabel(body)
    preview.setFixedHeight(32)
    preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_preview() -> None:
        prefix = _format_numbering_prefix(style.currentText(), start.value()) if mode == "numbering" else style.currentText()
        preview.setText(prefix + "  Sample text")
        preview_font = QFont(font_box.currentText() or "Times New Roman", size.value(), QFont.Weight.Normal)
        preview_font.setItalic(False)
        preview.setFont(preview_font)
        preview.setStyleSheet("QLabel{background:#f6fbff;border:1px solid #b7c9dc;border-radius:8px;color:" + selected["color"] + ";font-style:normal;}")

    def choose(value: str) -> None:
        selected["color"] = value
        update_preview()

    form.addRow("Style", style)
    form.addRow("Size", size)
    if mode == "numbering":
        form.addRow("Start numbering", start)
    form.addRow("Start indent", indent)
    form.addRow("Distance to text", gap)
    form.addRow("Font", font_box)
    body_layout.addLayout(form)
    body_layout.addWidget(preview)

    colors = list(PALETTE)
    color_holder = QWidget(body)
    color_row = QHBoxLayout(color_holder)
    color_row.setContentsMargins(0, 0, 0, 0)
    color_row.setSpacing(0)

    def rebuild_colors() -> None:
        while color_row.count():
            item = color_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        palette = QWidget(color_holder)
        columns = max(4, (len(colors) + 1) // 2)
        palette.setFixedSize(columns * 18, 36)
        grid = QGridLayout(palette)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(0)
        grid.setVerticalSpacing(0)
        for index, color in enumerate(colors):
            swatch = QPushButton(palette)
            swatch.setFixedSize(18, 18)
            swatch.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            swatch.setToolTip(COLOR_NAMES.get(color.lower(), color))
            swatch.setStyleSheet("QPushButton{background:" + color + ";border:1px solid #243d58;border-radius:2px;padding:0;margin:0;} QPushButton:hover{border:2px solid #ff8a35;}")
            swatch.clicked.connect(lambda checked=False, c=color: choose(c))
            grid.addWidget(swatch, index % 2, index // 2)
        add = QPushButton("＋", color_holder)
        add.setFixedSize(20, 36)
        add.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        add.setToolTip("Add custom color")
        add.setStyleSheet(_add_color_button_style())

        def add_color() -> None:
            value = _open_custom_color_dialog(dialog, selected["color"])
            if value:
                if value not in colors and len(colors) < 28:
                    colors.append(value)
                choose(value)
                rebuild_colors()

        add.clicked.connect(add_color)
        color_row.addWidget(palette)
        color_row.addWidget(add)
        color_row.addStretch(1)

    style.currentTextChanged.connect(lambda _value: update_preview())
    size.valueChanged.connect(lambda _value: update_preview())
    start.valueChanged.connect(lambda _value: update_preview())
    indent.valueChanged.connect(lambda _value: update_preview())
    gap.valueChanged.connect(lambda _value: update_preview())
    font_box.currentTextChanged.connect(lambda _value: update_preview())
    update_preview()
    rebuild_colors()
    body_layout.addWidget(color_holder)
    actions = QHBoxLayout()
    actions.addStretch(1)
    ok = QPushButton("OK")
    cancel = QPushButton("Cancel")
    for button in (ok, cancel):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(_button_style("QPushButton"))
    ok.clicked.connect(dialog.accept)
    cancel.clicked.connect(dialog.reject)
    actions.addWidget(ok)
    actions.addWidget(cancel)
    body_layout.addLayout(actions)
    _prepare_dialog_masks(dialog)
    if dialog.exec() == QDialog.DialogCode.Accepted and root is not None:
        settings = {
            "mode": mode,
            "style": style.currentText(),
            "size": size.value(),
            "start_numbering": start.value(),
            "indent_mm": indent.value(),
            "gap_mm": gap.value(),
            "font": font_box.currentText(),
            "color": selected["color"],
        }
        setattr(root, "_last_text_list_settings", settings)
        _apply_custom_list_style(root, settings)


def _wire_popup_button(button: QPushButton, property_name: str, callback) -> None:
    old_menu = button.menu()
    if old_menu is not None:
        try:
            button.setMenu(None)
        except TypeError:
            pass
        old_menu.deleteLater()
    if button.property(property_name) == PATCH_VERSION:
        return
    try:
        button.clicked.disconnect()
    except Exception:
        pass
    button.clicked.connect(callback)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setProperty(property_name, PATCH_VERSION)


def _apply_text_menus(root: QWidget | None) -> None:
    buttons = _buttons(root)

    line = buttons.get("Line spacing")
    if isinstance(line, QPushButton):
        _wire_popup_button(line, "lineMenuVersion", lambda checked=False, b=line, w=root: _show_line_popup(w, b))
        line.setToolTip("Line spacing")

    math = buttons.get("Math symbols")
    if isinstance(math, QPushButton):
        _wire_popup_button(math, "mathMenuVersion", lambda checked=False, b=math, w=root: _show_math_popup(w, b))
        math.setToolTip("Math symbols")

    bullet = buttons.get("Bullet")
    if isinstance(bullet, QPushButton):
        _wire_popup_button(bullet, "bulletMenuVersion", lambda checked=False, b=bullet, w=root: _show_list_popup(w, b, "bullet"))
        bullet.setToolTip("Bullet")

    numbering = buttons.get("Numbering")
    if isinstance(numbering, QPushButton):
        _wire_popup_button(numbering, "numberingMenuVersion", lambda checked=False, b=numbering, w=root: _show_list_popup(w, b, "numbering"))
        numbering.setToolTip("Numbering")


def apply_text_line_math_symbols_patch() -> None:
    from . import text_color_inline_palette_patch as inline_palette
    from . import text_color_swatch_patch as swatch
    from . import text_list_settings_final_patch as list_final
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_line_math_symbols_patch", "") == PATCH_VERSION:
        return

    _patch_text_edit_key_handlers()
    inline_palette._open_settings = _open_list_settings
    swatch._open_settings = _open_list_settings
    list_final._open_settings = _open_list_settings

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _patch_text_edit_key_handlers()
        _apply_text_menus(self)
        for delay in (0, 180, 600):
            QTimer.singleShot(delay, lambda root=self: (_patch_text_edit_key_handlers(), _apply_text_menus(root)))
        logging.info("text_line_math_symbols_patch: installed version=%s", PATCH_VERSION)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_line_math_symbols_patch = PATCH_VERSION

"""Final Line Spacing, Math Symbols, and white list settings patch."""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-text-line-math-symbols-2026-07-02-a"

PALETTE = ["#132238", "#2f7df6", "#36a9e1", "#f18a2a", "#ffbf36", "#c9342b", "#168a50", "#6e4ad6"]
COLOR_NAMES = {
    "#132238": "Navy",
    "#2f7df6": "Blue",
    "#36a9e1": "Sky blue",
    "#f18a2a": "Orange",
    "#ffbf36": "Yellow",
    "#c9342b": "Red",
    "#168a50": "Green",
    "#6e4ad6": "Purple",
}
GREEK = ("α", "β", "γ", "δ", "ε", "ζ", "η", "θ", "λ", "μ", "π", "ρ", "σ", "τ", "φ", "ω", "Γ", "Δ", "Θ", "Λ", "Π", "Σ", "Φ", "Ω")
OPERATORS = ("±", "×", "÷", "≠", "≤", "≥", "≈", "≡", "∞", "√", "∛", "∑", "∏", "∫", "∂", "∇", "∈", "∉", "∩", "∪", "⊂", "⊆")
ARROWS = ("←", "→", "↑", "↓", "↔", "↕", "↦", "⇒", "⇐", "⇔", "↗", "↘", "↙", "↖")


def _font(widget: QWidget, size: int = 10) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(False)
    widget.setFont(font)


def _button_style(selector: str = "QPushButton") -> str:
    return (
        f"{selector}{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:.55 #fff6d6,stop:1 #ffc969);"
        "border:1px solid #b98920;border-radius:8px;color:#132238;font-family:'Times New Roman';"
        "font-weight:900;font-style:normal;padding:4px 12px;outline:0;}"
        f"{selector}:hover{{background:#fff4cf;border-color:#ff8a35;}}"
        f"{selector}:pressed{{background:#f18a2a;color:#ffffff;padding-top:5px;}}"
        f"{selector}:focus{{outline:0;border:1px solid #b98920;}}"
    )


def _combo_style(combo: QComboBox) -> None:
    combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    combo.setFixedHeight(30)
    combo.setStyleSheet(
        "QComboBox{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#132238;"
        "font-family:'Times New Roman';font-size:11px;font-weight:800;padding:1px 35px 1px 9px;}"
        "QComboBox::drop-down{width:32px;border:0;subcontrol-origin:border;subcontrol-position:center right;"
        "background:#fff0a8;border-top-right-radius:8px;border-bottom-right-radius:8px;}"
    )
    _font(combo, 10)


def _spin_style(spin) -> None:
    spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    spin.setFixedHeight(30)
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#132238;"
        "font-family:'Times New Roman';font-size:11px;font-weight:800;padding:1px 34px 1px 8px;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{width:31px;border:0;subcontrol-position:top right;background:#fff0a8;border-top-right-radius:8px;}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{width:31px;border:0;subcontrol-position:bottom right;background:#fff0a8;border-bottom-right-radius:8px;}"
    )
    _font(spin, 10)


def _root_editor(root: QWidget | None):
    canvas = getattr(root, "_canvas", None) if root is not None else None
    editor = getattr(canvas, "_active_text_editor", None) if canvas is not None else None
    return canvas, editor


def _save(root: QWidget | None) -> None:
    canvas, _editor = _root_editor(root)
    if canvas is None:
        return
    try:
        from . import text_toolbar_word_behavior_patch as word
        word._save_active_editor(canvas)
    except Exception:
        pass


def _insert_symbol(root: QWidget | None, symbol: str) -> None:
    _canvas, editor = _root_editor(root)
    if editor is None:
        return
    editor.textCursor().insertText(symbol)
    _save(root)


def _apply_line_spacing(root: QWidget | None, value: float) -> None:
    try:
        from . import text_toolbar_word_behavior_patch as word
        word._apply_line_spacing(root, value)
    except Exception:
        pass


def _buttons(root: QWidget | None) -> dict:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


def _add_symbol_section(menu: QMenu, title: str, symbols: tuple[str, ...], root: QWidget | None) -> None:
    section = menu.addMenu(title)
    for symbol in symbols:
        action = section.addAction(symbol)
        action.triggered.connect(lambda checked=False, s=symbol, w=root: _insert_symbol(w, s))


def _open_list_settings(root: QWidget | None, mode: str) -> None:
    try:
        from . import ui_text_runtime_guard_patch as guard
        font_choices = list(guard.FONT_CHOICES)
    except Exception:
        font_choices = ["Times New Roman", "B Zar", "B Nazanin", "Arial"]

    dialog = QDialog(root)
    title = "Custom Bullet Settings" if mode == "bullet" else "Custom Numbering Settings"
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
    dialog.setMinimumSize(480, 380)
    dialog.setStyleSheet(
        "QDialog{background:#ffffff;border-radius:16px;}"
        "QWidget#DialogHeader{background:#102238;border-top-left-radius:16px;border-top-right-radius:16px;}"
        "QWidget#DialogBody{background:#ffffff;border-bottom-left-radius:16px;border-bottom-right-radius:16px;}"
        "QLabel{color:#173454;font-family:'Times New Roman';font-weight:900;}"
    )
    root_layout = QVBoxLayout(dialog)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    header = QWidget(dialog)
    header.setObjectName("DialogHeader")
    header.setFixedHeight(42)
    header_row = QHBoxLayout(header)
    header_row.setContentsMargins(12, 4, 10, 4)
    logo = QLabel("A", header)
    logo.setFixedSize(28, 28)
    logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    logo.setStyleSheet("QLabel{background:#ffffff;border:1px solid #7fa6ca;border-radius:5px;color:#123d6f;font-size:16px;font-weight:900;}")
    title_label = QLabel(title, header)
    _font(title_label, 12)
    title_label.setStyleSheet("QLabel{color:#ffffff;font-style:italic;font-weight:900;}")
    header_row.addWidget(logo)
    header_row.addWidget(title_label, 1)
    root_layout.addWidget(header)

    body = QWidget(dialog)
    body.setObjectName("DialogBody")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(16, 14, 16, 14)
    body_layout.setSpacing(9)
    root_layout.addWidget(body, 1)

    form = QFormLayout()
    form.setHorizontalSpacing(10)
    form.setVerticalSpacing(7)
    style = QComboBox(); style.addItems(["●", "○", "■", "◆", "➤", "✓"] if mode == "bullet" else ["1.", "1)", "I.", "A.", "a.", "i."])
    _combo_style(style)
    size = QSpinBox(); size.setRange(4, 96); size.setValue(12); size.setSuffix(" pt"); _spin_style(size)
    start = QSpinBox(); start.setRange(1, 9999); start.setValue(1); _spin_style(start)
    indent = QDoubleSpinBox(); indent.setRange(0, 100); indent.setDecimals(2); indent.setValue(7.0); indent.setSuffix(" mm"); _spin_style(indent)
    gap = QDoubleSpinBox(); gap.setRange(0, 80); gap.setDecimals(2); gap.setValue(4.0); gap.setSuffix(" mm"); _spin_style(gap)
    font_box = QComboBox(); font_box.addItems(font_choices); _combo_style(font_box)
    selected = {"color": "#132238"}
    color_preview = QLabel("■")
    _font(color_preview, 14)

    def choose(value: str) -> None:
        selected["color"] = value
        color_preview.setToolTip(COLOR_NAMES.get(value.lower(), value))
        color_preview.setStyleSheet(f"color:{value};font-size:18px;font-weight:900;")

    choose(selected["color"])
    form.addRow("Style", style)
    form.addRow("Size", size)
    if mode == "numbering":
        form.addRow("Start numbering", start)
    form.addRow("Start indent", indent)
    form.addRow("Distance to text", gap)
    form.addRow("Font", font_box)
    form.addRow("Color", color_preview)
    body_layout.addLayout(form)

    colors = list(PALETTE)
    color_holder = QWidget(body)
    color_row = QHBoxLayout(color_holder)
    color_row.setContentsMargins(0, 0, 0, 0)
    color_row.setSpacing(2)

    def rebuild_colors() -> None:
        while color_row.count():
            item = color_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        palette = QWidget(color_holder)
        columns = max(4, (len(colors) + 1) // 2)
        palette.setFixedSize(columns * 18 + max(0, columns - 1) * 2, 38)
        grid = QGridLayout(palette)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(2)
        grid.setVerticalSpacing(2)
        for index, color in enumerate(colors):
            swatch = QPushButton(palette)
            swatch.setFixedSize(18, 18)
            swatch.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            swatch.setToolTip(COLOR_NAMES.get(color.lower(), color))
            swatch.setStyleSheet(f"QPushButton{{background:{color};border:1px solid #243d58;border-radius:2px;padding:0;margin:0;}} QPushButton:hover{{border:2px solid #ff8a35;}}")
            swatch.clicked.connect(lambda checked=False, c=color: choose(c))
            grid.addWidget(swatch, index % 2, index // 2)
        add = QPushButton("＋", color_holder)
        add.setFixedSize(18, 38)
        add.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        add.setToolTip("Add custom color")
        add.setStyleSheet(_button_style("QPushButton"))

        def add_color() -> None:
            picked = QColorDialog.getColor(QColor("#132238"), dialog, "Add Custom Color")
            if picked.isValid():
                value = picked.name()
                if value not in colors and len(colors) < 28:
                    colors.append(value)
                choose(value)
                rebuild_colors()

        add.clicked.connect(add_color)
        color_row.addWidget(palette)
        color_row.addWidget(add)

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

    if dialog.exec() == QDialog.DialogCode.Accepted and root is not None:
        setattr(root, "_last_text_list_settings", {
            "mode": mode,
            "style": style.currentText(),
            "size": size.value(),
            "start_numbering": start.value(),
            "indent_mm": indent.value(),
            "gap_mm": gap.value(),
            "font": font_box.currentText(),
            "color": selected["color"],
        })


def _apply_text_menus(root: QWidget | None) -> None:
    buttons = _buttons(root)
    line = buttons.get("Line spacing")
    if isinstance(line, QPushButton):
        menu = QMenu(line)
        for label, value in (("1.0", 1.0), ("1.15", 1.15), ("1.5", 1.5), ("2.0", 2.0)):
            action = menu.addAction(label)
            action.triggered.connect(lambda checked=False, v=value, w=root: _apply_line_spacing(w, v))
        menu.addSeparator()
        action = menu.addAction("Line and paragraph settings...")
        action.triggered.connect(lambda checked=False, w=root: _apply_line_spacing(w, 1.15))
        line.setMenu(menu)
        line.setToolTip("Line spacing")
        line.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    math = buttons.get("Math symbols")
    if isinstance(math, QPushButton):
        menu = QMenu(math)
        _add_symbol_section(menu, "Greek letters", GREEK, root)
        _add_symbol_section(menu, "Math operators", OPERATORS, root)
        _add_symbol_section(menu, "Arrows", ARROWS, root)
        math.setMenu(menu)
        math.setToolTip("Math symbols")
        math.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    bullet = buttons.get("Bullet")
    if isinstance(bullet, QPushButton) and bullet.menu() is not None:
        menu = bullet.menu()
        menu.addSeparator()
        action = menu.addAction("Custom bullet settings...")
        action.triggered.connect(lambda checked=False, w=root: _open_list_settings(w, "bullet"))
    numbering = buttons.get("Numbering")
    if isinstance(numbering, QPushButton) and numbering.menu() is not None:
        menu = numbering.menu()
        menu.addSeparator()
        action = menu.addAction("Custom numbering settings...")
        action.triggered.connect(lambda checked=False, w=root: _open_list_settings(w, "numbering"))


def apply_text_line_math_symbols_patch() -> None:
    from . import text_color_inline_palette_patch as inline_palette
    from . import text_color_swatch_patch as swatch
    from . import text_list_settings_final_patch as list_final
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_line_math_symbols_patch", "") == PATCH_VERSION:
        return

    inline_palette._open_settings = _open_list_settings
    swatch._open_settings = _open_list_settings
    list_final._open_settings = _open_list_settings

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _apply_text_menus(self)
        for delay in (0, 180, 600):
            QTimer.singleShot(delay, lambda root=self: _apply_text_menus(root))
        logging.info("text_line_math_symbols_patch: installed version=%s", PATCH_VERSION)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_line_math_symbols_patch = PATCH_VERSION

"""Bullet and numbering settings for the top Text bar."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
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

PATCH_VERSION = "engineering-text-list-settings-2026-07-01-a"

DEFAULT_COLORS = (
    ("Navy", "#132238"),
    ("Blue", "#2f7df6"),
    ("Sky", "#36a9e1"),
    ("Orange", "#f18a2a"),
    ("Gold", "#ffbf36"),
    ("Red", "#c9342b"),
    ("Green", "#168a50"),
    ("Purple", "#6e4ad6"),
)


def _font(widget: QWidget, size: int = 10) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(False)
    widget.setFont(font)


def _symbol_icon(symbol: str, color: str = "#132238") -> QIcon:
    pixmap = QPixmap(28, 28)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor("#6f91b2"), 1.0))
    painter.setBrush(QColor("#ffffff"))
    painter.drawRoundedRect(2, 2, 24, 24, 5, 5)
    font = painter.font()
    font.setFamily("Times New Roman")
    font.setBold(True)
    font.setPointSize(14)
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, symbol)
    painter.end()
    return QIcon(pixmap)


def _color_button(name: str, color: str, callback) -> QPushButton:
    button = QPushButton(name)
    button.setFixedSize(82, 28)
    button.setStyleSheet(
        f"QPushButton{{background:{color};border:1px solid #6f91b2;border-radius:7px;color:#ffffff;font-family:'Times New Roman';font-weight:900;}}"
        "QPushButton:hover{border:2px solid #ff8a35;}"
    )
    button.clicked.connect(lambda checked=False, value=color: callback(value))
    return button


def _open_list_settings(root: QWidget | None, mode: str) -> None:
    dialog = QDialog(root)
    title = "Custom Bullet Settings" if mode == "bullet" else "Custom Numbering Settings"
    dialog.setObjectName("TextListSettingsDialog")
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setMinimumSize(430, 360)
    dialog.setStyleSheet(
        "QDialog#TextListSettingsDialog{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.52 #eef8ff,stop:1 #fff0c8);border-radius:16px;}"
        "QLabel{color:#173454;font-family:'Times New Roman';font-weight:900;font-style:normal;}"
        "QComboBox,QSpinBox,QDoubleSpinBox{background:#fffefa;border:1px solid #b98920;border-radius:8px;color:#123d6f;font-family:'Times New Roman';font-weight:800;padding:3px 8px;}"
        "QPushButton{background:#ffffff;border:1px solid #7fa6ca;border-radius:8px;color:#123d6f;font-family:'Times New Roman';font-weight:900;padding:5px 12px;}"
        "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"
    )
    root_layout = QVBoxLayout(dialog)
    root_layout.setContentsMargins(14, 14, 14, 14)
    root_layout.setSpacing(10)
    header = QLabel(title)
    _font(header, 13)
    root_layout.addWidget(header)

    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
    form.setFormAlignment(Qt.AlignmentFlag.AlignTop)

    symbol = QComboBox()
    if mode == "bullet":
        symbol.addItems(["● Filled circle", "○ Hollow circle", "■ Square", "◆ Diamond", "➤ Arrow", "✓ Check"])
    else:
        symbol.addItems(["1. 2. 3.", "1) 2) 3)", "I. II. III.", "A. B. C.", "a. b. c.", "i. ii. iii."])
    size = QSpinBox(); size.setRange(4, 96); size.setValue(12); size.setSuffix(" pt")
    indent = QDoubleSpinBox(); indent.setRange(0.0, 100.0); indent.setDecimals(2); indent.setValue(7.0); indent.setSuffix(" mm")
    text_gap = QDoubleSpinBox(); text_gap.setRange(0.0, 80.0); text_gap.setDecimals(2); text_gap.setValue(4.0); text_gap.setSuffix(" mm")
    font_box = QComboBox()
    try:
        from . import ui_text_runtime_guard_patch as guard
        font_box.addItems(list(guard.FONT_CHOICES))
    except Exception:
        font_box.addItems(["Times New Roman", "B Zar", "B Nazanin", "Tahoma", "Arial"])
    selected_color = {"value": "#132238"}
    color_label = QLabel("Selected: Navy")

    for widget in (symbol, size, indent, text_gap, font_box, color_label):
        _font(widget, 10)
    form.addRow("Style", symbol)
    form.addRow("Size", size)
    form.addRow("Start indent", indent)
    form.addRow("Distance to text", text_gap)
    form.addRow("Font", font_box)
    form.addRow("Color", color_label)
    root_layout.addLayout(form)

    color_grid = QGridLayout()
    color_grid.setHorizontalSpacing(6)
    color_grid.setVerticalSpacing(6)

    def choose_color(value: str) -> None:
        selected_color["value"] = value
        color_label.setText(f"Selected: {value}")
        color_label.setStyleSheet(f"color:{value};font-family:'Times New Roman';font-weight:900;")

    for index, (name, color) in enumerate(DEFAULT_COLORS):
        color_grid.addWidget(_color_button(name, color, choose_color), index // 4, index % 4)
    custom = QPushButton("Custom color...")
    custom.clicked.connect(lambda: choose_color(QColorDialog.getColor(QColor(selected_color["value"]), dialog, "Custom color").name()))
    color_grid.addWidget(custom, 2, 0, 1, 4)
    root_layout.addLayout(color_grid)

    buttons = QHBoxLayout()
    buttons.addStretch(1)
    apply_btn = QPushButton("Apply")
    cancel_btn = QPushButton("Cancel")
    apply_btn.clicked.connect(dialog.accept)
    cancel_btn.clicked.connect(dialog.reject)
    buttons.addWidget(apply_btn)
    buttons.addWidget(cancel_btn)
    root_layout.addLayout(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        settings = {
            "mode": mode,
            "style": symbol.currentText(),
            "size": size.value(),
            "indent_mm": indent.value(),
            "gap_mm": text_gap.value(),
            "font": font_box.currentText(),
            "color": selected_color["value"],
        }
        if root is not None:
            setattr(root, "_last_text_list_settings", settings)


def _menu_action(menu: QMenu, text: str, callback, icon: QIcon | None = None) -> None:
    action = menu.addAction(text)
    if icon is not None:
        action.setIcon(icon)
    action.triggered.connect(lambda checked=False, cb=callback: cb())


def _apply(root, command: str, value=None) -> None:
    from . import ui_text_tool_runtime_fix_patch as runtime
    runtime._apply_text_action(root, command, value)


def _attach_button_menus(bar: QWidget) -> None:
    from PySide6.QtWidgets import QHBoxLayout

    window = bar.window()
    for button in bar.findChildren(QPushButton):
        tooltip = button.toolTip()
        if tooltip == "Bullet" and button.menu() is None:
            menu = QMenu(button)
            _menu_action(menu, "None", lambda w=window: _apply(w, "bullet", "none"), _symbol_icon("∅"))
            _menu_action(menu, "●  Filled circle", lambda w=window: _apply(w, "bullet", "filled"), _symbol_icon("●"))
            _menu_action(menu, "○  Hollow circle", lambda w=window: _apply(w, "bullet", "hollow"), _symbol_icon("○"))
            _menu_action(menu, "■  Square", lambda w=window: _apply(w, "bullet", "square"), _symbol_icon("■"))
            _menu_action(menu, "◆  Diamond", lambda w=window: _apply(w, "bullet", "diamond"), _symbol_icon("◆"))
            _menu_action(menu, "➤  Arrow", lambda w=window: _apply(w, "bullet", "arrow"), _symbol_icon("➤", "#2f7df6"))
            _menu_action(menu, "✓  Check", lambda w=window: _apply(w, "bullet", "check"), _symbol_icon("✓", "#168a50"))
            menu.addSeparator()
            _menu_action(menu, "Custom bullet settings...", lambda w=window: _open_list_settings(w, "bullet"), _symbol_icon("⚙", "#f18a2a"))
            button.setMenu(menu)
        elif tooltip == "Numbering" and button.menu() is None:
            menu = QMenu(button)
            _menu_action(menu, "None", lambda w=window: _apply(w, "numbering", "none"), _symbol_icon("∅"))
            _menu_action(menu, "1. 2. 3.", lambda w=window: _apply(w, "numbering", "decimal_dot"), _symbol_icon("1."))
            _menu_action(menu, "1) 2) 3)", lambda w=window: _apply(w, "numbering", "decimal_paren"), _symbol_icon("1)"))
            _menu_action(menu, "I. II. III.", lambda w=window: _apply(w, "numbering", "roman"), _symbol_icon("I"))
            _menu_action(menu, "A. B. C.", lambda w=window: _apply(w, "numbering", "alpha_upper"), _symbol_icon("A"))
            _menu_action(menu, "a. b. c.", lambda w=window: _apply(w, "numbering", "alpha_lower"), _symbol_icon("a"))
            _menu_action(menu, "i. ii. iii.", lambda w=window: _apply(w, "numbering", "roman_lower"), _symbol_icon("i"))
            menu.addSeparator()
            _menu_action(menu, "Custom numbering settings...", lambda w=window: _open_list_settings(w, "numbering"), _symbol_icon("⚙", "#f18a2a"))
            button.setMenu(menu)
        elif tooltip == "Italic":
            font = button.font(); font.setItalic(True); button.setFont(font)
        elif tooltip == "Align left":
            button.setText("☰")
            button.clicked.connect(lambda checked=False, w=window: _apply(w, "align", "left"))
        elif tooltip == "Align center":
            button.setText("≡")
            button.clicked.connect(lambda checked=False, w=window: _apply(w, "align", "center"))
        elif tooltip == "Align right":
            button.setText("☷")
            button.clicked.connect(lambda checked=False, w=window: _apply(w, "align", "right"))
        elif tooltip == "Justify":
            button.setText("▤")
            button.clicked.connect(lambda checked=False, w=window: _apply(w, "align", "justify"))
    if bar.findChild(QPushButton, "TextColorButton") is None:
        color = QPushButton("A")
        color.setObjectName("TextColorButton")
        color.setToolTip("Text and bullet color")
        color.setFixedSize(38, 32)
        color.setStyleSheet("QPushButton#TextColorButton{background:#ffffff;border:1px solid #7fa6ca;border-radius:9px;color:#123d6f;font-family:'Times New Roman';font-size:12px;font-weight:900;} QPushButton#TextColorButton:hover{background:#fff4cf;border-color:#ff8a35;}")
        menu = QMenu(color)
        for name, value in DEFAULT_COLORS:
            _menu_action(menu, f"■ {name}", lambda w=window, v=value: _apply(w, "text_color", v), _symbol_icon("■", value))
        menu.addSeparator()
        _menu_action(menu, "Custom text color...", lambda w=window: _apply(w, "text_color", QColorDialog.getColor(QColor("#132238"), w, "Text color").name()), _symbol_icon("⚙", "#f18a2a"))
        color.setMenu(menu)
        layout = bar.layout()
        if isinstance(layout, QHBoxLayout):
            layout.addWidget(color)


def apply_text_list_settings_patch() -> None:
    from . import ui_text_tool_runtime_fix_patch as runtime
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_list_settings_patch", "") == PATCH_VERSION:
        return
    runtime._attach_button_menus = _attach_button_menus
    edw.EngineeringDesignWorkspace._engineering_text_list_settings_patch = PATCH_VERSION

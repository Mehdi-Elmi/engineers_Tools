"""Compact color swatches for Text, Bullet, and Numbering controls."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QColorDialog, QDialog, QGridLayout, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget, QWidgetAction

PATCH_VERSION = "engineering-text-color-swatch-2026-07-01-a"

SWATCHES = ["#132238", "#2f7df6", "#36a9e1", "#f18a2a", "#ffbf36", "#c9342b", "#168a50", "#6e4ad6"]


def _palette_icon() -> QIcon:
    pixmap = QPixmap(28, 28)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    positions = [(5, 5), (15, 5), (5, 15), (15, 15)]
    colors = ["#2f7df6", "#f18a2a", "#168a50", "#6e4ad6"]
    for (x, y), color in zip(positions, colors):
        painter.setBrush(QColor(color))
        painter.setPen(QPen(QColor("#102238"), 0.7))
        painter.drawRoundedRect(x, y, 8, 8, 2, 2)
    painter.end()
    return QIcon(pixmap)


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
    font.setItalic(False)
    font.setPointSize(14)
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, symbol)
    painter.end()
    return QIcon(pixmap)


def _apply(root, command: str, value=None) -> None:
    from . import ui_text_tool_runtime_fix_patch as runtime
    runtime._apply_text_action(root, command, value)


def _swatch(color: str, apply_color) -> QPushButton:
    button = QPushButton()
    button.setFixedSize(22, 22)
    button._swatch_color = color

    def paint(value: str) -> None:
        button._swatch_color = value
        button.setStyleSheet(f"QPushButton{{background:{value};border:1px solid #314b68;border-radius:4px;}} QPushButton:hover{{border:2px solid #ff8a35;}}")

    def choose_custom() -> None:
        picked = QColorDialog.getColor(QColor(button._swatch_color), button, "Custom color")
        if picked.isValid():
            paint(picked.name())
            apply_color(picked.name())

    paint(color)
    button.clicked.connect(lambda checked=False: apply_color(button._swatch_color))
    button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    button.customContextMenuRequested.connect(lambda _pos: choose_custom())
    return button


def _swatch_menu(parent: QPushButton, root, apply_color) -> QMenu:
    menu = QMenu(parent)
    holder = QWidget(menu)
    grid = QGridLayout(holder)
    grid.setContentsMargins(6, 6, 6, 6)
    grid.setHorizontalSpacing(5)
    grid.setVerticalSpacing(5)
    for index, color in enumerate(SWATCHES):
        grid.addWidget(_swatch(color, apply_color), index // 4, index % 4)
    custom = QPushButton()
    custom.setIcon(_symbol_icon("+", "#f18a2a"))
    custom.setIconSize(custom.sizeHint())
    custom.setFixedSize(22, 22)
    custom.setStyleSheet("QPushButton{background:#ffffff;border:1px solid #7fa6ca;border-radius:4px;} QPushButton:hover{border:2px solid #ff8a35;}")
    custom.clicked.connect(lambda: _choose_direct_color(custom, apply_color))
    grid.addWidget(custom, 2, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)
    action = QWidgetAction(menu)
    action.setDefaultWidget(holder)
    menu.addAction(action)
    return menu


def _choose_direct_color(parent: QWidget, apply_color) -> None:
    picked = QColorDialog.getColor(QColor("#132238"), parent, "Custom color")
    if picked.isValid():
        apply_color(picked.name())


def _open_settings(root, mode: str) -> None:
    from . import text_list_settings_patch as lists

    dialog = QDialog(root)
    dialog.setWindowTitle("Custom Bullet Settings" if mode == "bullet" else "Custom Numbering Settings")
    dialog.setModal(True)
    dialog.setMinimumSize(390, 300)
    dialog.setStyleSheet(
        "QDialog{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.55 #eef8ff,stop:1 #fff0c8);border-radius:16px;}"
        "QLabel{color:#173454;font-family:'Times New Roman';font-weight:900;font-style:normal;}"
        "QPushButton{background:#ffffff;border:1px solid #7fa6ca;border-radius:8px;color:#123d6f;font-family:'Times New Roman';font-weight:900;padding:5px 12px;}"
        "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"
    )
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(14, 14, 14, 14)
    title = QLabel(dialog.windowTitle())
    layout.addWidget(title)
    helper = QLabel("Color swatches: left click applies, right click replaces a preset with a custom color.")
    layout.addWidget(helper)
    grid = QGridLayout()
    selected = {"color": "#132238"}

    def choose(value: str) -> None:
        selected["color"] = value

    for index, color in enumerate(lists.DEFAULT_COLORS if isinstance(lists.DEFAULT_COLORS, list) else SWATCHES):
        value = color[1] if isinstance(color, tuple) else color
        grid.addWidget(_swatch(value, choose), index // 4, index % 4)
    layout.addLayout(grid)
    actions = QHBoxLayout()
    actions.addStretch(1)
    apply_btn = QPushButton("Apply")
    cancel_btn = QPushButton("Cancel")
    apply_btn.clicked.connect(dialog.accept)
    cancel_btn.clicked.connect(dialog.reject)
    actions.addWidget(apply_btn)
    actions.addWidget(cancel_btn)
    layout.addLayout(actions)
    if dialog.exec() == QDialog.DialogCode.Accepted and root is not None:
        setattr(root, "_last_text_list_settings", {"mode": mode, "color": selected["color"]})


def _attach_button_menus(bar: QWidget) -> None:
    window = bar.window()
    for button in bar.findChildren(QPushButton):
        tooltip = button.toolTip()
        if tooltip == "Bullet" and button.menu() is None:
            menu = QMenu(button)
            for text, value, symbol in (("None", "none", "∅"), ("Filled circle", "filled", "●"), ("Hollow circle", "hollow", "○"), ("Square", "square", "■"), ("Diamond", "diamond", "◆"), ("Arrow", "arrow", "➤"), ("Check", "check", "✓")):
                action = menu.addAction(_symbol_icon(symbol), text)
                action.triggered.connect(lambda checked=False, w=window, v=value: _apply(w, "bullet", v))
            menu.addSeparator()
            action = menu.addAction(_symbol_icon("+", "#f18a2a"), "Custom bullet settings...")
            action.triggered.connect(lambda checked=False, w=window: _open_settings(w, "bullet"))
            button.setMenu(menu)
        elif tooltip == "Numbering" and button.menu() is None:
            menu = QMenu(button)
            for text, value, symbol in (("None", "none", "∅"), ("1. 2. 3.", "decimal_dot", "1."), ("1) 2) 3)", "decimal_paren", "1)"), ("I. II. III.", "roman", "I"), ("A. B. C.", "alpha_upper", "A"), ("a. b. c.", "alpha_lower", "a"), ("i. ii. iii.", "roman_lower", "i")):
                action = menu.addAction(_symbol_icon(symbol), text)
                action.triggered.connect(lambda checked=False, w=window, v=value: _apply(w, "numbering", v))
            menu.addSeparator()
            action = menu.addAction(_symbol_icon("+", "#f18a2a"), "Custom numbering settings...")
            action.triggered.connect(lambda checked=False, w=window: _open_settings(w, "numbering"))
            button.setMenu(menu)
        elif tooltip == "Text and bullet color" or button.objectName() == "TextColorButton":
            button.setText("")
            button.setIcon(_palette_icon())
            button.setIconSize(button.size())
            button.setMenu(_swatch_menu(button, window, lambda value, w=window: _apply(w, "text_color", value)))
        elif tooltip == "Italic":
            font = button.font(); font.setItalic(True); button.setFont(font)
        elif tooltip == "Align left":
            button.setText("☰")
        elif tooltip == "Align center":
            button.setText("≡")
        elif tooltip == "Align right":
            button.setText("☷")
        elif tooltip == "Justify":
            button.setText("▤")
    if bar.findChild(QPushButton, "TextColorButton") is None:
        color = QPushButton()
        color.setObjectName("TextColorButton")
        color.setToolTip("Text and bullet color")
        color.setFixedSize(72, 32)
        color.setIcon(_palette_icon())
        color.setIconSize(color.size())
        color.setStyleSheet("QPushButton#TextColorButton{background:#ffffff;border:1px solid #7fa6ca;border-radius:9px;} QPushButton#TextColorButton:hover{background:#fff4cf;border-color:#ff8a35;}")
        color.setMenu(_swatch_menu(color, window, lambda value, w=window: _apply(w, "text_color", value)))
        layout = bar.layout()
        if isinstance(layout, QHBoxLayout):
            layout.addWidget(color)


def apply_text_color_swatch_patch() -> None:
    from . import text_list_settings_patch as lists
    from . import ui_text_tool_runtime_fix_patch as runtime
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_color_swatch_patch", "") == PATCH_VERSION:
        return
    lists.DEFAULT_COLORS = SWATCHES
    runtime._attach_button_menus = _attach_button_menus
    edw.EngineeringDesignWorkspace._engineering_text_color_swatch_patch = PATCH_VERSION

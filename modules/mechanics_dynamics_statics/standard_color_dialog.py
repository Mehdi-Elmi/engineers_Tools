"""Shared project-standard Add Custom Color dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

_BASE_COLORS = [
    ("#000000", "Black"),
    ("#ffffff", "White"),
    ("#c9342b", "Red"),
    ("#f08a24", "Orange"),
    ("#f4c542", "Yellow"),
    ("#2f9e44", "Green"),
    ("#1f6fba", "Blue"),
    ("#6f42c1", "Purple"),
    ("#173454", "Dark Blue"),
    ("#8a5a2b", "Brown"),
    ("#7a8699", "Gray"),
    ("#21a6a6", "Cyan"),
    ("#d63384", "Pink"),
    ("#5f3dc4", "Violet"),
    ("#0b7285", "Teal"),
    ("#495057", "Slate"),
]

_CLOSE_STYLE = (
    "QPushButton{background:#102238;border:1px solid #102238;border-radius:9px;color:#ffffff;"
    "font-family:'Times New Roman';font-size:14px;font-weight:900;font-style:normal;padding:0;outline:0;}"
    "QPushButton:hover{background:#c9342b;border-color:#9d241f;color:#ffffff;}"
    "QPushButton:pressed{background:#8f1f1a;color:#ffffff;}"
    "QPushButton:focus{outline:0;border:1px solid #102238;}"
)

_SWATCH_STYLE = (
    "QPushButton{background:%s;border:1px solid #9fb1c7;border-radius:5px;min-width:26px;max-width:26px;"
    "min-height:22px;max-height:22px;padding:0;outline:0;}"
    "QPushButton:hover{border:2px solid #173454;}"
    "QPushButton:pressed{border:2px solid #b88718;}"
    "QPushButton:focus{outline:0;border:2px solid #173454;}"
)

_PREVIEW_STYLE = (
    "QFrame{background:%s;border:1px solid #9fb1c7;border-radius:7px;min-width:58px;min-height:28px;}"
)


def _polish_shell_close_button(dialog) -> None:
    for button in dialog.findChildren(QPushButton):
        if button.text().strip() == "×":
            button.setStyleSheet(_CLOSE_STYLE)
            button.setCursor(Qt.CursorShape.ArrowCursor)


def _normal_hex(value: str | None) -> str:
    color = QColor(value or "#000000")
    if not color.isValid():
        return "#000000"
    return color.name(QColor.NameFormat.HexRgb)


def get_custom_color(parent: QWidget | None, current: str = "#000000", title: str = "Add Custom Color") -> str | None:
    """Open the reusable project-standard custom color picker and return a hex color."""
    try:
        from . import text_line_math_symbols_patch as ui_shell
    except Exception:
        return None

    selected = {"value": _normal_hex(current)}
    dialog, body, body_layout = ui_shell._dialog_shell(parent, title, (460, 360))
    _polish_shell_close_button(dialog)
    body.setStyleSheet("QWidget{background:#ffffff;border:0;}")

    caption = QLabel("Select a project color or pick a custom one.", body)
    caption.setStyleSheet(
        "QLabel{font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:italic;color:#173454;}"
    )
    body_layout.addWidget(caption)

    preview_row = QHBoxLayout()
    preview_row.setContentsMargins(0, 0, 0, 0)
    preview_row.setSpacing(8)
    preview_label = QLabel("Selected Color", body)
    preview_label.setStyleSheet(
        "QLabel{font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:italic;color:#173454;}"
    )
    preview = QFrame(body)
    preview.setStyleSheet(_PREVIEW_STYLE % selected["value"])
    preview_row.addWidget(preview_label)
    preview_row.addWidget(preview)
    preview_row.addStretch(1)
    body_layout.addLayout(preview_row)

    grid = QGridLayout()
    grid.setContentsMargins(0, 4, 0, 4)
    grid.setHorizontalSpacing(3)
    grid.setVerticalSpacing(3)
    body_layout.addLayout(grid)

    def choose(hex_value: str) -> None:
        selected["value"] = _normal_hex(hex_value)
        preview.setStyleSheet(_PREVIEW_STYLE % selected["value"])

    for index, (hex_value, name) in enumerate(_BASE_COLORS):
        swatch = QPushButton("", body)
        swatch.setToolTip(name)
        swatch.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        swatch.setCursor(Qt.CursorShape.ArrowCursor)
        swatch.setStyleSheet(_SWATCH_STYLE % hex_value)
        swatch.clicked.connect(lambda checked=False, value=hex_value: choose(value))
        grid.addWidget(swatch, index // 8, index % 8)

    picker_row = QHBoxLayout()
    picker_row.setContentsMargins(0, 3, 0, 0)
    picker_row.setSpacing(8)
    pick = QPushButton("Pick Custom Color", body)
    pick.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    pick.setCursor(Qt.CursorShape.ArrowCursor)
    pick.setStyleSheet(ui_shell._button_style("QPushButton"))

    def pick_color() -> None:
        color = QColorDialog.getColor(QColor(selected["value"]), dialog, "Pick Custom Color")
        if color.isValid():
            choose(color.name(QColor.NameFormat.HexRgb))

    pick.clicked.connect(pick_color)
    picker_row.addWidget(pick)
    picker_row.addStretch(1)
    body_layout.addLayout(picker_row)

    buttons = QHBoxLayout()
    buttons.setContentsMargins(0, 8, 0, 0)
    buttons.setSpacing(8)
    buttons.addStretch(1)
    ok = QPushButton("OK", body)
    cancel = QPushButton("Cancel", body)
    for button in (ok, cancel):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setCursor(Qt.CursorShape.ArrowCursor)
        button.setStyleSheet(ui_shell._button_style("QPushButton"))
    ok.clicked.connect(dialog.accept)
    cancel.clicked.connect(dialog.reject)
    buttons.addWidget(ok)
    buttons.addWidget(cancel)
    body_layout.addLayout(buttons)

    if hasattr(ui_shell, "_prepare_dialog_masks"):
        ui_shell._prepare_dialog_masks(dialog)
    return selected["value"] if dialog.exec() == dialog.DialogCode.Accepted else None

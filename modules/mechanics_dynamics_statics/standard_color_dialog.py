"""Shared standard Add Custom Color dialog for Engineering Design Tools."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QPushButton, QWidget


_CLOSE_STYLE = (
    "QPushButton{background:#102238;border:1px solid #102238;border-radius:9px;color:#ffffff;"
    "font-family:'Times New Roman';font-size:14px;font-weight:900;font-style:normal;padding:0;outline:0;}"
    "QPushButton:hover{background:#c9342b;border-color:#9d241f;color:#ffffff;}"
    "QPushButton:pressed{background:#8f1f1a;color:#ffffff;}"
    "QPushButton:focus{outline:0;border:1px solid #102238;}"
)


def _polish_shell_close_button(dialog) -> None:
    for button in dialog.findChildren(QPushButton):
        if button.text().strip() == "×":
            button.setStyleSheet(_CLOSE_STYLE)
            button.setCursor(Qt.CursorShape.ArrowCursor)


def get_custom_color(parent: QWidget | None, current: str = "#000000", title: str = "Add Custom Color") -> str | None:
    """Open the project-standard color dialog and return a hex color."""
    try:
        from . import text_line_math_symbols_patch as ui_shell
    except Exception:
        return None

    dialog, body, body_layout = ui_shell._dialog_shell(parent, title, (580, 455))
    _polish_shell_close_button(dialog)
    picker = QColorDialog(QColor(current or "#000000"), body)
    picker.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
    picker.setOption(QColorDialog.ColorDialogOption.NoButtons, True)
    picker.setStyleSheet(
        "QColorDialog{background:#ffffff;border:0;}"
        "QLabel{font-family:'Times New Roman';font-weight:900;font-style:italic;color:#173454;}"
        "QPushButton{font-family:'Times New Roman';font-weight:900;font-style:normal;}"
        "QLineEdit,QSpinBox{font-family:'Times New Roman';font-weight:800;font-style:normal;}"
    )
    body_layout.addWidget(picker, 1)

    actions = QHBoxLayout()
    actions.addStretch(1)
    ok = QPushButton("OK", body)
    cancel = QPushButton("Cancel", body)
    for button in (ok, cancel):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setCursor(Qt.CursorShape.ArrowCursor)
        button.setStyleSheet(ui_shell._button_style("QPushButton"))
    ok.clicked.connect(dialog.accept)
    cancel.clicked.connect(dialog.reject)
    actions.addWidget(ok)
    actions.addWidget(cancel)
    body_layout.addLayout(actions)

    ui_shell._prepare_dialog_masks(dialog)
    if dialog.exec() == dialog.DialogCode.Accepted and picker.currentColor().isValid():
        return picker.currentColor().name()
    return None

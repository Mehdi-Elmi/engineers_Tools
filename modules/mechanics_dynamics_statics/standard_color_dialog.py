"""Shared standard Add Custom Color dialog for Engineering Design Tools."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QPushButton, QWidget


def get_custom_color(parent: QWidget | None, current: str = "#000000", title: str = "Add Custom Color") -> str | None:
    """Open the project-standard color dialog and return a hex color."""
    try:
        from . import text_line_math_symbols_patch as ui_shell
    except Exception:
        return None

    dialog, body, body_layout = ui_shell._dialog_shell(parent, title, (560, 430))
    picker = QColorDialog(QColor(current or "#000000"), body)
    picker.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
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

"""Final full Custom Bullet/Numbering settings dialog with compact swatches."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

PATCH_VERSION = "engineering-text-list-settings-final-2026-07-01-a"


def _font(widget: QWidget, size: int = 10) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(False)
    widget.setFont(font)


def _swatch(color: str, apply_color) -> QPushButton:
    button = QPushButton()
    button.setFixedSize(22, 22)
    button._swatch_color = color

    def paint(value: str) -> None:
        button._swatch_color = value
        button.setStyleSheet(f"QPushButton{{background:{value};border:1px solid #314b68;border-radius:4px;}} QPushButton:hover{{border:2px solid #ff8a35;}}")

    def custom() -> None:
        picked = QColorDialog.getColor(QColor(button._swatch_color), button, "Custom color")
        if picked.isValid():
            paint(picked.name())
            apply_color(picked.name())

    paint(color)
    button.clicked.connect(lambda checked=False: apply_color(button._swatch_color))
    button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    button.customContextMenuRequested.connect(lambda _pos: custom())
    return button


def _open_settings(root, mode: str) -> None:
    from . import text_color_swatch_patch as swatch
    from . import ui_text_runtime_guard_patch as guard

    dialog = QDialog(root)
    title = "Custom Bullet Settings" if mode == "bullet" else "Custom Numbering Settings"
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setMinimumSize(440, 370)
    dialog.setStyleSheet(
        "QDialog{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.55 #eef8ff,stop:1 #fff0c8);border-radius:16px;}"
        "QLabel{color:#173454;font-family:'Times New Roman';font-weight:900;font-style:normal;}"
        "QComboBox,QSpinBox,QDoubleSpinBox{background:#fffefa;border:1px solid #b98920;border-radius:8px;color:#123d6f;font-family:'Times New Roman';font-weight:800;padding:3px 8px;}"
        "QPushButton{background:#ffffff;border:1px solid #7fa6ca;border-radius:8px;color:#123d6f;font-family:'Times New Roman';font-weight:900;padding:5px 12px;}"
        "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"
    )
    root_layout = QVBoxLayout(dialog)
    root_layout.setContentsMargins(14, 14, 14, 14)
    root_layout.setSpacing(9)
    title_label = QLabel(title)
    _font(title_label, 13)
    root_layout.addWidget(title_label)

    form = QFormLayout()
    style = QComboBox()
    style.addItems(["●", "○", "■", "◆", "➤", "✓"] if mode == "bullet" else ["1.", "1)", "I.", "A.", "a.", "i."])
    size = QSpinBox(); size.setRange(4, 96); size.setValue(12); size.setSuffix(" pt")
    indent = QDoubleSpinBox(); indent.setRange(0, 100); indent.setDecimals(2); indent.setValue(7.0); indent.setSuffix(" mm")
    gap = QDoubleSpinBox(); gap.setRange(0, 80); gap.setDecimals(2); gap.setValue(4.0); gap.setSuffix(" mm")
    font_box = QComboBox(); font_box.addItems(list(guard.FONT_CHOICES))
    selected = {"color": "#132238"}
    color_preview = QLabel("■")
    color_preview.setFixedHeight(24)
    _font(color_preview, 14)

    def choose_color(value: str) -> None:
        selected["color"] = value
        color_preview.setStyleSheet(f"color:{value};font-size:18px;font-weight:900;")

    choose_color(selected["color"])
    for widget in (style, size, indent, gap, font_box):
        _font(widget, 10)
    form.addRow("Style", style)
    form.addRow("Size", size)
    form.addRow("Start indent", indent)
    form.addRow("Distance to text", gap)
    form.addRow("Font", font_box)
    form.addRow("Color", color_preview)
    root_layout.addLayout(form)

    color_grid = QGridLayout()
    color_grid.setHorizontalSpacing(5)
    color_grid.setVerticalSpacing(5)
    for index, color in enumerate(swatch.SWATCHES):
        color_grid.addWidget(_swatch(color, choose_color), index // 4, index % 4)
    root_layout.addLayout(color_grid)

    hint = QLabel("Left click applies a color. Right click replaces a preset with a custom color.")
    _font(hint, 9)
    root_layout.addWidget(hint)

    actions = QHBoxLayout()
    actions.addStretch(1)
    apply_btn = QPushButton("Apply")
    cancel_btn = QPushButton("Cancel")
    apply_btn.clicked.connect(dialog.accept)
    cancel_btn.clicked.connect(dialog.reject)
    actions.addWidget(apply_btn)
    actions.addWidget(cancel_btn)
    root_layout.addLayout(actions)

    if dialog.exec() == QDialog.DialogCode.Accepted and root is not None:
        setattr(root, "_last_text_list_settings", {
            "mode": mode,
            "style": style.currentText(),
            "size": size.value(),
            "indent_mm": indent.value(),
            "gap_mm": gap.value(),
            "font": font_box.currentText(),
            "color": selected["color"],
        })


def apply_text_list_settings_final_patch() -> None:
    from . import text_color_swatch_patch as swatch
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_list_settings_final_patch", "") == PATCH_VERSION:
        return
    swatch._open_settings = _open_settings
    edw.EngineeringDesignWorkspace._engineering_text_list_settings_final_patch = PATCH_VERSION

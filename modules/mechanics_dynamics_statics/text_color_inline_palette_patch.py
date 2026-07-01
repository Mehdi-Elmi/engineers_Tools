"""Inline compact color palette for the Text toolbar and list settings dialogs."""

from __future__ import annotations

from PySide6.QtCore import Qt
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
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-text-color-inline-palette-2026-07-01-a"
PALETTE = ["#132238", "#2f7df6", "#36a9e1", "#f18a2a", "#ffbf36", "#c9342b", "#168a50", "#6e4ad6"]


def _font(widget: QWidget, size: int = 10) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(False)
    widget.setFont(font)


def _apply_text_color(root, value: str) -> None:
    from . import ui_text_tool_runtime_fix_patch as runtime
    runtime._apply_text_action(root, "text_color", value)


def _set_swatch_style(button: QPushButton, value: str, *, tight: bool = True) -> None:
    radius = 1 if tight else 3
    button._swatch_color = value
    button.setStyleSheet(
        f"QPushButton{{background:{value};border:1px solid #243d58;border-radius:{radius}px;padding:0;margin:0;}}"
        "QPushButton:hover{border:2px solid #ff8a35;}"
    )


def _make_swatch(value: str, callback, *, size: int = 17) -> QPushButton:
    button = QPushButton()
    button.setFixedSize(size, size)
    _set_swatch_style(button, value)

    def choose_custom() -> None:
        picked = QColorDialog.getColor(QColor(button._swatch_color), button, "Custom color")
        if picked.isValid():
            _set_swatch_style(button, picked.name())
            callback(picked.name())

    button.clicked.connect(lambda checked=False: callback(button._swatch_color))
    button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    button.customContextMenuRequested.connect(lambda _pos: choose_custom())
    return button


def _install_inline_palette(bar: QWidget) -> None:
    window = bar.window()
    old = bar.findChild(QPushButton, "TextColorButton")
    if old is not None:
        old.hide()
        old.setParent(None)
        old.deleteLater()
    if bar.findChild(QWidget, "InlineColorPalette") is not None:
        return
    palette = QWidget(bar)
    palette.setObjectName("InlineColorPalette")
    palette.setFixedSize(84, 39)
    grid = QGridLayout(palette)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(0)
    grid.setVerticalSpacing(0)
    for index, color in enumerate(PALETTE):
        grid.addWidget(_make_swatch(color, lambda value, w=window: _apply_text_color(w, value), size=18), index // 4, index % 4)
    add = QPushButton("+")
    add.setObjectName("AddInlineColor")
    add.setFixedSize(18, 36)
    add.setStyleSheet("QPushButton#AddInlineColor{background:#ffffff;border:1px solid #7fa6ca;border-radius:3px;color:#f18a2a;font-weight:900;padding:0;margin:0;} QPushButton#AddInlineColor:hover{background:#fff4cf;border-color:#ff8a35;}")
    add.clicked.connect(lambda checked=False, w=window: _pick_new_color(w))
    grid.addWidget(add, 0, 4, 2, 1)
    layout = bar.layout()
    if isinstance(layout, QHBoxLayout):
        layout.addWidget(palette)


def _pick_new_color(root) -> None:
    picked = QColorDialog.getColor(QColor("#132238"), root, "Add custom color")
    if picked.isValid():
        _apply_text_color(root, picked.name())


def _style_spin(spin) -> None:
    try:
        from . import svg_cursor_assets_activation_patch as svg
        styler = getattr(svg, "_style_spin", None)
        if callable(styler):
            styler(spin)
            return
    except Exception:
        pass
    spin.setStyleSheet("QSpinBox,QDoubleSpinBox{background:#fffefa;border:1px solid #b98920;border-radius:8px;color:#123d6f;font-family:'Times New Roman';font-weight:800;padding:3px 24px 3px 6px;}")


def _open_settings(root, mode: str) -> None:
    from . import ui_text_runtime_guard_patch as guard

    dialog = QDialog(root)
    title = "Custom Bullet Settings" if mode == "bullet" else "Custom Numbering Settings"
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setMinimumSize(440, 350)
    dialog.setStyleSheet(
        "QDialog{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.55 #eef8ff,stop:1 #fff0c8);border-radius:16px;}"
        "QLabel{color:#173454;font-family:'Times New Roman';font-weight:900;font-style:normal;}"
        "QComboBox{background:#fffefa;border:1px solid #b98920;border-radius:8px;color:#123d6f;font-family:'Times New Roman';font-weight:800;padding:3px 8px;}"
        "QPushButton{background:#ffffff;border:1px solid #7fa6ca;border-radius:8px;color:#123d6f;font-family:'Times New Roman';font-weight:900;padding:5px 12px;}"
        "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"
    )
    root_layout = QVBoxLayout(dialog)
    root_layout.setContentsMargins(14, 14, 14, 14)
    root_layout.setSpacing(8)
    title_label = QLabel(title)
    _font(title_label, 13)
    root_layout.addWidget(title_label)

    form = QFormLayout()
    form.setHorizontalSpacing(8)
    form.setVerticalSpacing(6)
    style = QComboBox()
    style.addItems(["●", "○", "■", "◆", "➤", "✓"] if mode == "bullet" else ["1.", "1)", "I.", "A.", "a.", "i."])
    size = QSpinBox(); size.setRange(4, 96); size.setValue(12); size.setSuffix(" pt"); _style_spin(size)
    indent = QDoubleSpinBox(); indent.setRange(0, 100); indent.setDecimals(2); indent.setValue(7.0); indent.setSuffix(" mm"); _style_spin(indent)
    gap = QDoubleSpinBox(); gap.setRange(0, 80); gap.setDecimals(2); gap.setValue(4.0); gap.setSuffix(" mm"); _style_spin(gap)
    font_box = QComboBox(); font_box.addItems(list(guard.FONT_CHOICES))
    selected = {"color": "#132238"}
    color_preview = QLabel("■")
    _font(color_preview, 14)

    def choose(value: str) -> None:
        selected["color"] = value
        color_preview.setStyleSheet(f"color:{value};font-size:18px;font-weight:900;")

    choose(selected["color"])
    for widget in (style, font_box):
        _font(widget, 10)
    form.addRow("Style", style)
    form.addRow("Size", size)
    form.addRow("Start indent", indent)
    form.addRow("Distance to text", gap)
    form.addRow("Font", font_box)
    form.addRow("Color", color_preview)
    root_layout.addLayout(form)

    color_holder = QWidget(dialog)
    color_grid = QGridLayout(color_holder)
    color_grid.setContentsMargins(0, 0, 0, 0)
    color_grid.setHorizontalSpacing(0)
    color_grid.setVerticalSpacing(0)
    for index, color in enumerate(PALETTE):
        color_grid.addWidget(_make_swatch(color, choose, size=20), index // 4, index % 4)
    add = QPushButton("Add Custom Color")
    add.setFixedHeight(28)
    add.clicked.connect(lambda checked=False: _pick_dialog_color(dialog, choose))
    color_grid.addWidget(add, 0, 4, 2, 1)
    root_layout.addWidget(color_holder)

    actions = QHBoxLayout()
    actions.setSpacing(8)
    actions.addStretch(1)
    apply_btn = QPushButton("OK")
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


def _pick_dialog_color(dialog: QDialog, callback) -> None:
    picked = QColorDialog.getColor(QColor("#132238"), dialog, "Add custom color")
    if picked.isValid():
        callback(picked.name())


def apply_text_color_inline_palette_patch() -> None:
    from . import text_color_swatch_patch as swatch
    from . import text_list_settings_final_patch as list_final
    from . import ui_text_tool_runtime_fix_patch as runtime
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_color_inline_palette_patch", "") == PATCH_VERSION:
        return
    old_attach = runtime._attach_button_menus

    def attach(bar: QWidget) -> None:
        old_attach(bar)
        _install_inline_palette(bar)

    runtime._attach_button_menus = attach
    swatch._open_settings = _open_settings
    list_final._open_settings = _open_settings
    edw.EngineeringDesignWorkspace._engineering_text_color_inline_palette_patch = PATCH_VERSION

"""List settings dialog styling for Text toolbar colors.

The top Text toolbar color palette is now owned by
ui_text_tool_runtime_fix_patch.py. This patch only owns the custom bullet and
numbering settings dialogs.
"""

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

PATCH_VERSION = "engineering-text-color-inline-palette-2026-07-01-c"
PALETTE = ["#132238", "#2f7df6", "#0f2a44", "#f18a2a", "#c9342b", "#168a50", "#6e4ad6", "#536271"]
_SWATCH_SIZE = 18
_SWATCH_GAP = 2
_ADD_WIDTH = 16
_ADD_GAP = 7


def _font(widget: QWidget, size: int = 10) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(False)
    widget.setFont(font)


def _asset_url(name: str) -> str:
    try:
        from . import svg_cursor_assets_activation_patch as svg
        return svg._asset_url(name) if hasattr(svg, "_asset_url") else ""
    except Exception:
        return ""


def _button_style(selector: str = "QPushButton") -> str:
    return (
        f"{selector}{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:.55 #fff6d6,stop:1 #ffc969);"
        "border:1px solid #b98920;border-radius:8px;color:#132238;font-family:'Times New Roman';"
        "font-weight:900;font-style:normal;padding:4px 12px;outline:0;}"
        f"{selector}:hover{{background:#fff4cf;border-color:#ff8a35;}}"
        f"{selector}:pressed{{background:#f18a2a;color:#ffffff;padding-top:5px;}}"
        f"{selector}:focus{{outline:0;border:1px solid #b98920;}}"
    )


def _style_spin(spin) -> None:
    up = _asset_url("spin_up.svg")
    down = _asset_url("spin_down.svg")
    spin.setFixedHeight(30)
    spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#132238;font-family:'Times New Roman';font-size:11px;font-weight:800;font-style:normal;padding:1px 34px 1px 8px;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{width:31px;border:0;subcontrol-origin:border;subcontrol-position:top right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);border-top-right-radius:8px;}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{width:31px;border:0;subcontrol-origin:border;subcontrol-position:bottom right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);border-bottom-right-radius:8px;}"
        f"QSpinBox::up-arrow,QDoubleSpinBox::up-arrow{{image:url({up});width:20px;height:12px;}}"
        f"QSpinBox::down-arrow,QDoubleSpinBox::down-arrow{{image:url({down});width:20px;height:12px;}}"
    )


def _style_combo(combo: QComboBox) -> None:
    arrow = _asset_url("combo_down.svg")
    combo.setFixedHeight(30)
    combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    combo.setStyleSheet(
        "QComboBox{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#132238;font-family:'Times New Roman';font-size:11px;font-weight:800;font-style:normal;padding:1px 35px 1px 9px;}"
        "QComboBox::drop-down{width:32px;border:0;subcontrol-origin:border;subcontrol-position:center right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);border-top-right-radius:8px;border-bottom-right-radius:8px;}"
        f"QComboBox::down-arrow{{image:url({arrow});width:20px;height:12px;}}"
    )
    _font(combo, 10)


def _set_swatch_style(button: QPushButton, value: str) -> None:
    button._swatch_color = value
    button.setStyleSheet(
        f"QPushButton{{background:{value};border:1px solid #243d58;border-radius:2px;padding:0;margin:0;outline:0;}}"
        "QPushButton:hover{border:2px solid #ff8a35;}"
        "QPushButton:focus{outline:0;border:1px solid #243d58;}"
    )


def _make_swatch(value: str, callback, *, size: int = _SWATCH_SIZE) -> QPushButton:
    button = QPushButton()
    button.setFixedSize(size, size)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    _set_swatch_style(button, value)

    def choose_custom() -> None:
        picked = QColorDialog.getColor(QColor(button._swatch_color), button, "Custom Color")
        if picked.isValid():
            _set_swatch_style(button, picked.name())
            callback(picked.name())

    button.clicked.connect(lambda checked=False: callback(button._swatch_color))
    button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    button.customContextMenuRequested.connect(lambda _pos: choose_custom())
    return button


def _build_header(dialog: QDialog, title: str) -> QWidget:
    header = QWidget(dialog)
    header.setObjectName("DialogHeader")
    header.setFixedHeight(42)
    row = QHBoxLayout(header)
    row.setContentsMargins(12, 4, 10, 4)
    row.setSpacing(8)
    logo = QLabel("A", header)
    logo.setFixedSize(28, 28)
    logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    logo.setStyleSheet("QLabel{background:#ffffff;border:1px solid #7fa6ca;border-radius:5px;color:#123d6f;font-family:'Times New Roman';font-weight:900;font-size:16px;}")
    title_label = QLabel(title, header)
    _font(title_label, 12)
    title_label.setStyleSheet("QLabel{color:#ffffff;font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:italic;}")
    row.addWidget(logo)
    row.addWidget(title_label, 1)
    return header


def _rebuild_color_grid(holder: QWidget, colors: list[str], choose) -> None:
    layout = holder.layout()
    if not isinstance(layout, QHBoxLayout):
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
    columns = max(4, (len(colors) + 1) // 2)
    palette_width = columns * _SWATCH_SIZE + max(0, columns - 1) * _SWATCH_GAP
    palette_height = 2 * _SWATCH_SIZE + _SWATCH_GAP
    palette = QWidget(holder)
    palette.setFixedSize(palette_width, palette_height)
    grid = QGridLayout(palette)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(_SWATCH_GAP)
    grid.setVerticalSpacing(_SWATCH_GAP)
    for index, color in enumerate(colors):
        grid.addWidget(_make_swatch(color, choose), index % 2, index // 2)
    add = QPushButton("+", holder)
    add.setFixedSize(_ADD_WIDTH, palette_height)
    add.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    add.setStyleSheet(_button_style("QPushButton"))

    def add_color() -> None:
        picked = QColorDialog.getColor(QColor("#132238"), holder, "Add Custom Color")
        if picked.isValid():
            value = picked.name()
            if value not in colors:
                colors.append(value)
            choose(value)
            _rebuild_color_grid(holder, colors, choose)

    add.clicked.connect(add_color)
    layout.setSpacing(_ADD_GAP)
    layout.addWidget(palette)
    layout.addWidget(add)


def _open_settings(root, mode: str) -> None:
    from . import ui_text_runtime_guard_patch as guard

    dialog = QDialog(root)
    title = "Custom Bullet Settings" if mode == "bullet" else "Custom Numbering Settings"
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
    dialog.setMinimumSize(470, 360)
    dialog.setStyleSheet(
        "QDialog{background:#eaf4ff;border-radius:16px;}"
        "QLabel{color:#173454;font-family:'Times New Roman';font-weight:900;font-style:normal;}"
        "QWidget#DialogHeader{background:#102238;border-top-left-radius:16px;border-top-right-radius:16px;}"
    )
    root_layout = QVBoxLayout(dialog)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)
    root_layout.addWidget(_build_header(dialog, title))

    body = QWidget(dialog)
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(16, 14, 16, 14)
    body_layout.setSpacing(9)
    root_layout.addWidget(body, 1)

    form = QFormLayout()
    form.setHorizontalSpacing(10)
    form.setVerticalSpacing(7)
    style = QComboBox()
    style.addItems(["●", "○", "■", "◆", "➤", "✓"] if mode == "bullet" else ["1.", "1)", "I.", "A.", "a.", "i."])
    _style_combo(style)
    size = QSpinBox(); size.setRange(4, 96); size.setValue(12); size.setSuffix(" pt"); _style_spin(size)
    indent = QDoubleSpinBox(); indent.setRange(0, 100); indent.setDecimals(2); indent.setValue(7.0); indent.setSuffix(" mm"); _style_spin(indent)
    gap = QDoubleSpinBox(); gap.setRange(0, 80); gap.setDecimals(2); gap.setValue(4.0); gap.setSuffix(" mm"); _style_spin(gap)
    font_box = QComboBox(); font_box.addItems(list(guard.FONT_CHOICES)); _style_combo(font_box)
    selected = {"color": "#132238"}
    color_preview = QLabel("■")
    _font(color_preview, 14)

    def choose(value: str) -> None:
        selected["color"] = value
        color_preview.setStyleSheet(f"color:{value};font-size:18px;font-weight:900;")

    choose(selected["color"])
    form.addRow("Style", style)
    form.addRow("Size", size)
    form.addRow("Start indent", indent)
    form.addRow("Distance to text", gap)
    form.addRow("Font", font_box)
    form.addRow("Color", color_preview)
    body_layout.addLayout(form)

    color_holder = QWidget(dialog)
    color_layout = QHBoxLayout(color_holder)
    color_layout.setContentsMargins(0, 0, 0, 0)
    color_layout.setSpacing(_ADD_GAP)
    custom_colors = list(PALETTE)
    _rebuild_color_grid(color_holder, custom_colors, choose)
    body_layout.addWidget(color_holder)

    actions = QHBoxLayout()
    actions.setSpacing(8)
    actions.addStretch(1)
    apply_btn = QPushButton("OK")
    cancel_btn = QPushButton("Cancel")
    for button in (apply_btn, cancel_btn):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(_button_style("QPushButton"))
    apply_btn.clicked.connect(dialog.accept)
    cancel_btn.clicked.connect(dialog.reject)
    actions.addWidget(apply_btn)
    actions.addWidget(cancel_btn)
    body_layout.addLayout(actions)

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


def apply_text_color_inline_palette_patch() -> None:
    from . import text_color_swatch_patch as swatch
    from . import text_list_settings_final_patch as list_final
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_color_inline_palette_patch", "") == PATCH_VERSION:
        return

    swatch._open_settings = _open_settings
    list_final._open_settings = _open_settings
    edw.EngineeringDesignWorkspace._engineering_text_color_inline_palette_patch = PATCH_VERSION

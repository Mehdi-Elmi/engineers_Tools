"""Shared project-standard Add Custom Color dialog."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRect, Signal, Qt
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QImage, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

_BASIC_COLORS = [
    ("#000000", "Black"), ("#800000", "Maroon"), ("#008000", "Green"), ("#cc6600", "Orange"),
    ("#00b000", "Bright Green"), ("#c0c000", "Olive"), ("#00ff00", "Lime"), ("#80ff00", "Spring Green"),
    ("#000080", "Navy"), ("#800080", "Purple"), ("#008080", "Teal"), ("#c070a0", "Rose"),
    ("#008c8c", "Dark Cyan"), ("#808000", "Olive"), ("#00ffff", "Cyan"), ("#a0ffa0", "Mint"),
    ("#0000ff", "Blue"), ("#ff00ff", "Magenta"), ("#0080ff", "Sky Blue"), ("#c080ff", "Lavender"),
    ("#00ccff", "Aqua"), ("#8080c0", "Blue Gray"), ("#80ffff", "Light Cyan"), ("#c0ffff", "Pale Cyan"),
    ("#800000", "Dark Red"), ("#ff0000", "Red"), ("#808000", "Dark Yellow"), ("#ff6600", "Amber"),
    ("#40a000", "Leaf"), ("#ffb020", "Gold"), ("#60ff00", "Neon Green"), ("#ffff00", "Yellow"),
    ("#8000ff", "Violet"), ("#ff00c0", "Hot Pink"), ("#8080a0", "Slate"), ("#ff6080", "Coral"),
    ("#60a080", "Sea Green"), ("#ffb090", "Peach"), ("#60ff90", "Fresh Green"), ("#ffff80", "Pale Yellow"),
    ("#2020ff", "Blue"), ("#ff40ff", "Magenta"), ("#8080ff", "Soft Blue"), ("#ff80ff", "Soft Pink"),
    ("#80ffff", "Light Cyan"), ("#c0ffff", "Pale Cyan"), ("#e6ffff", "Ice"), ("#ffffff", "White"),
]
_ARROW_CACHE: dict[str, str] = {}
_CLOSE_STYLE = (
    "QPushButton{background:#102238;border:1px solid #102238;border-radius:9px;color:#ffffff;"
    "font-family:'Times New Roman';font-size:14px;font-weight:900;font-style:normal;padding:0;outline:0;}"
    "QPushButton:hover{background:#c9342b;border-color:#9d241f;color:#ffffff;}"
    "QPushButton:pressed{background:#8f1f1a;color:#ffffff;}"
    "QPushButton:focus{outline:0;border:1px solid #102238;}"
)
_TEXT_STYLE = "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:italic;color:#173454;"
_BUTTON_STYLE = (
    "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:.55 #fff6d6,stop:1 #ffc969);"
    "border:1px solid #b98920;border-radius:8px;color:#132238;font-family:'Times New Roman';font-size:12px;font-weight:900;"
    "font-style:normal;padding:4px 12px;outline:0;}"
    "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"
    "QPushButton:pressed{background:#f18a2a;color:#ffffff;padding-top:5px;}"
    "QPushButton:focus{outline:0;border:1px solid #b98920;}"
)
_SWATCH_STYLE = (
    "QPushButton{background:%s;border:1px solid #566d86;border-radius:2px;min-width:18px;max-width:18px;"
    "min-height:15px;max-height:15px;padding:0;outline:0;}"
    "QPushButton:hover{border:2px solid #ff8a35;}"
    "QPushButton:pressed{border:2px solid #173454;}"
)
_GROUP_STYLE = (
    "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.58 #f5fbff,stop:1 #e8f3ff);"
    "border:1px solid #9fb1c7;border-radius:10px;}"
)
_BODY_STYLE = (
    "QWidget#DialogBody{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #f8fcff,stop:.55 #edf7ff,stop:1 #e7f1fb);"
    "border-bottom-left-radius:16px;border-bottom-right-radius:16px;} QWidget{background:transparent;}"
)


def _arrow_path(direction: str) -> str:
    cached = _ARROW_CACHE.get(direction)
    if cached:
        return cached
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(QColor("#173454"))
    painter.setPen(Qt.PenStyle.NoPen)
    points = [QPointF(9, 4), QPointF(14, 12), QPointF(4, 12)] if direction == "up" else [QPointF(4, 6), QPointF(14, 6), QPointF(9, 14)]
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    path = Path(tempfile.gettempdir()) / f"engineering_custom_color_arrow_{direction}_20260702b.png"
    pixmap.save(path.as_posix(), "PNG")
    _ARROW_CACHE[direction] = path.as_posix()
    return path.as_posix()


def _spin_style() -> str:
    return (
        "QSpinBox{background:#fffefa;border:1px solid #b88718;border-radius:7px;color:#173454;"
        "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:1px 24px 1px 6px;outline:0;}"
        "QSpinBox::up-button{width:21px;border-left:1px solid #b88718;border-top-right-radius:6px;"
        "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        "QSpinBox::down-button{width:21px;border-left:1px solid #b88718;border-bottom-right-radius:6px;"
        "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        f"QSpinBox::up-arrow{{image:url({_arrow_path('up')});width:14px;height:14px;}}"
        f"QSpinBox::down-arrow{{image:url({_arrow_path('down')});width:14px;height:14px;}}"
    )


class _ColorPlane(QWidget):
    colorChanged = Signal(QColor)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(188, 168)
        self._hue = 216
        self._sat = 206
        self._val = 246
        self._image: QImage | None = None
        self._image_val = -1
        self.setCursor(Qt.CursorShape.CrossCursor)

    def set_hsv(self, hue: int, sat: int, val: int) -> None:
        self._hue = max(0, min(359, int(hue)))
        self._sat = max(0, min(255, int(sat)))
        self._val = max(0, min(255, int(val)))
        if self._image_val != self._val:
            self._image = None
        self.update()

    def _ensure_image(self) -> None:
        if self._image is not None and self._image_val == self._val:
            return
        self._image = QImage(self.width(), self.height(), QImage.Format.Format_RGB32)
        for x in range(self.width()):
            hue = int((x / max(1, self.width() - 1)) * 359)
            for y in range(self.height()):
                sat = int((1.0 - y / max(1, self.height() - 1)) * 255)
                self._image.setPixelColor(x, y, QColor.fromHsv(hue, sat, self._val))
        self._image_val = self._val

    def paintEvent(self, event) -> None:  # noqa: N802
        self._ensure_image()
        painter = QPainter(self)
        if self._image is not None:
            painter.drawImage(0, 0, self._image)
        x = int(self._hue / 359 * (self.width() - 1))
        y = int((1.0 - self._sat / 255) * (self.height() - 1))
        painter.setPen(QPen(QColor("#102238"), 1))
        painter.drawLine(x - 9, y, x + 9, y)
        painter.drawLine(x, y - 9, x, y + 9)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawEllipse(QPoint(x, y), 4, 4)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._apply_point(event.position().toPoint())

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        self._apply_point(event.position().toPoint())

    def _apply_point(self, point: QPoint) -> None:
        x = max(0, min(self.width() - 1, point.x()))
        y = max(0, min(self.height() - 1, point.y()))
        self._hue = int(x / max(1, self.width() - 1) * 359)
        self._sat = int((1.0 - y / max(1, self.height() - 1)) * 255)
        self.update()
        self.colorChanged.emit(QColor.fromHsv(self._hue, self._sat, self._val))


class _ValueSlider(QWidget):
    valueChanged = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(16, 168)
        self._value = 246
        self.setCursor(Qt.CursorShape.SizeVerCursor)

    def set_value(self, value: int) -> None:
        self._value = max(0, min(255, int(value)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        for y in range(self.height()):
            v = int((1.0 - y / max(1, self.height() - 1)) * 255)
            painter.setPen(QColor(v, v, v))
            painter.drawLine(0, y, self.width() - 5, y)
        painter.setPen(QPen(QColor("#173454"), 1))
        painter.drawRect(QRect(0, 0, self.width() - 5, self.height() - 1))
        y = int((1.0 - self._value / 255) * (self.height() - 1))
        painter.setPen(QPen(QColor("#1f6fba"), 2))
        painter.drawLine(self.width() - 4, y, self.width() - 1, y)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._apply_y(event.position().toPoint().y())

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        self._apply_y(event.position().toPoint().y())

    def _apply_y(self, y: int) -> None:
        y = max(0, min(self.height() - 1, y))
        self._value = int((1.0 - y / max(1, self.height() - 1)) * 255)
        self.update()
        self.valueChanged.emit(self._value)


def _polish_shell_close_button(dialog) -> bool:
    found = False
    for button in dialog.findChildren(QPushButton):
        if button.text().strip() == "×":
            button.setStyleSheet(_CLOSE_STYLE)
            button.setCursor(Qt.CursorShape.ArrowCursor)
            button.setFixedSize(28, 28)
            button.show()
            button.raise_()
            found = True
    return found


def _ensure_close_button(dialog, body: QWidget, body_layout: QVBoxLayout) -> None:
    if _polish_shell_close_button(dialog):
        return
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.addStretch(1)
    close = QPushButton("×", body)
    close.setFixedSize(28, 28)
    close.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    close.setStyleSheet(_CLOSE_STYLE)
    close.clicked.connect(dialog.reject)
    row.addWidget(close)
    body_layout.insertLayout(0, row)


def _normal_hex(value: str | None) -> str:
    color = QColor(value or "#000000")
    return color.name(QColor.NameFormat.HexRgb) if color.isValid() else "#000000"


def _style_label(label: QLabel) -> None:
    label.setStyleSheet(f"QLabel{{{_TEXT_STYLE}}}")


def _make_spin(value: int, parent: QWidget, maximum: int = 255) -> QSpinBox:
    spin = QSpinBox(parent)
    spin.setRange(0, maximum)
    spin.setValue(max(0, min(maximum, int(value))))
    spin.setFixedWidth(82)
    spin.setKeyboardTracking(True)
    spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    try:
        spin.lineEdit().setReadOnly(False)
        spin.lineEdit().setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    except Exception:
        pass
    spin.setStyleSheet(_spin_style())
    return spin


def _group(parent: QWidget, title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(parent)
    frame.setStyleSheet(_GROUP_STYLE)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(8, 7, 8, 8)
    layout.setSpacing(5)
    if title:
        label = QLabel(title, frame)
        _style_label(label)
        layout.addWidget(label)
    return frame, layout


def get_custom_color(parent: QWidget | None, current: str = "#000000", title: str = "Add Custom Color") -> str | None:
    """Open the reusable project-standard custom color picker and return a hex color."""
    try:
        from . import text_line_math_symbols_patch as ui_shell
    except Exception:
        return None

    selected = {"color": QColor(_normal_hex(current))}
    custom_colors = ["#ffffff"] * 16
    dialog, body, body_layout = ui_shell._dialog_shell(parent, title or "Add Custom Color", (620, 470))
    _ensure_close_button(dialog, body, body_layout)
    body.setStyleSheet(_BODY_STYLE)
    body_layout.setContentsMargins(10, 10, 10, 10)
    body_layout.setSpacing(7)

    main = QHBoxLayout()
    main.setContentsMargins(0, 0, 0, 0)
    main.setSpacing(10)
    body_layout.addLayout(main)

    left_column = QVBoxLayout()
    left_column.setContentsMargins(0, 0, 0, 0)
    left_column.setSpacing(7)
    main.addLayout(left_column)

    colors_group, colors_layout = _group(body, "Basic colors")
    colors_group.setFixedWidth(252)
    left_column.addWidget(colors_group)
    basic_grid = QGridLayout()
    basic_grid.setHorizontalSpacing(4)
    basic_grid.setVerticalSpacing(4)
    colors_layout.addLayout(basic_grid)

    for index, (hex_value, name) in enumerate(_BASIC_COLORS):
        button = QPushButton("", colors_group)
        button.setToolTip(name)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(_SWATCH_STYLE % hex_value)
        button.clicked.connect(lambda checked=False, value=hex_value: set_color(QColor(value)))
        basic_grid.addWidget(button, index // 8, index % 8)

    pick_screen = QPushButton("Pick Screen Color", colors_group)
    pick_screen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    pick_screen.setStyleSheet(_BUTTON_STYLE)
    colors_layout.addWidget(pick_screen)

    custom_label = QLabel("Custom colors", colors_group)
    _style_label(custom_label)
    colors_layout.addWidget(custom_label)
    custom_grid = QGridLayout()
    custom_grid.setHorizontalSpacing(4)
    custom_grid.setVerticalSpacing(4)
    colors_layout.addLayout(custom_grid)
    custom_buttons: list[QPushButton] = []
    for index in range(16):
        button = QPushButton("", colors_group)
        button.setToolTip("Custom Color")
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(_SWATCH_STYLE % custom_colors[index])
        button.clicked.connect(lambda checked=False, i=index: set_color(QColor(custom_colors[i])))
        custom_buttons.append(button)
        custom_grid.addWidget(button, index // 8, index % 8)
    add_custom = QPushButton("Add to Custom Colors", colors_group)
    add_custom.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    add_custom.setStyleSheet(_BUTTON_STYLE)
    colors_layout.addWidget(add_custom)

    values_group, values_layout = _group(body, "Color values")
    values_group.setFixedWidth(252)
    left_column.addWidget(values_group)
    value_grid = QGridLayout()
    value_grid.setContentsMargins(0, 0, 0, 0)
    value_grid.setHorizontalSpacing(6)
    value_grid.setVerticalSpacing(4)
    values_layout.addLayout(value_grid)

    hue_spin = _make_spin(216, values_group, 359)
    sat_spin = _make_spin(206, values_group)
    val_spin = _make_spin(246, values_group)
    red_spin = _make_spin(47, values_group)
    green_spin = _make_spin(125, values_group)
    blue_spin = _make_spin(246, values_group)

    def add_value_cell(row: int, column: int, label_text: str, spin: QSpinBox) -> None:
        holder = QWidget(values_group)
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        label = QLabel(label_text, holder)
        label.setFixedWidth(34)
        _style_label(label)
        layout.addWidget(label)
        layout.addWidget(spin)
        value_grid.addWidget(holder, row, column)

    add_value_cell(0, 0, "Hue:", hue_spin)
    add_value_cell(1, 0, "Sat:", sat_spin)
    add_value_cell(2, 0, "Val:", val_spin)
    add_value_cell(0, 1, "Red:", red_spin)
    add_value_cell(1, 1, "Green:", green_spin)
    add_value_cell(2, 1, "Blue:", blue_spin)

    html_row = QHBoxLayout()
    html_row.setSpacing(5)
    html_label = QLabel("HTML:", values_group)
    html_label.setFixedWidth(38)
    _style_label(html_label)
    html_edit = QLineEdit(values_group)
    html_edit.setFixedWidth(176)
    html_edit.setStyleSheet("QLineEdit{background:#ffffff;border:1px solid #9fb1c7;border-radius:6px;color:#173454;font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:2px 5px;}")
    html_row.addWidget(html_label)
    html_row.addWidget(html_edit)
    values_layout.addLayout(html_row)
    left_column.addStretch(1)

    spectrum_group, spectrum_layout = _group(body, None)
    spectrum_group.setFixedWidth(238)
    main.addWidget(spectrum_group)
    plane_row = QHBoxLayout()
    plane_row.setContentsMargins(0, 0, 0, 0)
    plane_row.setSpacing(8)
    plane_row.addStretch(1)
    plane = _ColorPlane(spectrum_group)
    value_slider = _ValueSlider(spectrum_group)
    plane_row.addWidget(plane)
    plane_row.addWidget(value_slider)
    plane_row.addStretch(1)
    spectrum_layout.addLayout(plane_row)

    preview_row = QHBoxLayout()
    preview_row.setContentsMargins(0, 0, 0, 0)
    preview_row.setSpacing(8)
    preview_row.addStretch(1)
    preview = QFrame(spectrum_group)
    preview.setFixedSize(58, 42)
    preview_row.addWidget(preview)
    preview_row.addStretch(1)
    spectrum_layout.addLayout(preview_row)
    spectrum_layout.addStretch(1)

    actions = QHBoxLayout()
    actions.addStretch(1)
    ok = QPushButton("OK", body)
    cancel = QPushButton("Cancel", body)
    for action_button in (ok, cancel):
        action_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        action_button.setStyleSheet(_BUTTON_STYLE)
    ok.clicked.connect(dialog.accept)
    cancel.clicked.connect(dialog.reject)
    actions.addWidget(ok)
    actions.addWidget(cancel)
    spectrum_layout.addLayout(actions)

    def set_color(color: QColor) -> None:
        if not color.isValid():
            return
        selected["color"] = QColor(color)
        hue, sat, val, _alpha = selected["color"].getHsv()
        if hue < 0:
            hue = 0
        plane.set_hsv(hue, sat, val)
        value_slider.set_value(val)
        for spin, spin_value in ((hue_spin, hue), (sat_spin, sat), (val_spin, val), (red_spin, color.red()), (green_spin, color.green()), (blue_spin, color.blue())):
            spin.blockSignals(True)
            spin.setValue(spin_value)
            spin.blockSignals(False)
        html_edit.setText(selected["color"].name(QColor.NameFormat.HexRgb))
        preview.setStyleSheet("QFrame{background:%s;border:1px solid #173454;border-radius:7px;}" % selected["color"].name())

    def from_hsv() -> None:
        set_color(QColor.fromHsv(hue_spin.value(), sat_spin.value(), val_spin.value()))

    def from_rgb() -> None:
        set_color(QColor(red_spin.value(), green_spin.value(), blue_spin.value()))

    hue_spin.valueChanged.connect(from_hsv)
    sat_spin.valueChanged.connect(from_hsv)
    val_spin.valueChanged.connect(from_hsv)
    red_spin.valueChanged.connect(from_rgb)
    green_spin.valueChanged.connect(from_rgb)
    blue_spin.valueChanged.connect(from_rgb)
    plane.colorChanged.connect(set_color)
    value_slider.valueChanged.connect(lambda value: set_color(QColor.fromHsv(hue_spin.value(), sat_spin.value(), value)))

    def choose_screen_color() -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        pos = QCursor.pos()
        image = screen.grabWindow(0, pos.x(), pos.y(), 1, 1).toImage()
        if not image.isNull():
            set_color(image.pixelColor(0, 0))

    pick_screen.clicked.connect(choose_screen_color)

    def add_to_custom() -> None:
        color = selected["color"].name(QColor.NameFormat.HexRgb)
        try:
            index = custom_colors.index("#ffffff")
        except ValueError:
            index = 0
        custom_colors[index] = color
        custom_buttons[index].setStyleSheet(_SWATCH_STYLE % color)
        custom_buttons[index].setToolTip(color)

    add_custom.clicked.connect(add_to_custom)
    set_color(selected["color"])

    if hasattr(ui_shell, "_prepare_dialog_masks"):
        ui_shell._prepare_dialog_masks(dialog)
    _polish_shell_close_button(dialog)
    return selected["color"].name(QColor.NameFormat.HexRgb) if dialog.exec() == dialog.DialogCode.Accepted else None

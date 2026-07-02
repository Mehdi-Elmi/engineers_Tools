"""Shared project-standard Add Custom Color dialog."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Signal, Qt
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QImage, QPainter, QPen
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
_SPIN_STYLE = (
    "QSpinBox{background:#fffefa;border:1px solid #b88718;border-radius:6px;color:#173454;"
    "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:1px 20px 1px 6px;outline:0;}"
    "QSpinBox::up-button{width:18px;border-left:1px solid #b88718;border-top-right-radius:5px;"
    "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
    "QSpinBox::down-button{width:18px;border-left:1px solid #b88718;border-bottom-right-radius:5px;"
    "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
)
_GROUP_STYLE = "QFrame{background:#f7fbff;border:1px solid #9fb1c7;border-radius:10px;}"


class _ColorPlane(QWidget):
    colorChanged = Signal(QColor)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(220, 200)
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
        painter.drawLine(x - 10, y, x + 10, y)
        painter.drawLine(x, y - 10, x, y + 10)
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
        self.setFixedSize(16, 200)
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


def _polish_shell_close_button(dialog) -> None:
    for button in dialog.findChildren(QPushButton):
        if button.text().strip() == "×":
            button.setStyleSheet(_CLOSE_STYLE)
            button.setCursor(Qt.CursorShape.ArrowCursor)


def _normal_hex(value: str | None) -> str:
    color = QColor(value or "#000000")
    return color.name(QColor.NameFormat.HexRgb) if color.isValid() else "#000000"


def _style_label(label: QLabel) -> None:
    label.setStyleSheet(f"QLabel{{{_TEXT_STYLE}}}")


def _make_spin(value: int, parent: QWidget, maximum: int = 255) -> QSpinBox:
    spin = QSpinBox(parent)
    spin.setRange(0, maximum)
    spin.setValue(max(0, min(maximum, int(value))))
    spin.setFixedWidth(74)
    spin.setKeyboardTracking(True)
    spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    try:
        spin.lineEdit().setReadOnly(False)
        spin.lineEdit().setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    except Exception:
        pass
    spin.setStyleSheet(_SPIN_STYLE)
    return spin


def _group(parent: QWidget, title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(parent)
    frame.setStyleSheet(_GROUP_STYLE)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(8, 7, 8, 8)
    layout.setSpacing(5)
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
    dialog, body, body_layout = ui_shell._dialog_shell(parent, title or "Add Custom Color", (660, 450))
    _polish_shell_close_button(dialog)
    body.setStyleSheet("QWidget#DialogBody{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #eef7ff,stop:1 #fff5dc);border-bottom-left-radius:16px;border-bottom-right-radius:16px;} QWidget{background:transparent;}")
    body_layout.setContentsMargins(10, 10, 10, 10)
    body_layout.setSpacing(7)

    main = QHBoxLayout()
    main.setContentsMargins(0, 0, 0, 0)
    main.setSpacing(10)
    body_layout.addLayout(main)

    left_group, left = _group(body, "Basic colors")
    main.addWidget(left_group)
    basic_grid = QGridLayout()
    basic_grid.setHorizontalSpacing(4)
    basic_grid.setVerticalSpacing(4)
    left.addLayout(basic_grid)

    center_group, center = _group(body, "Color spectrum")
    main.addWidget(center_group)
    plane_row = QHBoxLayout()
    plane_row.setContentsMargins(0, 0, 0, 0)
    plane_row.setSpacing(8)
    plane = _ColorPlane(center_group)
    value_slider = _ValueSlider(center_group)
    plane_row.addWidget(plane)
    plane_row.addWidget(value_slider)
    center.addLayout(plane_row)
    preview = QFrame(center_group)
    preview.setFixedSize(58, 52)
    center.addWidget(preview, alignment=Qt.AlignmentFlag.AlignLeft)

    right_group, right = _group(body, "Color values")
    main.addWidget(right_group)

    hue_spin = _make_spin(216, right_group, 359)
    sat_spin = _make_spin(206, right_group)
    val_spin = _make_spin(246, right_group)
    red_spin = _make_spin(47, right_group)
    green_spin = _make_spin(125, right_group)
    blue_spin = _make_spin(246, right_group)

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

    for index, (hex_value, name) in enumerate(_BASIC_COLORS):
        button = QPushButton("", left_group)
        button.setToolTip(name)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(_SWATCH_STYLE % hex_value)
        button.clicked.connect(lambda checked=False, value=hex_value: set_color(QColor(value)))
        basic_grid.addWidget(button, index // 8, index % 8)

    pick_screen = QPushButton("Pick Screen Color", left_group)
    pick_screen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    pick_screen.setStyleSheet(_BUTTON_STYLE)
    left.addWidget(pick_screen)
    custom_label = QLabel("Custom colors", left_group)
    _style_label(custom_label)
    left.addWidget(custom_label)
    custom_grid = QGridLayout()
    custom_grid.setHorizontalSpacing(4)
    custom_grid.setVerticalSpacing(4)
    left.addLayout(custom_grid)
    custom_buttons: list[QPushButton] = []
    for index in range(16):
        button = QPushButton("", left_group)
        button.setToolTip("Custom Color")
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(_SWATCH_STYLE % custom_colors[index])
        button.clicked.connect(lambda checked=False, i=index: set_color(QColor(custom_colors[i])))
        custom_buttons.append(button)
        custom_grid.addWidget(button, index // 8, index % 8)
    add_custom = QPushButton("Add to Custom Colors", left_group)
    add_custom.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    add_custom.setStyleSheet(_BUTTON_STYLE)
    left.addWidget(add_custom)
    left.addStretch(1)

    def add_spin_row(label_text: str, spin: QSpinBox) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        label = QLabel(label_text, right_group)
        _style_label(label)
        row.addWidget(label)
        row.addWidget(spin)
        right.addLayout(row)

    add_spin_row("Hue:", hue_spin)
    add_spin_row("Sat:", sat_spin)
    add_spin_row("Val:", val_spin)
    add_spin_row("Red:", red_spin)
    add_spin_row("Green:", green_spin)
    add_spin_row("Blue:", blue_spin)
    html_row = QHBoxLayout()
    html_row.setSpacing(6)
    html_label = QLabel("HTML:", right_group)
    _style_label(html_label)
    html_edit = QLineEdit(right_group)
    html_edit.setFixedWidth(150)
    html_edit.setStyleSheet("QLineEdit{background:#ffffff;border:1px solid #9fb1c7;border-radius:6px;color:#173454;font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:2px 5px;}")
    html_row.addWidget(html_label)
    html_row.addWidget(html_edit)
    right.addLayout(html_row)
    right.addStretch(1)

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

    actions = QHBoxLayout()
    actions.addStretch(1)
    ok = QPushButton("OK", body)
    cancel = QPushButton("Cancel", body)
    for button in (ok, cancel):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(_BUTTON_STYLE)
    ok.clicked.connect(dialog.accept)
    cancel.clicked.connect(dialog.reject)
    actions.addWidget(ok)
    actions.addWidget(cancel)
    body_layout.addLayout(actions)

    if hasattr(ui_shell, "_prepare_dialog_masks"):
        ui_shell._prepare_dialog_masks(dialog)
    return selected["color"].name(QColor.NameFormat.HexRgb) if dialog.exec() == dialog.DialogCode.Accepted else None

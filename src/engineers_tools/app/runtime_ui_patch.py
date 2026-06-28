"""Runtime UI refinements for the shared engineering workspace."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QShortcut
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


def _triangle_arrow_head(painter: QPainter, tip: QPointF, tail: QPointF, color: QColor, size: float = 7.0) -> None:
    direction = tip - tail
    length = max(0.01, (direction.x() ** 2 + direction.y() ** 2) ** 0.5)
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    base = QPointF(tip.x() - unit.x() * size, tip.y() - unit.y() * size)
    left = QPointF(base.x() + normal.x() * size * 0.58, base.y() + normal.y() * size * 0.58)
    right = QPointF(base.x() - normal.x() * size * 0.58, base.y() - normal.y() * size * 0.58)
    painter.setBrush(color)
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(QPolygonF([tip, left, right]))


def _solid_arrow_head(painter: QPainter, tip: QPointF, back: QPointF, size: float = 6.0) -> None:
    _triangle_arrow_head(painter, tip, back, painter.pen().color(), size)


def _radio_icon(checked: bool) -> QIcon:
    pixmap = QPixmap(22, 22)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(QPen(QColor("#18314f"), 2.0))
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(QPointF(11, 11), 8.0, 8.0)
    if checked:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2f7df6"))
        painter.drawEllipse(QPointF(11, 11), 4.6, 4.6)
    painter.end()
    return QIcon(pixmap)


def _style_numeric_spin(spin: QDoubleSpinBox) -> None:
    spin.setStyleSheet(
        """
        QDoubleSpinBox#FileNameInput {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:8px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:4px 22px 4px 7px;
        }
        QDoubleSpinBox#FileNameInput::up-button, QDoubleSpinBox#FileNameInput::down-button {
            width:18px; border:0; background:#fff9de; subcontrol-origin:border;
        }
        QDoubleSpinBox#FileNameInput::up-button { subcontrol-position:top right; border-top-right-radius:7px; }
        QDoubleSpinBox#FileNameInput::down-button { subcontrol-position:bottom right; border-bottom-right-radius:7px; }
        QDoubleSpinBox#FileNameInput::up-arrow {
            width:0; height:0; border-left:5px solid transparent; border-right:5px solid transparent; border-bottom:6px solid #132238;
        }
        QDoubleSpinBox#FileNameInput::down-arrow {
            width:0; height:0; border-left:5px solid transparent; border-right:5px solid transparent; border-top:6px solid #132238;
        }
        """
    )


def _style_combo_arrow(combo: QComboBox) -> None:
    combo.setStyleSheet(
        """
        QComboBox#FileTypeCombo {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:8px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:5px 28px 5px 8px;
        }
        QComboBox#FileTypeCombo::drop-down {
            width:24px; border:0; background:#fff9de; border-top-right-radius:7px; border-bottom-right-radius:7px;
        }
        QComboBox#FileTypeCombo::down-arrow {
            width:0; height:0; border-left:6px solid transparent; border-right:6px solid transparent; border-top:7px solid #132238;
        }
        QComboBox#FileTypeCombo QAbstractItemView {
            background:#ffffff; border:1px solid #8fa2bb; border-radius:8px; selection-background-color:#cfe7ff;
        }
        """
    )


def _paint_rotation_glyph(painter: QPainter, center: QPointF, radius: float, color: QColor) -> None:
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(color, 2.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawArc(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), 45 * 16, 280 * 16)
    tip = QPointF(center.x() + radius * 0.76, center.y() - radius * 0.63)
    tail = QPointF(center.x() + radius * 0.06, center.y() - radius * 0.95)
    _triangle_arrow_head(painter, tip, tail, color, max(7.0, radius * 0.82))
    painter.restore()


def _plus_icon() -> QIcon:
    pixmap = QPixmap(28, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    rect = QRectF(3, 3, 22, 18)
    path = QPainterPath()
    path.addRoundedRect(rect, 7, 7)
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, QColor("#ffffff"))
    gradient.setColorAt(0.45, QColor("#fff1bf"))
    gradient.setColorAt(1.0, QColor("#43d3bd"))
    painter.fillPath(path, gradient)
    painter.setPen(QPen(QColor("#4b778b"), 1.1))
    painter.drawPath(path)
    painter.setPen(QPen(QColor("#132238"), 2.4, Qt.SolidLine, Qt.RoundCap))
    painter.drawLine(QPointF(14, 8), QPointF(14, 18))
    painter.drawLine(QPointF(9, 13), QPointF(19, 13))
    painter.end()
    return QIcon(pixmap)


def _paper_choice_icon(landscape: bool, checked: bool) -> QIcon:
    pixmap = QPixmap(58, 30)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(QPen(QColor("#18314f"), 2.0))
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(QPointF(11, 15), 7.6, 7.6)
    if checked:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2f7df6"))
        painter.drawEllipse(QPointF(11, 15), 4.2, 4.2)
    rect = QRectF(35, 5, 13, 20) if not landscape else QRectF(29, 8, 23, 14)
    painter.setBrush(QColor("#ffffff"))
    painter.setPen(QPen(QColor("#132238"), 1.4))
    painter.drawRoundedRect(rect, 2, 2)
    painter.setPen(QPen(QColor("#ff8a35"), 1.3))
    painter.drawLine(rect.left() + 3, rect.top() + 5, rect.right() - 3, rect.top() + 5)
    painter.end()
    return QIcon(pixmap)


def _position_icon(row: int, column: int) -> QIcon:
    pixmap = QPixmap(34, 30)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    paper = QRectF(6, 4, 22, 22)
    painter.setBrush(QColor("#ffffff"))
    painter.setPen(QPen(QColor("#8fa2bb"), 1.2))
    painter.drawRoundedRect(paper, 3, 3)
    object_rect = QRectF(0, 0, 8, 6)
    object_rect.moveCenter(QPointF(paper.left() + (column + 0.5) * paper.width() / 3, paper.top() + (row + 0.5) * paper.height() / 3))
    painter.setBrush(QColor("#2f7df6"))
    painter.setPen(QPen(QColor("#174d9a"), 1.0))
    painter.drawRoundedRect(object_rect, 1.5, 1.5)
    painter.end()
    return QIcon(pixmap)


def _layer_icon(kind: str, active: bool = True) -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    base = QPainterPath()
    base.addRoundedRect(QRectF(2.5, 2.5, 27, 27), 9, 9)
    gradient = QLinearGradient(2, 2, 30, 30)
    gradient.setColorAt(0.0, QColor("#ffffff"))
    gradient.setColorAt(0.52, QColor("#eaf7ff" if active else "#eef1f5"))
    gradient.setColorAt(1.0, QColor("#65c8e8" if active else "#9aa9ba"))
    painter.fillPath(base, gradient)
    painter.setPen(QPen(QColor("#55708f"), 1.1))
    painter.drawPath(base)
    ink = QColor("#132238")
    painter.setPen(QPen(ink, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    if kind == "eye":
        eye = QPainterPath()
        eye.moveTo(6.5, 16)
        eye.cubicTo(10, 9.5, 22, 9.5, 25.5, 16)
        eye.cubicTo(22, 22.5, 10, 22.5, 6.5, 16)
        painter.drawPath(eye)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2f7df6" if active else "#8b98a8"))
        painter.drawEllipse(QPointF(16, 16), 4.0, 4.0)
    elif kind == "lock":
        painter.drawArc(QRectF(10, 6.5, 12, 13), 0, 180 * 16)
        body = QPainterPath()
        body.addRoundedRect(QRectF(8.5, 14.5, 15, 10), 3, 3)
        painter.drawPath(body)
        painter.setPen(Qt.NoPen)
        painter.setBrush(ink)
        painter.drawEllipse(QPointF(16, 19.2), 1.7, 1.7)
    else:
        _paint_rotation_glyph(painter, QPointF(16, 16), 8.0, ink)
    if not active:
        painter.setPen(QPen(QColor("#d44777"), 2.2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(8, 24), QPointF(24, 8))
    painter.end()
    return QIcon(pixmap)


class PageSetupPreview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(260, 360)
        self.paper_width_mm = 390.0
        self.paper_height_mm = 210.0
        self.margin_top = 12.0
        self.margin_bottom = 12.0
        self.margin_left = 10.0
        self.margin_right = 10.0
        self.position = (1, 1)

    def set_state(self, paper_size: tuple[float, float], landscape: bool, margins: tuple[float, float, float, float], position: tuple[int, int]) -> None:
        width, height = paper_size
        if landscape and height > width:
            width, height = height, width
        elif not landscape and width > height and width != 390.0:
            width, height = height, width
        self.paper_width_mm = max(1.0, width)
        self.paper_height_mm = max(1.0, height)
        self.margin_top, self.margin_right, self.margin_bottom, self.margin_left = margins
        self.position = position
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#eef4fb"))
        available = self.rect().adjusted(22, 22, -22, -22)
        paper_ratio = self.paper_height_mm / self.paper_width_mm
        paper_width = min(available.width(), available.height() / paper_ratio)
        paper_height = paper_width * paper_ratio
        if paper_height > available.height():
            paper_height = available.height()
            paper_width = paper_height / paper_ratio
        paper = QRectF(available.center().x() - paper_width / 2, available.center().y() - paper_height / 2, paper_width, paper_height)
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#132238"), 1.4))
        painter.drawRoundedRect(paper, 5, 5)
        left = paper.left() + paper.width() * min(self.margin_left, self.paper_width_mm * 0.45) / self.paper_width_mm
        right = paper.right() - paper.width() * min(self.margin_right, self.paper_width_mm * 0.45) / self.paper_width_mm
        top = paper.top() + paper.height() * min(self.margin_top, self.paper_height_mm * 0.45) / self.paper_height_mm
        bottom = paper.bottom() - paper.height() * min(self.margin_bottom, self.paper_height_mm * 0.45) / self.paper_height_mm
        printable = QRectF(left, top, max(12, right - left), max(12, bottom - top))
        painter.setPen(QPen(QColor("#2f7df6"), 1.2, Qt.DashLine))
        painter.setBrush(QColor(47, 125, 246, 24))
        painter.drawRoundedRect(printable, 4, 4)
        row, column = self.position
        object_width = max(24.0, printable.width() * 0.34)
        object_height = max(18.0, printable.height() * 0.24)
        x_positions = (printable.left(), printable.center().x() - object_width / 2, printable.right() - object_width)
        y_positions = (printable.top(), printable.center().y() - object_height / 2, printable.bottom() - object_height)
        content = QRectF(x_positions[column], y_positions[row], object_width, object_height)
        painter.setPen(QPen(QColor("#ff8a35"), 1.8))
        painter.setBrush(QColor(255, 138, 53, 40))
        painter.drawRoundedRect(content, 5, 5)
        painter.end()


class PageSetupDialog(QDialog):
    PAPER_SIZES = {
        "Workspace": (390.0, 210.0),
        "A0": (841.0, 1189.0),
        "A1": (594.0, 841.0),
        "A2": (420.0, 594.0),
        "A3": (297.0, 420.0),
        "A4": (210.0, 297.0),
        "A5": (148.0, 210.0),
        "Letter": (215.9, 279.4),
        "Legal": (215.9, 355.6),
        "Tabloid": (279.4, 431.8),
        "Custom": (390.0, 210.0),
    }
    DPI_VALUES = ("200", "300", "600", "1200", "Custom")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectHelpDialog")
        self.setWindowTitle("Page Setup")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.resize(900, 600)
        self._paper_name = "Workspace"
        self._landscape = True
        self._position = (1, 1)
        self._margin_spins: dict[str, QDoubleSpinBox] = {}
        self._custom_size_spins: dict[str, QDoubleSpinBox] = {}
        self._sync_vertical = False
        self._sync_horizontal = False
        self._drag_offset: QPoint | None = None
        shell = QWidget()
        shell.setObjectName("ProjectHelpShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 14)
        layout.setSpacing(10)
        layout.addWidget(self._build_header())
        body = QHBoxLayout()
        body.setContentsMargins(14, 8, 14, 0)
        body.setSpacing(14)
        self._preview = PageSetupPreview()
        body.addWidget(self._preview, 1)
        body.addWidget(self._build_controls(), 1)
        layout.addLayout(body, 1)
        buttons = QHBoxLayout()
        buttons.setContentsMargins(14, 0, 14, 0)
        buttons.addStretch(1)
        apply_button = QPushButton("Apply")
        apply_button.setObjectName("PrimaryDialogButton")
        apply_button.clicked.connect(self.accept)
        buttons.addWidget(apply_button)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryDialogButton")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)
        self._update_preview()

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("HelpHeader")
        header.setFixedHeight(44)
        self._drag_header = header
        header.installEventFilter(self)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 8, 0)
        builder = getattr(self.parentWidget(), "_build_window_mark", None)
        mark = builder() if callable(builder) else QLabel("AT")
        mark.setFixedSize(36, 32)
        mark.setAlignment(Qt.AlignCenter)
        layout.addWidget(mark)
        title = QLabel("Page Setup")
        title.setObjectName("HelpTitle")
        layout.addWidget(title, 1)
        close = QPushButton("×")
        close.setObjectName("MenuDialogClose")
        close.setFixedSize(28, 26)
        close.clicked.connect(self.reject)
        layout.addWidget(close)
        return header

    def _build_controls(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("SidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self._section_label("Paper"))
        self._paper_combo = QComboBox()
        self._paper_combo.setObjectName("FileTypeCombo")
        _style_combo_arrow(self._paper_combo)
        for name, size in self.PAPER_SIZES.items():
            self._paper_combo.addItem(f"{name}  {size[0]:.1f} × {size[1]:.1f} mm", name)
        self._paper_combo.currentIndexChanged.connect(self._paper_combo_changed)
        layout.addWidget(self._paper_combo)
        custom_grid = QGridLayout()
        custom_grid.setHorizontalSpacing(7)
        custom_grid.setVerticalSpacing(4)
        custom_grid.setContentsMargins(18, 0, 18, 0)
        for column, (key, label) in enumerate((("width", "W"), ("height", "H"))):
            field_label = QLabel(label)
            field_label.setFixedWidth(18)
            field_label.setAlignment(Qt.AlignCenter)
            custom_grid.addWidget(field_label, 0, column * 2)
            spin = self._number_spin(1, 5000, 0.5, " mm")
            spin.setFixedWidth(116)
            spin.setValue(self.PAPER_SIZES["Custom"][column])
            spin.setEnabled(False)
            spin.valueChanged.connect(lambda value, spin_key=key: self._custom_size_changed(spin_key, value))
            self._custom_size_spins[key] = spin
            custom_grid.addWidget(spin, 0, column * 2 + 1)
        layout.addLayout(custom_grid)
        layout.addWidget(self._section_label("Orientation"))
        orient = QHBoxLayout()
        portrait = self._choice_button("Portrait", not self._landscape, lambda: self._set_orientation(False))
        landscape = self._choice_button("Landscape", self._landscape, lambda: self._set_orientation(True))
        portrait.setIcon(_paper_choice_icon(False, not self._landscape))
        landscape.setIcon(_paper_choice_icon(True, self._landscape))
        portrait.setIconSize(QSize(58, 30))
        landscape.setIconSize(QSize(58, 30))
        self._orientation_buttons = (portrait, landscape)
        orient.addWidget(portrait)
        orient.addWidget(landscape)
        layout.addLayout(orient)
        layout.addWidget(self._section_label("Margins"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(5)
        for index, name in enumerate(("Top", "Right", "Bottom", "Left")):
            grid.addWidget(QLabel(name), index // 2, (index % 2) * 2)
            spin = self._number_spin(0, 300, 0.5, " mm")
            spin.setValue(12 if name in {"Top", "Bottom"} else 10)
            spin.valueChanged.connect(lambda value, key=name.lower(): self._margin_changed(key, value))
            self._margin_spins[name.lower()] = spin
            grid.addWidget(spin, index // 2, (index % 2) * 2 + 1)
        layout.addLayout(grid)
        sync_row = QHBoxLayout()
        vertical = self._choice_button("Top = Bottom", False, self._toggle_vertical_sync)
        horizontal = self._choice_button("Left = Right", False, self._toggle_horizontal_sync)
        self._sync_buttons = (vertical, horizontal)
        sync_row.addWidget(vertical)
        sync_row.addWidget(horizontal)
        layout.addLayout(sync_row)
        layout.addWidget(self._section_label("Object Position"))
        pos_grid = QGridLayout()
        pos_grid.setSpacing(0)
        self._position_buttons: list[QPushButton] = []
        for row in range(3):
            for column in range(3):
                button = QPushButton()
                button.setObjectName("ToolButton")
                button.setCheckable(True)
                button.setChecked((row, column) == self._position)
                button.setIcon(_position_icon(row, column))
                button.setIconSize(QSize(34, 30))
                button.setFixedSize(38, 32)
                button.clicked.connect(lambda checked=False, r=row, c=column: self._set_position(r, c))
                self._position_buttons.append(button)
                pos_grid.addWidget(button, row, column)
        layout.addLayout(pos_grid)
        layout.addWidget(self._section_label("Quality"))
        dpi_row = QHBoxLayout()
        self._dpi_buttons: list[QPushButton] = []
        for value in self.DPI_VALUES:
            button = self._choice_button(value, value == "600", lambda checked=False, selected=value: self._set_dpi(selected))
            self._dpi_buttons.append(button)
            dpi_row.addWidget(button)
        layout.addLayout(dpi_row)
        self._custom_dpi = self._number_spin(72, 4800, 1, " DPI")
        self._custom_dpi.setDecimals(0)
        self._custom_dpi.setValue(600)
        self._custom_dpi.setEnabled(False)
        layout.addWidget(self._custom_dpi)
        layout.addStretch(1)
        return panel

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("PanelTitle")
        return label

    def _choice_button(self, text: str, checked: bool, callback: Callable[[], None]) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("MenuItemButton")
        button.setCheckable(True)
        button.setChecked(checked)
        button.setIcon(_radio_icon(checked))
        button.setIconSize(QSize(22, 22))
        button.clicked.connect(lambda checked=False: callback())
        return button

    def _number_spin(self, minimum: float, maximum: float, step: float, suffix: str) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setObjectName("FileNameInput")
        spin.setRange(minimum, maximum)
        spin.setDecimals(2)
        spin.setSingleStep(step)
        spin.setSuffix(suffix)
        _style_numeric_spin(spin)
        return spin

    def _paper_combo_changed(self, index: int = 0) -> None:
        name = self._paper_combo.currentData()
        if isinstance(name, str):
            self._paper_name = name
            custom = name == "Custom"
            for spin in self._custom_size_spins.values():
                spin.setEnabled(custom)
            self._update_preview()

    def _custom_size_changed(self, key: str, value: float) -> None:
        if self._paper_name == "Custom":
            self._update_preview()

    def _set_orientation(self, landscape: bool) -> None:
        self._landscape = landscape
        for button, state in zip(self._orientation_buttons, (not landscape, landscape), strict=True):
            button.setChecked(state)
        self._orientation_buttons[0].setIcon(_paper_choice_icon(False, not landscape))
        self._orientation_buttons[1].setIcon(_paper_choice_icon(True, landscape))
        self._update_preview()

    def _margin_changed(self, key: str, value: float) -> None:
        if self._sync_vertical and key in {"top", "bottom"}:
            other = "bottom" if key == "top" else "top"
            self._margin_spins[other].blockSignals(True)
            self._margin_spins[other].setValue(value)
            self._margin_spins[other].blockSignals(False)
        if self._sync_horizontal and key in {"left", "right"}:
            other = "right" if key == "left" else "left"
            self._margin_spins[other].blockSignals(True)
            self._margin_spins[other].setValue(value)
            self._margin_spins[other].blockSignals(False)
        self._update_preview()

    def _toggle_vertical_sync(self) -> None:
        self._sync_vertical = not self._sync_vertical
        self._sync_buttons[0].setChecked(self._sync_vertical)
        self._sync_buttons[0].setIcon(_radio_icon(self._sync_vertical))
        self._margin_changed("top", self._margin_spins["top"].value())

    def _toggle_horizontal_sync(self) -> None:
        self._sync_horizontal = not self._sync_horizontal
        self._sync_buttons[1].setChecked(self._sync_horizontal)
        self._sync_buttons[1].setIcon(_radio_icon(self._sync_horizontal))
        self._margin_changed("left", self._margin_spins["left"].value())

    def _set_position(self, row: int, column: int) -> None:
        self._position = (row, column)
        for index, button in enumerate(self._position_buttons):
            button.setChecked((index // 3, index % 3) == self._position)
        self._update_preview()

    def _set_dpi(self, selected: str) -> None:
        for button in self._dpi_buttons:
            active = button.text() == selected
            button.setChecked(active)
            button.setIcon(_radio_icon(active))
        self._custom_dpi.setEnabled(selected == "Custom")
        if selected != "Custom":
            self._custom_dpi.setValue(float(selected))

    def _current_paper_size(self) -> tuple[float, float]:
        if self._paper_name == "Custom":
            return (self._custom_size_spins["width"].value(), self._custom_size_spins["height"].value())
        return self.PAPER_SIZES.get(self._paper_name, self.PAPER_SIZES["Workspace"])

    def _update_preview(self) -> None:
        margins = (
            self._margin_spins.get("top").value() if "top" in self._margin_spins else 12.0,
            self._margin_spins.get("right").value() if "right" in self._margin_spins else 10.0,
            self._margin_spins.get("bottom").value() if "bottom" in self._margin_spins else 12.0,
            self._margin_spins.get("left").value() if "left" in self._margin_spins else 10.0,
        )
        self._preview.set_state(self._current_paper_size(), self._landscape, margins, self._position)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 54:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is getattr(self, "_drag_header", None):
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            if event.type() == QEvent.Type.MouseMove and self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self._drag_offset)
                return True
            if event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_offset = None
                return True
        return super().eventFilter(watched, event)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        from .module_window import _apply_rounded_mask

        _apply_rounded_mask(self, 16)


def apply_runtime_ui_patch() -> None:
    from . import module_window as mw
    from . import project_file_dialog as pfd
    from ..ui import start_bar as sb

    if getattr(mw.ModuleWindow, "_page_setup_patch_applied", False):
        return
    mw._paint_rotation_glyph = _paint_rotation_glyph
    mw._layer_icon = _layer_icon
    sb._arrow_head = _solid_arrow_head

    def file_item_size(self, name: str):
        return QSize(max(42, min(540, self.fontMetrics().horizontalAdvance(name) + 39)), 30)

    def place_item_width(self, name: str) -> int:
        return max(42, min(160, self.fontMetrics().horizontalAdvance(name) + 39))

    def paint_selection_frame(self, painter, rect):
        select = QColor("#2f7df6")
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(select, 1.5, Qt.DashLine))
        painter.drawRect(rect.adjusted(-5, -5, 5, 5))
        handles = (
            rect.topLeft(), QPointF(rect.center().x(), rect.top()), rect.topRight(),
            QPointF(rect.right(), rect.center().y()), rect.bottomRight(), QPointF(rect.center().x(), rect.bottom()),
            rect.bottomLeft(), QPointF(rect.left(), rect.center().y()),
        )
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        painter.setBrush(select)
        for point in handles:
            painter.drawRoundedRect(QRectF(point.x() - 4, point.y() - 4, 8, 8), 2, 2)
        rotate_center = QPointF(rect.center().x(), rect.top() - 34)
        painter.setPen(QPen(select, 1.2, Qt.DashLine))
        painter.drawLine(QPointF(rect.center().x() - 5, rect.top() - 5), QPointF(rotate_center.x() - 5, rotate_center.y() + 11))
        painter.drawLine(QPointF(rect.center().x() + 5, rect.top() - 5), QPointF(rotate_center.x() + 5, rotate_center.y() + 11))
        painter.setBrush(QColor("#fff9de"))
        painter.setPen(QPen(QColor("#7e5b10"), 1.4))
        painter.drawEllipse(rotate_center, 13, 13)
        _paint_rotation_glyph(painter, rotate_center, 7.4, QColor("#ff8a35"))

    pfd.ProjectFileDialog._file_item_size = file_item_size
    pfd.ProjectFileDialog._place_item_width = place_item_width
    mw.GridCanvas._paint_selection_frame = paint_selection_frame

    def canvas_snapshot(self):
        canvas = getattr(self, "_canvas", None)
        if canvas is None:
            return None
        rect = getattr(canvas, "_object_rect", None)
        return {
            "file_path": getattr(canvas, "_file_path", None),
            "file_pixmap": QPixmap(getattr(canvas, "_file_pixmap", QPixmap())),
            "object_rect": QRectF(rect) if rect is not None else None,
            "rotation": getattr(canvas, "_rotation_degrees", 0.0),
            "layers": list(getattr(self, "_layers", [])),
        }

    def restore_canvas(self, snapshot):
        canvas = getattr(self, "_canvas", None)
        if canvas is None or snapshot is None:
            return
        canvas._file_path = snapshot["file_path"]
        canvas._file_pixmap = QPixmap(snapshot["file_pixmap"])
        canvas._object_rect = QRectF(snapshot["object_rect"]) if snapshot["object_rect"] is not None else None
        canvas._rotation_degrees = snapshot["rotation"]
        self._layers = list(snapshot["layers"])
        self._refresh_layers()
        canvas.update()

    def push_history(self):
        snapshot = canvas_snapshot(self)
        if snapshot is None:
            return
        undo_stack = getattr(self, "_runtime_undo_stack", [])
        undo_stack.append(snapshot)
        self._runtime_undo_stack = undo_stack[-40:]
        self._runtime_redo_stack = []

    def has_canvas_object(self) -> bool:
        canvas = getattr(self, "_canvas", None)
        return canvas is not None and getattr(canvas, "_object_rect", None) is not None

    def copy_canvas_object(self) -> bool:
        canvas = getattr(self, "_canvas", None)
        if canvas is None or getattr(canvas, "_object_rect", None) is None:
            return False
        self._runtime_clipboard_object = {
            "file_path": getattr(canvas, "_file_path", None),
            "file_pixmap": QPixmap(getattr(canvas, "_file_pixmap", QPixmap())),
            "object_rect": QRectF(canvas._object_rect),
            "rotation": getattr(canvas, "_rotation_degrees", 0.0),
        }
        return True

    def undo(self):
        stack = getattr(self, "_runtime_undo_stack", [])
        if not stack:
            self._run_focus_command("undo")
            self._set_status("Undo")
            return
        redo_stack = getattr(self, "_runtime_redo_stack", [])
        redo_stack.append(canvas_snapshot(self))
        self._runtime_redo_stack = redo_stack[-40:]
        restore_canvas(self, stack.pop())
        self._runtime_undo_stack = stack
        self._set_status("Undo")

    def redo(self):
        stack = getattr(self, "_runtime_redo_stack", [])
        if not stack:
            self._run_focus_command("redo")
            self._set_status("Redo")
            return
        undo_stack = getattr(self, "_runtime_undo_stack", [])
        undo_stack.append(canvas_snapshot(self))
        self._runtime_undo_stack = undo_stack[-40:]
        restore_canvas(self, stack.pop())
        self._runtime_redo_stack = stack
        self._set_status("Redo")

    def copy(self):
        focused = QApplication.focusWidget()
        if focused is not None and focused is not self and self._run_focus_command("copy"):
            self._set_status("Copy")
            return
        self._set_status("Copied object" if copy_canvas_object(self) else "Copy")

    def cut(self):
        if copy_canvas_object(self):
            push_history(self)
            canvas = self._canvas
            canvas._object_rect = None
            canvas._file_path = None
            canvas._file_pixmap = QPixmap()
            if self._layers:
                self._layers.pop()
                self._refresh_layers()
            canvas.update()
            self._set_status("Cut object")
            return
        self._run_focus_command("cut")
        self._set_status("Cut")

    def paste(self):
        clip = getattr(self, "_runtime_clipboard_object", None)
        canvas = getattr(self, "_canvas", None)
        if clip is None or canvas is None:
            self._run_focus_command("paste")
            self._set_status("Paste")
            return
        push_history(self)
        rect = QRectF(clip["object_rect"]).translated(18, 18)
        canvas._file_path = clip["file_path"]
        canvas._file_pixmap = QPixmap(clip["file_pixmap"])
        canvas._object_rect = rect
        canvas._rotation_degrees = clip["rotation"]
        if clip["file_path"] is not None:
            self._add_layer(getattr(clip["file_path"], "stem", "Object"))
        canvas.update()
        self._set_status("Pasted object")

    def delete(self):
        if has_canvas_object(self):
            push_history(self)
            canvas = self._canvas
            canvas._object_rect = None
            canvas._file_path = None
            canvas._file_pixmap = QPixmap()
            if self._layers:
                self._layers.pop()
                self._refresh_layers()
            canvas.update()
            self._set_status("Deleted object")
            return
        self._set_status("Delete")

    def repeat_last_tools(self):
        if copy_canvas_object(self):
            paste(self)
            self._set_status("Repeated object")
        else:
            self._set_status("Repeat Last Tools")

    def select_all(self):
        if has_canvas_object(self):
            self._canvas.setFocus(Qt.FocusReason.ShortcutFocusReason)
            self._canvas.update()
            self._set_status("Selected all")
            return
        self._run_focus_command("selectAll")
        self._set_status("Select All")

    def toggle_start_bar(self):
        self._view_state["start_bar"] = not self._view_state["start_bar"]
        if self._start_bar_widget is not None:
            self._start_bar_widget.setVisible(self._view_state["start_bar"])
        self._set_status(f"Start Bar {'On' if self._view_state['start_bar'] else 'Off'}")

    def toggle_grid(self):
        self._view_state["grid"] = not self._view_state["grid"]
        if self._start_bar_widget is not None and hasattr(self._start_bar_widget, "_set_grid_enabled"):
            self._start_bar_widget._set_grid_enabled(self._view_state["grid"])
        elif self._canvas is not None:
            self._canvas.set_grid_visible(self._view_state["grid"])
        self._set_status(f"Grid {'On' if self._view_state['grid'] else 'Off'}")

    def toggle_ruler(self):
        self._view_state["ruler"] = not self._view_state["ruler"]
        if self._start_bar_widget is not None and hasattr(self._start_bar_widget, "_set_ruler"):
            self._start_bar_widget._set_ruler(self._view_state["ruler"])
        self._set_status(f"Ruler {'On' if self._view_state['ruler'] else 'Off'}")

    def toggle_snap(self):
        self._view_state["snap"] = not self._view_state["snap"]
        self._set_status(f"Snap {'On' if self._view_state['snap'] else 'Off'}")

    def build_page_bar(self):
        bar = QWidget()
        bar.setObjectName("PageBar")
        bar.setFixedHeight(38)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(5)
        page_strip = QWidget()
        page_strip.setObjectName("PageStrip")
        self._page_buttons_layout = QHBoxLayout(page_strip)
        self._page_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self._page_buttons_layout.setSpacing(4)
        layout.addWidget(page_strip)
        layout.addStretch(1)
        self._refresh_page_buttons()
        return bar

    def refresh_page_buttons(self):
        if self._page_buttons_layout is None:
            return
        while self._page_buttons_layout.count():
            item = self._page_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for index, label in enumerate(self._pages):
            page = QPushButton(label)
            page.setObjectName("PageButtonActive" if index == self._active_page_index else "PageButton")
            page.setToolTip(f"{label}\nRight-click for page actions")
            page.setContextMenuPolicy(Qt.CustomContextMenu)
            page.clicked.connect(lambda checked=False, selected=index: self._select_page(selected))
            page.customContextMenuRequested.connect(lambda pos, selected=index, anchor=page: self._show_page_context_menu(selected, anchor))
            self._page_buttons_layout.addWidget(page)
        add_page = QPushButton()
        add_page.setObjectName("AddPageButton")
        add_page.setToolTip("Add page")
        add_page.setFixedSize(28, 24)
        add_page.setStyleSheet("QPushButton#AddPageButton { min-width:24px; max-width:28px; min-height:20px; max-height:24px; padding:0px; }")
        add_page.setIcon(_plus_icon())
        add_page.setIconSize(QSize(28, 24))
        add_page.clicked.connect(self._add_page)
        self._page_buttons_layout.addWidget(add_page)

    def show_file_menu(self, anchor):
        self._show_menu("File", (
            mw.MenuItemSpec("New", self._new_file, "Ctrl+N"), mw.MenuItemSpec("Open", self._open_file, "Ctrl+O"),
            mw.MenuItemSpec("Save", self._save_file, "Ctrl+S"), mw.MenuItemSpec("Save As", self._save_as_file, "Ctrl+Shift+S"),
            mw.MenuItemSpec("Import", self._import_file), mw.MenuItemSpec("Export", self._export_file),
            mw.MenuItemSpec("Page Setup", self._page_setup), mw.MenuItemSpec("Print Setup", self._print_setup),
            mw.MenuItemSpec("Properties", self._file_properties),
        ), anchor)

    def show_edit_menu(self, anchor):
        self._show_menu("Edit", (
            mw.MenuItemSpec("Copy", self._copy, "Ctrl+C"), mw.MenuItemSpec("Cut", self._cut, "Ctrl+X"),
            mw.MenuItemSpec("Paste", self._paste, "Ctrl+V"), mw.MenuItemSpec("Move", self._move),
            mw.MenuItemSpec("Undo", self._undo, "Ctrl+Z"), mw.MenuItemSpec("Redo", self._redo, "Ctrl+Y"),
            mw.MenuItemSpec("Delete", self._delete, "Delete"),
            mw.MenuItemSpec("Repeat Last Tools", self._repeat_last_tools, "Ctrl+R"), mw.MenuItemSpec("Select All", self._select_all, "Ctrl+A"),
            mw.MenuItemSpec("Group", self._group, "Ctrl+G"), mw.MenuItemSpec("Ungroup", self._ungroup, "Ctrl+Shift+G"),
        ), anchor)

    def show_canvas_context_menu(self, global_pos):
        self._show_menu_at("Object", (
            mw.MenuItemSpec("Repeat", self._repeat_last_tools), mw.MenuItemSpec("Copy", self._copy),
            mw.MenuItemSpec("Cut", self._cut), mw.MenuItemSpec("Paste", self._paste), mw.MenuItemSpec("Delete", self._delete),
            mw.MenuItemSpec("Rotate", self._rotation), mw.MenuItemSpec("Bring to Front", self._bring_to_front),
            mw.MenuItemSpec("Send to Back", self._send_to_back), mw.MenuItemSpec("Group", self._group), mw.MenuItemSpec("Ungroup", self._ungroup),
        ), global_pos)

    def install_shortcuts(self):
        for sequence, handler in (
            ("Ctrl+N", self._new_file), ("Ctrl+O", self._open_file), ("Ctrl+S", self._save_file),
            ("Ctrl+Shift+S", self._save_as_file), ("Ctrl+Z", self._undo), ("Ctrl+Y", self._redo),
            ("Ctrl+X", self._cut), ("Ctrl+C", self._copy), ("Ctrl+V", self._paste),
            ("Delete", self._delete), ("Backspace", self._delete), ("Ctrl+R", self._repeat_last_tools),
            ("Ctrl+A", self._select_all), ("Ctrl+G", self._group), ("Ctrl+Shift+G", self._ungroup),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(handler)
            shortcut.activatedAmbiguously.connect(handler)

    def page_setup(self):
        dialog = PageSetupDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._set_status("Page Setup applied")
        else:
            self._set_status("Page Setup canceled")

    mw.ModuleWindow._build_page_bar = build_page_bar
    mw.ModuleWindow._refresh_page_buttons = refresh_page_buttons
    mw.ModuleWindow._show_file_menu = show_file_menu
    mw.ModuleWindow._show_edit_menu = show_edit_menu
    mw.ModuleWindow._show_canvas_context_menu = show_canvas_context_menu
    mw.ModuleWindow._install_shortcuts = install_shortcuts
    mw.ModuleWindow._undo = undo
    mw.ModuleWindow._redo = redo
    mw.ModuleWindow._copy = copy
    mw.ModuleWindow._cut = cut
    mw.ModuleWindow._paste = paste
    mw.ModuleWindow._delete = delete
    mw.ModuleWindow._repeat_last_tools = repeat_last_tools
    mw.ModuleWindow._select_all = select_all
    mw.ModuleWindow._toggle_start_bar = toggle_start_bar
    mw.ModuleWindow._toggle_grid = toggle_grid
    mw.ModuleWindow._toggle_ruler = toggle_ruler
    mw.ModuleWindow._toggle_snap = toggle_snap
    mw.ModuleWindow._page_setup = page_setup
    mw.ModuleWindow._page_setup_patch_applied = True

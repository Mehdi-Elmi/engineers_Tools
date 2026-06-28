"""Runtime UI refinements for the shared engineering workspace."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QDialog, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


def _triangle_arrow_head(painter: QPainter, tip: QPointF, tail: QPointF, color: QColor, size: float = 7.0) -> None:
    direction = tip - tail
    length = max(0.01, (direction.x() ** 2 + direction.y() ** 2) ** 0.5)
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    base = QPointF(tip.x() - unit.x() * size, tip.y() - unit.y() * size)
    left = QPointF(base.x() + normal.x() * size * 0.42, base.y() + normal.y() * size * 0.42)
    right = QPointF(base.x() - normal.x() * size * 0.42, base.y() - normal.y() * size * 0.42)
    painter.setBrush(color)
    painter.setPen(QPen(color, 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPolygon(QPolygonF([tip, left, right]))


def _paint_rotation_glyph(painter: QPainter, center: QPointF, radius: float, color: QColor) -> None:
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(color, 2.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawArc(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), 35 * 16, 285 * 16)
    tip = QPointF(center.x() + radius * 0.88, center.y() - radius * 0.50)
    tail = QPointF(center.x() + radius * 0.20, center.y() - radius * 0.84)
    _triangle_arrow_head(painter, tip, tail, color, max(5.0, radius * 0.70))
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


def _paper_icon(landscape: bool = False) -> QIcon:
    pixmap = QPixmap(38, 28)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    rect = QRectF(11, 4, 16, 20) if not landscape else QRectF(7, 7, 24, 14)
    painter.setBrush(QColor("#ffffff"))
    painter.setPen(QPen(QColor("#132238"), 1.5))
    painter.drawRoundedRect(rect, 2, 2)
    painter.setPen(QPen(QColor("#ff8a35"), 1.4))
    painter.drawLine(rect.left() + 4, rect.top() + 5, rect.right() - 4, rect.top() + 5)
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
    dot_x = paper.left() + (column + 0.5) * paper.width() / 3
    dot_y = paper.top() + (row + 0.5) * paper.height() / 3
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#2f7df6"))
    painter.drawEllipse(QPointF(dot_x, dot_y), 3.3, 3.3)
    painter.end()
    return QIcon(pixmap)


class PageSetupPreview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(260, 360)
        self.paper_ratio = 297 / 210
        self.margin_top = 12.0
        self.margin_bottom = 12.0
        self.margin_left = 10.0
        self.margin_right = 10.0
        self.position = (1, 1)

    def set_state(self, paper_ratio: float, landscape: bool, margins: tuple[float, float, float, float], position: tuple[int, int]) -> None:
        self.paper_ratio = 1 / paper_ratio if landscape else paper_ratio
        self.margin_top, self.margin_right, self.margin_bottom, self.margin_left = margins
        self.position = position
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#eef4fb"))
        available = self.rect().adjusted(22, 22, -22, -22)
        paper_width = min(available.width(), available.height() / self.paper_ratio)
        paper_height = paper_width * self.paper_ratio
        if paper_height > available.height():
            paper_height = available.height()
            paper_width = paper_height / self.paper_ratio
        paper = QRectF(
            available.center().x() - paper_width / 2,
            available.center().y() - paper_height / 2,
            paper_width,
            paper_height,
        )
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#132238"), 1.4))
        painter.drawRoundedRect(paper, 5, 5)
        left = paper.left() + paper.width() * min(self.margin_left, 45) / 100
        right = paper.right() - paper.width() * min(self.margin_right, 45) / 100
        top = paper.top() + paper.height() * min(self.margin_top, 45) / 100
        bottom = paper.bottom() - paper.height() * min(self.margin_bottom, 45) / 100
        content = QRectF(left, top, max(12, right - left), max(12, bottom - top))
        painter.setPen(QPen(QColor("#2f7df6"), 1.2, Qt.DashLine))
        painter.setBrush(QColor(47, 125, 246, 24))
        painter.drawRoundedRect(content, 4, 4)
        row, column = self.position
        marker = QPointF(
            content.left() + (column + 0.5) * content.width() / 3,
            content.top() + (row + 0.5) * content.height() / 3,
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#ff8a35"))
        painter.drawEllipse(marker, 5, 5)
        painter.end()


class PageSetupDialog(QDialog):
    PAPER_SIZES = ("A0", "A1", "A2", "A3", "A4", "A5", "Letter", "Legal", "Tabloid")
    PAPER_RATIOS = {
        "A0": 1189 / 841,
        "A1": 841 / 594,
        "A2": 594 / 420,
        "A3": 420 / 297,
        "A4": 297 / 210,
        "A5": 210 / 148,
        "Letter": 11 / 8.5,
        "Legal": 14 / 8.5,
        "Tabloid": 17 / 11,
    }
    DPI_VALUES = ("200", "300", "600", "1200", "Custom")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectHelpDialog")
        self.setWindowTitle("Page Setup")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.resize(820, 560)
        self._paper_name = "A4"
        self._landscape = False
        self._position = (1, 1)
        self._margin_spins: dict[str, QDoubleSpinBox] = {}
        self._paper_buttons: dict[str, QPushButton] = {}
        self._sync_vertical = False
        self._sync_horizontal = False
        shell = QWidget()
        shell.setObjectName("ProjectHelpShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(12)
        layout.addWidget(self._build_header())
        body = QHBoxLayout()
        body.setSpacing(14)
        self._preview = PageSetupPreview()
        body.addWidget(self._preview, 1)
        body.addWidget(self._build_controls(), 1)
        layout.addLayout(body, 1)
        buttons = QHBoxLayout()
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
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 8, 0)
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
        layout.setSpacing(9)
        layout.addWidget(self._section_label("Paper"))
        paper_row = QHBoxLayout()
        for paper in self.PAPER_SIZES:
            button = self._choice_button(paper, paper == "A4", lambda checked=False, name=paper: self._choose_paper(name))
            self._paper_buttons[paper] = button
            paper_row.addWidget(button)
        layout.addLayout(paper_row)
        layout.addWidget(self._section_label("Orientation"))
        orient = QHBoxLayout()
        portrait = self._choice_button("Portrait", True, lambda: self._set_orientation(False))
        portrait.setIcon(_paper_icon(False))
        portrait.setIconSize(QSize(34, 24))
        landscape = self._choice_button("Landscape", False, lambda: self._set_orientation(True))
        landscape.setIcon(_paper_icon(True))
        landscape.setIconSize(QSize(34, 24))
        self._orientation_buttons = (portrait, landscape)
        orient.addWidget(portrait)
        orient.addWidget(landscape)
        layout.addLayout(orient)
        layout.addWidget(self._section_label("Margins"))
        grid = QGridLayout()
        for index, name in enumerate(("Top", "Right", "Bottom", "Left")):
            grid.addWidget(QLabel(name), index // 2, (index % 2) * 2)
            spin = QDoubleSpinBox()
            spin.setObjectName("FileNameInput")
            spin.setRange(0, 80)
            spin.setDecimals(2)
            spin.setValue(12 if name in {"Top", "Bottom"} else 10)
            spin.setSuffix(" mm")
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
        self._position_buttons: list[QPushButton] = []
        for row in range(3):
            for column in range(3):
                button = QPushButton()
                button.setObjectName("ToolButton")
                button.setCheckable(True)
                button.setChecked((row, column) == self._position)
                button.setIcon(_position_icon(row, column))
                button.setIconSize(QSize(34, 30))
                button.setFixedSize(42, 36)
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
        self._custom_dpi = QDoubleSpinBox()
        self._custom_dpi.setObjectName("FileNameInput")
        self._custom_dpi.setRange(72, 4800)
        self._custom_dpi.setDecimals(0)
        self._custom_dpi.setValue(600)
        self._custom_dpi.setSuffix(" DPI")
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
        button.clicked.connect(lambda checked=False: callback())
        return button

    def _choose_paper(self, name: str) -> None:
        self._paper_name = name
        for paper, button in self._paper_buttons.items():
            button.setChecked(paper == name)
        self._update_preview()

    def _set_orientation(self, landscape: bool) -> None:
        self._landscape = landscape
        for button, state in zip(self._orientation_buttons, (not landscape, landscape), strict=True):
            button.setChecked(state)
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
        self._margin_changed("top", self._margin_spins["top"].value())

    def _toggle_horizontal_sync(self) -> None:
        self._sync_horizontal = not self._sync_horizontal
        self._sync_buttons[1].setChecked(self._sync_horizontal)
        self._margin_changed("left", self._margin_spins["left"].value())

    def _set_position(self, row: int, column: int) -> None:
        self._position = (row, column)
        for index, button in enumerate(self._position_buttons):
            button.setChecked((index // 3, index % 3) == self._position)
        self._update_preview()

    def _set_dpi(self, selected: str) -> None:
        for button in self._dpi_buttons:
            button.setChecked(button.text() == selected)
        if selected != "Custom":
            self._custom_dpi.setValue(float(selected))

    def _update_preview(self) -> None:
        margins = (
            self._margin_spins.get("top").value() if "top" in self._margin_spins else 12.0,
            self._margin_spins.get("right").value() if "right" in self._margin_spins else 10.0,
            self._margin_spins.get("bottom").value() if "bottom" in self._margin_spins else 12.0,
            self._margin_spins.get("left").value() if "left" in self._margin_spins else 10.0,
        )
        self._preview.set_state(self.PAPER_RATIOS.get(self._paper_name, self.PAPER_RATIOS["A4"]), self._landscape, margins, self._position)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        from .module_window import _apply_rounded_mask

        _apply_rounded_mask(self, 16)


def apply_runtime_ui_patch() -> None:
    from . import module_window as mw

    if getattr(mw.ModuleWindow, "_page_setup_patch_applied", False):
        return
    mw._paint_rotation_glyph = _paint_rotation_glyph

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

    def page_setup(self):
        dialog = PageSetupDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._set_status("Page Setup applied")
        else:
            self._set_status("Page Setup canceled")

    mw.ModuleWindow._build_page_bar = build_page_bar
    mw.ModuleWindow._refresh_page_buttons = refresh_page_buttons
    mw.ModuleWindow._show_file_menu = show_file_menu
    mw.ModuleWindow._page_setup = page_setup
    mw.ModuleWindow._page_setup_patch_applied = True

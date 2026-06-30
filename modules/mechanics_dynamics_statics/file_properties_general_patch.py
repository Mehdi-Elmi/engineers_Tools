"""Move common default settings into File > Properties > General.

This patch intentionally keeps the right-side runtime Properties panel clean.
The shared startup/default settings belong to the File Properties dialog.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFontComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-file-properties-general-2026-06-30-a"
UNITS = ("mm", "cm", "m", "px", "pt", "in")


def _font(widget, size: int = 10, *, italic: bool = True, bold: bool = True) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setItalic(italic)
    font.setBold(bold)
    widget.setFont(font)


def _radio_icon(checked: bool) -> QIcon:
    pixmap = QPixmap(20, 20)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor("#18314f"), 1.8))
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(QPointF(10, 10), 7.0, 7.0)
    if checked:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2f7df6"))
        painter.drawEllipse(QPointF(10, 10), 4.0, 4.0)
    painter.end()
    return QIcon(pixmap)


class _WaveSection(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None, *, collapsed: bool = False, open_height: int = 118) -> None:
        super().__init__(parent)
        self._title = title
        self._collapsed = False
        self._open_height = open_height
        self.setObjectName("FilePropertiesWaveSection")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(12, 40, 12, 10)
        self._root.setSpacing(5)
        self._body = QWidget(self)
        self._body.setObjectName("FilePropertiesWaveBody")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(5)
        self._root.addWidget(self._body)
        self.setStyleSheet("QFrame#FilePropertiesWaveSection {background:transparent; border:0;} QWidget#FilePropertiesWaveBody {background:transparent; border:0;}")
        self._set_collapsed(collapsed)

    def add_body_widget(self, widget: QWidget) -> None:
        self._body_layout.addWidget(widget)
        self._set_collapsed(self._collapsed)

    def _set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self._body.setVisible(not collapsed)
        if collapsed:
            self.setMinimumHeight(44)
            self.setMaximumHeight(44)
        else:
            self.setMinimumHeight(self._open_height)
            self.setMaximumHeight(16777215)
        self.updateGeometry()
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 42:
            self._set_collapsed(not self._collapsed)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer = QRectF(2.0, 16.0, max(1.0, self.width() - 4.0), max(1.0, self.height() - 18.0))
        tab_left = outer.left() + 14.0
        tab_right = min(outer.left() + 124.0, outer.right() - 36.0)
        tab_top = outer.top() - 13.0

        body = QPainterPath()
        body.moveTo(outer.left() + 14.0, outer.top())
        body.lineTo(tab_left - 9.0, outer.top())
        body.cubicTo(tab_left + 1.0, outer.top(), tab_left - 1.0, tab_top + 7.5, tab_left + 15.0, tab_top + 6.5)
        body.lineTo(tab_right - 16.0, tab_top + 6.5)
        body.cubicTo(tab_right - 1.0, tab_top + 6.5, tab_right - 6.0, outer.top(), tab_right + 16.0, outer.top())
        body.lineTo(outer.right() - 14.0, outer.top())
        body.quadTo(outer.right(), outer.top(), outer.right(), outer.top() + 14.0)
        body.lineTo(outer.right(), outer.bottom() - 14.0)
        body.quadTo(outer.right(), outer.bottom(), outer.right() - 14.0, outer.bottom())
        body.lineTo(outer.left() + 14.0, outer.bottom())
        body.quadTo(outer.left(), outer.bottom(), outer.left(), outer.bottom() - 14.0)
        body.lineTo(outer.left(), outer.top() + 14.0)
        body.quadTo(outer.left(), outer.top(), outer.left() + 14.0, outer.top())

        fill = QLinearGradient(outer.topLeft(), outer.bottomRight())
        fill.setColorAt(0.0, QColor("#ffffff"))
        fill.setColorAt(0.52, QColor("#eef8ff"))
        fill.setColorAt(1.0, QColor("#fff0c8"))
        painter.fillPath(body, fill)
        painter.setPen(QPen(QColor("#2d7eea"), 1.15))
        painter.drawPath(body)

        tab = QPainterPath()
        tab.moveTo(tab_left - 9.0, outer.top())
        tab.cubicTo(tab_left + 1.0, outer.top(), tab_left - 1.0, tab_top + 7.5, tab_left + 15.0, tab_top + 6.5)
        tab.lineTo(tab_right - 16.0, tab_top + 6.5)
        tab.cubicTo(tab_right - 1.0, tab_top + 6.5, tab_right - 6.0, outer.top(), tab_right + 16.0, outer.top())
        tab.cubicTo(tab_right - 2.0, outer.top() + 22.0, tab_left + 18.0, outer.top() + 23.0, tab_left - 9.0, outer.top())
        tab_fill = QLinearGradient(tab_left, tab_top, tab_right, outer.top() + 23.0)
        tab_fill.setColorAt(0.0, QColor("#0b63d8"))
        tab_fill.setColorAt(0.50, QColor("#168bff"))
        tab_fill.setColorAt(1.0, QColor("#0b4ab0"))
        painter.fillPath(tab, tab_fill)
        painter.setPen(QPen(QColor("#ffffff"), 0.5))
        painter.drawPath(tab)

        painter.setPen(QColor("#ffffff"))
        font = painter.font()
        font.setFamily("Times New Roman")
        font.setBold(True)
        font.setItalic(True)
        font.setPointSize(11)
        painter.setFont(font)
        arrow = "▾" if not self._collapsed else "▸"
        painter.drawText(QRectF(tab_left + 6.0, tab_top + 6.0, max(1.0, tab_right - tab_left - 8.0), 22.0), Qt.AlignmentFlag.AlignCenter, f"{self._title} {arrow}")
        painter.end()


def _unit_button(unit: str, checked: bool, callback) -> QPushButton:
    button = QPushButton(unit)
    button.setObjectName("FilePropertiesUnitChoice")
    button.setCheckable(True)
    button.setChecked(checked)
    button.setIcon(_radio_icon(checked))
    button.setIconSize(QSize(20, 20))
    _font(button, 10, italic=True, bold=True)
    button.setStyleSheet(
        "QPushButton#FilePropertiesUnitChoice {background:transparent; border:0; color:#223a58; text-align:left; padding:3px 5px;}"
        "QPushButton#FilePropertiesUnitChoice:hover {color:#0b63d8;}"
    )
    button.clicked.connect(callback)
    return button


def _unit_block(dialog, general: dict) -> _WaveSection:
    section = _WaveSection("Unit", dialog, collapsed=False, open_height=116)
    content = QWidget()
    content.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    grid = QGridLayout(content)
    grid.setContentsMargins(2, 0, 2, 0)
    grid.setHorizontalSpacing(10)
    grid.setVerticalSpacing(4)

    current = str(general.get("unit", "mm")) if str(general.get("unit", "mm")) in UNITS else "mm"
    buttons: dict[str, QPushButton] = {}

    def select_unit(selected: str) -> None:
        dialog.unit_combo.setCurrentText(selected)
        for key, button in buttons.items():
            active = key == selected
            button.setChecked(active)
            button.setIcon(_radio_icon(active))

    for index, unit in enumerate(UNITS):
        button = _unit_button(unit, unit == current, lambda checked=False, selected=unit: select_unit(selected))
        buttons[unit] = button
        grid.addWidget(button, index // 3, index % 3)

    section.add_body_widget(content)
    return section


def _placeholder_section(title: str, text: str, parent: QWidget) -> _WaveSection:
    section = _WaveSection(title, parent, collapsed=True, open_height=82)
    label = QLabel(text)
    label.setWordWrap(True)
    _font(label, 10, italic=True, bold=True)
    label.setStyleSheet("QLabel {background:transparent; color:#5d6f85; padding:2px 4px;}")
    section.add_body_widget(label)
    return section


def _clean_runtime_properties_panel(workspace) -> QWidget:
    panel = QWidget()
    panel.setObjectName("SidePanel")
    panel.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)

    title = QLabel("Properties")
    title.setObjectName("PanelTitle")
    layout.addWidget(title)

    empty = QLabel("No active selection.")
    empty.setObjectName("PanelItem")
    empty.setMinimumHeight(28)
    layout.addWidget(empty)

    hint = QLabel("Select a drawing tool, object, group, or layer to view and edit its properties here.")
    hint.setObjectName("PanelItem")
    hint.setWordWrap(True)
    hint.setMinimumHeight(76)
    layout.addWidget(hint)

    layout.addStretch(1)
    return panel


def apply_file_properties_general_patch() -> None:
    from . import workspace as edw
    from src.engineers_tools.app import engineering_properties_patch as epp

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_file_properties_general_patch", "") == PATCH_VERSION:
        return

    def general_page(self) -> QWidget:
        page = QWidget()
        page.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        general = self._settings.get("general", {})

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(list(UNITS))
        self.unit_combo.setCurrentText(str(general.get("unit", "mm")) if str(general.get("unit", "mm")) in UNITS else "mm")
        self.unit_combo.hide()

        self.grid_check = QCheckBox()
        self.grid_check.setChecked(bool(general.get("grid_enabled", True)))
        self.grid_check.hide()

        self.snap_check = QCheckBox()
        self.snap_check.setChecked(bool(general.get("snap_enabled", False)))
        self.snap_check.hide()

        self.grid_spacing = QDoubleSpinBox()
        self.grid_spacing.setRange(0.000001, 1000000.0)
        self.grid_spacing.setDecimals(6)
        self.grid_spacing.setValue(float(general.get("grid_spacing", 1.0) or 1.0))
        self.grid_spacing.hide()

        self.text_font = QFontComboBox()
        self.text_font.setCurrentText(str(general.get("text_font", "Times New Roman")))
        self.text_font.hide()

        self.text_size = QSpinBox()
        self.text_size.setRange(1, 300)
        self.text_size.setValue(int(general.get("text_size", 12) or 12))
        self.text_size.hide()

        hidden = QWidget()
        hidden_layout = QVBoxLayout(hidden)
        hidden_layout.setContentsMargins(0, 0, 0, 0)
        for widget in (self.unit_combo, self.grid_check, self.snap_check, self.grid_spacing, self.text_font, self.text_size):
            hidden_layout.addWidget(widget)
        hidden.hide()
        layout.addWidget(hidden)

        layout.addWidget(_unit_block(self, general))
        layout.addWidget(_placeholder_section("Font", "Font defaults will be defined here.", page))
        layout.addWidget(_placeholder_section("Snap", "Snap defaults will be defined here.", page))
        layout.addWidget(_placeholder_section("Page Setup", "Page setup defaults will be defined here.", page))
        layout.addStretch(1)
        return page

    def build_side_panel(self, title: str, rows: tuple[str, ...]) -> QWidget:
        if title == "Properties":
            return _clean_runtime_properties_panel(self)
        panel = QWidget()
        panel.setObjectName("SidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("PanelTitle")
        layout.addWidget(heading)
        for row in rows:
            item = QLabel(row)
            item.setObjectName("PanelItem")
            item.setMinimumHeight(28)
            layout.addWidget(item)
        layout.addStretch(1)
        return panel

    epp.PropertiesDialog._general_page = general_page
    edw.EngineeringDesignWorkspace._build_side_panel = build_side_panel
    edw.EngineeringDesignWorkspace._engineering_file_properties_general_patch = PATCH_VERSION

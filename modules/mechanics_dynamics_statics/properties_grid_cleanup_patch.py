"""Final cleanup for Properties blocks, ruler origin, and grid unit behavior."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-properties-grid-cleanup-2026-06-30-a"
UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "px": 25.4 / 96.0, "pt": 25.4 / 72.0, "in": 25.4}
UNIT_ORDER = ("mm", "cm", "m", "px", "pt", "in")


def _font(widget, size: int = 10, italic: bool = True, bold: bool = True) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setItalic(italic)
    font.setBold(bold)
    widget.setFont(font)


def _page_rect(canvas) -> QRectF:
    getter = getattr(canvas, "_page_rect", None)
    if callable(getter):
        return QRectF(getter())
    return QRectF(0, 0, max(1, canvas.width()), max(1, canvas.height()))


def _ruler_corner_origin(sb_module) -> QPointF:
    return QPointF(float(sb_module.RULER_THICKNESS), float(sb_module.RULER_THICKNESS))


def _unit_minor_step(unit: str) -> tuple[float, int]:
    if unit == "cm":
        return 0.1, 10  # 1 mm ticks, labels every 1 cm
    if unit == "m":
        return 0.1, 10
    if unit == "in":
        return 0.1, 10
    if unit == "pt":
        return 1.0, 12
    return 1.0, 10  # mm, px and fallback


def _format_ruler_label(index: int, minor_step: float, unit: str) -> str:
    value = index * minor_step
    if abs(value) < 1e-9:
        return "0"
    if unit in {"cm", "m", "in"}:
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        return text or "0"
    return str(int(round(value))) if abs(value - round(value)) < 1e-9 else f"{value:.2f}".rstrip("0").rstrip(".")


def _arrow_icon(direction: str) -> QIcon:
    pixmap = QPixmap(20, 9)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor("#ffffff"), 0.9))
    painter.setBrush(QColor("#132238"))
    points = QPolygonF([QPointF(10, 1), QPointF(18, 8), QPointF(2, 8)]) if direction == "up" else QPolygonF([QPointF(2, 1), QPointF(18, 1), QPointF(10, 8)])
    painter.drawPolygon(points)
    painter.end()
    return QIcon(pixmap)


def _arrow_button(direction: str) -> QPushButton:
    button = QPushButton()
    button.setObjectName("GeometryArrowButton")
    button.setFixedSize(22, 10)
    button.setIcon(_arrow_icon(direction))
    button.setIconSize(QSize(18, 8))
    button.setStyleSheet(
        "QPushButton#GeometryArrowButton {background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fff9de, stop:1 #ffc35a); border:1px solid #7e5b10; border-radius:4px; padding:0px;}"
        "QPushButton#GeometryArrowButton:hover {background:#ff8a35; border-color:#ffffff;}"
        "QPushButton#GeometryArrowButton:pressed {background:#d46a16;}"
    )
    return button


def _radio_icon(checked: bool) -> QIcon:
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor("#18314f"), 1.7))
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(QPointF(9, 9), 6.4, 6.4)
    if checked:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2f7df6"))
        painter.drawEllipse(QPointF(9, 9), 3.8, 3.8)
    painter.end()
    return QIcon(pixmap)


def _numeric_control(suffix: str = "") -> QWidget:
    control = QWidget()
    control.setFixedHeight(24)
    layout = QHBoxLayout(control)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)

    spin = QDoubleSpinBox()
    spin.setObjectName("GeometrySpin")
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    spin.setRange(-1000000.0, 1000000.0)
    spin.setDecimals(3)
    spin.setSingleStep(1.0)
    spin.setValue(0.0)
    spin.setSuffix(suffix)
    spin.setFixedHeight(23)
    _font(spin, 9, italic=False, bold=True)
    spin.setStyleSheet("QDoubleSpinBox#GeometrySpin {background:#fff9de; border:1px solid #b38621; border-radius:7px; color:#132238; padding:1px 5px;}")
    layout.addWidget(spin, 1)

    arrows = QWidget()
    arrows_layout = QVBoxLayout(arrows)
    arrows_layout.setContentsMargins(0, 0, 0, 0)
    arrows_layout.setSpacing(1)
    up = _arrow_button("up")
    down = _arrow_button("down")
    up.clicked.connect(spin.stepUp)
    down.clicked.connect(spin.stepDown)
    arrows_layout.addWidget(up)
    arrows_layout.addWidget(down)
    layout.addWidget(arrows)
    return control


def _row(label_text: str, editor: QWidget) -> QWidget:
    row = QWidget()
    row.setObjectName("GeometryRow")
    row.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    layout = QHBoxLayout(row)
    layout.setContentsMargins(3, 1, 3, 1)
    layout.setSpacing(5)
    label = QLabel(label_text)
    label.setObjectName("GeometryLabel")
    label.setFixedWidth(44)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    _font(label, 10, italic=label_text not in {"X", "Y"}, bold=True)
    layout.addWidget(label)
    layout.addWidget(editor, 1)
    return row


class _WaveSection(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None, *, collapsed: bool = False, min_open_height: int = 118) -> None:
        super().__init__(parent)
        self._title = title
        self._collapsed = False
        self._min_open_height = min_open_height
        self.setObjectName("WavePropertiesSection")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(9, 38, 9, 8)
        self._root.setSpacing(4)
        self._body = QWidget(self)
        self._body.setObjectName("WaveSectionBody")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(4)
        self._root.addWidget(self._body)
        self.setStyleSheet("QFrame#WavePropertiesSection {background:transparent; border:0;} QWidget#WaveSectionBody {background:transparent; border:0;}")
        self._set_collapsed(collapsed)

    def add_body_widget(self, widget: QWidget) -> None:
        self._body_layout.addWidget(widget)
        self._set_collapsed(self._collapsed)

    def _set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self._body.setVisible(not collapsed)
        if collapsed:
            self.setMinimumHeight(42)
            self.setMaximumHeight(42)
        else:
            self.setMinimumHeight(self._min_open_height)
            self.setMaximumHeight(16777215)
        self.updateGeometry()
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 40:
            self._set_collapsed(not self._collapsed)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        outer = QRectF(2.0, 15.0, max(1.0, self.width() - 4.0), max(1.0, self.height() - 17.0))
        tab_left = outer.left() + 12.0
        tab_right = min(outer.left() + 112.0, outer.right() - 30.0)
        tab_top = outer.top() - 12.0

        body = QPainterPath()
        body.moveTo(outer.left() + 13.0, outer.top())
        body.lineTo(tab_left - 8.0, outer.top())
        body.cubicTo(tab_left + 1.0, outer.top(), tab_left - 1.0, tab_top + 7.0, tab_left + 14.0, tab_top + 6.0)
        body.lineTo(tab_right - 15.0, tab_top + 6.0)
        body.cubicTo(tab_right - 1.0, tab_top + 6.0, tab_right - 6.0, outer.top(), tab_right + 15.0, outer.top())
        body.lineTo(outer.right() - 13.0, outer.top())
        body.quadTo(outer.right(), outer.top(), outer.right(), outer.top() + 13.0)
        body.lineTo(outer.right(), outer.bottom() - 13.0)
        body.quadTo(outer.right(), outer.bottom(), outer.right() - 13.0, outer.bottom())
        body.lineTo(outer.left() + 13.0, outer.bottom())
        body.quadTo(outer.left(), outer.bottom(), outer.left(), outer.bottom() - 13.0)
        body.lineTo(outer.left(), outer.top() + 13.0)
        body.quadTo(outer.left(), outer.top(), outer.left() + 13.0, outer.top())
        fill = QLinearGradient(outer.topLeft(), outer.bottomRight())
        fill.setColorAt(0.0, QColor("#ffffff"))
        fill.setColorAt(0.55, QColor("#eef8ff"))
        fill.setColorAt(1.0, QColor("#fff0c8"))
        painter.fillPath(body, fill)
        painter.setPen(QPen(QColor("#2d7eea"), 1.1))
        painter.drawPath(body)

        tab = QPainterPath()
        tab.moveTo(tab_left - 8.0, outer.top())
        tab.cubicTo(tab_left + 1.0, outer.top(), tab_left - 1.0, tab_top + 7.0, tab_left + 14.0, tab_top + 6.0)
        tab.lineTo(tab_right - 15.0, tab_top + 6.0)
        tab.cubicTo(tab_right - 1.0, tab_top + 6.0, tab_right - 6.0, outer.top(), tab_right + 15.0, outer.top())
        tab.cubicTo(tab_right - 2.0, outer.top() + 21.0, tab_left + 17.0, outer.top() + 22.0, tab_left - 8.0, outer.top())
        tab_fill = QLinearGradient(tab_left, tab_top, tab_right, outer.top() + 22.0)
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


class _GeometrySection(_WaveSection):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Geometry", parent, collapsed=False, min_open_height=148)
        legend = QLineEdit()
        legend.setObjectName("GeometryLegendInput")
        legend.setPlaceholderText("Legend")
        legend.setFixedHeight(23)
        legend.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        _font(legend, 9, italic=False, bold=True)
        legend.setStyleSheet("QLineEdit#GeometryLegendInput {background:#fff9de; border:1px solid #b38621; border-radius:7px; color:#132238; padding:1px 5px;}")
        self.add_body_widget(_row("Legend", legend))
        self.add_body_widget(_row("X", _numeric_control(" mm")))
        self.add_body_widget(_row("Y", _numeric_control(" mm")))
        self.add_body_widget(_row("Angle", _numeric_control(" °")))


def _unit_button(label: str, checked: bool, callback) -> QPushButton:
    button = QPushButton(label)
    button.setObjectName("UnitRadioChoice")
    button.setCheckable(True)
    button.setChecked(checked)
    button.setIcon(_radio_icon(checked))
    button.setIconSize(QSize(18, 18))
    _font(button, 9, italic=True, bold=True)
    button.setStyleSheet(
        "QPushButton#UnitRadioChoice {background:transparent; border:0; color:#223a58; text-align:left; padding:2px 3px;}"
        "QPushButton#UnitRadioChoice:hover {color:#0b63d8;}"
    )
    button.clicked.connect(callback)
    return button


def _unit_grid_widget(host, title: str) -> QWidget:
    wrapper = QWidget()
    wrapper.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(2, 0, 2, 0)
    layout.setSpacing(2)
    label = QLabel(title)
    _font(label, 9, italic=True, bold=True)
    label.setStyleSheet("QLabel {background:transparent; color:#223a58;}")
    layout.addWidget(label)
    grid = QGridLayout()
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(2)
    grid.setVerticalSpacing(1)
    start_bar = getattr(host, "_start_bar_widget", None)
    current = getattr(start_bar, "_unit", "mm") if start_bar is not None else "mm"
    for index, unit in enumerate(UNIT_ORDER):
        button = _unit_button(unit, unit == current, lambda checked=False, selected=unit: getattr(start_bar, "_set_unit", lambda _u: None)(selected))
        grid.addWidget(button, index // 3, index % 3)
    layout.addLayout(grid)
    return wrapper


def _placeholder(text: str) -> QWidget:
    label = QLabel(text)
    _font(label, 9, italic=True, bold=True)
    label.setWordWrap(True)
    label.setStyleSheet("QLabel {background:transparent; color:#5d6f85; padding:2px 4px;}")
    return label


def apply_properties_grid_cleanup_patch() -> None:
    from . import workspace as edw
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_properties_grid_cleanup_patch", "") == PATCH_VERSION:
        return

    original_build_side_panel = edw.EngineeringDesignWorkspace._build_side_panel
    original_ensure_hooks = sb.StartBar._ensure_canvas_hooks
    original_set_ruler = sb.StartBar._set_ruler

    def build_side_panel(self, title: str, rows: tuple[str, ...]) -> QWidget:
        if title != "Properties":
            return original_build_side_panel(self, title, rows)
        panel = QWidget()
        panel.setObjectName("SidePanel")
        panel.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        heading = QLabel("Properties")
        heading.setObjectName("PanelTitle")
        _font(heading, 11, italic=True, bold=True)
        layout.addWidget(heading)

        layout.addWidget(_GeometrySection(panel))

        general = _WaveSection("General", panel, collapsed=False, min_open_height=150)
        general.add_body_widget(_unit_grid_widget(self, "Unit"))
        general.add_body_widget(_unit_grid_widget(self, "Grid Unit"))
        layout.addWidget(general)

        font_section = _WaveSection("Font", panel, collapsed=True, min_open_height=82)
        font_section.add_body_widget(_placeholder("Font settings will be defined here."))
        layout.addWidget(font_section)

        snap_section = _WaveSection("Snap", panel, collapsed=True, min_open_height=82)
        snap_section.add_body_widget(_placeholder("Snap settings will be defined here."))
        layout.addWidget(snap_section)

        page_section = _WaveSection("Page Setup", panel, collapsed=True, min_open_height=82)
        page_section.add_body_widget(_placeholder("Page setup shortcuts will be defined here."))
        layout.addWidget(page_section)

        layout.addStretch(1)
        return panel

    def ruler_origin(self) -> None:
        self._ruler_origin = _ruler_corner_origin(sb)
        self._ruler_corner_origin_active = False
        self._ruler_previous_origin = None
        self._ruler_previous_origin_custom = False

    def toggle_ruler_corner_origin(self) -> None:
        if self._ruler_corner_origin_active:
            previous = QPointF(self._ruler_previous_origin) if self._ruler_previous_origin is not None else _ruler_corner_origin(sb)
            previous_custom = self._ruler_previous_origin_custom
            self._ruler_corner_origin_active = False
            self._ruler_previous_origin = None
            self._ruler_previous_origin_custom = False
            self._set_ruler_origin(previous, custom=previous_custom)
            return
        self._ruler_previous_origin = QPointF(self._ruler_origin)
        self._ruler_previous_origin_custom = self._ruler_origin_custom
        self._ruler_corner_origin_active = True
        self._set_ruler_origin(_ruler_corner_origin(sb), custom=True)

    def ensure_hooks(self) -> None:
        original_ensure_hooks(self)
        canvas = self._canvas()
        if canvas is None:
            return

        def paint_grid(canvas_self, painter: QPainter) -> None:
            if not getattr(canvas_self, "_grid_visible", True):
                return
            page = _page_rect(canvas_self)
            unit = getattr(self, "_unit", "mm")
            spacing_value = max(0.000001, float(getattr(self, "_grid_spacing", 1.0)))
            spacing = max(1.0, min(self._unit_to_canvas_px(spacing_value, unit), 10000.0))
            origin = QPointF(getattr(self, "_ruler_origin", _ruler_corner_origin(sb)))
            painter.save()
            painter.setClipRect(page)
            minor = QPen(QColor(70, 96, 130, 42), 1)
            major = QPen(QColor(39, 74, 116, 72), 1)
            first_x = origin.x() + math.floor((page.left() - origin.x()) / spacing) * spacing
            x = first_x
            while x <= page.right() + 0.5:
                index = int(round((x - origin.x()) / spacing))
                painter.setPen(major if index % 10 == 0 else minor)
                painter.drawLine(QPointF(x, page.top()), QPointF(x, page.bottom()))
                x += spacing
            first_y = origin.y() + math.floor((page.top() - origin.y()) / spacing) * spacing
            y = first_y
            while y <= page.bottom() + 0.5:
                index = int(round((y - origin.y()) / spacing))
                painter.setPen(major if index % 10 == 0 else minor)
                painter.drawLine(QPointF(page.left(), y), QPointF(page.right(), y))
                y += spacing
            painter.restore()

        canvas._paint_grid = paint_grid.__get__(canvas, canvas.__class__)
        canvas._grid_spacing = self._grid_spacing
        canvas._grid_unit = self._unit

    def set_unit(self, unit: str) -> None:
        if unit not in UNIT_TO_MM:
            return
        self._unit = unit
        self._grid_spacing = 1.0
        self._apply_unit_to_host()
        ensure_hooks(self)
        self._apply_grid_to_host()
        if getattr(self, "_ruler_enabled", False):
            if not getattr(self, "_ruler_origin_custom", False) or getattr(self, "_ruler_corner_origin_active", False):
                self._ruler_origin = _ruler_corner_origin(sb)
            self._sync_rulers()
        self.unit_changed.emit(unit)
        self.grid_changed.emit(self._grid_enabled, self._grid_spacing, self._unit)
        self.tool_requested.emit(f"unit_{unit}")
        self._refresh_tooltips()
        if getattr(self, "_popup", None) is not None:
            self._popup.close()

    def set_ruler(self, enabled: bool) -> None:
        original_set_ruler(self, enabled)
        if enabled and (not getattr(self, "_ruler_origin_custom", False) or getattr(self, "_ruler_corner_origin_active", False)):
            self._ruler_origin = _ruler_corner_origin(sb)
            self._sync_rulers()

    def ruler_paint(self, event) -> None:  # noqa: ARG001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(20, 37, 58, 230))
        unit = getattr(self._start_bar, "_unit", "mm")
        minor_value, major_every = _unit_minor_step(unit)
        spacing = max(1.0, self._start_bar._unit_to_canvas_px(minor_value, unit))
        length = self.width() if self._orientation == "top" else self.height()
        zero = self._start_bar._ruler_origin.x() - self.x() if self._orientation == "top" else self._start_bar._ruler_origin.y() - self.y()
        font = painter.font()
        font.setFamily("Times New Roman")
        font.setPointSize(7)
        font.setBold(True)
        font.setItalic(False)
        painter.setFont(font)
        start_index = math.floor((0 - zero) / spacing) - 2
        index = start_index
        while True:
            position = zero + index * spacing
            if position > length + spacing:
                break
            if position >= 0:
                tick = 23 if index % major_every == 0 else 14 if index % max(1, major_every // 2) == 0 else 8
                painter.setPen(QPen(QColor("#ffffff"), 1.0))
                if self._orientation == "top":
                    painter.drawLine(QPointF(position, self.height()), QPointF(position, self.height() - tick))
                    if index % major_every == 0:
                        painter.drawText(QRectF(position + 2, 1, 54, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, _format_ruler_label(index, minor_value, unit))
                else:
                    painter.drawLine(QPointF(self.width(), position), QPointF(self.width() - tick, position))
                    if index % major_every == 0:
                        painter.drawText(QRectF(2, position + 1, self.width() - 4, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, _format_ruler_label(index, minor_value, unit))
            index += 1
        painter.end()

    edw.EngineeringDesignWorkspace._build_side_panel = build_side_panel
    sb.StartBar._center_ruler_origin = ruler_origin
    sb.StartBar._toggle_ruler_corner_origin = toggle_ruler_corner_origin
    sb.StartBar._ensure_canvas_hooks = ensure_hooks
    sb.StartBar._set_unit = set_unit
    sb.StartBar._set_ruler = set_ruler
    sb._RulerOverlay.paintEvent = ruler_paint
    edw.EngineeringDesignWorkspace._engineering_properties_grid_cleanup_patch = PATCH_VERSION

"""Final unit, ruler, grid, Page Setup unit, SVG quality, and Geometry panel fixes."""

from __future__ import annotations

import base64
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-unit-grid-properties-final-2026-06-30-a"
UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "px": 25.4 / 96.0, "pt": 25.4 / 72.0, "in": 25.4}
UNIT_DECIMALS = {"mm": 2, "cm": 3, "m": 5, "px": 2, "pt": 2, "in": 4}


def _current_unit(workspace) -> str:
    start_bar = getattr(workspace, "_start_bar_widget", None)
    unit = str(getattr(start_bar, "_unit", "mm") if start_bar is not None else "mm")
    return unit if unit in UNIT_TO_MM else "mm"


def _page_rect(canvas) -> QRectF:
    getter = getattr(canvas, "_page_rect", None)
    if callable(getter):
        return QRectF(getter())
    return QRectF(0, 0, max(1, canvas.width()), max(1, canvas.height()))


def _default_ruler_origin(start_bar) -> QPointF:
    canvas = start_bar._canvas() if hasattr(start_bar, "_canvas") else None
    if canvas is None:
        return QPointF(0, 0)
    return QPointF(_page_rect(canvas).topLeft())


def _convert_mm_to_unit(value_mm: float, unit: str) -> float:
    return float(value_mm) / UNIT_TO_MM.get(unit, 1.0)


def _convert_unit_to_mm(value: float, unit: str) -> float:
    return float(value) * UNIT_TO_MM.get(unit, 1.0)


def _set_spin_display(spin: QDoubleSpinBox, value_mm: float, unit: str) -> None:
    spin.blockSignals(True)
    spin.setDecimals(UNIT_DECIMALS.get(unit, 2))
    spin.setSuffix(f" {unit}")
    spin.setValue(_convert_mm_to_unit(value_mm, unit))
    spin.blockSignals(False)


def _refresh_page_size_spins(dialog, unit: str) -> None:
    if not hasattr(dialog, "_custom_size_spins"):
        return
    size = dialog.PAPER_SIZES.get(getattr(dialog, "_paper_name", "Workspace"), dialog.PAPER_SIZES.get("Workspace", (400.0, 220.0)))
    width_mm, height_mm = float(size[0]), float(size[1])
    landscape = bool(getattr(dialog, "_landscape", True))
    if landscape and height_mm > width_mm:
        width_mm, height_mm = height_mm, width_mm
    if not landscape and width_mm > height_mm:
        width_mm, height_mm = height_mm, width_mm
    for key, value in (("width", width_mm), ("height", height_mm)):
        spin = dialog._custom_size_spins.get(key)
        if spin is not None:
            _set_spin_display(spin, value, unit)


def _refresh_paper_combo_labels(dialog, unit: str) -> None:
    combo = getattr(dialog, "_paper_combo", None)
    if combo is None:
        return
    blocked = combo.blockSignals(True)
    try:
        for index in range(combo.count()):
            name = combo.itemData(index)
            if not isinstance(name, str):
                continue
            width_mm, height_mm = dialog.PAPER_SIZES.get(name, (0.0, 0.0))
            width = _convert_mm_to_unit(width_mm, unit)
            height = _convert_mm_to_unit(height_mm, unit)
            combo.setItemText(index, f"{name}  {width:.3f} × {height:.3f} {unit}".replace(".000", ""))
    finally:
        combo.blockSignals(blocked)


def _apply_unit_to_page_dialog(dialog, unit: str) -> None:
    dialog._display_unit = unit
    _refresh_paper_combo_labels(dialog, unit)
    _refresh_page_size_spins(dialog, unit)
    for spin in getattr(dialog, "_margin_spins", {}).values():
        _set_spin_display(spin, spin.value(), unit)
    original_update_preview = getattr(dialog, "_update_preview", None)

    def update_preview() -> None:
        margins = (
            _convert_unit_to_mm(dialog._margin_spins.get("top").value(), unit) if "top" in dialog._margin_spins else 10.0,
            _convert_unit_to_mm(dialog._margin_spins.get("right").value(), unit) if "right" in dialog._margin_spins else 10.0,
            _convert_unit_to_mm(dialog._margin_spins.get("bottom").value(), unit) if "bottom" in dialog._margin_spins else 10.0,
            _convert_unit_to_mm(dialog._margin_spins.get("left").value(), unit) if "left" in dialog._margin_spins else 10.0,
        )
        size = dialog.PAPER_SIZES.get(getattr(dialog, "_paper_name", "Workspace"), dialog.PAPER_SIZES.get("Workspace", (400.0, 220.0)))
        if getattr(dialog, "_paper_name", "") == "Custom":
            size = (
                _convert_unit_to_mm(dialog._custom_size_spins["width"].value(), unit),
                _convert_unit_to_mm(dialog._custom_size_spins["height"].value(), unit),
            )
        dialog._preview.set_state(size, bool(getattr(dialog, "_landscape", True)), margins, getattr(dialog, "_position", (1, 1)))

    dialog._update_preview = update_preview
    paper_combo = getattr(dialog, "_paper_combo", None)
    if paper_combo is not None:
        paper_combo.currentIndexChanged.connect(lambda _index=0: _refresh_page_size_spins(dialog, unit))
    for button in getattr(dialog, "_orientation_buttons", ()):
        button.clicked.connect(lambda _checked=False: _refresh_page_size_spins(dialog, unit))
    if callable(original_update_preview):
        dialog._update_preview()


def _runtime_state_from_dialog(dialog, unit: str) -> dict[str, object]:
    if getattr(dialog, "_paper_name", "") == "Custom":
        paper_size = [
            _convert_unit_to_mm(dialog._custom_size_spins["width"].value(), unit),
            _convert_unit_to_mm(dialog._custom_size_spins["height"].value(), unit),
        ]
    else:
        paper_size = list(dialog._current_paper_size())
    return {
        "paper_name": dialog._paper_name,
        "paper_size": paper_size,
        "landscape": bool(dialog._landscape),
        "margins": [
            _convert_unit_to_mm(dialog._margin_spins.get("top").value(), unit) if "top" in dialog._margin_spins else 10.0,
            _convert_unit_to_mm(dialog._margin_spins.get("right").value(), unit) if "right" in dialog._margin_spins else 10.0,
            _convert_unit_to_mm(dialog._margin_spins.get("bottom").value(), unit) if "bottom" in dialog._margin_spins else 10.0,
            _convert_unit_to_mm(dialog._margin_spins.get("left").value(), unit) if "left" in dialog._margin_spins else 10.0,
        ],
        "position": list(getattr(dialog, "_position", (1, 1))),
        "dpi": int(dialog._custom_dpi.value()) if hasattr(dialog, "_custom_dpi") else 600,
        "unit": unit,
    }


def _export_state_from_runtime(state: dict[str, object], unit: str) -> dict[str, object]:
    paper_size = state.get("paper_size", [400.0, 220.0])
    width_mm = float(paper_size[0]) if isinstance(paper_size, (list, tuple)) and len(paper_size) >= 2 else 400.0
    height_mm = float(paper_size[1]) if isinstance(paper_size, (list, tuple)) and len(paper_size) >= 2 else 220.0
    landscape = bool(state.get("landscape", True))
    if landscape and height_mm > width_mm:
        width_mm, height_mm = height_mm, width_mm
    if not landscape and width_mm > height_mm:
        width_mm, height_mm = height_mm, width_mm
    margins = state.get("margins", [10.0, 10.0, 10.0, 10.0])
    if not isinstance(margins, (list, tuple)) or len(margins) < 4:
        margins = [10.0, 10.0, 10.0, 10.0]
    position_lookup = {
        (0, 0): "Top Left", (1, 0): "Top", (2, 0): "Top Right",
        (0, 1): "Left", (1, 1): "Center", (2, 1): "Right",
        (0, 2): "Bottom Left", (1, 2): "Bottom", (2, 2): "Bottom Right",
    }
    position_raw = state.get("position", [1, 1])
    try:
        position_key = tuple(int(v) for v in position_raw[:2])
    except Exception:
        position_key = (1, 1)
    return {
        "paper": str(state.get("paper_name", "Workspace")),
        "orientation": "Landscape" if landscape else "Portrait",
        "width_mm": width_mm,
        "height_mm": height_mm,
        "dpi": int(state.get("dpi", 600) or 600),
        "unit": unit,
        "margins_mm": {"top": float(margins[0]), "right": float(margins[1]), "bottom": float(margins[2]), "left": float(margins[3])},
        "position": position_lookup.get(position_key, "Center"),
    }


def _arrow_icon(direction: str) -> QIcon:
    pixmap = QPixmap(22, 10)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor("#ffffff"), 0.9))
    painter.setBrush(QColor("#132238"))
    points = QPolygonF([QPointF(11, 1), QPointF(20, 9), QPointF(2, 9)]) if direction == "up" else QPolygonF([QPointF(2, 1), QPointF(20, 1), QPointF(11, 9)])
    painter.drawPolygon(points)
    painter.end()
    return QIcon(pixmap)


def _arrow_button(direction: str) -> QPushButton:
    button = QPushButton()
    button.setObjectName("GeometryArrowButton")
    button.setFixedSize(24, 10)
    button.setIcon(_arrow_icon(direction))
    button.setIconSize(QSize(18, 8))
    button.setStyleSheet(
        "QPushButton#GeometryArrowButton {background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fff9de, stop:1 #ffc35a); border:1px solid #7e5b10; border-radius:4px; padding:0px;}"
        "QPushButton#GeometryArrowButton:hover {background:#ff8a35; border-color:#ffffff;}"
        "QPushButton#GeometryArrowButton:pressed {background:#d46a16; padding-top:1px;}"
    )
    return button


def _geometry_font(widget, point_size: int = 10) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setBold(True)
    font.setItalic(True)
    font.setPointSize(point_size)
    widget.setFont(font)


def _numeric_control(suffix: str = "") -> QWidget:
    control = QWidget()
    control.setObjectName("GeometryNumericControl")
    control.setFixedHeight(26)
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
    spin.setFixedHeight(25)
    _geometry_font(spin, 9)
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
    layout = QHBoxLayout(row)
    layout.setContentsMargins(7, 1, 7, 1)
    layout.setSpacing(6)
    label = QLabel(label_text)
    label.setObjectName("GeometryLabel")
    label.setFixedWidth(48)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    _geometry_font(label, 10)
    layout.addWidget(label)
    layout.addWidget(editor, 1)
    row.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    return row


class _CompactWaveGeometrySection(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        self._collapsed = False
        self.setObjectName("WaveGeometrySection")
        self.setMinimumHeight(162)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 42, 10, 9)
        root.setSpacing(4)
        self._body = QWidget(self)
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(4)
        legend = QLineEdit()
        legend.setObjectName("GeometryLegendInput")
        legend.setPlaceholderText("Legend")
        legend.setFixedHeight(25)
        legend.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        _geometry_font(legend, 10)
        body_layout.addWidget(_row("Legend", legend))
        body_layout.addWidget(_row("X", _numeric_control(" mm")))
        body_layout.addWidget(_row("Y", _numeric_control(" mm")))
        body_layout.addWidget(_row("Angle", _numeric_control(" °")))
        root.addWidget(self._body)
        self.setStyleSheet(
            "QLineEdit#GeometryLegendInput {background:#fff9de; border:1px solid #b38621; border-radius:7px; color:#132238; padding:1px 6px;}"
            "QWidget#GeometryRow {background:rgba(255,255,255,150); border:1px solid rgba(137,165,198,95); border-radius:7px;}"
            "QLabel#GeometryLabel {background:transparent; color:#223a58;}"
        )

    def _set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self._body.setVisible(not collapsed)
        if collapsed:
            self.setMinimumHeight(44)
            self.setMaximumHeight(44)
        else:
            self.setMinimumHeight(162)
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
        tab_right = min(outer.left() + 124.0, outer.right() - 35.0)
        tab_top = outer.top() - 14.0
        body = QPainterPath()
        body.moveTo(outer.left() + 14.0, outer.top())
        body.lineTo(tab_left - 9.0, outer.top())
        body.cubicTo(tab_left + 1.0, outer.top(), tab_left - 1.0, tab_top + 8.0, tab_left + 15.0, tab_top + 7.0)
        body.lineTo(tab_right - 16.0, tab_top + 7.0)
        body.cubicTo(tab_right - 1.0, tab_top + 7.0, tab_right - 6.0, outer.top(), tab_right + 16.0, outer.top())
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
        painter.setPen(QPen(QColor("#2d7eea"), 1.2))
        painter.drawPath(body)
        tab = QPainterPath()
        tab.moveTo(tab_left - 9.0, outer.top())
        tab.cubicTo(tab_left + 1.0, outer.top(), tab_left - 1.0, tab_top + 8.0, tab_left + 15.0, tab_top + 7.0)
        tab.lineTo(tab_right - 16.0, tab_top + 7.0)
        tab.cubicTo(tab_right - 1.0, tab_top + 7.0, tab_right - 6.0, outer.top(), tab_right + 16.0, outer.top())
        tab.cubicTo(tab_right - 2.0, outer.top() + 24.0, tab_left + 18.0, outer.top() + 25.0, tab_left - 9.0, outer.top())
        tab_fill = QLinearGradient(tab_left, tab_top, tab_right, outer.top() + 24.0)
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
        font.setPointSize(12)
        painter.setFont(font)
        arrow = "▾" if not self._collapsed else "▸"
        painter.drawText(QRectF(tab_left + 7.0, tab_top + 7.0, max(1.0, tab_right - tab_left - 10.0), 23.0), Qt.AlignmentFlag.AlignCenter, f"{self._title} {arrow}")
        painter.end()


def _high_quality_svg(workspace) -> str:
    from . import file_export_project_fixes as fixes

    canvas = getattr(workspace, "_canvas", None)
    if canvas is None:
        return '<svg xmlns="http://www.w3.org/2000/svg"/>\n'
    fixes._apply_page_setup_to_canvas(workspace)
    width_mm, height_mm = fixes._page_size_mm(canvas)
    options = getattr(workspace, "_save_options", {}) or {}
    remove_white = bool(options.get("remove_white_background", False))
    objects = [obj for obj in getattr(canvas, "objects", []) if getattr(obj, "visible", True)]
    source = fixes._content_bounds(canvas, objects)
    printable = fixes._printable_rect(canvas, QRectF(0, 0, width_mm, height_mm))
    placed = fixes._placed_target(printable, source, str(getattr(canvas, "_page_setup_position", None) or "Center"))
    scale = placed.width() / max(1.0, source.width()) if objects else 1.0
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:.3f}mm" height="{height_mm:.3f}mm" viewBox="0 0 {width_mm:.3f} {height_mm:.3f}">']
    if not remove_white:
        parts.append(f'<rect x="0" y="0" width="{width_mm:.3f}" height="{height_mm:.3f}" fill="white"/>')
    for obj in objects:
        rect = QRectF(getattr(obj, "rect", QRectF()))
        x = placed.left() + (rect.left() - source.left()) * scale
        y = placed.top() + (rect.top() - source.top()) * scale
        width = rect.width() * scale
        height = rect.height() * scale
        cx = x + width / 2.0
        cy = y + height / 2.0
        angle = float(getattr(obj, "rotation", 0.0))
        pixmap = getattr(obj, "pixmap", QPixmap())
        raw_href = ""
        path = Path(str(getattr(obj, "path", "")))
        if not remove_white and path.exists() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
            raw_href = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
        elif isinstance(pixmap, QPixmap) and not pixmap.isNull():
            image = fixes._white_to_transparent_image(pixmap) if remove_white else pixmap.toImage()
            raw_href = "data:image/png;base64," + fixes._png_base64_from_image(image)
        parts.append(f'<g transform="rotate({angle:.6f} {cx:.6f} {cy:.6f})">')
        if raw_href:
            parts.append(f'<image x="{x:.6f}" y="{y:.6f}" width="{width:.6f}" height="{height:.6f}" href="{raw_href}" preserveAspectRatio="none"/>')
        parts.append("</g>")
    parts.append("</svg>\n")
    return "".join(parts)


def apply_unit_grid_properties_final_patch() -> None:
    from . import file_export_project_fixes as fixes
    from . import workspace as edw
    from src.engineers_tools.app import engineering_fixed_viewport_patch as fixed_viewport
    from src.engineers_tools.app import runtime_ui_patch as rtp
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_unit_grid_properties_final_patch", "") == PATCH_VERSION:
        return

    original_init = edw.EngineeringDesignWorkspace.__init__
    original_build_side_panel = edw.EngineeringDesignWorkspace._build_side_panel
    original_start_set_unit = sb.StartBar._set_unit
    original_set_ruler = sb.StartBar._set_ruler
    original_ensure_hooks = sb.StartBar._ensure_canvas_hooks

    def apply_page_setup_to_canvas(workspace, state=None):
        unit = _current_unit(workspace)
        runtime_state = state if isinstance(state, dict) else getattr(workspace, "_page_setup_state", None)
        if not isinstance(runtime_state, dict):
            runtime_state = {"paper_name": "Workspace", "paper_size": [400.0, 220.0], "landscape": True, "margins": [10.0, 10.0, 10.0, 10.0], "position": [1, 1], "dpi": 600, "unit": unit}
        export_state = _export_state_from_runtime(runtime_state, unit)
        canvas = getattr(workspace, "_canvas", None)
        if canvas is not None:
            canvas._page_setup_size_mm = (float(export_state["width_mm"]), float(export_state["height_mm"]))
            canvas._page_setup_dpi = int(export_state["dpi"])
            canvas._page_setup_position = str(export_state["position"])
            canvas._page_setup_margins_mm = dict(export_state["margins_mm"])
            m = export_state["margins_mm"]
            canvas._page_setup_margins = (m["top"], m["right"], m["bottom"], m["left"])
            canvas._page_setup_unit = unit
        workspace._page_setup_state = dict(runtime_state, unit=unit)
        return export_state

    def init(self, module) -> None:
        original_init(self, module)
        apply_page_setup_to_canvas(self)

    def page_setup(self) -> None:
        unit = _current_unit(self)
        canvas = getattr(self, "_canvas", None)
        shadow = self.__dict__.get("_page_setup")
        if isinstance(shadow, dict):
            del self.__dict__["_page_setup"]
        dialog = rtp.PageSetupDialog(self)
        if canvas is not None:
            fixed_viewport._apply_state_to_page_setup_dialog(dialog, fixed_viewport._page_setup_state(self, canvas))
        _apply_unit_to_page_dialog(dialog, unit)
        if dialog.exec() == dialog.DialogCode.Accepted:
            state = _runtime_state_from_dialog(dialog, unit)
            if canvas is not None:
                fixed_viewport._apply_page_setup_state(self, canvas, state)
                canvas.update()
            self._page_setup_state = state
            apply_page_setup_to_canvas(self, state)
            self._set_status(f"Page Setup applied: {state['paper_name']} {state['dpi']} DPI | unit {unit}")
            return
        self._set_status("Page Setup canceled")

    def build_side_panel(self, title: str, rows: tuple[str, ...]) -> QWidget:
        if title != "Properties":
            return original_build_side_panel(self, title, rows)
        panel = QWidget()
        panel.setObjectName("SidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        heading = QLabel("Properties")
        heading.setObjectName("PanelTitle")
        layout.addWidget(heading)
        layout.addWidget(_CompactWaveGeometrySection("Geometry", panel))
        layout.addStretch(1)
        return panel

    def center_ruler_origin(self) -> None:
        self._ruler_origin = _default_ruler_origin(self)
        self._ruler_corner_origin_active = False
        self._ruler_previous_origin = None
        self._ruler_previous_origin_custom = False

    def ensure_hooks(self) -> None:
        original_ensure_hooks(self)
        canvas = self._canvas()
        if canvas is None:
            return

        def paint_grid(canvas_self, painter: QPainter) -> None:
            if not getattr(canvas_self, "_grid_visible", True):
                return
            page = _page_rect(canvas_self)
            spacing = max(1.0, min(self._unit_to_canvas_px(float(getattr(self, "_grid_spacing", 1.0)), getattr(self, "_unit", "mm")), 10000.0))
            painter.save()
            painter.setClipRect(page)
            minor = QPen(QColor(70, 96, 130, 42), 1)
            major = QPen(QColor(39, 74, 116, 72), 1)
            x = page.left()
            index = 0
            while x <= page.right() + 0.5:
                painter.setPen(major if index % 10 == 0 else minor)
                painter.drawLine(QPointF(x, page.top()), QPointF(x, page.bottom()))
                x += spacing
                index += 1
            y = page.top()
            index = 0
            while y <= page.bottom() + 0.5:
                painter.setPen(major if index % 10 == 0 else minor)
                painter.drawLine(QPointF(page.left(), y), QPointF(page.right(), y))
                y += spacing
                index += 1
            painter.restore()

        canvas._paint_grid = paint_grid.__get__(canvas, canvas.__class__)
        canvas._grid_spacing = self._grid_spacing
        canvas._grid_unit = self._unit

    def set_unit(self, unit: str) -> None:
        if unit not in UNIT_TO_MM:
            return
        if unit == getattr(self, "_unit", "mm"):
            if getattr(self, "_popup", None) is not None:
                self._popup.close()
            return
        self._unit = unit
        self._grid_spacing = 1.0
        self._apply_unit_to_host()
        ensure_hooks(self)
        self._apply_grid_to_host()
        if getattr(self, "_ruler_enabled", False):
            center_ruler_origin(self)
            self._sync_rulers()
        self.unit_changed.emit(unit)
        self.grid_changed.emit(self._grid_enabled, self._grid_spacing, self._unit)
        self.tool_requested.emit(f"unit_{unit}")
        self._refresh_tooltips()
        if getattr(self, "_popup", None) is not None:
            self._popup.close()
        host = self.window()
        if host is not None:
            apply_page_setup_to_canvas(host)

    def set_ruler(self, enabled: bool) -> None:
        original_set_ruler(self, enabled)
        if enabled and not getattr(self, "_ruler_origin_custom", False):
            center_ruler_origin(self)
            self._sync_rulers()

    def ruler_paint(self, event) -> None:  # noqa: ARG001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(20, 37, 58, 230))
        unit = getattr(self._start_bar, "_unit", "mm")
        spacing = max(1.0, self._start_bar._unit_to_canvas_px(1.0, unit))
        major_every = 10 if unit == "mm" else 1
        length = self.width() if self._orientation == "top" else self.height()
        zero = self._start_bar._ruler_origin.x() - self.x() if self._orientation == "top" else self._start_bar._ruler_origin.y() - self.y()
        font = painter.font()
        font.setPointSize(7)
        font.setBold(True)
        font.setItalic(False)
        painter.setFont(font)
        start_index = int((0 - zero) / spacing) - 2
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
                        label = str(index)
                        painter.drawText(QRectF(position + 2, 1, 52, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
                else:
                    painter.drawLine(QPointF(self.width(), position), QPointF(self.width() - tick, position))
                    if index % major_every == 0:
                        label = str(index)
                        painter.drawText(QRectF(2, position + 1, self.width() - 4, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
            index += 1
        painter.end()

    def sync_open_rulers(start_bar, canvas) -> None:
        try:
            if not hasattr(canvas, "_page_setup_size_mm"):
                canvas._page_setup_size_mm = (400.0, 220.0)
            if getattr(start_bar, "_ruler_enabled", False):
                if not getattr(start_bar, "_ruler_origin_custom", False):
                    start_bar._ruler_origin = QPointF(_page_rect(canvas).topLeft())
                if hasattr(start_bar, "_position_rulers"):
                    start_bar._position_rulers()
            canvas.update()
        except Exception:
            return

    def build_svg(workspace) -> str:
        return _high_quality_svg(workspace)

    edw.EngineeringDesignWorkspace.__init__ = init
    edw.EngineeringDesignWorkspace._page_setup = page_setup
    edw.EngineeringDesignWorkspace._build_side_panel = build_side_panel
    fixes._apply_page_setup_to_canvas = apply_page_setup_to_canvas
    fixes._build_svg = build_svg
    sb.StartBar._center_ruler_origin = center_ruler_origin
    sb.StartBar._ensure_canvas_hooks = ensure_hooks
    sb.StartBar._set_unit = set_unit
    sb.StartBar._set_ruler = set_ruler
    sb._RulerOverlay.paintEvent = ruler_paint
    fixed_viewport._sync_open_rulers = sync_open_rulers
    edw.EngineeringDesignWorkspace._engineering_unit_grid_properties_final_patch = PATCH_VERSION

"""Final hotfix for the original Page Setup handler and the right Geometry properties block."""

from __future__ import annotations

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

PATCH_VERSION = "engineering-page-setup-properties-hotfix-2026-06-30-b"


_POSITION_MAP = {
    "Top Left": (0, 0),
    "Top": (1, 0),
    "Top Right": (2, 0),
    "Left": (0, 1),
    "Center": (1, 1),
    "Right": (2, 1),
    "Bottom Left": (0, 2),
    "Bottom": (1, 2),
    "Bottom Right": (2, 2),
}


def _export_state_to_runtime_state(state: dict[str, object]) -> dict[str, object]:
    """Convert the export patch Page Setup state into the original runtime Page Setup state."""
    if "paper_name" in state or "paper_size" in state:
        return dict(state)
    width = float(state.get("width_mm", 400.0) or 400.0)
    height = float(state.get("height_mm", 220.0) or 220.0)
    margins = state.get("margins_mm", {})
    if not isinstance(margins, dict):
        margins = {}
    return {
        "paper_name": str(state.get("paper", "Workspace") or "Workspace"),
        "paper_size": [width, height],
        "landscape": str(state.get("orientation", "Landscape")) == "Landscape",
        "margins": [
            float(margins.get("top", 10.0) or 0.0),
            float(margins.get("right", 10.0) or 0.0),
            float(margins.get("bottom", 10.0) or 0.0),
            float(margins.get("left", 10.0) or 0.0),
        ],
        "position": list(_POSITION_MAP.get(str(state.get("position", "Center")), (1, 1))),
        "dpi": int(float(state.get("dpi", 600) or 600)),
    }


def _cleanup_page_setup_shadow(workspace) -> dict[str, object]:
    """Remove instance-level _page_setup dicts so the original _page_setup method is callable."""
    shadow = workspace.__dict__.get("_page_setup")
    if isinstance(shadow, dict):
        workspace._page_setup_state = _export_state_to_runtime_state(shadow)
        del workspace.__dict__["_page_setup"]
    elif not isinstance(getattr(workspace, "_page_setup_state", None), dict):
        workspace._page_setup_state = {
            "paper_name": "Workspace",
            "paper_size": [400.0, 220.0],
            "landscape": True,
            "margins": [10.0, 10.0, 10.0, 10.0],
            "position": [1, 1],
            "dpi": 600,
        }
    return workspace._page_setup_state


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
    button.setFixedSize(28, 12)
    button.setIcon(_arrow_icon(direction))
    button.setIconSize(QSize(22, 10))
    button.setStyleSheet(
        "QPushButton#GeometryArrowButton {"
        "background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fff9de, stop:1 #ffc35a);"
        "border:1px solid #7e5b10; border-radius:4px; padding:0px;}"
        "QPushButton#GeometryArrowButton:hover {background:#ff8a35; border-color:#ffffff;}"
        "QPushButton#GeometryArrowButton:pressed {background:#d46a16; padding-top:1px;}"
    )
    return button


def _numeric_control(suffix: str = "") -> QWidget:
    control = QWidget()
    control.setObjectName("GeometryNumericControl")
    control.setFixedHeight(30)
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
    spin.setFixedHeight(28)
    spin.setStyleSheet(
        "QDoubleSpinBox#GeometrySpin {background:#fff9de; border:1px solid #b38621; border-radius:8px;"
        "color:#132238; font-size:11px; font-style:normal; font-weight:800; padding:2px 6px;}"
    )
    layout.addWidget(spin, 1)

    arrows = QWidget()
    arrows_layout = QVBoxLayout(arrows)
    arrows_layout.setContentsMargins(0, 0, 0, 0)
    arrows_layout.setSpacing(2)
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
    layout.setContentsMargins(8, 2, 8, 2)
    layout.setSpacing(7)
    label = QLabel(label_text)
    label.setObjectName("GeometryLabel")
    label.setFixedWidth(48)
    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(label)
    layout.addWidget(editor, 1)
    return row


class _WavePropertiesSection(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        self._collapsed = False
        self.setObjectName("WaveGeometrySection")
        self.setMinimumHeight(194)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 52, 12, 12)
        root.setSpacing(6)

        self._body = QWidget(self)
        self._body.setObjectName("GeometryBody")
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(5)

        legend = QLineEdit()
        legend.setObjectName("GeometryLegendInput")
        legend.setPlaceholderText("Legend")
        legend.setFixedHeight(28)
        body_layout.addWidget(_row("Legend", legend))
        body_layout.addWidget(_row("X", _numeric_control(" mm")))
        body_layout.addWidget(_row("Y", _numeric_control(" mm")))
        body_layout.addWidget(_row("Angle", _numeric_control(" °")))
        root.addWidget(self._body)

        self.setStyleSheet(
            "QLineEdit#GeometryLegendInput {background:#fff9de; border:1px solid #b38621; border-radius:8px;"
            "color:#132238; font-size:11px; font-style:normal; font-weight:800; padding:2px 7px;}"
            "QWidget#GeometryRow {background:rgba(255,255,255,140); border:1px solid rgba(137,165,198,110); border-radius:7px;}"
            "QLabel#GeometryLabel {background:transparent; color:#223a58; font-size:11px; font-style:normal; font-weight:900;}"
        )

    def _set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self._body.setVisible(not collapsed)
        if collapsed:
            self.setMinimumHeight(52)
            self.setMaximumHeight(52)
        else:
            self.setMinimumHeight(194)
            self.setMaximumHeight(16777215)
        self.updateGeometry()
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 48:
            self._set_collapsed(not self._collapsed)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer = QRectF(2.0, 18.0, max(1.0, self.width() - 4.0), max(1.0, self.height() - 20.0))
        tab_left = outer.left() + 18.0
        tab_right = min(outer.left() + 150.0, outer.right() - 42.0)
        tab_top = outer.top() - 17.0
        tab_bottom = outer.top() + 16.0

        body = QPainterPath()
        body.moveTo(outer.left() + 15.0, outer.top())
        body.lineTo(tab_left - 8.0, outer.top())
        body.cubicTo(tab_left - 1.0, outer.top(), tab_left - 1.0, tab_top + 9.0, tab_left + 14.0, tab_top + 8.0)
        body.lineTo(tab_right - 18.0, tab_top + 8.0)
        body.cubicTo(tab_right - 2.0, tab_top + 8.0, tab_right - 7.0, outer.top(), tab_right + 18.0, outer.top())
        body.lineTo(outer.right() - 16.0, outer.top())
        body.quadTo(outer.right(), outer.top(), outer.right(), outer.top() + 16.0)
        body.lineTo(outer.right(), outer.bottom() - 16.0)
        body.quadTo(outer.right(), outer.bottom(), outer.right() - 16.0, outer.bottom())
        body.lineTo(outer.left() + 16.0, outer.bottom())
        body.quadTo(outer.left(), outer.bottom(), outer.left(), outer.bottom() - 16.0)
        body.lineTo(outer.left(), outer.top() + 16.0)
        body.quadTo(outer.left(), outer.top(), outer.left() + 15.0, outer.top())

        fill = QLinearGradient(outer.topLeft(), outer.bottomRight())
        fill.setColorAt(0.0, QColor("#ffffff"))
        fill.setColorAt(0.48, QColor("#eef8ff"))
        fill.setColorAt(1.0, QColor("#fff0c8"))
        painter.fillPath(body, fill)
        painter.setPen(QPen(QColor("#2d7eea"), 1.35))
        painter.drawPath(body)

        tab = QPainterPath()
        tab.moveTo(tab_left - 8.0, outer.top())
        tab.cubicTo(tab_left - 1.0, outer.top(), tab_left - 1.0, tab_top + 9.0, tab_left + 14.0, tab_top + 8.0)
        tab.lineTo(tab_right - 18.0, tab_top + 8.0)
        tab.cubicTo(tab_right - 2.0, tab_top + 8.0, tab_right - 7.0, outer.top(), tab_right + 18.0, outer.top())
        tab.cubicTo(tab_right + 2.0, tab_bottom + 11.0, tab_left + 18.0, tab_bottom + 12.0, tab_left - 8.0, outer.top())

        tab_fill = QLinearGradient(tab_left, tab_top, tab_right, tab_bottom)
        tab_fill.setColorAt(0.0, QColor("#0b6ff6"))
        tab_fill.setColorAt(0.55, QColor("#168bff"))
        tab_fill.setColorAt(1.0, QColor("#0f4fbd"))
        painter.fillPath(tab, tab_fill)
        painter.setPen(QPen(QColor("#ffffff"), 0.55))
        painter.drawPath(tab)

        painter.setPen(QColor("#ffffff"))
        font = painter.font()
        font.setBold(True)
        font.setItalic(False)
        font.setPointSize(11)
        painter.setFont(font)
        arrow = "▾" if not self._collapsed else "▸"
        painter.drawText(QRectF(tab_left + 10.0, tab_top + 9.0, max(1.0, tab_right - tab_left - 14.0), 28.0), Qt.AlignmentFlag.AlignCenter, f"{self._title} {arrow}")
        painter.end()


def apply_page_setup_properties_hotfix() -> None:
    from . import workspace as edw
    from src.engineers_tools.app import engineering_fixed_viewport_patch as fixed_viewport
    from src.engineers_tools.app import runtime_ui_patch as rtp
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_page_setup_properties_hotfix", "") == PATCH_VERSION:
        return

    original_init = edw.EngineeringDesignWorkspace.__init__
    original_start_set_unit = sb.StartBar._set_unit
    original_build_side_panel = edw.EngineeringDesignWorkspace._build_side_panel

    def init(self, module) -> None:
        original_init(self, module)
        _cleanup_page_setup_shadow(self)

    def page_setup(self) -> None:
        _cleanup_page_setup_shadow(self)
        canvas = getattr(self, "_canvas", None)
        dialog = rtp.PageSetupDialog(self)
        if canvas is not None:
            fixed_viewport._apply_state_to_page_setup_dialog(dialog, fixed_viewport._page_setup_state(self, canvas))
        if dialog.exec() == dialog.DialogCode.Accepted:
            state = {
                "paper_name": dialog._paper_name,
                "paper_size": list(dialog._current_paper_size()),
                "landscape": bool(dialog._landscape),
                "margins": [
                    dialog._margin_spins.get("top").value() if "top" in dialog._margin_spins else 0.0,
                    dialog._margin_spins.get("right").value() if "right" in dialog._margin_spins else 0.0,
                    dialog._margin_spins.get("bottom").value() if "bottom" in dialog._margin_spins else 0.0,
                    dialog._margin_spins.get("left").value() if "left" in dialog._margin_spins else 0.0,
                ],
                "position": list(getattr(dialog, "_position", (1, 1))),
                "dpi": int(dialog._custom_dpi.value()) if hasattr(dialog, "_custom_dpi") else 600,
            }
            if canvas is not None:
                fixed_viewport._apply_page_setup_state(self, canvas, state)
                canvas.update()
            self._set_status(f"Page Setup applied: {state['paper_name']} {state['dpi']} DPI")
            return
        self._set_status("Page Setup canceled")

    def start_set_unit(self, unit: str) -> None:
        original_start_set_unit(self, unit)
        host = self.window()
        if host is not None:
            _cleanup_page_setup_shadow(host)

    def build_side_panel(self, title: str, rows: tuple[str, ...]) -> QWidget:
        if title != "Properties":
            return original_build_side_panel(self, title, rows)
        panel = QWidget()
        panel.setObjectName("SidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        heading = QLabel("Properties")
        heading.setObjectName("PanelTitle")
        layout.addWidget(heading)
        layout.addWidget(_WavePropertiesSection("Geometry", panel))
        layout.addStretch(1)
        return panel

    edw.EngineeringDesignWorkspace.__init__ = init
    edw.EngineeringDesignWorkspace._page_setup = page_setup
    edw.EngineeringDesignWorkspace._build_side_panel = build_side_panel
    sb.StartBar._set_unit = start_set_unit
    edw.EngineeringDesignWorkspace._engineering_page_setup_properties_hotfix = PATCH_VERSION

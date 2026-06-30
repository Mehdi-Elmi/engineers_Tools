"""Final hotfix for page setup handler state and the right properties panel."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

PATCH_VERSION = "engineering-page-setup-properties-hotfix-2026-06-30-a"


def _cleanup_page_setup_shadow(workspace, fixes) -> dict[str, object]:
    shadow = workspace.__dict__.get("_page_setup")
    if isinstance(shadow, dict):
        workspace._page_setup_state = fixes._normalize_page_setup(shadow)
        del workspace.__dict__["_page_setup"]
    elif not isinstance(getattr(workspace, "_page_setup_state", None), dict):
        workspace._page_setup_state = fixes._default_page_setup()
    return workspace._page_setup_state


class _WavePropertiesSection(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        self._collapsed = False
        self.setMinimumHeight(86)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 38:
            self._collapsed = not self._collapsed
            self.setMinimumHeight(38 if self._collapsed else 86)
            self.setMaximumHeight(38 if self._collapsed else 16777215)
            self.updateGeometry()
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        outer = QRectF(2, 10, self.width() - 4, self.height() - 12)
        body = QPainterPath()
        body.moveTo(outer.left() + 12, outer.top())
        body.lineTo(outer.left() + 48, outer.top())
        body.cubicTo(outer.left() + 63, outer.top() - 10, outer.left() + 78, outer.top() - 10, outer.left() + 93, outer.top())
        body.lineTo(outer.right() - 12, outer.top())
        body.quadTo(outer.right(), outer.top(), outer.right(), outer.top() + 12)
        body.lineTo(outer.right(), outer.bottom() - 12)
        body.quadTo(outer.right(), outer.bottom(), outer.right() - 12, outer.bottom())
        body.lineTo(outer.left() + 12, outer.bottom())
        body.quadTo(outer.left(), outer.bottom(), outer.left(), outer.bottom() - 12)
        body.lineTo(outer.left(), outer.top() + 12)
        body.quadTo(outer.left(), outer.top(), outer.left() + 12, outer.top())
        gradient = QLinearGradient(outer.topLeft(), outer.bottomRight())
        gradient.setColorAt(0.0, QColor("#ffffff"))
        gradient.setColorAt(0.42, QColor("#e8f7ff"))
        gradient.setColorAt(1.0, QColor("#ffe0a3"))
        painter.fillPath(body, gradient)
        painter.setPen(QPen(QColor("#6f86a6"), 1.1))
        painter.drawPath(body)

        tab = QRectF(18, 2, 112, 28)
        tab_path = QPainterPath()
        tab_path.moveTo(tab.left() + 12, tab.bottom())
        tab_path.cubicTo(tab.left() + 28, tab.top() - 7, tab.left() + 84, tab.top() - 7, tab.right() - 12, tab.bottom())
        tab_path.lineTo(tab.left() + 12, tab.bottom())
        tab_grad = QLinearGradient(tab.topLeft(), tab.bottomRight())
        tab_grad.setColorAt(0.0, QColor("#11243c"))
        tab_grad.setColorAt(1.0, QColor("#215983"))
        painter.fillPath(tab_path, tab_grad)
        painter.setPen(QPen(QColor("#ffc35a"), 1.0))
        painter.drawPath(tab_path)

        painter.setPen(QColor("#ffffff"))
        font = painter.font()
        font.setBold(True)
        font.setItalic(False)
        font.setPointSize(9)
        painter.setFont(font)
        arrow = "v" if not self._collapsed else ">"
        painter.drawText(QRectF(24, 6, 100, 20), Qt.AlignmentFlag.AlignCenter, f"{self._title}  {arrow}")
        painter.end()


def apply_page_setup_properties_hotfix() -> None:
    from . import file_export_project_fixes as fixes
    from . import workspace as edw
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_page_setup_properties_hotfix", "") == PATCH_VERSION:
        return

    original_init = edw.EngineeringDesignWorkspace.__init__
    original_start_set_unit = sb.StartBar._set_unit
    original_build_side_panel = edw.EngineeringDesignWorkspace._build_side_panel

    def apply_page_setup_to_canvas(workspace, state=None):
        if state is None:
            state = getattr(workspace, "_page_setup_state", None)
        normalized = fixes._normalize_page_setup(state)
        workspace._page_setup_state = normalized
        canvas = getattr(workspace, "_canvas", None)
        if canvas is not None:
            canvas._page_setup_size_mm = (float(normalized["width_mm"]), float(normalized["height_mm"]))
            canvas._page_setup_dpi = int(normalized["dpi"])
            canvas._page_setup_position = str(normalized["position"])
            canvas._page_setup_margins_mm = dict(normalized["margins_mm"])
            canvas._page_setup_unit = str(normalized["unit"])
        return normalized

    def init(self, module) -> None:
        original_init(self, module)
        _cleanup_page_setup_shadow(self, fixes)
        apply_page_setup_to_canvas(self, self._page_setup_state)

    def page_setup(self) -> None:
        _cleanup_page_setup_shadow(self, fixes)
        fixes._show_page_setup_dialog(self)
        _cleanup_page_setup_shadow(self, fixes)
        apply_page_setup_to_canvas(self, self._page_setup_state)

    def start_set_unit(self, unit: str) -> None:
        original_start_set_unit(self, unit)
        host = self.window()
        if host is not None and hasattr(host, "_page_setup_state"):
            _cleanup_page_setup_shadow(host, fixes)
            state = fixes._normalize_page_setup(host._page_setup_state)
            state["unit"] = unit
            host._page_setup_state = state
            apply_page_setup_to_canvas(host, state)

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

    fixes._apply_page_setup_to_canvas = apply_page_setup_to_canvas
    edw.EngineeringDesignWorkspace.__init__ = init
    edw.EngineeringDesignWorkspace._page_setup = page_setup
    edw.EngineeringDesignWorkspace._build_side_panel = build_side_panel
    sb.StartBar._set_unit = start_set_unit
    edw.EngineeringDesignWorkspace._engineering_page_setup_properties_hotfix = PATCH_VERSION

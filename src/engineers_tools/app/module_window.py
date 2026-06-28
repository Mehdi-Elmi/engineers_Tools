"""Shared engineering workspace window."""

from __future__ import annotations

import base64
import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QRegion, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..ui.start_bar import DEFAULT_START_BAR_TOOLS, StartBar, StartBarTool
from .modules import LauncherModule
from .project_file_dialog import ProjectFileDialog

UI_BUILD_MARKER = "ENGINEER_TOOLS_ACTIVE_UI_2026_06_27_B"


def _apply_rounded_mask(widget: QWidget, radius: float) -> None:
    if widget.width() <= 0 or widget.height() <= 0:
        return
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, widget.width(), widget.height()), radius, radius)
    widget.setMask(QRegion(path.toFillPolygon().toPolygon()))


def _paint_rotation_glyph(painter: QPainter, center: QPointF, radius: float, color: QColor) -> None:
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(color, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawArc(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), 35 * 16, 285 * 16)
    painter.setBrush(color)
    painter.drawPolygon(
        QPolygonF(
            [
                QPointF(center.x() + radius - 1, center.y() - radius * 0.48),
                QPointF(center.x() + radius + 6, center.y() - radius * 0.12),
                QPointF(center.x() + radius - 2, center.y() + radius * 0.18),
            ]
        )
    )
    painter.restore()


def _select_icon(checked: bool) -> QIcon:
    pixmap = QPixmap(28, 28)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(QPen(QColor("#18314f"), 2.1))
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(4, 4, 20, 20)
    if checked:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2f7df6"))
        painter.drawEllipse(9, 9, 10, 10)
    painter.end()
    return QIcon(pixmap)


def _layer_icon(kind: str, active: bool = True) -> QIcon:
    pixmap = QPixmap(30, 30)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    base = QPainterPath()
    base.addRoundedRect(QRectF(2, 2, 26, 26), 8, 8)
    gradient = QLinearGradient(2, 2, 28, 28)
    gradient.setColorAt(0.0, QColor("#ffffff"))
    gradient.setColorAt(0.55, QColor("#dff2ff" if active else "#e8edf3"))
    gradient.setColorAt(1.0, QColor("#57b8d9" if active else "#9aa9ba"))
    painter.fillPath(base, gradient)
    painter.setPen(QPen(QColor("#55708f"), 1.0))
    painter.drawPath(base)
    painter.setPen(QPen(QColor("#132238"), 1.9, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    if kind == "eye":
        eye = QPainterPath()
        eye.moveTo(6, 15)
        eye.cubicTo(9, 9, 21, 9, 24, 15)
        eye.cubicTo(21, 21, 9, 21, 6, 15)
        painter.drawPath(eye)
        painter.setBrush(QColor("#2f7df6" if active else "#8b98a8"))
        painter.drawEllipse(QPointF(15, 15), 3.8, 3.8)
        if not active:
            painter.setPen(QPen(QColor("#d44777"), 2.2, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(7, 23), QPointF(23, 7))
    elif kind == "lock":
        if active:
            painter.drawArc(QRectF(9, 6, 12, 13), 0, 180 * 16)
        else:
            painter.drawArc(QRectF(10, 6, 12, 13), 35 * 16, 145 * 16)
            painter.drawLine(QPointF(20, 10), QPointF(23, 8))
        painter.drawRoundedRect(QRectF(8, 14, 14, 9), 2.5, 2.5)
        painter.setBrush(QColor("#132238"))
        painter.drawEllipse(QPointF(15, 18), 1.6, 1.6)
    else:
        _paint_rotation_glyph(painter, QPointF(15, 15), 7.5, QColor("#132238"))
        if not active:
            painter.setPen(QPen(QColor("#d44777"), 2.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(7, 23), QPointF(23, 7))
    painter.end()
    return QIcon(pixmap)


@dataclass(frozen=True)
class MenuItemSpec:
    label: str
    handler: Callable[[], None] | None = None
    shortcut: str = ""
    checkable: bool = False
    checked: bool = False


class GridCanvas(QWidget):
    mouse_position_changed = Signal(float, float)
    context_actions_requested = Signal(QPoint)

    def __init__(self) -> None:
        super().__init__()
        self._grid_visible = True
        self._zoom = 1.0
        self._file_path: Path | None = None
        self._file_pixmap = QPixmap()
        self._object_rect: QRectF | None = None
        self._rotation_degrees = 0.0
        self._drag_action: str | None = None
        self._drag_start = QPointF()
        self._drag_start_rect = QRectF()
        self._drag_start_rotation = 0.0
        self.setMouseTracking(True)

    def set_grid_visible(self, visible: bool) -> None:
        self._grid_visible = visible
        self.update()

    def set_zoom(self, zoom_percent: float) -> None:
        self._zoom = max(0.05, zoom_percent / 100.0)
        self.update()

    def load_file(self, path: Path) -> None:
        self._file_path = path
        self._file_pixmap = QPixmap(str(path))
        self._rotation_degrees = 0.0
        if self.width() <= 0 or self.height() <= 0:
            return
        if not self._file_pixmap.isNull():
            width = float(self._file_pixmap.width())
            height = float(self._file_pixmap.height())
        elif path.suffix.lower() == ".pdf":
            width, height = 595.0, 842.0
        else:
            width, height = 520.0, 360.0
        max_width = max(180.0, self.width() * 0.62)
        max_height = max(160.0, self.height() * 0.74)
        scale = min(max_width / width, max_height / height, 1.0)
        width *= scale
        height *= scale
        self._object_rect = QRectF((self.width() - width) / 2, (self.height() - height) / 2, width, height)
        self.update()

    def _to_canvas_coordinates(self, point: QPointF) -> QPointF:
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        x = ((point.x() - center_x) / self._zoom) + center_x
        y = ((point.y() - center_y) / self._zoom) + center_y
        return QPointF(x, y)

    def _rotation_center(self) -> QPointF | None:
        if self._object_rect is None:
            return None
        return QPointF(self._object_rect.center().x(), self._object_rect.top() - 33)

    def _hit_test(self, point: QPointF) -> str | None:
        rect = self._object_rect
        if rect is None:
            return None
        rotate_center = self._rotation_center()
        if rotate_center is not None and math.hypot(point.x() - rotate_center.x(), point.y() - rotate_center.y()) <= 14:
            return "rotate"
        tolerance = 9.0
        handles = {
            "resize_nw": rect.topLeft(), "resize_n": QPointF(rect.center().x(), rect.top()), "resize_ne": rect.topRight(),
            "resize_e": QPointF(rect.right(), rect.center().y()), "resize_se": rect.bottomRight(), "resize_s": QPointF(rect.center().x(), rect.bottom()),
            "resize_sw": rect.bottomLeft(), "resize_w": QPointF(rect.left(), rect.center().y()),
        }
        for action, handle in handles.items():
            if abs(point.x() - handle.x()) <= tolerance and abs(point.y() - handle.y()) <= tolerance:
                return action
        if rect.adjusted(-4, -4, 4, 4).contains(point):
            return "move"
        return None

    def _apply_drag(self, point: QPointF) -> None:
        if self._object_rect is None or self._drag_action is None:
            return
        dx = point.x() - self._drag_start.x()
        dy = point.y() - self._drag_start.y()
        if self._drag_action == "move":
            self._object_rect = self._drag_start_rect.translated(dx, dy)
        elif self._drag_action == "rotate":
            center = self._drag_start_rect.center()
            start_angle = math.degrees(math.atan2(self._drag_start.y() - center.y(), self._drag_start.x() - center.x()))
            current_angle = math.degrees(math.atan2(point.y() - center.y(), point.x() - center.x()))
            self._rotation_degrees = self._drag_start_rotation + current_angle - start_angle
        elif self._drag_action.startswith("resize"):
            rect = QRectF(self._drag_start_rect)
            if "w" in self._drag_action:
                rect.setLeft(rect.left() + dx)
            if "e" in self._drag_action:
                rect.setRight(rect.right() + dx)
            if "n" in self._drag_action:
                rect.setTop(rect.top() + dy)
            if "s" in self._drag_action:
                rect.setBottom(rect.bottom() + dy)
            if rect.width() < 35:
                if "w" in self._drag_action:
                    rect.setLeft(rect.right() - 35)
                else:
                    rect.setRight(rect.left() + 35)
            if rect.height() < 35:
                if "n" in self._drag_action:
                    rect.setTop(rect.bottom() - 35)
                else:
                    rect.setBottom(rect.top() + 35)
            self._object_rect = rect.normalized()
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            point = self._to_canvas_coordinates(event.position())
            action = self._hit_test(point)
            if action is not None and self._object_rect is not None:
                self._drag_action = action
                self._drag_start = point
                self._drag_start_rect = QRectF(self._object_rect)
                self._drag_start_rotation = self._rotation_degrees
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        point = self._to_canvas_coordinates(event.position())
        self.mouse_position_changed.emit(point.x(), point.y())
        if self._drag_action is not None:
            self._apply_drag(point)
            event.accept()
            return
        hover = self._hit_test(point)
        if hover == "move":
            self.setCursor(Qt.SizeAllCursor)
        elif hover == "rotate":
            self.setCursor(Qt.CrossCursor)
        elif hover in {"resize_n", "resize_s"}:
            self.setCursor(Qt.SizeVerCursor)
        elif hover in {"resize_e", "resize_w"}:
            self.setCursor(Qt.SizeHorCursor)
        elif hover in {"resize_ne", "resize_sw"}:
            self.setCursor(Qt.SizeBDiagCursor)
        elif hover in {"resize_nw", "resize_se"}:
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_action = None
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        self.context_actions_requested.emit(event.globalPos())
        event.accept()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._file_path is not None and self._object_rect is None:
            self.load_file(self._file_path)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#fbfdff"))
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._zoom, self._zoom)
        painter.translate(-self.width() / 2, -self.height() / 2)
        self._paint_grid(painter)
        self._paint_loaded_object(painter)

    def _paint_grid(self, painter: QPainter) -> None:
        if not self._grid_visible:
            return
        painter.setPen(QPen(QColor(70, 96, 130, 42), 1))
        for column in range(1, 16):
            x = round(self.width() * column / 16)
            painter.drawLine(x, 0, x, self.height())
        for row in range(1, 12):
            y = round(self.height() * row / 12)
            painter.drawLine(0, y, self.width(), y)

    def _paint_loaded_object(self, painter: QPainter) -> None:
        if self._object_rect is None or self._file_path is None:
            return
        rect = self._object_rect
        painter.save()
        painter.translate(rect.center())
        painter.rotate(self._rotation_degrees)
        local = QRectF(-rect.width() / 2, -rect.height() / 2, rect.width(), rect.height())
        painter.setPen(QPen(QColor("#d6e2f0"), 1.2))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(local)
        if not self._file_pixmap.isNull():
            painter.drawPixmap(local.toRect(), self._file_pixmap)
        else:
            painter.setPen(QPen(QColor("#465d78"), 1.2))
            painter.drawText(local.adjusted(10, 10, -10, -10), Qt.AlignCenter, self._file_path.name)
        painter.restore()
        self._paint_selection_frame(painter, rect)

    def _paint_selection_frame(self, painter: QPainter, rect: QRectF) -> None:
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


class ProjectHelpDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectHelpDialog")
        self.setWindowTitle("Help")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumSize(480, 300)
        shell = QWidget()
        shell.setObjectName("ProjectHelpShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(12)
        header = QWidget()
        header.setObjectName("HelpHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 8, 0)
        title = QLabel("Engineer Tools Help")
        title.setObjectName("HelpTitle")
        header_layout.addWidget(title, 1)
        close = QPushButton("×")
        close.setObjectName("MenuDialogClose")
        close.setFixedSize(28, 26)
        close.clicked.connect(self.accept)
        header_layout.addWidget(close)
        layout.addWidget(header)
        body = QLabel("File manages documents. Edit handles object and clipboard operations. View controls shared workspace visibility.")
        body.setObjectName("HelpBody")
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(body, 1)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        _apply_rounded_mask(self, 16)


class ProjectMenuDialog(QDialog):
    def __init__(self, title: str, items: tuple[MenuItemSpec, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectMenuDialog")
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        shell = QWidget()
        shell.setObjectName("ProjectMenuShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setSpacing(4)
        if not items:
            empty = QLabel("No tools defined yet.")
            empty.setObjectName("MenuDialogEmpty")
            layout.addWidget(empty)
        for item in items:
            button = QPushButton(self._build_button_text(item))
            button.setObjectName("MenuItemButton")
            button.setMinimumHeight(24)
            if item.checkable:
                button.setIcon(_select_icon(item.checked))
                button.setIconSize(QSize(24, 24))
            if item.handler is not None:
                button.clicked.connect(self._wrap_handler(item.handler))
            layout.addWidget(button)
        self.setFixedWidth(self._preferred_width(items))

    def _preferred_width(self, items: tuple[MenuItemSpec, ...]) -> int:
        if not items:
            return 150
        longest = max(self.fontMetrics().horizontalAdvance(self._build_button_text(item)) for item in items)
        icon_padding = 32 if any(item.checkable for item in items) else 0
        return max(142, min(204, longest + icon_padding + 34))

    def _build_button_text(self, item: MenuItemSpec) -> str:
        shortcut = f"    {item.shortcut}" if item.shortcut else ""
        return f"{item.label}{shortcut}"

    def _wrap_handler(self, handler: Callable[[], None]) -> Callable[[], None]:
        def run() -> None:
            handler()
            self.accept()
        return run

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        _apply_rounded_mask(self, 12)


class ModuleWindow(QMainWindow):
    back_requested = Signal()
    new_workspace_requested = Signal(object)

    def __init__(self, module: LauncherModule) -> None:
        super().__init__()
        self.module = module
        self.setWindowTitle(module.title)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(960, 620)
        self.resize(1180, 760)
        self._drag_position: QPoint | None = None
        self._normal_geometry: QRect | None = None
        self._is_manually_maximized = False
        self._maximize_button: QPushButton | None = None
        self._start_bar_widget: StartBar | None = None
        self._canvas: GridCanvas | None = None
        self._status_items: list[QLabel] = []
        self._current_file_path: Path | None = None
        self._last_file_dir: Path | None = None
        self._view_state = {"start_bar": True, "grid": True, "ruler": False, "snap": False}
        self._pages: list[str] = ["Page 1"]
        self._layers: list[str] = ["Page 1"]
        self._active_page_index = 0
        self._page_buttons_layout: QHBoxLayout | None = None
        self._layer_list_layout: QVBoxLayout | None = None
        root = QWidget()
        root.setObjectName("WindowRoot")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_top_bar())
        layout.addWidget(self._build_command_bar())
        layout.addWidget(self._build_start_bar())
        layout.addWidget(self._build_workspace(), 1)
        layout.addWidget(self._build_page_bar())
        layout.addWidget(self._build_status_bar())
        self._install_shortcuts()

    def get_start_bar_tools(self) -> tuple[StartBarTool, ...]:
        return DEFAULT_START_BAR_TOOLS

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(46)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 10, 0)
        layout.setSpacing(10)
        layout.addWidget(self._build_window_mark())
        title = QLabel(self.module.title)
        title.setObjectName("WindowTitle")
        layout.addWidget(title, 1)
        minimize = QPushButton("-")
        minimize.setObjectName("WindowButton")
        minimize.setFixedSize(34, 30)
        minimize.clicked.connect(self._minimize_window)
        layout.addWidget(minimize)
        maximize = QPushButton("[]")
        maximize.setObjectName("WindowButton")
        maximize.setFixedSize(34, 30)
        maximize.clicked.connect(self._toggle_maximize)
        self._maximize_button = maximize
        layout.addWidget(maximize)
        close = QPushButton("×")
        close.setObjectName("CloseButton")
        close.setFixedSize(34, 30)
        close.clicked.connect(self.close)
        layout.addWidget(close)
        return bar

    def _build_window_mark(self) -> QLabel:
        mark = QLabel("AT")
        mark.setObjectName("WindowMark")
        mark.setFixedSize(42, 36)
        mark.setAlignment(Qt.AlignCenter)
        logo_path = self._find_logo_path()
        if logo_path is None:
            return mark
        pixmap = QPixmap(str(logo_path))
        if pixmap.isNull():
            return mark
        mark.setText("")
        mark.setObjectName("WindowLogoMark")
        mark.setPixmap(pixmap.scaled(36, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return mark

    def _find_logo_path(self) -> Path | None:
        logo_dir = Path(__file__).resolve().parents[3] / "logo"
        if not logo_dir.exists():
            return None
        suffixes = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
        candidates = sorted(path for path in logo_dir.iterdir() if path.is_file() and path.suffix.lower() in suffixes)
        return candidates[0] if candidates else None

    def _build_command_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("CommandBar")
        bar.setFixedHeight(40)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 4, 14, 4)
        layout.setSpacing(10)
        home = QPushButton()
        home.setObjectName("HomeButton")
        home.setToolTip("Back to launcher")
        home.setFixedSize(48, 30)
        home.setIcon(self._build_home_icon())
        home.setIconSize(QSize(31, 25))
        home.clicked.connect(self.back_requested.emit)
        layout.addWidget(home)
        for label, handler in (("File", self._show_file_menu), ("Edit", self._show_edit_menu), ("View", self._show_view_menu), ("Insert", self._show_insert_menu), ("Draw", self._show_draw_menu), ("Help", lambda source: self._open_help_page())):
            button = QPushButton(label)
            button.setObjectName("MenuButton")
            button.setFixedHeight(26)
            button.clicked.connect(lambda checked=False, source=button, action=handler: action(source))
            layout.addWidget(button)
        layout.addStretch(1)
        return bar

    def _build_start_bar(self) -> QWidget:
        self._start_bar_widget = StartBar(self.get_start_bar_tools())
        return self._start_bar_widget

    def _build_workspace(self) -> QWidget:
        area = QWidget()
        area.setObjectName("WorkspaceArea")
        layout = QHBoxLayout(area)
        layout.setContentsMargins(14, 14, 14, 10)
        layout.setSpacing(12)
        layers = self._build_layers_panel()
        layers.setFixedWidth(236)
        layout.addWidget(layers)
        canvas_shell = QWidget()
        canvas_shell.setObjectName("CanvasShell")
        canvas_layout = QVBoxLayout(canvas_shell)
        canvas_layout.setContentsMargins(12, 12, 12, 12)
        self._canvas = GridCanvas()
        self._canvas.setObjectName("GridCanvas")
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._canvas.mouse_position_changed.connect(self._update_canvas_coordinates)
        self._canvas.context_actions_requested.connect(self._show_canvas_context_menu)
        canvas_layout.addWidget(self._canvas, 1)
        layout.addWidget(canvas_shell, 1)
        properties = self._build_side_panel("Properties", ("Selection", "Coordinates", "Size", "Style", "Behavior"))
        properties.setFixedWidth(220)
        layout.addWidget(properties)
        return area

    def _build_layers_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("SidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        heading = QLabel("Layers")
        heading.setObjectName("PanelTitle")
        layout.addWidget(heading)
        self._layer_list_layout = QVBoxLayout()
        self._layer_list_layout.setSpacing(6)
        layout.addLayout(self._layer_list_layout)
        layout.addStretch(1)
        self._refresh_layers()
        return panel

    def _refresh_layers(self) -> None:
        if self._layer_list_layout is None:
            return
        while self._layer_list_layout.count():
            item = self._layer_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for layer in self._layers:
            self._layer_list_layout.addWidget(self._build_layer_row(layer, visible=True, locked=False, rotation=True, grouped=layer.startswith("Group")))

    def _add_layer(self, name: str) -> None:
        candidate = name or "Object"
        existing = set(self._layers)
        label = candidate
        counter = 1
        while label in existing:
            counter += 1
            label = f"{candidate} {counter}"
        self._layers.append(label)
        self._refresh_layers()

    def _build_layer_row(self, name: str, visible: bool, locked: bool, rotation: bool, grouped: bool = False) -> QWidget:
        row = QWidget()
        row.setObjectName("LayerRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(5, 4, 5, 4)
        layout.setSpacing(4)
        if grouped:
            expander = QPushButton("▾")
            expander.setObjectName("LayerExpandButton")
            expander.setFixedSize(18, 24)
            layout.addWidget(expander)
        for kind, state, tooltip in (("eye", visible, "Show or hide layer"), ("lock", locked, "Lock layer"), ("rotation", rotation, "Show rotation handle")):
            button = QPushButton()
            button.setObjectName("LayerIconButton")
            button.setCheckable(True)
            button.setChecked(state)
            button.setToolTip(tooltip)
            button.setFixedSize(28, 26)
            button.setIcon(_layer_icon(kind, state))
            button.setIconSize(QSize(24, 24))
            button.toggled.connect(lambda checked, b=button, icon_kind=kind: b.setIcon(_layer_icon(icon_kind, checked)))
            layout.addWidget(button)
        name_input = QLineEdit(name)
        name_input.setObjectName("LayerNameInput")
        layout.addWidget(name_input, 1)
        return row

    def _build_side_panel(self, title: str, rows: tuple[str, ...]) -> QWidget:
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
            item.setFixedHeight(30)
            layout.addWidget(item)
        layout.addStretch(1)
        return panel

    def _build_page_bar(self) -> QWidget:
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
        self._refresh_page_buttons()
        layout.addStretch(1)
        add_page = self._build_page_action_button("Add Page", self._add_page)
        add_page.setObjectName("AddPageButton")
        layout.addWidget(add_page)
        return bar

    def _build_page_action_button(self, label: str, handler: Callable[[], None]) -> QPushButton:
        button = QPushButton(label)
        button.setMinimumWidth(62)
        button.clicked.connect(handler)
        return button

    def _refresh_page_buttons(self) -> None:
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

    def _show_page_context_menu(self, index: int, anchor: QWidget) -> None:
        self._select_page(index)
        self._show_menu("Page", (MenuItemSpec("Copy", self._copy_page), MenuItemSpec("Duplicate Page", self._duplicate_page), MenuItemSpec("Delete Page", self._delete_page)), anchor)

    def _child_page_label(self) -> str:
        current = self._pages[self._active_page_index]
        base = current.split("-")[0]
        counter = 1
        existing = set(self._pages)
        while f"{base}-{counter}" in existing:
            counter += 1
        return f"{base}-{counter}"

    def _renumber_pages(self) -> None:
        root_map: dict[str, str] = {}
        child_counters: dict[str, int] = {}
        next_root = 1
        renamed: list[str] = []
        for page in self._pages:
            root = page.split("-")[0]
            if root not in root_map:
                root_map[root] = f"Page {next_root}"
                child_counters[root_map[root]] = 0
                next_root += 1
            new_root = root_map[root]
            if "-" in page:
                child_counters[new_root] += 1
                renamed.append(f"{new_root}-{child_counters[new_root]}")
            else:
                renamed.append(new_root)
        self._pages = renamed

    def _select_page(self, index: int) -> None:
        self._active_page_index = max(0, min(index, len(self._pages) - 1))
        self._refresh_page_buttons()
        self._set_status(f"Selected {self._pages[self._active_page_index]}")

    def _add_page(self) -> None:
        number = 1
        existing = set(self._pages)
        while f"Page {number}" in existing:
            number += 1
        self._pages.append(f"Page {number}")
        self._active_page_index = len(self._pages) - 1
        self._refresh_page_buttons()
        self._set_status(f"Added {self._pages[self._active_page_index]}")

    def _copy_page(self) -> None:
        label = self._child_page_label()
        self._pages.insert(self._active_page_index + 1, label)
        self._active_page_index += 1
        self._refresh_page_buttons()
        self._set_status(f"Copied page settings to {label}")

    def _duplicate_page(self) -> None:
        label = self._child_page_label()
        self._pages.insert(self._active_page_index + 1, label)
        self._active_page_index += 1
        self._refresh_page_buttons()
        self._set_status(f"Duplicated page content to {label}")

    def _delete_page(self) -> None:
        if len(self._pages) == 1:
            self._set_status("At least one page is required")
            return
        removed = self._pages.pop(self._active_page_index)
        self._active_page_index = min(self._active_page_index, len(self._pages) - 1)
        self._renumber_pages()
        self._refresh_page_buttons()
        self._set_status(f"Deleted {removed}")

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(34)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)
        self._status_items = []
        for text in ("Tool Select: Ready", "X: 0  Y: 0", "Unit: mm"):
            item = QLabel(text)
            item.setObjectName("StatusItem")
            layout.addWidget(item)
            self._status_items.append(item)
        layout.addStretch(1)
        return bar

    def _install_shortcuts(self) -> None:
        for sequence, handler in (("Ctrl+N", self._new_file), ("Ctrl+O", self._open_file), ("Ctrl+S", self._save_file), ("Ctrl+Shift+S", self._save_as_file), ("Ctrl+Z", self._undo), ("Ctrl+Y", self._redo), ("Ctrl+X", self._cut), ("Ctrl+C", self._copy), ("Ctrl+V", self._paste), ("Delete", self._delete), ("Ctrl+R", self._repeat_last_tools), ("Ctrl+A", self._select_all), ("Ctrl+G", self._group), ("Ctrl+Shift+G", self._ungroup)):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(handler)

    def _show_menu(self, title: str, items: tuple[MenuItemSpec, ...], anchor: QWidget) -> None:
        position = anchor.mapToGlobal(QPoint(0, anchor.height() + 3))
        self._show_menu_at(title, items, position)

    def _show_menu_at(self, title: str, items: tuple[MenuItemSpec, ...], position: QPoint) -> None:
        dialog = ProjectMenuDialog(title, items, self)
        dialog.adjustSize()
        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry()
            if position.x() + dialog.width() > available.right():
                position.setX(max(available.left(), available.right() - dialog.width()))
            if position.y() + dialog.height() > available.bottom():
                position.setY(max(available.top(), available.bottom() - dialog.height()))
        dialog.move(position)
        dialog.exec()

    def _show_canvas_context_menu(self, global_pos: QPoint) -> None:
        self._show_menu_at("Object", (
            MenuItemSpec("Repeat", self._repeat_last_tools),
            MenuItemSpec("Copy", self._copy),
            MenuItemSpec("Cut", self._cut),
            MenuItemSpec("Paste", self._paste),
            MenuItemSpec("Rotate", self._rotation),
            MenuItemSpec("Bring to Front", self._bring_to_front),
            MenuItemSpec("Send to Back", self._send_to_back),
            MenuItemSpec("Group", self._group),
            MenuItemSpec("Ungroup", self._ungroup),
        ), global_pos)

    def _show_file_menu(self, anchor: QWidget) -> None:
        self._show_menu("File", (
            MenuItemSpec("New", self._new_file, "Ctrl+N"), MenuItemSpec("Open", self._open_file, "Ctrl+O"),
            MenuItemSpec("Save", self._save_file, "Ctrl+S"), MenuItemSpec("Save As", self._save_as_file, "Ctrl+Shift+S"),
            MenuItemSpec("Page Setup", self._page_setup), MenuItemSpec("Print Setup", self._print_setup),
            MenuItemSpec("Import", self._import_file), MenuItemSpec("Export", self._export_file), MenuItemSpec("Properties", self._file_properties),
        ), anchor)

    def _show_edit_menu(self, anchor: QWidget) -> None:
        self._show_menu("Edit", (
            MenuItemSpec("Copy", self._copy, "Ctrl+C"), MenuItemSpec("Cut", self._cut, "Ctrl+X"),
            MenuItemSpec("Paste", self._paste, "Ctrl+V"), MenuItemSpec("Move", self._move),
            MenuItemSpec("Undo", self._undo, "Ctrl+Z"), MenuItemSpec("Redo", self._redo, "Ctrl+Y"),
            MenuItemSpec("Repeat Last Tools", self._repeat_last_tools, "Ctrl+R"), MenuItemSpec("Select All", self._select_all, "Ctrl+A"),
            MenuItemSpec("Group", self._group, "Ctrl+G"), MenuItemSpec("Ungroup", self._ungroup, "Ctrl+Shift+G"),
        ), anchor)

    def _show_view_menu(self, anchor: QWidget) -> None:
        self._show_menu("View", (
            MenuItemSpec("Start Bar", self._toggle_start_bar, checkable=True, checked=self._view_state["start_bar"]),
            MenuItemSpec("Grid", self._toggle_grid, checkable=True, checked=self._view_state["grid"]),
            MenuItemSpec("Ruler", self._toggle_ruler, checkable=True, checked=self._view_state["ruler"]),
            MenuItemSpec("Snap", self._toggle_snap, checkable=True, checked=self._view_state["snap"]),
        ), anchor)

    def _show_insert_menu(self, anchor: QWidget) -> None: self._show_menu("Insert", (MenuItemSpec("Text", self._insert_text),), anchor)
    def _show_draw_menu(self, anchor: QWidget) -> None: self._show_menu("Draw", (), anchor)
    def _open_help_page(self) -> None: ProjectHelpDialog(self).exec(); self._set_status("Help opened")

    def _new_file(self) -> None:
        self.new_workspace_requested.emit(self.module)
        self._set_status("New workspace opened")

    def _open_file(self) -> None:
        result = ProjectFileDialog.get_open_file(self, self._last_file_dir)
        if result is None:
            self._set_status("Open canceled")
            return
        self._current_file_path = result.path
        self._last_file_dir = result.path.parent
        if self._canvas is not None:
            self._canvas.load_file(result.path)
        self._add_layer(result.path.stem)
        self._set_status(f"Opened {result.path.name}")

    def _save_file(self) -> None:
        if self._current_file_path is None:
            self._save_as_file()
            return
        self._write_document(self._current_file_path)
        self._set_status(f"Saved {self._current_file_path.name}")

    def _save_as_file(self) -> None:
        result = ProjectFileDialog.get_save_file(self, self._last_file_dir)
        if result is None:
            self._set_status("Save As canceled")
            return
        self._write_document(result.path)
        self._current_file_path = result.path
        self._last_file_dir = result.path.parent
        self._set_status(f"Saved As {result.path.name}")

    def _write_document(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            path.write_bytes(self._blank_pdf_bytes())
        elif suffix == ".svg":
            path.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"800\" height=\"600\"></svg>\n", encoding="utf-8")
        elif suffix == ".png":
            path.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="))
        else:
            path.write_text("Engineer Tools document placeholder\n", encoding="utf-8")

    def _blank_pdf_bytes(self) -> bytes:
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000053 00000 n \n0000000102 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n169\n%%EOF\n"

    def _page_setup(self) -> None: self._set_status("Page Setup opened")
    def _print_setup(self) -> None: self._set_status("Print Setup opened")

    def _import_file(self) -> None:
        result = ProjectFileDialog.get_import_file(self, self._last_file_dir)
        if result and self._canvas is not None:
            self._canvas.load_file(result.path)
            self._add_layer(result.path.stem)
        self._set_status(f"Imported {result.path.name}" if result else "Import canceled")

    def _export_file(self) -> None:
        result = ProjectFileDialog.get_export_file(self, self._last_file_dir)
        if result:
            self._write_document(result.path)
            self._set_status(f"Exported {result.path.name}")
        else:
            self._set_status("Export canceled")

    def _file_properties(self) -> None: self._set_status("File Properties opened")

    def _run_focus_command(self, command: str) -> bool:
        focused = QApplication.focusWidget()
        if focused is None or focused is self:
            return False
        action = getattr(focused, command, None)
        if not callable(action):
            return False
        action()
        return True

    def _undo(self) -> None: self._run_focus_command("undo"); self._set_status("Undo")
    def _redo(self) -> None: self._run_focus_command("redo"); self._set_status("Redo")
    def _cut(self) -> None: self._run_focus_command("cut"); self._set_status("Cut")
    def _copy(self) -> None: self._run_focus_command("copy"); self._set_status("Copy")
    def _paste(self) -> None: self._run_focus_command("paste"); self._set_status("Paste")
    def _delete(self) -> None: self._set_status("Delete")
    def _repeat_last_tools(self) -> None: self._set_status("Repeat Last Tools")
    def _select_all(self) -> None: self._run_focus_command("selectAll"); self._set_status("Select All")
    def _group(self) -> None:
        if not any(layer.startswith("Group") for layer in self._layers):
            self._layers.append("Group 1")
            self._refresh_layers()
        self._set_status("Group")
    def _ungroup(self) -> None: self._set_status("Ungroup")
    def _move(self) -> None: self._set_status("Move")
    def _rotation(self) -> None: self._set_status("Rotate tool ready")
    def _bring_to_front(self) -> None: self._set_status("Bring to Front")
    def _send_to_back(self) -> None: self._set_status("Send to Back")

    def _toggle_start_bar(self) -> None:
        self._view_state["start_bar"] = not self._view_state["start_bar"]
        if self._start_bar_widget is not None:
            self._start_bar_widget.setVisible(self._view_state["start_bar"])
        self._set_status(f"Start Bar {'On' if self._view_state['start_bar'] else 'Off'}")

    def _toggle_grid(self) -> None:
        self._view_state["grid"] = not self._view_state["grid"]
        if self._canvas is not None:
            self._canvas.set_grid_visible(self._view_state["grid"])
        self._set_status(f"Grid {'On' if self._view_state['grid'] else 'Off'}")

    def _toggle_ruler(self) -> None: self._view_state["ruler"] = not self._view_state["ruler"]; self._set_status(f"Ruler {'On' if self._view_state['ruler'] else 'Off'}")
    def _toggle_snap(self) -> None: self._view_state["snap"] = not self._view_state["snap"]; self._set_status(f"Snap {'On' if self._view_state['snap'] else 'Off'}")
    def _insert_text(self) -> None: self._set_status("Text tool ready")

    def _set_zoom(self, value: float) -> None:
        if self._canvas is not None:
            self._canvas.set_zoom(value)
        self._set_status(f"Zoom {value:.2f}%")

    def _update_canvas_coordinates(self, x: float, y: float) -> None:
        for item in self._status_items:
            if item.text().startswith("X:"):
                item.setText(f"X: {x:.0f}  Y: {y:.0f}")
                return

    def _set_status(self, text: str) -> None:
        if self._status_items:
            self._status_items[0].setText(f"Tool Select: {text}")

    def _minimize_window(self) -> None:
        self.setWindowState(self.windowState() | Qt.WindowMinimized)
        self.showMinimized()

    def _toggle_maximize(self) -> None:
        if self._is_manually_maximized:
            self._restore_from_maximize()
            return
        self._normal_geometry = self.geometry()
        screen = self.windowHandle().screen() if self.windowHandle() is not None else self.screen()
        if screen is not None:
            self.setGeometry(screen.availableGeometry())
        else:
            self.showMaximized()
        self._is_manually_maximized = True
        if self._maximize_button is not None:
            self._maximize_button.setText("[ ]")
            self._maximize_button.setToolTip("Restore")

    def _restore_from_maximize(self) -> None:
        self.showNormal()
        if self._normal_geometry is not None:
            self.setGeometry(self._normal_geometry)
        self._is_manually_maximized = False
        if self._maximize_button is not None:
            self._maximize_button.setText("[]")
            self._maximize_button.setToolTip("Maximize")

    def _build_home_icon(self) -> QIcon:
        pixmap = QPixmap(42, 30)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        base = QPainterPath()
        base.addRoundedRect(QRectF(5, 4.5, 32, 22), 8, 8)
        base_gradient = QLinearGradient(5, 4, 37, 27)
        base_gradient.setColorAt(0.0, QColor("#fff9e8"))
        base_gradient.setColorAt(0.52, QColor("#b8ecff"))
        base_gradient.setColorAt(1.0, QColor("#5e72c9"))
        painter.fillPath(base, base_gradient)
        painter.setPen(QPen(QColor("#ffffff"), 1.1))
        painter.drawPath(base)
        roof = QPolygonF([QPointF(10.5, 15.2), QPointF(21, 6.8), QPointF(31.5, 15.2), QPointF(28.8, 17.8), QPointF(21, 11.5), QPointF(13.2, 17.8)])
        roof_gradient = QLinearGradient(11, 7, 31, 18)
        roof_gradient.setColorAt(0.0, QColor("#ff9b42"))
        roof_gradient.setColorAt(1.0, QColor("#d44777"))
        painter.setBrush(roof_gradient)
        painter.drawPolygon(roof)
        body = QPainterPath()
        body.addRoundedRect(QRectF(14, 15, 14, 9), 2.4, 2.4)
        body_gradient = QLinearGradient(14, 15, 28, 24)
        body_gradient.setColorAt(0.0, QColor("#ffffff"))
        body_gradient.setColorAt(0.48, QColor("#4ed8c3"))
        body_gradient.setColorAt(1.0, QColor("#24548f"))
        painter.fillPath(body, body_gradient)
        painter.drawPath(body)
        painter.end()
        return QIcon(pixmap)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        _apply_rounded_mask(self, 18)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and event.position().y() <= 46:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_position is not None and event.buttons() & Qt.LeftButton and not self._is_manually_maximized:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_position = None
        event.accept()

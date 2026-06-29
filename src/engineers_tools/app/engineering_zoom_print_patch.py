"""Workspace scale, zoom-pan, asset icons, and print setup patch."""

from __future__ import annotations

import logging
import math
from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QCursor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .interaction_ui_patch import _asset_icon_path, _paint_asset_icon


WORKSPACE_SIZE_MM = (400.0, 220.0)


def _first_existing(names: tuple[str, ...]) -> str | None:
    for name in names:
        if _asset_icon_path(name) is not None:
            return name
    return None


def _paint_first_asset(painter: QPainter, names: tuple[str, ...], rect: QRectF) -> bool:
    name = _first_existing(names)
    return bool(name and _paint_asset_icon(painter, name, rect))


def _asset_cursor(names: tuple[str, ...], fallback: Qt.CursorShape, hot_x: int = 10, hot_y: int = 10) -> QCursor:
    name = _first_existing(names)
    if name is None:
        return QCursor(fallback)
    pixmap = QPixmap(str(_asset_icon_path(name)))
    if pixmap.isNull():
        return QCursor(fallback)
    return QCursor(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation), hot_x, hot_y)


def _asset_icon(names: tuple[str, ...], fallback: QIcon | None = None) -> QIcon:
    pixmap = QPixmap(36, 36)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    ok = _paint_first_asset(painter, names, QRectF(3, 3, 30, 30))
    painter.end()
    if ok:
        return QIcon(pixmap)
    return fallback or QIcon()


def _printer_icon(name: str, active: bool = False) -> QIcon:
    lower = name.lower()
    pixmap = QPixmap(72, 72)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    shadow = QColor("#203040")
    shadow.setAlpha(35)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(shadow)
    painter.drawRoundedRect(QRectF(14, 18, 46, 42).translated(2, 3), 9, 9)

    shell = QLinearGradient(14, 16, 58, 60)
    shell.setColorAt(0.0, QColor("#ffffff"))
    shell.setColorAt(0.45, QColor("#d6dde6"))
    shell.setColorAt(1.0, QColor("#53606d"))
    painter.setBrush(shell)
    painter.setPen(QPen(QColor("#27313b"), 2.0))
    painter.drawRoundedRect(QRectF(14, 20, 46, 32), 8, 8)

    paper = QLinearGradient(21, 8, 51, 34)
    paper.setColorAt(0.0, QColor("#ffffff"))
    paper.setColorAt(1.0, QColor("#e9f3ff"))
    painter.setBrush(paper)
    painter.setPen(QPen(QColor("#708090"), 1.6))
    painter.drawRoundedRect(QRectF(21, 8, 30, 22), 4, 4)

    accent = QColor("#f28a1d")
    if "pdf" in lower:
        accent = QColor("#2d7eea")
    elif "fax" in lower:
        accent = QColor("#6b7280")
    elif "epson" in lower:
        accent = QColor("#1d63d1")
    elif "canon" in lower:
        accent = QColor("#d62728")
    painter.setBrush(accent)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(20, 44, 34, 7), 2, 2)
    painter.drawEllipse(QRectF(48, 25, 7, 7))

    if active:
        painter.setBrush(QColor("#1d63d1"))
        painter.setPen(QPen(QColor("#ffffff"), 1.5))
        painter.drawEllipse(QRectF(50, 48, 16, 16))
        painter.drawLine(QPointF(54, 56), QPointF(58, 60))
        painter.drawLine(QPointF(58, 60), QPointF(63, 52))

    painter.end()
    return QIcon(pixmap)


def _set_asset_cursor(widget: QWidget, names: tuple[str, ...], fallback: Qt.CursorShape, hot_x: int = 10, hot_y: int = 10) -> None:
    widget.setCursor(_asset_cursor(names, fallback, hot_x, hot_y))


def _start_tool_asset(key: str) -> tuple[str, ...]:
    return {
        "select": ("select_edit_object.svg", "mouse_cursor.svg"),
        "line": ("line.svg",),
        "vector": ("vector.svg",),
        "angle": ("angle_moment.svg",),
        "text": ("text.svg",),
        "grid": ("grid.svg",),
        "snap": ("snap.svg",),
        "unit": ("unit.svg",),
        "ruler": ("ruler.svg",),
        "zoom": ("zoom.svg",),
    }.get(key, ())


def _workspace_page_count(workspace: QWidget | None) -> int:
    if workspace is None:
        return 1
    for name in ("_pages", "pages", "_page_buttons", "_page_tabs"):
        value = getattr(workspace, name, None)
        if isinstance(value, (list, tuple, dict)) and value:
            return max(1, len(value))
    canvas = getattr(workspace, "_canvas", None)
    if callable(canvas):
        canvas = canvas()
    objects = getattr(canvas, "objects", None)
    if isinstance(objects, list):
        return 1
    return 1


class PrintPreviewPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(230, 300)
        self._paper_name = "Workspace"
        self._page_count = 1

    def set_page_count(self, value: int) -> None:
        self._page_count = max(1, value)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#f7faff"))

        outer = QRectF(16, 16, self.width() - 32, self.height() - 32)
        card = QPainterPath()
        card.addRoundedRect(outer, 14, 14)
        painter.fillPath(card, QColor("#ffffff"))
        painter.setPen(QPen(QColor("#d3dde8"), 1.2))
        painter.drawPath(card)

        title_pen = QPen(QColor("#1f2d3d"))
        painter.setPen(title_pen)
        painter.drawText(QRectF(outer.left() + 12, outer.top() + 10, outer.width() - 24, 22), Qt.AlignmentFlag.AlignLeft, "Preview")

        paper_width = outer.width() * 0.55
        paper_height = paper_width * 1.42
        if paper_height > outer.height() - 82:
            paper_height = outer.height() - 82
            paper_width = paper_height / 1.42
        paper = QRectF(
            outer.center().x() - paper_width / 2,
            outer.top() + 48,
            paper_width,
            paper_height,
        )
        shadow = QColor("#172033")
        shadow.setAlpha(32)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(shadow)
        painter.drawRoundedRect(paper.translated(4, 5), 5, 5)
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#9fb0c1"), 1.2))
        painter.drawRoundedRect(paper, 5, 5)

        work = paper.adjusted(18, 20, -18, -22)
        painter.setBrush(QColor("#eaf4ff"))
        painter.setPen(QPen(QColor("#2b7de9"), 1.0, Qt.PenStyle.DashLine))
        painter.drawRoundedRect(work, 4, 4)

        painter.setPen(QPen(QColor("#536170"), 1.0))
        painter.drawText(
            QRectF(outer.left() + 12, outer.bottom() - 42, outer.width() - 24, 22),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._paper_name} | {self._page_count} page(s)",
        )
        painter.end()


def _paint_asset_or_arc(painter: QPainter, center: QPointF, radius: float, color: QColor, reverse: bool = False) -> None:
    painter.save()
    rect = QRectF(center.x() - radius * 1.55, center.y() - radius * 1.55, radius * 3.1, radius * 3.1)
    names = ("redo.svg",) if reverse else ("rotate_arrow_pro.svg", "rotate_arrow.svg", "rotate.svg", "rotation.svg", "layer_rotate.svg")
    if _paint_first_asset(painter, names, rect):
        painter.restore()
        return
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(color, 2.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawArc(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), 40 * 16, 275 * 16)
    tip = QPointF(center.x() + radius * 0.78, center.y() - radius * 0.62)
    tail = QPointF(center.x() + radius * 0.10, center.y() - radius * 0.98)
    direction = tip - tail
    length = max(0.01, math.hypot(direction.x(), direction.y()))
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    size = max(6.5, radius * 0.9)
    base = QPointF(tip.x() - unit.x() * size, tip.y() - unit.y() * size)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(
        QPolygonF(
        [
            tip,
            QPointF(base.x() + normal.x() * size * 0.55, base.y() + normal.y() * size * 0.55),
            QPointF(base.x() - normal.x() * size * 0.55, base.y() - normal.y() * size * 0.55),
        ]
        )
    )
    painter.restore()


def _layer_asset_icon(kind: str, active: bool = True) -> QIcon:
    candidates = {
        "eye": ("eye_open.svg", "eye.svg", "show.svg", "layer_eye.svg") if active else ("eye_closed.svg", "hide.svg", "layer_eye_closed.svg"),
        "lock": ("lock_closed.svg", "lock.svg", "locked.svg", "layer_lock_closed.svg") if active else ("lock_open.svg", "unlock.svg", "unlocked.svg", "layer_lock_open.svg"),
        "rotate": ("rotate_arrow_pro.svg", "rotate_arrow.svg", "rotate.svg", "rotation.svg", "layer_rotate.svg"),
        "rotation": ("rotate_arrow_pro.svg", "rotate_arrow.svg", "rotate.svg", "rotation.svg", "layer_rotate.svg"),
    }.get(kind, ("rotate.svg",))
    pixmap = QPixmap(34, 34)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    shell = QPainterPath()
    shell.addRoundedRect(QRectF(2.5, 2.5, 29, 29), 10, 10)
    gradient = QLinearGradient(2, 2, 32, 32)
    gradient.setColorAt(0.0, QColor("#ffffff"))
    gradient.setColorAt(0.50, QColor("#e8f8ff" if active else "#eef1f5"))
    gradient.setColorAt(1.0, QColor("#5fd0ea" if active else "#9aa9ba"))
    painter.fillPath(shell, gradient)
    painter.setPen(QPen(QColor("#55708f"), 1.1))
    painter.drawPath(shell)
    if not _paint_first_asset(painter, candidates, QRectF(6, 6, 22, 22)):
        _paint_asset_or_arc(painter, QPointF(17, 17), 8.3, QColor("#132238"))
    if not active:
        painter.setPen(QPen(QColor("#d44777"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(8, 26), QPointF(26, 8))
    painter.end()
    return QIcon(pixmap)


def _page_rect(canvas) -> QRectF:
    getter = getattr(canvas, "_page_rect", None)
    if callable(getter):
        return QRectF(getter())
    return QRectF(0, 0, max(1, canvas.width()), max(1, canvas.height()))


def _page_mm(canvas) -> tuple[float, float]:
    width, height = getattr(canvas, "_page_setup_size_mm", WORKSPACE_SIZE_MM)
    return max(1.0, float(width)), max(1.0, float(height))


def _scene_unit_px(canvas, value: float, unit: str, unit_to_mm: dict[str, float]) -> float:
    page = _page_rect(canvas)
    width_mm, _height_mm = _page_mm(canvas)
    return max(0.25, page.width() * value * unit_to_mm[unit] / width_mm)


def _scene_to_view(canvas, point: QPointF) -> QPointF:
    zoom = max(0.01, float(getattr(canvas, "_zoom", 1.0)))
    pan = getattr(canvas, "_pan_offset", QPointF(0, 0))
    center = QPointF(canvas.width() / 2.0, canvas.height() / 2.0)
    return QPointF(center.x() + pan.x() + (point.x() - center.x()) * zoom, center.y() + pan.y() + (point.y() - center.y()) * zoom)


def _view_to_scene(canvas, point: QPointF) -> QPointF:
    zoom = max(0.01, float(getattr(canvas, "_zoom", 1.0)))
    pan = getattr(canvas, "_pan_offset", QPointF(0, 0))
    center = QPointF(canvas.width() / 2.0, canvas.height() / 2.0)
    return QPointF(((point.x() - center.x() - pan.x()) / zoom) + center.x(), ((point.y() - center.y() - pan.y()) / zoom) + center.y())


class PrintSetupDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectHelpDialog")
        self.setWindowTitle("Print Setup")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.resize(780, 500)
        self._drag_offset: QPoint | None = None
        self._printer = None
        self._printer_cards: list[QToolButton] = []
        self._selected_printer_name = ""
        self._page_count = _workspace_page_count(parent)

        shell = QWidget()
        shell.setObjectName("ProjectHelpShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 14)
        layout.setSpacing(10)
        layout.addWidget(self._header())
        body = QHBoxLayout()
        body.setContentsMargins(16, 10, 16, 0)
        body.setSpacing(14)

        settings = QVBoxLayout()
        settings.setContentsMargins(0, 0, 0, 0)
        settings.setSpacing(10)
        label = QLabel("Printer")
        label.setObjectName("DialogSectionTitle")
        settings.addWidget(label)
        self._printer_grid = QGridLayout()
        self._printer_grid.setContentsMargins(0, 0, 0, 0)
        self._printer_grid.setHorizontalSpacing(10)
        self._printer_grid.setVerticalSpacing(10)
        self._printer_group = QButtonGroup(self)
        self._printer_group.setExclusive(True)
        self._printer_group.idClicked.connect(self._select_printer_index)
        self._printers = QComboBox()
        self._printers.setObjectName("FileTypeCombo")
        self._printers.hide()
        self._load_printers()
        settings.addLayout(self._printer_grid)

        copies_row = QHBoxLayout()
        copies_label = QLabel("Copies")
        copies_label.setObjectName("DialogSectionTitle")
        self._copies = QSpinBox()
        self._copies.setObjectName("ZoomSpinBox")
        self._copies.setRange(1, 999)
        self._copies.setValue(1)
        copies_row.addWidget(copies_label)
        copies_row.addWidget(self._copies, 1)
        settings.addLayout(copies_row)

        pages_label = QLabel("Pages")
        pages_label.setObjectName("DialogSectionTitle")
        settings.addWidget(pages_label)
        pages_row = QHBoxLayout()
        pages_row.addWidget(QLabel("From"))
        self._page_from = QSpinBox()
        self._page_from.setObjectName("ZoomSpinBox")
        self._page_from.setRange(1, self._page_count)
        self._page_from.setValue(1)
        pages_row.addWidget(self._page_from)
        pages_row.addWidget(QLabel("To"))
        self._page_to = QSpinBox()
        self._page_to.setObjectName("ZoomSpinBox")
        self._page_to.setRange(1, self._page_count)
        self._page_to.setValue(self._page_count)
        pages_row.addWidget(self._page_to)
        settings.addLayout(pages_row)
        self._page_from.valueChanged.connect(self._normalize_page_range)
        self._page_to.valueChanged.connect(self._normalize_page_range)

        native = QPushButton("System Print Setup")
        native.setObjectName("PrimaryDialogButton")
        native.clicked.connect(self._open_native_dialog)
        settings.addWidget(native)
        self._status = QLabel("Select a printer, then apply.")
        self._status.setObjectName("StatusItem")
        settings.addWidget(self._status)
        settings.addStretch(1)

        self._preview = PrintPreviewPanel(self)
        self._preview.set_page_count(self._page_count)
        body.addLayout(settings, 3)
        body.addWidget(self._preview, 2)
        layout.addLayout(body, 1)
        buttons = QHBoxLayout()
        buttons.setContentsMargins(16, 0, 16, 0)
        buttons.addStretch(1)
        print_button = QPushButton("Print")
        print_button.setObjectName("PrimaryDialogButton")
        print_button.clicked.connect(self.accept)
        buttons.addWidget(print_button)
        apply_button = QPushButton("Apply")
        apply_button.setObjectName("SecondaryDialogButton")
        apply_button.clicked.connect(self.accept)
        buttons.addWidget(apply_button)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryDialogButton")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

    def _header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("HelpHeader")
        header.setFixedHeight(44)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 8, 0)
        builder = getattr(self.parentWidget(), "_build_window_mark", None)
        mark = builder() if callable(builder) else QLabel("AT")
        mark.setFixedSize(36, 32)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(mark)
        title = QLabel("Print Setup")
        title.setObjectName("HelpTitle")
        layout.addWidget(title, 1)
        close = QPushButton("×")
        close.setObjectName("MenuDialogClose")
        close.setFixedSize(28, 26)
        close.clicked.connect(self.reject)
        layout.addWidget(close)
        return header

    def _load_printers(self) -> None:
        try:
            from PySide6.QtPrintSupport import QPrinterInfo
        except Exception as error:  # noqa: BLE001
            logging.exception("Print setup printer discovery failed: %s", error)
            self._printers.addItem("No Qt print support available")
            return
        printers = QPrinterInfo.availablePrinters()
        default = QPrinterInfo.defaultPrinter().printerName()
        if not printers:
            self._printers.addItem("No printers found")
            self._add_printer_card("No printers found", "", True)
            return
        for index, printer in enumerate(printers):
            name = printer.printerName()
            self._printers.addItem(name + ("  (Default)" if name == default else ""), name)
            checked = bool(name == default or (not default and index == 0))
            self._add_printer_card(name, name, checked)
        if default:
            index = self._printers.findData(default)
            if index >= 0:
                self._printers.setCurrentIndex(index)
                self._selected_printer_name = default
        elif self._printers.count() > 0:
            self._printers.setCurrentIndex(0)
            data = self._printers.currentData()
            self._selected_printer_name = data if isinstance(data, str) else self._printers.currentText()

    def _add_printer_card(self, title: str, data: str, checked: bool = False) -> None:
        button = QToolButton()
        button.setObjectName("PrinterCard")
        button.setCheckable(True)
        button.setChecked(checked)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setIcon(_printer_icon(title, checked))
        button.setIconSize(QSize(62, 62))
        button.setText(title)
        button.setMinimumSize(138, 112)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.setProperty("printerName", data)
        row = len(self._printer_cards) // 3
        column = len(self._printer_cards) % 3
        self._printer_grid.addWidget(button, row, column)
        self._printer_group.addButton(button, len(self._printer_cards))
        self._printer_cards.append(button)
        if checked:
            self._selected_printer_name = data or title

    def _normalize_page_range(self) -> None:
        if self._page_from.value() > self._page_to.value():
            sender = self.sender()
            if sender is self._page_from:
                self._page_to.setValue(self._page_from.value())
            else:
                self._page_from.setValue(self._page_to.value())

    def _select_printer_index(self, index: int) -> None:
        if index < 0 or index >= len(self._printer_cards):
            return
        for card_index, card in enumerate(self._printer_cards):
            active = card_index == index
            card.setIcon(_printer_icon(card.text(), active))
            card.setProperty("active", active)
        card = self._printer_cards[index]
        name = card.property("printerName")
        self._selected_printer_name = name if isinstance(name, str) and name else card.text()
        combo_index = self._printers.findData(self._selected_printer_name)
        if combo_index >= 0:
            self._printers.setCurrentIndex(combo_index)
        self._status.setText(f"Selected: {self._selected_printer_name}")
        if hasattr(self, "_preview"):
            self._preview._paper_name = self._selected_printer_name or "Printer"
            self._preview.update()

    def _open_native_dialog(self) -> None:
        try:
            from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        except Exception as error:  # noqa: BLE001
            logging.exception("Native print dialog import failed: %s", error)
            self._status.setText("Qt print support is not available.")
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        name = self._selected_printer_name or self._printers.currentData()
        if isinstance(name, str) and name:
            printer.setPrinterName(name)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._printer = printer
            self._status.setText(f"Selected: {printer.printerName()}")

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

    def selected_printer_name(self) -> str:
        if self._selected_printer_name:
            return self._selected_printer_name
        data = self._printers.currentData()
        return data if isinstance(data, str) else self._printers.currentText()

    def settings(self) -> dict[str, object]:
        return {
            "printer": self.selected_printer_name(),
            "copies": self._copies.value(),
            "page_from": self._page_from.value(),
            "page_to": self._page_to.value(),
        }


def apply_engineering_zoom_print_patch() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from ..ui import start_bar as sb
    except Exception:
        logging.exception("engineering_zoom_print_patch: imports failed")
        return

    if getattr(edw.EngineeringDesignWorkspace, "_zoom_print_patch_applied", False):
        return

    original_canvas_init = edw.EngineeringCanvas.__init__
    original_mouse_press = edw.EngineeringCanvas.mousePressEvent
    original_mouse_move = edw.EngineeringCanvas.mouseMoveEvent
    original_mouse_release = edw.EngineeringCanvas.mouseReleaseEvent
    original_ensure_hooks = sb.StartBar._ensure_canvas_hooks
    original_event_filter = sb.StartBar.eventFilter
    original_activate_zoom = sb.StartBar._activate_zoom
    original_layer_button = edw.EngineeringDesignWorkspace._layer_button
    original_history_icon = edw.EngineeringDesignWorkspace._build_history_icon
    original_tool_icon = sb._tool_icon
    original_mini_zoom_icon = sb._mini_zoom_icon
    original_zoom_cursor = sb._zoom_cursor

    def canvas_init(self, *args, **kwargs):
        original_canvas_init(self, *args, **kwargs)
        self._page_setup_size_mm = WORKSPACE_SIZE_MM
        self._pan_offset = QPointF(0, 0)

    def to_canvas_point(self, point: QPointF) -> QPointF:
        return _view_to_scene(self, point)

    def set_zoom(self, zoom_percent: float) -> None:
        self._zoom = max(0.05, zoom_percent / 100.0)
        if self._zoom <= 1.0001:
            self._pan_offset = QPointF(0, 0)
        self.update()

    def paint_event(self, event) -> None:
        if not hasattr(self, "_pan_offset"):
            self._pan_offset = QPointF(0, 0)
        QWidget.paintEvent(self, event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#fbfdff"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pan = getattr(self, "_pan_offset", QPointF(0, 0))
        painter.translate(self.width() / 2 + pan.x(), self.height() / 2 + pan.y())
        painter.scale(self._zoom, self._zoom)
        painter.translate(-self.width() / 2, -self.height() / 2)
        self._paint_grid(painter)
        group_id = self._selection_group_id()
        for index, obj in enumerate(self.objects):
            if obj.visible:
                self._paint_object(painter, obj)
                if index in self.selected_indices and group_id is None:
                    self._paint_selection_frame(painter, obj)
        if group_id is not None:
            self._paint_group_selection(painter)
        if self._selection_rect is not None:
            fill = QColor("#2f7df6")
            fill.setAlpha(28)
            painter.fillRect(self._selection_rect, fill)
            painter.setPen(QPen(QColor("#2f7df6"), 1.2, Qt.PenStyle.DashLine))
            painter.drawRect(self._selection_rect)
        painter.end()

    def draw_arc_arrow(painter, center, radius, color, reverse=False):
        _paint_asset_or_arc(painter, center, radius, color, reverse)

    def build_history_icon(self, direction: str) -> QIcon:
        fallback = None
        icon = _asset_icon(("undo.svg",) if direction == "undo" else ("redo.svg",), fallback)
        if not icon.isNull():
            return icon
        return original_history_icon(self, direction)

    def start_tool_icon(key: str) -> QIcon:
        names = _start_tool_asset(key)
        if names:
            return _asset_icon(names, original_tool_icon(key))
        return original_tool_icon(key)

    def mini_zoom_icon(action: str) -> QIcon:
        names = {
            "zoom_in": ("zoom_in.svg",),
            "zoom_out": ("zoom_out.svg",),
            "zoom_fit": ("zoom_fit.svg",),
        }.get(action, ())
        if names:
            return _asset_icon(names, original_mini_zoom_icon(action))
        return original_mini_zoom_icon(action)

    def zoom_cursor(mode: str) -> QCursor:
        names = ("zoom_in.svg",) if mode == "zoom_in" else ("zoom_out.svg",)
        asset = _first_existing(names)
        if asset is None:
            return original_zoom_cursor(mode)
        return _asset_cursor((asset,), Qt.CursorShape.CrossCursor, 12, 12)

    def canvas_mouse_press(self, event) -> None:
        original_mouse_press(self, event)
        if getattr(self, "_drag_action", None) == "rotate":
            self.setCursor(_asset_cursor(("hand_closed.svg", "closed_hand.svg", "grab.svg", "mouse_cursor_closed.svg"), Qt.CursorShape.ClosedHandCursor, 12, 12))
        elif getattr(self, "_drag_action", None) == "move":
            self.setCursor(_asset_cursor(("move.svg", "move_cursor.svg", "cursor_move.svg"), Qt.CursorShape.SizeAllCursor, 16, 16))

    def canvas_mouse_move(self, event) -> None:
        original_mouse_move(self, event)
        action = getattr(self, "_drag_action", None)
        if action == "rotate":
            self.setCursor(_asset_cursor(("hand_closed.svg", "closed_hand.svg", "grab.svg", "mouse_cursor_closed.svg"), Qt.CursorShape.ClosedHandCursor, 12, 12))
        elif action == "move":
            self.setCursor(_asset_cursor(("move.svg", "move_cursor.svg", "cursor_move.svg"), Qt.CursorShape.SizeAllCursor, 16, 16))

    def canvas_mouse_release(self, event) -> None:
        original_mouse_release(self, event)
        if getattr(self, "_zoom", 1.0) > 1.0001:
            self.setCursor(_asset_cursor(("hand_open.svg", "open_hand.svg", "hand.svg", "mouse_cursor.svg"), Qt.CursorShape.OpenHandCursor, 12, 12))

    def layer_button(self, kind: str, active: bool, tooltip: str, callback):
        button = original_layer_button(self, kind, active, tooltip, callback)
        button.setIcon(_layer_asset_icon(kind, active))
        button.setIconSize(QSize(23, 23))
        return button

    def unit_to_canvas_px(self, value: float, unit: str) -> float:
        canvas = self._canvas()
        if canvas is not None:
            return max(0.25, _scene_unit_px(canvas, value, unit, sb.UNIT_TO_MM) * max(0.01, getattr(canvas, "_zoom", 1.0)))
        return max(1.0, value * sb.UNIT_TO_MM[unit] * sb.MM_TO_SCREEN_PX)

    def center_ruler_origin(self) -> None:
        canvas = self._canvas()
        if canvas is not None:
            self._ruler_origin = _scene_to_view(canvas, _page_rect(canvas).center())
            self._ruler_corner_origin_active = False
            self._ruler_previous_origin = None
            self._ruler_previous_origin_custom = False

    def toggle_ruler_corner_origin(self) -> None:
        canvas = self._canvas()
        if canvas is None:
            return
        if self._ruler_corner_origin_active:
            previous = QPointF(self._ruler_previous_origin) if self._ruler_previous_origin is not None else None
            previous_custom = self._ruler_previous_origin_custom
            self._ruler_corner_origin_active = False
            self._ruler_previous_origin = None
            self._ruler_previous_origin_custom = False
            if previous is None:
                center_ruler_origin(self)
                self._set_ruler_origin(QPointF(self._ruler_origin), custom=False)
            else:
                self._set_ruler_origin(previous, custom=previous_custom)
            return
        self._ruler_previous_origin = QPointF(self._ruler_origin)
        self._ruler_previous_origin_custom = self._ruler_origin_custom
        self._ruler_corner_origin_active = True
        self._set_ruler_origin(_scene_to_view(canvas, _page_rect(canvas).topLeft()), custom=True)

    def ensure_canvas_hooks(self) -> None:
        original_ensure_hooks(self)
        canvas = self._canvas()
        if canvas is None:
            return

        def paint_grid(canvas_self, painter: QPainter) -> None:
            page = _page_rect(canvas_self)
            painter.save()
            shadow = QPainterPath()
            shadow.addRoundedRect(page.translated(2, 2), 5, 5)
            color = QColor("#4a617a")
            color.setAlpha(28)
            painter.fillPath(shadow, color)
            painter.setBrush(QColor("#ffffff"))
            painter.setPen(QPen(QColor("#ccd9e6"), 1.0))
            painter.drawRoundedRect(page, 5, 5)
            if getattr(canvas_self, "_grid_visible", True):
                spacing = max(0.25, _scene_unit_px(canvas_self, self._grid_spacing, self._unit, sb.UNIT_TO_MM))
                origin = _view_to_scene(canvas_self, self._ruler_origin)
                painter.setClipRect(page)
                painter.setPen(QPen(QColor(70, 96, 130, 42), 1))
                x = origin.x()
                while x <= page.right():
                    painter.drawLine(QPointF(x, page.top()), QPointF(x, page.bottom()))
                    x += spacing
                x = origin.x() - spacing
                while x >= page.left():
                    painter.drawLine(QPointF(x, page.top()), QPointF(x, page.bottom()))
                    x -= spacing
                y = origin.y()
                while y <= page.bottom():
                    painter.drawLine(QPointF(page.left(), y), QPointF(page.right(), y))
                    y += spacing
                y = origin.y() - spacing
                while y >= page.top():
                    painter.drawLine(QPointF(page.left(), y), QPointF(page.right(), y))
                    y -= spacing
            painter.restore()

        canvas._paint_grid = paint_grid.__get__(canvas, canvas.__class__)
        canvas._grid_spacing = self._grid_spacing
        canvas._grid_unit = self._unit
        canvas.update()

    def apply_drag_zoom(self, mode: str, rect: QRect) -> None:
        canvas = self._canvas()
        if canvas is None or rect.width() < 8 or rect.height() < 8:
            self._set_host_status("Zoom canceled")
            return
        current = getattr(canvas, "_zoom", 1.0) * 100.0
        canvas_area = max(1.0, float(canvas.width() * canvas.height()))
        rect_area = max(1.0, float(rect.width() * rect.height()))
        raw = math.sqrt(canvas_area / rect_area)
        factor = 1.0 + min(0.55, max(0.08, (raw - 1.0) * 0.16))
        value = current * factor if mode == "zoom_in" else current / factor
        self._set_zoom_value(max(5.0, min(3200.0, value)))
        self._set_host_status(f"{'Zoom In' if mode == 'zoom_in' else 'Zoom Out'} active | {value:.2f}%")
        canvas.setCursor(sb._zoom_cursor(mode))

    def activate_zoom(self, mode: str) -> None:
        original_activate_zoom(self, mode)
        canvas = self._canvas()
        if canvas is not None and mode in {"zoom_in", "zoom_out"}:
            canvas.setFocus(Qt.FocusReason.MouseFocusReason)
            canvas.setCursor(sb._zoom_cursor(mode))

    def event_filter(self, watched, event) -> bool:
        canvas = self._canvas()
        if watched is canvas and canvas is not None:
            if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
                self._zoom_mode = None
                self._zoom_origin = None
                if self._rubber_band is not None:
                    self._rubber_band.hide()
                canvas.unsetCursor()
                return True
            if self._zoom_mode in {"zoom_in", "zoom_out"}:
                if event.type() in {QEvent.Type.Enter, QEvent.Type.MouseMove} and self._zoom_origin is None:
                    canvas.setCursor(sb._zoom_cursor(self._zoom_mode))
                    return event.type() == QEvent.Type.MouseMove
                if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                    canvas.setCursor(sb._zoom_cursor(self._zoom_mode))
                    self._zoom_origin = event.position().toPoint()
                    self._ensure_rubber_band()
                    if self._rubber_band is not None:
                        self._rubber_band.setGeometry(QRect(self._zoom_origin, QSize()))
                        self._rubber_band.show()
                    return True
                if event.type() == QEvent.Type.MouseMove and self._zoom_origin is not None:
                    self._ensure_rubber_band()
                    if self._rubber_band is not None:
                        self._rubber_band.setGeometry(QRect(self._zoom_origin, event.position().toPoint()).normalized())
                    return True
                if event.type() == QEvent.Type.MouseButtonRelease and self._zoom_origin is not None:
                    rect = QRect(self._zoom_origin, event.position().toPoint()).normalized()
                    if self._rubber_band is not None:
                        self._rubber_band.hide()
                    self._zoom_origin = None
                    if rect.width() < 8 or rect.height() < 8:
                        self._zoom_mode = None
                        canvas.unsetCursor()
                        self._set_host_status("Zoom mode closed")
                    else:
                        apply_drag_zoom(self, self._zoom_mode, rect)
                    return True
            if getattr(canvas, "_zoom", 1.0) > 1.0001 and self._zoom_mode is None:
                if event.type() == QEvent.Type.MouseButtonPress and event.button() in {Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton}:
                    self._pan_active = True
                    self._pan_origin = event.position().toPoint()
                    self._pan_start_offset = QPointF(getattr(canvas, "_pan_offset", QPointF(0, 0)))
                    canvas.setCursor(_asset_cursor(("hand_closed.svg", "closed_hand.svg", "grab.svg", "mouse_cursor_closed.svg"), Qt.CursorShape.ClosedHandCursor, 12, 12))
                    return True
                if event.type() == QEvent.Type.MouseMove and getattr(self, "_pan_active", False):
                    delta = event.position().toPoint() - getattr(self, "_pan_origin", QPoint())
                    start = getattr(self, "_pan_start_offset", QPointF(0, 0))
                    canvas._pan_offset = QPointF(start.x() + delta.x(), start.y() + delta.y())
                    canvas.update()
                    self._position_rulers()
                    return True
                if event.type() == QEvent.Type.MouseButtonRelease and getattr(self, "_pan_active", False):
                    self._pan_active = False
                    canvas.setCursor(_asset_cursor(("hand_open.svg", "open_hand.svg", "hand.svg", "mouse_cursor.svg"), Qt.CursorShape.OpenHandCursor, 12, 12))
                    return True
        return original_event_filter(self, watched, event)

    def print_setup(self) -> None:
        dialog = PrintSetupDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._print_settings = dialog.settings()
            self._set_status(
                f"Print Setup: {self._print_settings['printer']} | "
                f"{self._print_settings['copies']} copy/copies | "
                f"pages {self._print_settings['page_from']}-{self._print_settings['page_to']}"
            )
        else:
            self._set_status("Print Setup canceled")

    edw.EngineeringCanvas.__init__ = canvas_init
    edw.EngineeringCanvas._to_canvas_point = to_canvas_point
    edw.EngineeringCanvas.set_zoom = set_zoom
    edw.EngineeringCanvas.paintEvent = paint_event
    edw.EngineeringCanvas.mousePressEvent = canvas_mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = canvas_mouse_move
    edw.EngineeringCanvas.mouseReleaseEvent = canvas_mouse_release
    edw._draw_arc_arrow = draw_arc_arrow
    edw._layer_icon = _layer_asset_icon
    edw.EngineeringDesignWorkspace._build_history_icon = build_history_icon
    edw.EngineeringDesignWorkspace._layer_button = layer_button
    edw.EngineeringDesignWorkspace._print_setup = print_setup
    sb._tool_icon = start_tool_icon
    sb._mini_zoom_icon = mini_zoom_icon
    sb._zoom_cursor = zoom_cursor
    sb.StartBar._unit_to_canvas_px = unit_to_canvas_px
    sb.StartBar._center_ruler_origin = center_ruler_origin
    sb.StartBar._toggle_ruler_corner_origin = toggle_ruler_corner_origin
    sb.StartBar._ensure_canvas_hooks = ensure_canvas_hooks
    sb.StartBar._apply_drag_zoom = apply_drag_zoom
    sb.StartBar._activate_zoom = activate_zoom
    sb.StartBar.eventFilter = event_filter
    edw.EngineeringDesignWorkspace._zoom_print_patch_applied = True
    logging.info("engineering_zoom_print_patch: installed")

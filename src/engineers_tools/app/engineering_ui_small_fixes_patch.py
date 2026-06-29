"""Final small UI fixes for rendering, cursors, layer icons and right properties panel."""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QCursor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

VERSION = "ui-small-fixes-4"
_ORIGINAL_EXPORT_RENDER = None
_ORIGINAL_EXPORT_WRITE_SVG = None
_ORIGINAL_SIDE_PANEL = None
_ORIGINAL_CANVAS_MOUSE_MOVE = None
_ORIGINAL_STARTBAR_INIT = None
_UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "px": 25.4 / 96.0, "pt": 25.4 / 72.0, "in": 25.4}


def _grid_requested(options: dict | None) -> bool:
    options = options or {}
    return bool(options.get("save_grid") or options.get("print_grid") or options.get("show_grid") or options.get("show_grade"))


def _workspace_page_size(workspace) -> tuple[float, float]:
    canvas = getattr(workspace, "_canvas", None)
    if canvas is not None:
        size = getattr(canvas, "_page_setup_size_mm", None)
        if isinstance(size, (tuple, list)) and len(size) == 2:
            return max(1.0, float(size[0])), max(1.0, float(size[1]))
    return 400.0, 220.0


def _workspace_grid_spacing_mm(workspace) -> float:
    start_bar = getattr(workspace, "_start_bar_widget", None)
    unit = getattr(start_bar, "_unit", "mm") if start_bar is not None else "mm"
    spacing = getattr(start_bar, "_grid_spacing", 10.0) if start_bar is not None else 10.0
    try:
        return max(0.25, float(spacing) * _UNIT_TO_MM.get(str(unit), 1.0))
    except Exception:
        return 10.0


def _draw_output_grid(painter: QPainter, target: QRectF, workspace) -> None:
    width_mm, height_mm = _workspace_page_size(workspace)
    spacing_mm = _workspace_grid_spacing_mm(workspace)
    x_step = max(3.0, target.width() * spacing_mm / width_mm)
    y_step = max(3.0, target.height() * spacing_mm / height_mm)
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    minor = QPen(QColor(84, 112, 148, 82), 1.0)
    major = QPen(QColor(39, 74, 116, 125), 1.15)
    x = target.left()
    index = 0
    while x <= target.right() + 0.5:
        painter.setPen(major if index % 5 == 0 else minor)
        painter.drawLine(QPointF(x, target.top()), QPointF(x, target.bottom()))
        x += x_step
        index += 1
    y = target.top()
    index = 0
    while y <= target.bottom() + 0.5:
        painter.setPen(major if index % 5 == 0 else minor)
        painter.drawLine(QPointF(target.left(), y), QPointF(target.right(), y))
        y += y_step
        index += 1
    painter.restore()


def _render_workspace_page(workspace, painter: QPainter, target: QRectF, show_grid: bool, transparent: bool = False) -> None:
    if workspace is None:
        if not transparent:
            painter.fillRect(target, QColor("#ffffff"))
        return
    old_options = dict(getattr(workspace, "_save_options", {}) or {})
    try:
        if not transparent:
            painter.fillRect(target, QColor("#ffffff"))
        if show_grid:
            _draw_output_grid(painter, target, workspace)
        workspace._save_options = dict(old_options, save_grid=False, print_grid=False, show_grid=False, show_grade=False)
        renderer = _ORIGINAL_EXPORT_RENDER
        if callable(renderer):
            renderer(workspace, painter, target, True)
            return
        try:
            from . import engineering_print_setup_hotfix as hotfix
            hotfix._fallback_render_engineering_export(workspace, painter, target, True)
        except Exception as error:  # noqa: BLE001
            logging.exception("engineering_ui_small_fixes_patch: fallback page render failed: %s", error)
    finally:
        workspace._save_options = old_options


def _unified_export_render(window, painter: QPainter, target: QRectF, transparent: bool = False) -> None:
    _render_workspace_page(window, painter, target, _grid_requested(dict(getattr(window, "_save_options", {}) or {})), transparent)


def _unified_write_svg(window, path: Path) -> bool:
    try:
        from . import engineering_export_patch as export_patch
    except Exception:
        return False
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return False
    width_mm, height_mm = _workspace_page_size(window)
    options = dict(getattr(window, "_save_options", {}) or {})
    objects = export_patch._visible_objects(canvas) if hasattr(export_patch, "_visible_objects") else [obj for obj in getattr(canvas, "objects", []) if getattr(obj, "visible", True)]
    background = "" if options.get("remove_white_background", False) else f'<rect width="{width_mm:.3f}" height="{height_mm:.3f}" fill="white"/>'
    grid = ""
    if _grid_requested(options):
        spacing_mm = _workspace_grid_spacing_mm(window)
        lines: list[str] = []
        x = 0.0
        index = 0
        while x <= width_mm + 0.001:
            color = "#9fb3cc" if index % 5 == 0 else "#c7d5e6"
            stroke = "0.35" if index % 5 == 0 else "0.22"
            lines.append(f'<line x1="{x:.3f}" y1="0" x2="{x:.3f}" y2="{height_mm:.3f}" stroke="{color}" stroke-width="{stroke}"/>')
            x += spacing_mm
            index += 1
        y = 0.0
        index = 0
        while y <= height_mm + 0.001:
            color = "#9fb3cc" if index % 5 == 0 else "#c7d5e6"
            stroke = "0.35" if index % 5 == 0 else "0.22"
            lines.append(f'<line x1="0" y1="{y:.3f}" x2="{width_mm:.3f}" y2="{y:.3f}" stroke="{color}" stroke-width="{stroke}"/>')
            y += spacing_mm
            index += 1
        grid = "\n".join(lines)
    source = export_patch._bounds(canvas, objects) if hasattr(export_patch, "_bounds") else QRectF(0, 0, max(1, canvas.width()), max(1, canvas.height()))
    printable = export_patch._printable(QRectF(0, 0, width_mm, height_mm), (width_mm, height_mm), getattr(canvas, "_page_setup_margins", None)) if hasattr(export_patch, "_printable") else QRectF(0, 0, width_mm, height_mm)
    scale = min(printable.width() / max(1.0, source.width()), printable.height() / max(1.0, source.height())) if objects else 1.0
    offset = QPointF(printable.center().x() - source.center().x() * scale, printable.center().y() - source.center().y() * scale)
    object_markup: list[str] = []
    for obj in objects:
        rect = QRectF(getattr(obj, "rect", QRectF()))
        x = rect.left() * scale + offset.x()
        y = rect.top() * scale + offset.y()
        width = rect.width() * scale
        height = rect.height() * scale
        name = str(getattr(obj, "name", "Object")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        object_markup.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" fill="#ffffff" stroke="#465d78" stroke-width="0.35"/><text x="{x + width / 2:.3f}" y="{y + height / 2:.3f}" text-anchor="middle" dominant-baseline="middle" font-size="4" fill="#132238">{name}</text>')
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:.3f}mm" height="{height_mm:.3f}mm" viewBox="0 0 {width_mm:.3f} {height_mm:.3f}">{background}{grid}{"".join(object_markup)}</svg>\n', encoding="utf-8")
    return True


def _render_print_preview(dialog, painter: QPainter, paper: QRectF) -> None:
    workspace = dialog.parentWidget() if dialog is not None else None
    show_grid = bool(getattr(dialog, "_print_grid", None) and dialog._print_grid.isChecked())
    _render_workspace_page(workspace, painter, paper.adjusted(8, 8, -8, -8), show_grid, False)


def _send_print_job(workspace, settings: dict[str, object]) -> bool:
    try:
        from PySide6.QtPrintSupport import QPrinter
        from . import engineering_print_setup_hotfix as hotfix
    except Exception as error:  # noqa: BLE001
        logging.exception("engineering_ui_small_fixes_patch: print imports failed: %s", error)
        return False
    try:
        printer_name = str(settings.get("printer") or "").strip()
        if not printer_name or "No printers" in printer_name:
            logging.error("engineering_ui_small_fixes_patch: no usable printer selected")
            return False
        pdf_output = ""
        if hotfix._is_pdf_printer_name(printer_name):
            pdf_output = hotfix._choose_pdf_output(workspace, printer_name)
            if not pdf_output:
                logging.info("engineering_ui_small_fixes_patch: pdf output canceled printer=%s", printer_name)
                return False
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(pdf_output)
        else:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPrinterName(printer_name)
            try:
                printer.setOutputFormat(QPrinter.OutputFormat.NativeFormat)
            except Exception:
                pass
        if hasattr(printer, "setFullPage"):
            printer.setFullPage(True)
        copies = max(1, int(settings.get("copies", 1) or 1))
        if hasattr(printer, "setCopyCount"):
            printer.setCopyCount(copies)
        page_count = hotfix._workspace_page_count(workspace)
        page_from = max(1, int(settings.get("page_from", 1) or 1))
        page_to = min(max(page_from, int(settings.get("page_to", page_count) or page_count)), max(1, page_count))
        if hasattr(printer, "setFromTo"):
            printer.setFromTo(page_from, page_to)
        try:
            printer.setPrintRange(QPrinter.PrintRange.PageRange)
        except Exception:
            pass
        show_grid = bool(settings.get("print_grid", False))
        logging.info("engineering_ui_small_fixes_patch: direct print version=%s printer=%s copies=%s pages=%s-%s grid=%s pdf=%s valid=%s", VERSION, printer_name, copies, page_from, page_to, show_grid, pdf_output, printer.isValid())
        painter = QPainter(printer)
        if not painter.isActive():
            logging.error("engineering_ui_small_fixes_patch: printer painter inactive printer=%s valid=%s output_file=%s", printer.printerName(), printer.isValid(), printer.outputFileName())
            return False
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            _render_workspace_page(workspace, painter, QRectF(0, 0, max(1, printer.width()), max(1, printer.height())), show_grid, False)
        finally:
            painter.end()
        logging.info("engineering_ui_small_fixes_patch: sent print job printer=%s output_file=%s copies=%s pages=%s-%s grid=%s", printer.printerName() or printer_name, pdf_output or printer.outputFileName(), copies, page_from, page_to, show_grid)
        return True
    except Exception as error:  # noqa: BLE001
        logging.exception("engineering_ui_small_fixes_patch: print failed: %s", error)
        return False


def _asset_cursor(file_name: str, fallback: QCursor, hot_x: int = 8, hot_y: int = 8, max_side: int = 24) -> QCursor:
    try:
        from . import interaction_ui_patch as interaction
        path = interaction._asset_icon_path(file_name)
    except Exception:
        path = None
    if path is None:
        return fallback
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return fallback
    if pixmap.width() > max_side or pixmap.height() > max_side:
        pixmap = pixmap.scaled(max_side, max_side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    safe_hot_x = max(0, min(int(hot_x), max(0, pixmap.width() - 1)))
    safe_hot_y = max(0, min(int(hot_y), max(0, pixmap.height() - 1)))
    return QCursor(pixmap, safe_hot_x, safe_hot_y)


def _set_canvas_hover_cursor(canvas, hover: str | None) -> None:
    if hover == "move":
        canvas.setCursor(_asset_cursor("move_cursor.svg", QCursor(Qt.CursorShape.SizeAllCursor), 12, 12, 24))
    elif hover == "rotate":
        canvas.setCursor(_asset_cursor("rotate_cursor.svg", QCursor(Qt.CursorShape.OpenHandCursor), 12, 12, 24))
    elif hover in {"resize_n", "resize_s"}:
        canvas.setCursor(_asset_cursor("resize_vertical.svg", QCursor(Qt.CursorShape.SizeVerCursor), 12, 12, 24))
    elif hover in {"resize_e", "resize_w"}:
        canvas.setCursor(_asset_cursor("resize_horizontal.svg", QCursor(Qt.CursorShape.SizeHorCursor), 12, 12, 24))
    elif hover in {"resize_ne", "resize_sw"}:
        canvas.setCursor(_asset_cursor("corner_resize_b.svg", QCursor(Qt.CursorShape.SizeBDiagCursor), 12, 12, 24))
    elif hover in {"resize_nw", "resize_se"}:
        canvas.setCursor(_asset_cursor("corner_resize_a.svg", QCursor(Qt.CursorShape.SizeFDiagCursor), 12, 12, 24))
    else:
        canvas.unsetCursor()


def _compact_cursor_from_asset(file_name: str, fallback: QCursor, hot_x: int = 8, hot_y: int = 8) -> QCursor:
    if "hand_pointer" in file_name:
        return _asset_cursor(file_name, fallback, hot_x, hot_y, 22)
    if "hand" in file_name:
        return _asset_cursor(file_name, fallback, hot_x, hot_y, 23)
    if "resize" in file_name or "move" in file_name or "rotate" in file_name or "corner" in file_name:
        return _asset_cursor(file_name, fallback, hot_x, hot_y, 24)
    return _asset_cursor(file_name, fallback, hot_x, hot_y, 22)


def _mouse_move_event(self, event) -> None:
    point = self._to_canvas_point(event.position())
    self.mouse_position_changed.emit(point.x(), point.y())
    if self._drag_action is not None:
        _set_canvas_hover_cursor(self, self._drag_action)
        self._apply_drag(point)
        event.accept()
        return
    if self._selection_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
        self._selection_rect = QRectF(self._selection_origin, point).normalized()
        self.update()
        event.accept()
        return
    _index, hover = self._hit_test_object(point)
    _set_canvas_hover_cursor(self, hover)
    event.accept()


def _layer_state_icon(kind: str, active: bool = True) -> QIcon:
    pixmap = QPixmap(30, 30)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    shell = QPainterPath(); shell.addRoundedRect(QRectF(2.5, 2.5, 25, 25), 8, 8)
    gradient = QLinearGradient(2, 2, 28, 28)
    gradient.setColorAt(0.0, QColor("#ffffff")); gradient.setColorAt(0.55, QColor("#e8f8ff" if active else "#eef1f5")); gradient.setColorAt(1.0, QColor("#63d5ed" if active else "#aab6c4"))
    painter.fillPath(shell, gradient); painter.setPen(QPen(QColor("#55708f"), 1.0)); painter.drawPath(shell)
    ink = QColor("#132238" if active else "#667789"); accent = QColor("#2f7df6" if active else "#8b98a8")
    painter.setPen(QPen(ink, 1.65, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)); painter.setBrush(Qt.BrushStyle.NoBrush)
    if kind == "eye":
        if active:
            eye = QPainterPath(); eye.moveTo(6.0, 15); eye.cubicTo(9.2, 9.2, 20.8, 9.2, 24.0, 15); eye.cubicTo(20.8, 20.8, 9.2, 20.8, 6.0, 15)
            painter.setBrush(QColor(255, 255, 255, 210)); painter.drawPath(eye); painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(accent); painter.drawEllipse(QPointF(15, 15), 3.6, 3.6); painter.setBrush(QColor("#07192f")); painter.drawEllipse(QPointF(15, 15), 1.55, 1.55); painter.setBrush(QColor("#ffffff")); painter.drawEllipse(QPointF(16.2, 13.8), 0.75, 0.75)
        else:
            painter.drawArc(QRectF(6.2, 10.8, 17.6, 8.4), 200 * 16, 140 * 16); painter.drawLine(QPointF(8, 15), QPointF(22, 15)); painter.drawLine(QPointF(10, 17.2), QPointF(8.8, 19.2)); painter.drawLine(QPointF(15, 17.8), QPointF(15, 20.2)); painter.drawLine(QPointF(20, 17.2), QPointF(21.2, 19.2))
    elif kind == "lock":
        painter.setPen(QPen(ink, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if active:
            painter.drawArc(QRectF(9.0, 7.0, 12.0, 12.0), 0, 180 * 16); painter.drawLine(QPointF(9, 13), QPointF(9, 16)); painter.drawLine(QPointF(21, 13), QPointF(21, 16))
        else:
            painter.drawArc(QRectF(10.0, 6.5, 12.0, 12.0), 35 * 16, 145 * 16); painter.drawLine(QPointF(20.5, 10.8), QPointF(23.8, 8.2))
        body = QPainterPath(); body.addRoundedRect(QRectF(7.6, 15.0, 14.8, 9.0), 2.8, 2.8)
        body_gradient = QLinearGradient(8, 15, 22, 24); body_gradient.setColorAt(0, QColor("#fff9de" if active else "#ffffff")); body_gradient.setColorAt(1, QColor("#ffc35a" if active else "#d7e2ef"))
        painter.setBrush(body_gradient); painter.drawPath(body); painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(ink); painter.drawEllipse(QPointF(15, 19.0), 1.2, 1.2); painter.drawRoundedRect(QRectF(14.4, 19.0, 1.2, 3.0), 0.6, 0.6)
    else:
        painter.setPen(QPen(ink, 1.9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)); painter.drawArc(QRectF(8.0, 8.0, 14.0, 14.0), 45 * 16, 280 * 16); painter.setBrush(ink); painter.drawPolygon(QPolygonF([QPointF(21.4, 9.9), QPointF(24.4, 13.0), QPointF(20.2, 13.7)]))
    painter.end(); return QIcon(pixmap)


def _layer_button(self, kind: str, active: bool, tooltip: str, callback) -> QPushButton:
    button = QPushButton(); button.setObjectName("LayerIconButton"); button.setToolTip(tooltip); button.setFixedSize(26, 24); button.setIcon(_layer_state_icon(kind, active)); button.setIconSize(QSize(23, 23)); button.setCursor(_asset_cursor("hand_pointer.svg", QCursor(Qt.CursorShape.PointingHandCursor), 10, 3, 22)); button.clicked.connect(callback); return button


def _build_empty_properties_panel(workspace) -> QWidget:
    panel = QWidget(); panel.setObjectName("SidePanel"); panel.setMinimumWidth(210)
    layout = QVBoxLayout(panel); layout.setContentsMargins(12, 12, 12, 12); layout.setSpacing(8)
    title = QLabel("Properties"); title.setObjectName("PanelTitle"); layout.addWidget(title)
    message = QLabel("No active selection.\n\nSelect a drawing tool, object, group, or layer to view and edit its properties here.")
    message.setObjectName("PanelItem"); message.setWordWrap(True); message.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft); message.setMinimumHeight(118); message.setStyleSheet("QLabel#PanelItem {background:rgba(255,255,255,150); border:1px solid #c3d0df; border-radius:10px; color:#39516f; font-size:11px; font-style:normal; font-weight:700; padding:9px;}"); layout.addWidget(message)
    hint = QLabel("Context properties will appear here after the active tool or selected object is known.")
    hint.setObjectName("PanelItem"); hint.setWordWrap(True); hint.setStyleSheet("QLabel#PanelItem {background:transparent; border:0; color:#6a7c91; font-size:10px; font-style:normal; font-weight:700; padding:2px;}"); layout.addWidget(hint); layout.addStretch(1)
    def refresh_properties_summary() -> None: return
    panel.refresh_properties_summary = refresh_properties_summary; return panel


def _install_rendering_patch() -> None:
    global _ORIGINAL_EXPORT_RENDER, _ORIGINAL_EXPORT_WRITE_SVG
    try:
        from . import engineering_export_patch as export_patch
        from . import engineering_print_setup_hotfix as hotfix
    except Exception:
        logging.exception("engineering_ui_small_fixes_patch: rendering imports failed"); return
    if _ORIGINAL_EXPORT_RENDER is None: _ORIGINAL_EXPORT_RENDER = getattr(export_patch, "_render", None)
    if _ORIGINAL_EXPORT_WRITE_SVG is None: _ORIGINAL_EXPORT_WRITE_SVG = getattr(export_patch, "_write_svg", None)
    export_patch._render = _unified_export_render; export_patch._write_svg = _unified_write_svg; hotfix._render_print_preview = _render_print_preview; hotfix._send_print_job = _send_print_job
    logging.info("engineering_ui_small_fixes_patch: unified grid/render pipeline installed version=%s", VERSION)


def _install_cursor_patch() -> None:
    global _ORIGINAL_CANVAS_MOUSE_MOVE, _ORIGINAL_STARTBAR_INIT
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from src.engineers_tools.ui import start_bar as sb
        from . import interaction_ui_patch as interaction
    except Exception:
        logging.exception("engineering_ui_small_fixes_patch: cursor imports failed"); return
    interaction._cursor_from_asset = _compact_cursor_from_asset
    if _ORIGINAL_CANVAS_MOUSE_MOVE is None: _ORIGINAL_CANVAS_MOUSE_MOVE = edw.EngineeringCanvas.mouseMoveEvent
    edw.EngineeringCanvas.mouseMoveEvent = _mouse_move_event
    if _ORIGINAL_STARTBAR_INIT is None: _ORIGINAL_STARTBAR_INIT = sb.StartBar.__init__
    def startbar_init(self, *args, **kwargs):
        _ORIGINAL_STARTBAR_INIT(self, *args, **kwargs)
        pointer = _asset_cursor("hand_pointer.svg", QCursor(Qt.CursorShape.PointingHandCursor), 10, 3, 22)
        for button in getattr(self, "_buttons", {}).values(): button.setCursor(pointer)
    if getattr(sb.StartBar, "_small_cursor_patch_version", "") != VERSION:
        sb.StartBar.__init__ = startbar_init; sb.StartBar._small_cursor_patch_version = VERSION
    logging.info("engineering_ui_small_fixes_patch: compact cursor and startbar pointer installed version=%s", VERSION)


def _install_layer_patch() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import engineering_export_patch as export_patch
    except Exception:
        logging.exception("engineering_ui_small_fixes_patch: layer imports failed"); return
    export_patch._better_layer_icon = _layer_state_icon; edw._layer_icon = _layer_state_icon; edw.EngineeringDesignWorkspace._layer_button = _layer_button
    logging.info("engineering_ui_small_fixes_patch: layer icons installed version=%s", VERSION)


def _install_properties_panel_patch() -> None:
    global _ORIGINAL_SIDE_PANEL
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_ui_small_fixes_patch: properties imports failed"); return
    if _ORIGINAL_SIDE_PANEL is None: _ORIGINAL_SIDE_PANEL = edw.EngineeringDesignWorkspace._build_side_panel
    def build_side_panel(self, title: str, rows: tuple[str, ...]) -> QWidget:
        if title == "Properties":
            panel = _build_empty_properties_panel(self); self._properties_panel_widget = panel; self._refresh_properties_summary_panel = panel.refresh_properties_summary; return panel
        return _ORIGINAL_SIDE_PANEL(self, title, rows)
    edw.EngineeringDesignWorkspace._build_side_panel = build_side_panel
    logging.info("engineering_ui_small_fixes_patch: empty right properties panel installed version=%s", VERSION)


def apply_engineering_ui_small_fixes_patch() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_ui_small_fixes_patch: engineering workspace import failed"); return
    if getattr(edw.EngineeringDesignWorkspace, "_ui_small_fixes_patch_version", "") == VERSION: return
    _install_rendering_patch(); _install_cursor_patch(); _install_layer_patch(); _install_properties_panel_patch()
    edw.EngineeringDesignWorkspace._ui_small_fixes_patch_version = VERSION
    logging.info("engineering_ui_small_fixes_patch: installed version=%s", VERSION)

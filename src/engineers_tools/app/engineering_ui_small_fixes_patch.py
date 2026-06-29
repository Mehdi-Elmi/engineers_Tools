"""Small UI fixes for print preview rendering and cursor polish."""
from __future__ import annotations

import logging

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPixmap

VERSION = "ui-small-fixes-1"


def _render_workspace_page(workspace, painter: QPainter, target: QRectF, print_grid: bool) -> None:
    """Render the real engineering page content into the target rect.

    This uses the export renderer when available, so preview and print share the
    same output pipeline as Save/Export. The grid flag is passed through the
    existing save_grid option because the export renderer already understands it.
    """
    if workspace is None:
        painter.fillRect(target, QColor("#ffffff"))
        return

    old_options = dict(getattr(workspace, "_save_options", {}) or {})
    workspace._save_options = dict(old_options, save_grid=bool(print_grid))
    try:
        from . import engineering_export_patch as export_patch
        renderer = getattr(export_patch, "_render", None)
        if callable(renderer):
            renderer(workspace, painter, target, False)
            return
    except Exception as error:  # noqa: BLE001
        logging.exception("engineering_ui_small_fixes_patch: export renderer failed: %s", error)

    try:
        from . import engineering_print_setup_hotfix as hotfix
        hotfix._fallback_render_engineering_export(workspace, painter, target, False)
    finally:
        workspace._save_options = old_options
        return

    workspace._save_options = old_options


def _render_print_preview(dialog, painter: QPainter, paper: QRectF) -> None:
    workspace = dialog.parentWidget() if dialog is not None else None
    print_grid = bool(getattr(dialog, "_print_grid", None) and dialog._print_grid.isChecked())
    target = paper.adjusted(8, 8, -8, -8)
    _render_workspace_page(workspace, painter, target, print_grid)


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
        page_to = max(page_from, int(settings.get("page_to", page_count) or page_count))
        page_to = min(max(1, page_count), page_to)
        if hasattr(printer, "setFromTo"):
            printer.setFromTo(page_from, page_to)
        try:
            printer.setPrintRange(QPrinter.PrintRange.PageRange)
        except Exception:
            pass

        print_grid = bool(settings.get("print_grid", False))
        logging.info(
            "engineering_ui_small_fixes_patch: direct print version=%s printer=%s copies=%s pages=%s-%s grid=%s pdf=%s valid=%s",
            VERSION,
            printer_name,
            copies,
            page_from,
            page_to,
            print_grid,
            pdf_output,
            printer.isValid(),
        )

        painter = QPainter(printer)
        if not painter.isActive():
            logging.error(
                "engineering_ui_small_fixes_patch: printer painter inactive printer=%s valid=%s output_file=%s",
                printer.printerName(),
                printer.isValid(),
                printer.outputFileName(),
            )
            return False
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            target = QRectF(0, 0, max(1, printer.width()), max(1, printer.height()))
            _render_workspace_page(workspace, painter, target, print_grid)
        finally:
            painter.end()

        logging.info(
            "engineering_ui_small_fixes_patch: sent print job printer=%s output_file=%s copies=%s pages=%s-%s grid=%s",
            printer.printerName() or printer_name,
            pdf_output or printer.outputFileName(),
            copies,
            page_from,
            page_to,
            print_grid,
        )
        return True
    except Exception as error:  # noqa: BLE001
        logging.exception("engineering_ui_small_fixes_patch: print failed: %s", error)
        return False


def _install_print_preview_patch() -> None:
    try:
        from . import engineering_print_setup_hotfix as hotfix
    except Exception:
        logging.exception("engineering_ui_small_fixes_patch: print hotfix import failed")
        return
    hotfix._render_print_preview = _render_print_preview
    hotfix._send_print_job = _send_print_job
    logging.info("engineering_ui_small_fixes_patch: print preview renderer installed version=%s", VERSION)


def _install_cursor_patch() -> None:
    try:
        from . import interaction_ui_patch as interaction
    except Exception:
        logging.exception("engineering_ui_small_fixes_patch: cursor patch import failed")
        return

    def compact_cursor_from_asset(file_name: str, fallback: QCursor, hot_x: int = 8, hot_y: int = 8) -> QCursor:
        path = interaction._asset_icon_path(file_name)
        if path is None:
            return fallback
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return fallback
        max_side = 28 if "hand" not in file_name else 30
        if pixmap.width() > max_side or pixmap.height() > max_side:
            pixmap = pixmap.scaled(max_side, max_side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        safe_hot_x = max(0, min(int(hot_x), max(0, pixmap.width() - 1)))
        safe_hot_y = max(0, min(int(hot_y), max(0, pixmap.height() - 1)))
        return QCursor(pixmap, safe_hot_x, safe_hot_y)

    interaction._cursor_from_asset = compact_cursor_from_asset
    logging.info("engineering_ui_small_fixes_patch: compact cursor loader installed version=%s", VERSION)


def apply_engineering_ui_small_fixes_patch() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_ui_small_fixes_patch: engineering workspace import failed")
        return
    if getattr(edw.EngineeringDesignWorkspace, "_ui_small_fixes_patch_version", "") == VERSION:
        return
    _install_print_preview_patch()
    _install_cursor_patch()
    edw.EngineeringDesignWorkspace._ui_small_fixes_patch_version = VERSION
    logging.info("engineering_ui_small_fixes_patch: installed version=%s", VERSION)

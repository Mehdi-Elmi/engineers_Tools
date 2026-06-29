"""Startup compatibility hooks for Engineer Tools."""

from __future__ import annotations

import builtins
import logging
import sys

_ORIGINAL_IMPORT = builtins.__import__
_INSTALLED = False


def _render_engineering_export_bridge(window, painter, target, transparent=False) -> None:
    try:
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QColor
    except Exception:  # pragma: no cover
        logging.exception("sitecustomize: Qt imports failed for print export bridge")
        return

    target = QRectF(target)
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        painter.fillRect(target, Qt.GlobalColor.transparent if transparent else QColor("#ffffff"))
        return

    if not transparent:
        painter.fillRect(target, QColor("#ffffff"))

    source_w = max(1, int(canvas.width()))
    source_h = max(1, int(canvas.height()))
    scale = min(target.width() / source_w, target.height() / source_h)
    target_w = source_w * scale
    target_h = source_h * scale

    painter.save()
    painter.translate(target.left() + (target.width() - target_w) / 2.0, target.top() + (target.height() - target_h) / 2.0)
    painter.scale(scale, scale)
    canvas.render(painter)
    painter.restore()


def _send_print_job_bridge(workspace, settings) -> bool:
    try:
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QPainter
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        from PySide6.QtWidgets import QDialog
    except Exception as error:  # pragma: no cover
        logging.exception("sitecustomize: print imports failed: %s", error)
        return False

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer_name = str((settings or {}).get("printer") or "")
    if printer_name and "No printers" not in printer_name:
        printer.setPrinterName(printer_name)

    copies = int((settings or {}).get("copies") or 1)
    page_from = int((settings or {}).get("page_from") or 1)
    page_to = int((settings or {}).get("page_to") or page_from)
    all_pages = bool((settings or {}).get("all_pages", page_from == 1 and page_to <= 1))

    try:
        printer.setCopyCount(max(1, copies))
        if not all_pages:
            printer.setFromTo(page_from, page_to)
            printer.setPrintRange(QPrinter.PrintRange.PageRange)
    except Exception:
        logging.exception("sitecustomize: printer range/copy setup failed")

    dialog = QPrintDialog(printer, workspace)
    dialog.setWindowTitle("Print")
    logging.info("sitecustomize: print job dialog opened printer=%s copies=%s pages=%s-%s all=%s", printer_name, copies, page_from, page_to, all_pages)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        logging.info("sitecustomize: print job canceled")
        return False

    painter = QPainter(printer)
    if not painter.isActive():
        logging.error("sitecustomize: printer painter is not active printer=%s", printer.printerName())
        return False
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        target = QRectF(0, 0, max(1, printer.width()), max(1, printer.height()))
        _render_engineering_export_bridge(workspace, painter, target, False)
    finally:
        painter.end()
    logging.info("sitecustomize: print job sent printer=%s copies=%s pages=%s-%s", printer.printerName(), copies, page_from, page_to)
    return True


def _patch_interaction_module(module) -> None:
    if module is None or not getattr(module, "__name__", "").endswith("interaction_ui_patch"):
        return
    if not hasattr(module, "_render_engineering_export"):
        module._render_engineering_export = _render_engineering_export_bridge
        logging.info("sitecustomize: installed _render_engineering_export bridge on %s", module.__name__)


def _patch_print_hotfix_module(module) -> None:
    if module is None or not getattr(module, "__name__", "").endswith("engineering_print_setup_hotfix"):
        return
    module._send_print_job = _send_print_job_bridge
    logging.info("sitecustomize: installed print hotfix bridge on %s", module.__name__)


def _patch_loaded_modules() -> None:
    for name, module in list(sys.modules.items()):
        if name.endswith("interaction_ui_patch"):
            _patch_interaction_module(module)
        elif name.endswith("engineering_print_setup_hotfix"):
            _patch_print_hotfix_module(module)


def _engineer_tools_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
    module = _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)
    text = str(name)
    if "interaction_ui_patch" in text or "engineering_print_setup_hotfix" in text:
        _patch_loaded_modules()
    return module


def _install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    builtins.__import__ = _engineer_tools_import
    _INSTALLED = True
    _patch_loaded_modules()
    logging.info("sitecustomize: Engineer Tools startup hooks installed")


_install()

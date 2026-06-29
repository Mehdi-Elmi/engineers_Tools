"""Print setup behavior hotfix for Engineering Design Tools."""

from __future__ import annotations

import logging

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton, QSpinBox, QToolButton


def _asset_path(name: str) -> str:
    try:
        from .interaction_ui_patch import _asset_icon_path
    except Exception:
        return ""
    path = _asset_icon_path(name)
    return path.as_posix() if path is not None else ""


def _style_print_spin(spin: QSpinBox, width: int = 68) -> None:
    up_icon = _asset_path("print_spin_up.svg")
    down_icon = _asset_path("print_spin_down.svg")
    spin.setObjectName("PrintSpinBox")
    spin.setFixedWidth(width)
    spin.setMinimumHeight(29)
    spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
    spin.setStyleSheet(
        """
        QSpinBox#PrintSpinBox {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:9px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800;
            padding:4px 25px 4px 7px;
        }
        QSpinBox#PrintSpinBox::up-button, QSpinBox#PrintSpinBox::down-button {
            width:24px; border:0px; margin:2px 2px 2px 0px;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #fff7d8, stop:0.52 #ffbd57, stop:1 #43d3bd);
            subcontrol-origin:border;
        }
        QSpinBox#PrintSpinBox::up-button { subcontrol-position:top right; border-top-right-radius:8px; }
        QSpinBox#PrintSpinBox::down-button { subcontrol-position:bottom right; border-bottom-right-radius:8px; }
        QSpinBox#PrintSpinBox::up-arrow { image:url(%s); width:14px; height:9px; }
        QSpinBox#PrintSpinBox::down-arrow { image:url(%s); width:14px; height:9px; }
        """ % (up_icon, down_icon)
    )


def _workspace_page_count(workspace) -> int:
    for name in ("_pages", "pages", "_page_buttons", "_page_tabs"):
        value = getattr(workspace, name, None)
        if isinstance(value, (list, tuple, dict)) and value:
            return max(1, len(value))
    return 1


def _fallback_render_engineering_export(window, painter: QPainter, target: QRectF, transparent: bool = False) -> None:
    from PySide6.QtGui import QColor
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


def _send_print_job(workspace, settings: dict[str, object]) -> bool:
    try:
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        from PySide6.QtWidgets import QDialog
        try:
            from .interaction_ui_patch import _render_engineering_export
        except Exception:
            _render_engineering_export = _fallback_render_engineering_export
    except Exception as error:  # noqa: BLE001
        logging.exception("engineering_print_setup_hotfix: print imports failed: %s", error)
        return False
    try:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer_name = str(settings.get("printer") or "").strip()
        if printer_name and "No printers found" not in printer_name:
            printer.setPrinterName(printer_name)
        if hasattr(printer, "setFullPage"):
            printer.setFullPage(True)

        copies = max(1, int(settings.get("copies", 1) or 1))
        if hasattr(printer, "setCopyCount"):
            printer.setCopyCount(copies)

        page_count = _workspace_page_count(workspace)
        all_pages = bool(settings.get("all_pages", True))
        page_from = max(1, int(settings.get("page_from", 1) or 1))
        page_to = max(page_from, int(settings.get("page_to", page_count) or page_count))
        if all_pages:
            page_from, page_to = 1, page_count
        elif hasattr(printer, "setFromTo"):
            printer.setFromTo(page_from, page_to)
        try:
            printer.setPrintRange(QPrinter.PrintRange.AllPages if all_pages else QPrinter.PrintRange.PageRange)
        except Exception:
            pass

        dialog = QPrintDialog(printer, workspace)
        dialog.setWindowTitle("Print")
        logging.info(
            "engineering_print_setup_hotfix: opening native print dialog printer=%s copies=%s pages=%s-%s all=%s",
            printer_name,
            copies,
            page_from,
            page_to,
            all_pages,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            logging.info("engineering_print_setup_hotfix: native print dialog canceled")
            return False

        painter = QPainter(printer)
        if not painter.isActive():
            logging.error("engineering_print_setup_hotfix: printer painter inactive printer=%s", printer.printerName())
            return False
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            target = QRectF(0, 0, max(1, printer.width()), max(1, printer.height()))
            _render_engineering_export(workspace, painter, target, False)
        finally:
            painter.end()
        logging.info(
            "engineering_print_setup_hotfix: sent print job printer=%s copies=%s pages=%s-%s all=%s",
            printer.printerName(),
            copies,
            page_from,
            page_to,
            all_pages,
        )
        return True
    except Exception as error:  # noqa: BLE001
        logging.exception("engineering_print_setup_hotfix: print failed: %s", error)
        return False


def _layout_contains_widget(layout, widget) -> bool:
    if layout is None or widget is None:
        return False
    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item.widget() is widget:
            return True
        child = item.layout()
        if child is not None and _layout_contains_widget(child, widget):
            return True
    return False


def _find_layout_with_widget(layout, widget):
    if layout is None or widget is None:
        return None
    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item.widget() is widget:
            return layout
        child = item.layout()
        found = _find_layout_with_widget(child, widget)
        if found is not None:
            return found
    return None


def apply_engineering_print_setup_hotfix() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import engineering_zoom_print_patch as zp
    except Exception:
        logging.exception("engineering_print_setup_hotfix: imports failed")
        return

    if getattr(edw.EngineeringDesignWorkspace, "_print_setup_hotfix_applied", False):
        return

    base_dialog = zp.PrintSetupDialog

    class PrintSetupDialog(base_dialog):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self._action = "apply"
            self._all_pages = None
            self._polish_form()

        def _polish_form(self) -> None:
            if isinstance(getattr(self, "_copies", None), QSpinBox):
                _style_print_spin(self._copies, 62)
            if isinstance(getattr(self, "_page_from", None), QSpinBox):
                _style_print_spin(self._page_from, 58)
            if isinstance(getattr(self, "_page_to", None), QSpinBox):
                _style_print_spin(self._page_to, 58)

            for label in self.findChildren(QLabel):
                if label.text() == "Copies":
                    label.setFixedWidth(42)
                    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif label.text() == "From":
                    label.setFixedWidth(32)
                    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif label.text() == "To":
                    label.setFixedWidth(18)
                    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            page_layout = _find_layout_with_widget(self.layout(), getattr(self, "_page_to", None))
            if page_layout is not None:
                self._all_pages = QCheckBox("All pages")
                self._all_pages.setObjectName("RadioLikeOption")
                self._all_pages.setChecked(True)
                self._all_pages.setStyleSheet(
                    """
                    QCheckBox#RadioLikeOption { color:#132238; font-size:12px; font-weight:800; spacing:6px; }
                    QCheckBox#RadioLikeOption::indicator { width:15px; height:15px; border-radius:8px; border:2px solid #2d7eea; background:#ffffff; }
                    QCheckBox#RadioLikeOption::indicator:checked { background:#2d7eea; border:3px solid #ffffff; }
                    """
                )
                self._all_pages.toggled.connect(self._sync_page_range_state)
                page_layout.addWidget(self._all_pages)
                self._sync_page_range_state(True)

            grid = getattr(self, "_printer_grid", None)
            cards = list(getattr(self, "_printer_cards", []))
            if grid is not None and cards:
                for card in cards:
                    grid.removeWidget(card)
                for index, card in enumerate(cards):
                    if isinstance(card, QToolButton):
                        card.setToolTip(card.text())
                        card.setMinimumSize(190, 118)
                    grid.addWidget(card, index // 2, index % 2)

            for button in self.findChildren(QPushButton):
                if button.text() == "Print":
                    try:
                        button.clicked.disconnect()
                    except Exception:
                        pass
                    button.clicked.connect(self._accept_print)
                elif button.text() == "Apply":
                    try:
                        button.clicked.disconnect()
                    except Exception:
                        pass
                    button.clicked.connect(self._accept_apply)

        def _sync_page_range_state(self, all_pages: bool) -> None:
            for spin in (getattr(self, "_page_from", None), getattr(self, "_page_to", None)):
                if isinstance(spin, QSpinBox):
                    spin.setEnabled(not all_pages)

        def _accept_print(self) -> None:
            self._action = "print"
            self.accept()

        def _accept_apply(self) -> None:
            self._action = "apply"
            self.accept()

        def settings(self) -> dict[str, object]:
            result = super().settings()
            result["all_pages"] = bool(self._all_pages.isChecked()) if self._all_pages is not None else True
            if result["all_pages"]:
                result["page_from"] = 1
                result["page_to"] = _workspace_page_count(self.parentWidget())
            return result

    def print_setup(self) -> None:
        dialog = PrintSetupDialog(self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            self._set_status("Print Setup canceled")
            return
        self._print_settings = dialog.settings()
        pages_text = "all pages" if self._print_settings.get("all_pages") else f"pages {self._print_settings['page_from']}-{self._print_settings['page_to']}"
        if getattr(dialog, "_action", "apply") == "print":
            if _send_print_job(self, self._print_settings):
                self._set_status(
                    f"Printed: {self._print_settings['printer']} | "
                    f"{self._print_settings['copies']} copy/copies | {pages_text}"
                )
            else:
                self._set_status("Print failed or canceled. Check runtime.log for details.")
            return
        self._set_status(
            f"Print Setup saved: {self._print_settings['printer']} | "
            f"{self._print_settings['copies']} copy/copies | {pages_text}"
        )

    zp.PrintSetupDialog = PrintSetupDialog
    edw.EngineeringDesignWorkspace._print_setup = print_setup
    edw.EngineeringDesignWorkspace._print_setup_hotfix_applied = True
    logging.info("engineering_print_setup_hotfix: installed")

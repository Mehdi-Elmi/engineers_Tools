"""Print setup behavior hotfix for Engineering Design Tools."""

from __future__ import annotations

import logging

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel, QPushButton, QSpinBox, QToolButton


def _style_print_spin(spin: QSpinBox) -> None:
    spin.setObjectName("PrintSpinBox")
    spin.setMinimumHeight(31)
    spin.setMinimumWidth(92)
    spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
    spin.setStyleSheet(
        """
        QSpinBox#PrintSpinBox {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:9px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800;
            padding:4px 32px 4px 8px;
        }
        QSpinBox#PrintSpinBox::up-button, QSpinBox#PrintSpinBox::down-button {
            width:28px; border:0px; margin:2px 2px 2px 0px;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.48 #fff2b8, stop:1 #5ed7c4);
            subcontrol-origin:border;
        }
        QSpinBox#PrintSpinBox::up-button { subcontrol-position:top right; border-top-right-radius:8px; }
        QSpinBox#PrintSpinBox::down-button { subcontrol-position:bottom right; border-bottom-right-radius:8px; }
        QSpinBox#PrintSpinBox::up-arrow { width:9px; height:7px; }
        QSpinBox#PrintSpinBox::down-arrow { width:9px; height:7px; }
        """
    )


def _workspace_page_count(workspace) -> int:
    for name in ("_pages", "pages", "_page_buttons", "_page_tabs"):
        value = getattr(workspace, name, None)
        if isinstance(value, (list, tuple, dict)) and value:
            return max(1, len(value))
    return 1


def _send_print_job(workspace, settings: dict[str, object]) -> bool:
    try:
        from PySide6.QtPrintSupport import QPrinter
        from .interaction_ui_patch import _render_engineering_export
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
        page_from = max(1, int(settings.get("page_from", 1) or 1))
        page_to = max(page_from, int(settings.get("page_to", page_from) or page_from))
        if hasattr(printer, "setFromTo"):
            printer.setFromTo(page_from, page_to)
        try:
            all_pages = page_from == 1 and page_to == _workspace_page_count(workspace)
            printer.setPrintRange(QPrinter.PrintRange.AllPages if all_pages else QPrinter.PrintRange.PageRange)
        except Exception:
            pass

        painter = QPainter(printer)
        if not painter.isActive():
            logging.error("engineering_print_setup_hotfix: printer painter inactive printer=%s", printer_name)
            return False
        target = QRectF(0, 0, max(1, printer.width()), max(1, printer.height()))
        _render_engineering_export(workspace, painter, target, False)
        painter.end()
        logging.info(
            "engineering_print_setup_hotfix: sent print job printer=%s copies=%s pages=%s-%s",
            printer_name,
            copies,
            page_from,
            page_to,
        )
        return True
    except Exception as error:  # noqa: BLE001
        logging.exception("engineering_print_setup_hotfix: print failed: %s", error)
        return False


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
            self._polish_form()

        def _polish_form(self) -> None:
            for spin in (getattr(self, "_copies", None), getattr(self, "_page_from", None), getattr(self, "_page_to", None)):
                if isinstance(spin, QSpinBox):
                    _style_print_spin(spin)

            for label in self.findChildren(QLabel):
                if label.text() == "Copies":
                    label.setFixedWidth(48)
                    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif label.text() == "From":
                    label.setFixedWidth(36)
                    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif label.text() == "To":
                    label.setFixedWidth(22)
                    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

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

        def _accept_print(self) -> None:
            self._action = "print"
            self.accept()

        def _accept_apply(self) -> None:
            self._action = "apply"
            self.accept()

    def print_setup(self) -> None:
        dialog = PrintSetupDialog(self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            self._set_status("Print Setup canceled")
            return
        self._print_settings = dialog.settings()
        if getattr(dialog, "_action", "apply") == "print":
            if _send_print_job(self, self._print_settings):
                self._set_status(
                    f"Printed: {self._print_settings['printer']} | "
                    f"{self._print_settings['copies']} copy/copies | "
                    f"pages {self._print_settings['page_from']}-{self._print_settings['page_to']}"
                )
            else:
                self._set_status("Print failed. Check runtime.log for details.")
            return
        self._set_status(
            f"Print Setup saved: {self._print_settings['printer']} | "
            f"{self._print_settings['copies']} copy/copies | "
            f"pages {self._print_settings['page_from']}-{self._print_settings['page_to']}"
        )

    zp.PrintSetupDialog = PrintSetupDialog
    edw.EngineeringDesignWorkspace._print_setup = print_setup
    edw.EngineeringDesignWorkspace._print_setup_hotfix_applied = True
    logging.info("engineering_print_setup_hotfix: installed")

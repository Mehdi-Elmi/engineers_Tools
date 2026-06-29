"""Final visible Print Setup patch for Engineering Design Tools."""
from __future__ import annotations

import logging

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
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

VERSION = "direct-print-final-1"


def _helpers():
    from . import engineering_print_setup_hotfix as h
    return h


def _printer_icon(title: str, active: bool = False) -> QIcon:
    pixmap = QPixmap(72, 72)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    shell = QPainterPath()
    shell.addRoundedRect(QRectF(5, 7, 62, 56), 14, 14)
    painter.fillPath(shell, QColor("#fff3cc" if active else "#f2f7ff"))
    painter.setPen(QPen(QColor("#e7a626" if active else "#9fb0c5"), 1.4))
    painter.drawPath(shell)
    painter.setBrush(QColor("#132238"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(18, 22, 36, 22), 5, 5)
    painter.setBrush(QColor("#ffffff"))
    painter.drawRect(QRectF(23, 12, 26, 18))
    painter.drawRect(QRectF(24, 41, 24, 15))
    painter.setPen(QPen(QColor("#e7a626"), 2.0))
    painter.drawLine(27, 47, 45, 47)
    painter.end()
    return QIcon(pixmap)


class _Preview(QWidget):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.setFixedSize(250, 320)

    def paintEvent(self, event) -> None:  # noqa: ARG002
        h = _helpers()
        dialog = self.parentWidget()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#f7faff"))
        outer = QRectF(8, 8, self.width() - 16, self.height() - 16)
        path = QPainterPath()
        path.addRoundedRect(outer, 12, 12)
        painter.fillPath(path, QColor("#ffffff"))
        painter.setPen(QPen(QColor("#cfdbea"), 1.1))
        painter.drawPath(path)
        painter.setPen(QColor("#132238"))
        painter.drawText(QRectF(outer.left() + 10, outer.top() + 8, outer.width() - 20, 20), Qt.AlignmentFlag.AlignLeft, "Preview")
        paper = QRectF(outer.left() + 36, outer.top() + 40, outer.width() - 72, outer.height() - 78)
        painter.fillRect(paper.translated(3, 4), QColor(20, 35, 55, 32))
        painter.setPen(QPen(QColor("#8fa2bb"), 1.1))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(paper, 4, 4)
        if dialog is not None:
            h._render_print_preview(dialog, painter, paper)
            page_count = h._workspace_page_count(dialog.parentWidget())
        else:
            page_count = 1
        painter.setPen(QColor("#536170"))
        painter.drawText(QRectF(outer.left() + 8, outer.bottom() - 26, outer.width() - 16, 18), Qt.AlignmentFlag.AlignCenter, f"{page_count} page(s)")
        painter.end()


class FinalPrintSetupDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectHelpDialog")
        self.setWindowTitle("Print Setup")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.resize(780, 500)
        self._action = "apply"
        self._selected_printer_name = ""
        self._printer_cards: list[QToolButton] = []
        self._page_count = _helpers()._workspace_page_count(parent)
        self._build_ui()

    def _build_ui(self) -> None:
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

        title = QLabel("Printer")
        title.setObjectName("DialogSectionTitle")
        settings.addWidget(title)
        self._printer_grid = QGridLayout()
        self._printer_grid.setContentsMargins(0, 0, 0, 0)
        self._printer_grid.setHorizontalSpacing(10)
        self._printer_grid.setVerticalSpacing(10)
        self._printer_group = QButtonGroup(self)
        self._printer_group.setExclusive(True)
        self._printer_group.idClicked.connect(self._select_printer_index)
        self._load_printers()
        settings.addLayout(self._printer_grid)

        h = _helpers()
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        self._copies = QSpinBox()
        self._copies.setRange(1, 999)
        self._copies.setValue(1)
        h._style_print_spin(self._copies, 54)
        self._page_from = QSpinBox()
        self._page_from.setRange(1, max(1, self._page_count))
        self._page_from.setValue(1)
        h._style_print_spin(self._page_from, 52)
        self._page_to = QSpinBox()
        self._page_to.setRange(1, max(1, self._page_count))
        self._page_to.setValue(max(1, self._page_count))
        h._style_print_spin(self._page_to, 52)
        self._page_from.valueChanged.connect(self._normalize_page_range)
        self._page_to.valueChanged.connect(self._normalize_page_range)
        row.addWidget(self._label("Copy", 36))
        row.addWidget(self._copies)
        row.addSpacing(8)
        row.addWidget(self._label("Page From", 70))
        row.addWidget(self._page_from)
        row.addSpacing(8)
        row.addWidget(self._label("Page To", 52))
        row.addWidget(self._page_to)
        row.addStretch(1)
        settings.addLayout(row)

        self._print_grid = QCheckBox("Show Grade")
        self._print_grid.setObjectName("RadioLikeOption")
        self._print_grid.setChecked(False)
        self._print_grid.setStyleSheet(h._radio_style())
        self._print_grid.toggled.connect(self._update_preview)
        settings.addWidget(self._print_grid)

        self._status = QLabel("Select a printer, then apply.")
        self._status.setObjectName("StatusItem")
        settings.addWidget(self._status)
        settings.addStretch(1)

        self._preview = _Preview(self)
        body.addLayout(settings, 3)
        body.addWidget(self._preview, 2)
        layout.addLayout(body, 1)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(16, 0, 16, 0)
        buttons.addStretch(1)
        for text, handler, obj in (
            ("Print", self._accept_print, "PrimaryDialogButton"),
            ("Apply", self._accept_apply, "SecondaryDialogButton"),
            ("Cancel", self.reject, "SecondaryDialogButton"),
        ):
            button = QPushButton(text)
            button.setObjectName(obj)
            button.clicked.connect(handler)
            buttons.addWidget(button)
        layout.addLayout(buttons)
        logging.info("engineering_print_setup_final_patch: controls built version=%s pages=%s", VERSION, self._page_count)

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
        label = QLabel("Print Setup")
        label.setObjectName("HelpTitle")
        layout.addWidget(label, 1)
        close = QPushButton("×")
        close.setObjectName("MenuDialogClose")
        close.setFixedSize(28, 26)
        close.clicked.connect(self.reject)
        layout.addWidget(close)
        return header

    def _label(self, text: str, width: int) -> QLabel:
        label = QLabel(text)
        label.setObjectName("DialogSectionTitle")
        label.setFixedWidth(width)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _load_printers(self) -> None:
        try:
            from PySide6.QtPrintSupport import QPrinterInfo
        except Exception as error:  # noqa: BLE001
            logging.exception("Print setup printer discovery failed: %s", error)
            self._add_printer_card("No Qt print support available", "", True)
            return
        printers = [p for p in QPrinterInfo.availablePrinters() if _helpers()._is_allowed_printer_name(p.printerName())]
        default = QPrinterInfo.defaultPrinter().printerName()
        if not printers:
            self._add_printer_card("No printers found", "", True)
            return
        for index, printer in enumerate(printers):
            name = printer.printerName()
            self._add_printer_card(name, name, bool(name == default or (not default and index == 0)))
        if not self._selected_printer_name and self._printer_cards:
            first = self._printer_cards[0]
            first.setChecked(True)
            self._selected_printer_name = str(first.property("printerName") or first.text())

    def _add_printer_card(self, title: str, data: str, checked: bool = False) -> None:
        button = QToolButton()
        button.setObjectName("PrinterCard")
        button.setCheckable(True)
        button.setChecked(checked)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setIcon(_printer_icon(title, checked))
        button.setIconSize(QSize(62, 62))
        button.setText(title)
        button.setMinimumSize(178, 104)
        button.setMaximumSize(198, 116)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.setProperty("printerName", data)
        row = len(self._printer_cards) // 2
        col = len(self._printer_cards) % 2
        self._printer_grid.addWidget(button, row, col)
        self._printer_group.addButton(button, len(self._printer_cards))
        self._printer_cards.append(button)
        if checked:
            self._selected_printer_name = data or title

    def _select_printer_index(self, index: int) -> None:
        if index < 0 or index >= len(self._printer_cards):
            return
        for card_index, card in enumerate(self._printer_cards):
            active = card_index == index
            card.setIcon(_printer_icon(card.text(), active))
            card.setProperty("active", active)
        card = self._printer_cards[index]
        self._selected_printer_name = str(card.property("printerName") or card.text())
        self._status.setText(f"Selected: {self._selected_printer_name}")
        self._update_preview()

    def _normalize_page_range(self) -> None:
        if self._page_from.value() > self._page_to.value():
            if self.sender() is self._page_from:
                self._page_to.setValue(self._page_from.value())
            else:
                self._page_from.setValue(self._page_to.value())
        self._update_preview()

    def _update_preview(self) -> None:
        self._preview.update()

    def _accept_print(self) -> None:
        self._action = "print"
        self.accept()

    def _accept_apply(self) -> None:
        self._action = "apply"
        self.accept()

    def settings(self) -> dict[str, object]:
        start = max(1, int(self._page_from.value()))
        end = max(start, int(self._page_to.value()))
        return {
            "printer": self._selected_printer_name,
            "copies": max(1, int(self._copies.value())),
            "page_from": start,
            "page_to": end,
            "all_pages": False,
            "print_grid": bool(self._print_grid.isChecked()),
        }


def apply_engineering_print_setup_final_patch() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import engineering_zoom_print_patch as zp
        from . import engineering_print_setup_hotfix as h
    except Exception:
        logging.exception("engineering_print_setup_final_patch: imports failed")
        return

    if getattr(edw.EngineeringDesignWorkspace, "_print_setup_final_patch_version", "") == VERSION:
        return

    def print_setup(self) -> None:
        dialog = FinalPrintSetupDialog(self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            self._set_status("Print Setup canceled")
            return
        self._print_settings = dialog.settings()
        pages_text = f"pages {self._print_settings['page_from']}-{self._print_settings['page_to']}"
        if getattr(dialog, "_action", "apply") == "print":
            if h._send_print_job(self, self._print_settings):
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

    zp.PrintSetupDialog = FinalPrintSetupDialog
    edw.EngineeringDesignWorkspace._print_setup = print_setup
    edw.EngineeringDesignWorkspace._print_setup_final_patch_version = VERSION
    logging.info("engineering_print_setup_final_patch: installed version=%s", VERSION)

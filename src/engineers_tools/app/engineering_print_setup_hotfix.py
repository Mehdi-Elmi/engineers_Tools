"""Print setup behavior hotfix for Engineering Design Tools."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel, QPushButton, QSpinBox, QToolButton


HOTFIX_VERSION = "direct-print-12"
_SKIP_PRINTER_TOKENS = ("fax", "onenote", "one note", "evernote", "xps", "microsoft xps")
_PDF_PRINTER_TOKENS = ("pdf", "foxit", "adobe", "nitro", "pdf24", "pdfcreator")


def _asset_path(name: str) -> str:
    try:
        from .interaction_ui_patch import _asset_icon_path
    except Exception:
        return ""
    path = _asset_icon_path(name)
    return path.as_posix() if path is not None else ""


def _is_allowed_printer_name(name: str) -> bool:
    lower = name.lower()
    return bool(name.strip()) and not any(token in lower for token in _SKIP_PRINTER_TOKENS)


def _is_pdf_printer_name(name: str) -> bool:
    lower = name.lower()
    return any(token in lower for token in _PDF_PRINTER_TOKENS)


def _style_print_spin(spin: QSpinBox, width: int = 58) -> None:
    up_icon = _asset_path("print_spin_up.svg") or _asset_path("spin_up.svg")
    down_icon = _asset_path("print_spin_down.svg") or _asset_path("spin_down.svg")
    spin.setObjectName("PrintSpinBox")
    spin.setFixedWidth(width)
    spin.setMinimumHeight(29)
    spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
    spin.setStyleSheet(
        """
        QSpinBox#PrintSpinBox {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:9px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800;
            padding:4px 24px 4px 6px;
        }
        QSpinBox#PrintSpinBox::up-button, QSpinBox#PrintSpinBox::down-button {
            width:22px; border:0px; margin:2px 2px 2px 0px;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #fff7d8, stop:0.52 #ffbd57, stop:1 #f2a12b);
            subcontrol-origin:border;
        }
        QSpinBox#PrintSpinBox::up-button { subcontrol-position:top right; border-top-right-radius:8px; }
        QSpinBox#PrintSpinBox::down-button { subcontrol-position:bottom right; border-bottom-right-radius:8px; }
        QSpinBox#PrintSpinBox::up-arrow { image:url(%s); width:13px; height:8px; }
        QSpinBox#PrintSpinBox::down-arrow { image:url(%s); width:13px; height:8px; }
        """ % (up_icon, down_icon)
    )


def _style_shared_numeric_spin(spin: QDoubleSpinBox) -> None:
    up_icon = _asset_path("print_spin_up.svg") or _asset_path("spin_up.svg")
    down_icon = _asset_path("print_spin_down.svg") or _asset_path("spin_down.svg")
    spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
    spin.setMinimumHeight(31)
    spin.setMinimumWidth(138)
    spin.setStyleSheet(
        """
        QDoubleSpinBox#FileNameInput {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:9px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:4px 35px 4px 8px;
        }
        QDoubleSpinBox#FileNameInput::up-button, QDoubleSpinBox#FileNameInput::down-button {
            width:31px; border:0px; margin:2px 2px 2px 0px;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #fff7d8, stop:0.52 #ffbd57, stop:1 #f2a12b);
            subcontrol-origin:border;
        }
        QDoubleSpinBox#FileNameInput::up-button { subcontrol-position:top right; border-top-right-radius:8px; }
        QDoubleSpinBox#FileNameInput::down-button { subcontrol-position:bottom right; border-bottom-right-radius:8px; }
        QDoubleSpinBox#FileNameInput::up-arrow { image:url(%s); width:18px; height:11px; }
        QDoubleSpinBox#FileNameInput::down-arrow { image:url(%s); width:18px; height:11px; }
        """ % (up_icon, down_icon)
    )


def _style_shared_combo_arrow(combo: QComboBox) -> None:
    down_icon = _asset_path("combo_down.svg") or _asset_path("print_spin_down.svg") or _asset_path("spin_down.svg")
    combo.setMinimumHeight(31)
    combo.setStyleSheet(
        """
        QComboBox#FileTypeCombo {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:9px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:5px 33px 5px 8px;
        }
        QComboBox#FileTypeCombo::drop-down {
            width:29px; border:0; margin:1px 1px 1px 0px;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #fff7d8, stop:0.52 #ffbd57, stop:1 #f2a12b);
            border-top-right-radius:8px; border-bottom-right-radius:8px;
        }
        QComboBox#FileTypeCombo::down-arrow { image:url(%s); width:18px; height:11px; }
        QComboBox#FileTypeCombo QAbstractItemView {
            background:#ffffff; border:1px solid #8fa2bb; border-radius:8px; selection-background-color:#cfe7ff;
        }
        """ % down_icon
    )


def _install_shared_arrow_styles() -> None:
    try:
        from . import interaction_ui_patch as interaction
    except Exception:
        logging.exception("engineering_print_setup_hotfix: shared arrow style import failed")
        return
    interaction._style_numeric_spin = _style_shared_numeric_spin
    interaction._style_combo_arrow = _style_shared_combo_arrow
    logging.info("engineering_print_setup_hotfix: shared yellow arrow styles installed")


def _radio_style() -> str:
    return """
        QCheckBox#RadioLikeOption { color:#132238; font-size:12px; font-weight:800; spacing:6px; }
        QCheckBox#RadioLikeOption::indicator { width:15px; height:15px; border-radius:8px; border:2px solid #2d7eea; background:#ffffff; }
        QCheckBox#RadioLikeOption::indicator:checked { background:#2d7eea; border:3px solid #ffffff; }
    """


def _workspace_page_count(workspace) -> int:
    for name in ("_pages", "pages", "_page_buttons", "_page_tabs"):
        value = getattr(workspace, name, None)
        if isinstance(value, (list, tuple, dict)) and value:
            return max(1, len(value))
    return 1


def _fallback_render_engineering_export(window, painter: QPainter, target: QRectF, transparent: bool = False) -> None:
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


def _render_print_preview(dialog, painter: QPainter, paper: QRectF) -> None:
    workspace = dialog.parentWidget()
    try:
        from .interaction_ui_patch import _render_engineering_export
    except Exception:
        _render_engineering_export = _fallback_render_engineering_export
    old_options = dict(getattr(workspace, "_save_options", {}) or {}) if workspace is not None else {}
    if workspace is not None:
        workspace._save_options = dict(old_options, save_grid=bool(getattr(dialog, "_print_grid", None) and dialog._print_grid.isChecked()))
    try:
        _render_engineering_export(workspace, painter, paper.adjusted(10, 10, -10, -10), False)
    finally:
        if workspace is not None:
            workspace._save_options = old_options


def _paint_preview(preview, event) -> None:  # noqa: ARG001
    dialog = preview.parentWidget()
    painter = QPainter(preview)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.fillRect(preview.rect(), QColor("#f7faff"))
    outer = QRectF(8, 8, preview.width() - 16, preview.height() - 16)
    card = QPainterPath()
    card.addRoundedRect(outer, 12, 12)
    painter.fillPath(card, QColor("#ffffff"))
    painter.setPen(QPen(QColor("#cfdbea"), 1.1))
    painter.drawPath(card)
    painter.setPen(QColor("#132238"))
    painter.drawText(QRectF(outer.left() + 10, outer.top() + 8, outer.width() - 20, 20), Qt.AlignmentFlag.AlignLeft, "Preview")
    paper = QRectF(outer.left() + 36, outer.top() + 40, outer.width() - 72, outer.height() - 78)
    painter.fillRect(paper.translated(3, 4), QColor(20, 35, 55, 32))
    painter.setPen(QPen(QColor("#8fa2bb"), 1.1))
    painter.setBrush(QColor("#ffffff"))
    painter.drawRoundedRect(paper, 4, 4)
    if dialog is not None:
        _render_print_preview(dialog, painter, paper)
    painter.setPen(QColor("#536170"))
    page_count = max(1, _workspace_page_count(dialog.parentWidget() if dialog is not None else None))
    painter.drawText(QRectF(outer.left() + 8, outer.bottom() - 26, outer.width() - 16, 18), Qt.AlignmentFlag.AlignCenter, f"{page_count} page(s)")
    painter.end()


def _choose_pdf_output(workspace, printer_name: str) -> str:
    default_dir = str(Path.home() / "Documents")
    path, _selected = QFileDialog.getSaveFileName(workspace, f"Save PDF - {printer_name}", str(Path(default_dir) / "EngineerTools_Print.pdf"), "PDF (*.pdf)")
    if not path:
        return ""
    if not path.lower().endswith(".pdf"):
        path += ".pdf"
    return path


def _send_print_job(workspace, settings: dict[str, object]) -> bool:
    try:
        from PySide6.QtPrintSupport import QPrinter
        try:
            from .interaction_ui_patch import _render_engineering_export
        except Exception:
            _render_engineering_export = _fallback_render_engineering_export
    except Exception as error:  # noqa: BLE001
        logging.exception("engineering_print_setup_hotfix: print imports failed: %s", error)
        return False
    try:
        printer_name = str(settings.get("printer") or "").strip()
        if not printer_name or "No printers" in printer_name:
            logging.error("engineering_print_setup_hotfix: no usable printer selected")
            return False

        pdf_output = ""
        if _is_pdf_printer_name(printer_name):
            pdf_output = _choose_pdf_output(workspace, printer_name)
            if not pdf_output:
                logging.info("engineering_print_setup_hotfix: pdf output canceled printer=%s", printer_name)
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

        old_options = dict(getattr(workspace, "_save_options", {}) or {})
        workspace._save_options = dict(old_options, save_grid=bool(settings.get("print_grid", False)))
        logging.info(
            "engineering_print_setup_hotfix: direct print version=%s printer=%s copies=%s pages=%s-%s all=%s grid=%s pdf=%s valid=%s",
            HOTFIX_VERSION,
            printer_name,
            copies,
            page_from,
            page_to,
            all_pages,
            bool(settings.get("print_grid", False)),
            pdf_output,
            printer.isValid(),
        )
        painter = QPainter(printer)
        if not painter.isActive():
            logging.error(
                "engineering_print_setup_hotfix: printer painter inactive printer=%s valid=%s output_file=%s",
                printer.printerName(),
                printer.isValid(),
                printer.outputFileName(),
            )
            workspace._save_options = old_options
            return False
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            target = QRectF(0, 0, max(1, printer.width()), max(1, printer.height()))
            _render_engineering_export(workspace, painter, target, False)
        finally:
            painter.end()
            workspace._save_options = old_options
        logging.info(
            "engineering_print_setup_hotfix: sent direct print job printer=%s output_file=%s copies=%s pages=%s-%s all=%s",
            printer.printerName() or printer_name,
            pdf_output or printer.outputFileName(),
            copies,
            page_from,
            page_to,
            all_pages,
        )
        return True
    except Exception as error:  # noqa: BLE001
        logging.exception("engineering_print_setup_hotfix: print failed: %s", error)
        return False


def _find_layout_index_with_widget(layout, widget):
    if layout is None or widget is None:
        return None, -1
    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item.widget() is widget:
            return layout, index
        child = item.layout()
        found_layout, found_index = _find_layout_index_with_widget(child, widget)
        if found_layout is not None:
            return found_layout, found_index
    return None, -1


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


def _make_print_spin(source: QSpinBox | None, width: int, default: int, minimum: int, maximum: int) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(minimum, maximum)
    value = default
    if isinstance(source, QSpinBox):
        value = source.value()
    spin.setValue(max(minimum, min(maximum, value)))
    _style_print_spin(spin, width)
    return spin


def _hide_widget(widget) -> None:
    if widget is not None:
        widget.hide()


def _find_button_by_text(dialog, text: str):
    for button in dialog.findChildren(QPushButton):
        if button.text() == text:
            return button
    return None


def _hide_buttons_by_text(dialog, text: str) -> int:
    hidden = 0
    for button in dialog.findChildren(QPushButton):
        if button.text() == text:
            button.hide()
            hidden += 1
    return hidden


def _inline_print_label(text: str, width: int) -> QLabel:
    label = QLabel(text)
    label.setObjectName("DialogSectionTitle")
    label.setFixedWidth(width)
    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return label


def _filter_printer_cards(dialog) -> None:
    grid = getattr(dialog, "_printer_grid", None)
    cards = list(getattr(dialog, "_printer_cards", []))
    combo = getattr(dialog, "_printers", None)
    if grid is None or not cards:
        return
    kept = [card for card in cards if _is_allowed_printer_name(card.text())]
    if not kept:
        kept = cards
    for card in cards:
        grid.removeWidget(card)
        card.hide()
    if combo is not None:
        combo.clear()
    group = QButtonGroup(dialog)
    group.setExclusive(True)
    dialog._printer_group = group
    dialog._printer_cards = []
    selected_set = False
    for index, card in enumerate(kept):
        card.show()
        card.setToolTip(card.text())
        card.setMinimumSize(178, 104)
        card.setMaximumSize(198, 116)
        card.setChecked(False)
        grid.addWidget(card, index // 2, index % 2)
        group.addButton(card, index)
        dialog._printer_cards.append(card)
        if combo is not None:
            data = card.property("printerName") or card.text()
            combo.addItem(card.text(), data)
        if not selected_set:
            card.setChecked(True)
            dialog._selected_printer_name = str(card.property("printerName") or card.text())
            selected_set = True
    group.idClicked.connect(dialog._select_printer_index)


def apply_engineering_print_setup_hotfix() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
        from . import engineering_zoom_print_patch as zp
    except Exception:
        logging.exception("engineering_print_setup_hotfix: imports failed")
        return

    if getattr(edw.EngineeringDesignWorkspace, "_print_setup_hotfix_version", "") == HOTFIX_VERSION:
        return
    _install_shared_arrow_styles()

    base_dialog = zp.PrintSetupDialog

    class PrintSetupDialog(base_dialog):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self._action = "apply"
            self._all_pages = None
            self._print_grid = None
            self._polish_form()

        def _polish_form(self) -> None:
            self.resize(760, 480)
            _filter_printer_cards(self)
            original_copies = getattr(self, "_copies", None)
            original_page_from = getattr(self, "_page_from", None)
            original_page_to = getattr(self, "_page_to", None)

            for label in self.findChildren(QLabel):
                if label.text() == "Copies":
                    label.hide()
                elif label.text() == "Pages":
                    label.hide()
                elif label.text() == "From":
                    label.hide()
                elif label.text() == "To":
                    label.hide()
            _hide_widget(original_copies)
            _hide_widget(original_page_from)
            _hide_widget(original_page_to)

            page_count = _workspace_page_count(self.parentWidget())
            self._copies = _make_print_spin(original_copies, 54, 1, 1, 999)
            self._page_from = _make_print_spin(original_page_from, 52, 1, 1, max(1, page_count))
            self._page_to = _make_print_spin(original_page_to, 52, max(1, page_count), 1, max(1, page_count))
            self._page_from.valueChanged.connect(self._normalize_page_range)
            self._page_to.valueChanged.connect(self._normalize_page_range)

            page_layout = _find_layout_with_widget(self.layout(), getattr(self, "_page_to", None))
            if page_layout is not None:
                try:
                    page_layout.setSpacing(4)
                    page_layout.setContentsMargins(0, 0, 0, 0)
                except Exception:
                    pass

            self._all_pages = None
            self._print_grid = QCheckBox("Show Grade")
            self._print_grid.setObjectName("RadioLikeOption")
            self._print_grid.setChecked(False)
            self._print_grid.setStyleSheet(_radio_style())
            self._print_grid.toggled.connect(self._update_preview)
            controls_row = QHBoxLayout()
            controls_row.setContentsMargins(0, 0, 0, 0)
            controls_row.setSpacing(4)
            controls_row.addWidget(_inline_print_label("Copy", 38))
            controls_row.addWidget(self._copies)
            controls_row.addSpacing(8)
            controls_row.addWidget(_inline_print_label("Page From", 72))
            controls_row.addWidget(self._page_from)
            controls_row.addSpacing(8)
            controls_row.addWidget(_inline_print_label("Page To", 54))
            controls_row.addWidget(self._page_to)
            controls_row.addStretch(1)
            options_row = QHBoxLayout()
            options_row.setContentsMargins(0, 0, 0, 0)
            options_row.setSpacing(12)
            options_row.addWidget(self._print_grid)
            options_row.addStretch(1)
            hidden_native = _hide_buttons_by_text(self, "System Print Setup")
            settings_layout, anchor_index = _find_layout_index_with_widget(self.layout(), getattr(self, "_status", None))
            if settings_layout is not None and anchor_index >= 0:
                settings_layout.insertLayout(anchor_index, controls_row)
                settings_layout.insertLayout(anchor_index + 1, options_row)
            elif page_layout is not None:
                page_layout.addLayout(controls_row)
                page_layout.addWidget(self._print_grid)
            logging.info(
                "engineering_print_setup_hotfix: print controls inserted version=%s hidden_native=%s anchor=%s",
                HOTFIX_VERSION,
                hidden_native,
                anchor_index,
            )
            self._sync_page_range_state(False)

            preview = getattr(self, "_preview", None)
            if preview is not None:
                preview.setFixedSize(250, 320)
                preview.paintEvent = lambda event, p=preview: _paint_preview(p, event)
                preview.update()

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

        def _update_preview(self) -> None:
            preview = getattr(self, "_preview", None)
            if preview is not None:
                preview.update()

        def _sync_page_range_state(self, all_pages: bool) -> None:
            for spin in (getattr(self, "_page_from", None), getattr(self, "_page_to", None)):
                if isinstance(spin, QSpinBox):
                    spin.setEnabled(not all_pages)
            self._update_preview()

        def _accept_print(self) -> None:
            self._action = "print"
            self.accept()

        def _accept_apply(self) -> None:
            self._action = "apply"
            self.accept()

        def settings(self) -> dict[str, object]:
            result = super().settings()
            result["all_pages"] = False
            result["print_grid"] = bool(self._print_grid.isChecked()) if self._print_grid is not None else False
            result["page_from"] = max(1, int(result.get("page_from", 1) or 1))
            result["page_to"] = max(result["page_from"], int(result.get("page_to", _workspace_page_count(self.parentWidget())) or 1))
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
    edw.EngineeringDesignWorkspace._print_setup_hotfix_version = HOTFIX_VERSION
    logging.info("engineering_print_setup_hotfix: installed version=%s", HOTFIX_VERSION)

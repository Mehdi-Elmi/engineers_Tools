"""Project window styling and cursor guard for Open/Save/Import/Export dialogs."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap, QPolygonF
from PySide6.QtWidgets import QComboBox, QLineEdit, QListWidget, QPushButton, QWidget

PATCH_VERSION = "engineering-project-dialog-style-cursor-2026-07-02-b"
_ARROW_CACHE: dict[str, str] = {}

DIALOG_STYLE = (
    "QDialog#ProjectFileDialog{background:transparent;}"
    "QWidget#ProjectFileShell{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #f8fcff,stop:.52 #eaf4ff,stop:1 #fff0c8);"
    "border:1px solid #6f91b2;border-radius:16px;}"
    "QWidget#FileDialogHeader{background:#102238;border-top-left-radius:16px;border-top-right-radius:16px;min-height:44px;}"
    "QLabel#FileDialogTitle{color:#ffffff;font-family:'Times New Roman';font-size:14px;font-weight:900;font-style:normal;}"
    "QPushButton#CloseButton{background:transparent;border:0;color:#ffffff;font-size:18px;font-weight:900;border-radius:8px;}"
    "QPushButton#CloseButton:hover{background:#d84a4a;}"
    "QWidget#FileDialogNavBar{background:#dce9f7;border-bottom:1px solid #b7c9dc;}"
    "QPushButton#FileNavButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:.48 #eaf7ff,stop:1 #b6d4f0);"
    "border:1px solid #7fa6ca;border-radius:9px;}"
    "QPushButton#FileNavButton:hover{background:#fff4cf;border-color:#ff8a35;}"
    "QLabel#FilePathLabel{color:#173454;font-family:'Times New Roman';font-weight:800;font-style:normal;}"
    "QWidget#FileDialogBody{background:rgba(255,255,255,120);}"
    "QListWidget#PlacesList,QListWidget#FilesList{background:rgba(255,255,255,185);border:1px solid #b8c5d4;border-radius:10px;color:#173454;"
    "font-family:'Times New Roman';font-weight:800;font-style:normal;}"
    "QWidget#FileDialogFooter{background:#dce9f7;border-bottom-left-radius:16px;border-bottom-right-radius:16px;}"
    "QLabel#FileFieldLabel{color:#173454;font-family:'Times New Roman';font-weight:900;font-style:normal;}"
    "QLineEdit#FileNameInput,QComboBox#FileTypeCombo{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#123d6f;"
    "font-family:'Times New Roman';font-weight:800;font-style:normal;padding:4px 8px;}"
    "QPushButton#PrimaryDialogButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffc35a,stop:1 #f18a2a);"
    "border:1px solid #7e5b10;border-radius:9px;color:#102238;font-family:'Times New Roman';font-weight:900;font-style:normal;padding:5px 16px;}"
    "QPushButton#SecondaryDialogButton{background:#ffffff;border:1px solid #7fa6ca;border-radius:9px;color:#123d6f;"
    "font-family:'Times New Roman';font-weight:900;font-style:normal;padding:5px 16px;}"
    "QPushButton#SaveOptionButton{background:#ffffff;border:1px solid #7fa6ca;border-radius:9px;color:#123d6f;"
    "font-family:'Times New Roman';font-weight:900;font-style:normal;padding:3px 8px;}"
    "QPushButton#SaveOptionButton:checked{background:#fff4cf;border-color:#ff8a35;}"
)


def _arrow_path(direction: str = "down") -> str:
    cached = _ARROW_CACHE.get(direction)
    if cached:
        return cached
    pixmap = QPixmap(18, 12)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#102238"))
    if direction == "up":
        points = [QPointF(9, 2), QPointF(3, 9), QPointF(15, 9)]
    else:
        points = [QPointF(3, 3), QPointF(15, 3), QPointF(9, 10)]
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    icon_dir = Path(tempfile.gettempdir()) / "engineer_tools_project_arrows"
    icon_dir.mkdir(parents=True, exist_ok=True)
    path = icon_dir / f"project_arrow_{direction}.png"
    pixmap.save(str(path), "PNG")
    result = path.as_posix()
    _ARROW_CACHE[direction] = result
    return result


def _apply_font(widget: QWidget, size: int = 10) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(False)
    widget.setFont(font)


def _style_combo(combo: QComboBox) -> None:
    arrow = _arrow_path("down")
    combo.setStyleSheet(
        combo.styleSheet()
        + "\nQComboBox#FileTypeCombo{padding-right:28px;}"
        + "QComboBox#FileTypeCombo::drop-down{width:26px;border:0;background:transparent;subcontrol-origin:border;subcontrol-position:center right;}"
        + f"QComboBox#FileTypeCombo::down-arrow{{image:url({arrow});width:14px;height:9px;}}"
    )


def _apply_project_cursor(root: QWidget, svg) -> None:
    cursor = svg.project_cursor("default")
    for widget in [root, *root.findChildren(QWidget)]:
        try:
            widget.setCursor(cursor)
        except Exception:
            pass


def _polish_dialog(dialog, svg) -> None:
    dialog.setStyleSheet(dialog.styleSheet() + "\n" + DIALOG_STYLE)
    for widget in dialog.findChildren(QWidget):
        if isinstance(widget, (QPushButton, QLineEdit, QComboBox, QListWidget)):
            _apply_font(widget, 10)
        if isinstance(widget, QComboBox):
            _style_combo(widget)
    _apply_project_cursor(dialog, svg)
    for delay in (0, 80, 250, 700):
        QTimer.singleShot(delay, lambda d=dialog: _apply_project_cursor(d, svg))


def apply_project_dialog_style_cursor_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from src.engineers_tools.app.project_file_dialog import ProjectFileDialog

    if getattr(ProjectFileDialog, "_engineering_project_dialog_style_cursor_patch", "") == PATCH_VERSION:
        return

    old_init = ProjectFileDialog.__init__

    def init(self, *args, **kwargs) -> None:
        old_init(self, *args, **kwargs)
        _polish_dialog(self, svg)

    ProjectFileDialog.__init__ = init
    ProjectFileDialog._engineering_project_dialog_style_cursor_patch = PATCH_VERSION

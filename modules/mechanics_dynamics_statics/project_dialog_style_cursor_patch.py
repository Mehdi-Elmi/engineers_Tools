"""Project dialog and shared control styling for the engineering UI.

This patch is also the last shared owner for ComboBox and SpinBox arrow styling.
The arrows intentionally use generated dark-blue PNG assets instead of Qt CSS
triangles, because the triangle fallback was rendering as square blocks on the
Windows runtime.
"""

from __future__ import annotations

import importlib
import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap, QPolygonF
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit, QListWidget, QPushButton, QSpinBox, QWidget

PATCH_VERSION = "engineering-project-dialog-style-cursor-2026-07-02-e"
_ARROW_CACHE: dict[str, str] = {}


def _arrow_path(direction: str = "down") -> str:
    cached = _ARROW_CACHE.get(direction)
    if cached:
        return cached
    size = 18
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(QColor("#173454"))
    painter.setPen(Qt.PenStyle.NoPen)
    if direction == "up":
        points = [QPointF(9, 4), QPointF(14, 12), QPointF(4, 12)]
    elif direction == "down":
        points = [QPointF(4, 6), QPointF(14, 6), QPointF(9, 14)]
    elif direction == "left":
        points = [QPointF(5, 9), QPointF(13, 4), QPointF(13, 14)]
    else:
        points = [QPointF(13, 9), QPointF(5, 4), QPointF(5, 14)]
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    path = Path(tempfile.gettempdir()) / f"engineering_shared_arrow_{direction}_20260702e.png"
    pixmap.save(path.as_posix(), "PNG")
    _ARROW_CACHE[direction] = path.as_posix()
    return path.as_posix()


def _style_combo_arrow(combo: QComboBox) -> None:
    combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    combo.setStyleSheet(
        "QComboBox{background:#fffefa;border:1px solid #b88718;border-radius:8px;color:#173454;"
        "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:2px 28px 2px 8px;outline:0;}"
        "QComboBox:hover{border-color:#173454;background:#ffffff;}"
        "QComboBox:focus{outline:0;border:1px solid #b88718;}"
        "QComboBox::drop-down{subcontrol-origin:padding;subcontrol-position:top right;width:24px;"
        "border-left:1px solid #b88718;border-top-right-radius:7px;border-bottom-right-radius:7px;"
        "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        f"QComboBox::down-arrow{{image:url({_arrow_path('down')});width:16px;height:16px;}}"
        "QComboBox QAbstractItemView{background:#ffffff;border:1px solid #9fb1c7;border-radius:8px;"
        "selection-background-color:#e7f1ff;selection-color:#173454;outline:0;}"
    )


def _style_numeric_spin(spin: QSpinBox | QDoubleSpinBox) -> None:
    spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
    spin.setKeyboardTracking(True)
    spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    try:
        edit = spin.lineEdit()
        edit.setReadOnly(False)
        edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        edit.setCursorPosition(0)
        edit.setStyleSheet(
            "QLineEdit{background:transparent;border:0;color:#173454;font-family:'Times New Roman';"
            "font-size:12px;font-weight:900;font-style:normal;padding:0;outline:0;}"
        )
    except Exception:
        pass
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffefa;border:1px solid #b88718;border-radius:8px;color:#173454;"
        "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:2px 26px 2px 8px;outline:0;}"
        "QSpinBox:focus,QDoubleSpinBox:focus{border:1px solid #173454;outline:0;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{subcontrol-origin:border;subcontrol-position:top right;width:23px;"
        "border-left:1px solid #b88718;border-top-right-radius:7px;"
        "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{subcontrol-origin:border;subcontrol-position:bottom right;width:23px;"
        "border-left:1px solid #b88718;border-bottom-right-radius:7px;"
        "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe8a8,stop:1 #f1b33d);}"
        f"QSpinBox::up-arrow,QDoubleSpinBox::up-arrow{{image:url({_arrow_path('up')});width:14px;height:14px;}}"
        f"QSpinBox::down-arrow,QDoubleSpinBox::down-arrow{{image:url({_arrow_path('down')});width:14px;height:14px;}}"
    )


def _polish_dialog(root: QWidget | None) -> None:
    if root is None:
        return
    for combo in root.findChildren(QComboBox):
        _style_combo_arrow(combo)
    for spin in root.findChildren(QSpinBox):
        _style_numeric_spin(spin)
    for spin in root.findChildren(QDoubleSpinBox):
        _style_numeric_spin(spin)
    for edit in root.findChildren(QLineEdit):
        edit.setStyleSheet(
            "QLineEdit{background:#fffefa;border:1px solid #b88718;border-radius:8px;color:#173454;"
            "font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;padding:3px 7px;outline:0;}"
            "QLineEdit:focus{border:1px solid #173454;}"
        )
    for view in root.findChildren(QListWidget):
        view.setStyleSheet(
            "QListWidget{background:#ffffff;border:1px solid #9fb1c7;border-radius:8px;color:#173454;"
            "font-family:'Times New Roman';font-weight:900;font-style:italic;outline:0;}"
            "QListWidget::item{padding:4px 6px;border-radius:5px;}"
            "QListWidget::item:selected{background:#e7f1ff;color:#173454;}"
        )
    for button in root.findChildren(QPushButton):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)


def _install_shared_arrow_styles() -> None:
    try:
        from src.engineers_tools.app import interaction_ui_patch as interaction
        interaction._control_arrow_path = _arrow_path
        interaction._style_numeric_spin = _style_numeric_spin
        interaction._style_combo_arrow = _style_combo_arrow
    except Exception:
        pass
    try:
        from . import text_line_math_symbols_patch as line_patch
        line_patch._combo_style = _style_combo_arrow
        line_patch._spin_style = _style_numeric_spin
    except Exception:
        pass


def _patch_dialog_class(cls) -> None:
    if getattr(cls, "_engineering_shared_arrow_patch", "") == PATCH_VERSION:
        return
    old_init = cls.__init__

    def dialog_init(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        _polish_dialog(self)
        QTimer.singleShot(0, lambda root=self: _polish_dialog(root))
        QTimer.singleShot(120, lambda root=self: _polish_dialog(root))

    cls.__init__ = dialog_init
    cls._engineering_shared_arrow_patch = PATCH_VERSION


def _patch_known_dialogs() -> None:
    module_names = (
        "modules.mechanics_dynamics_statics.project_file_dialog",
        "modules.mechanics_dynamics_statics.project_dialogs_patch",
        "modules.mechanics_dynamics_statics.file_dialog_patch",
        "src.engineers_tools.app.engineering_properties_patch",
    )
    class_names = (
        "ProjectFileDialog",
        "EngineeringFileDialog",
        "FilePropertiesDialog",
        "PropertiesDialog",
        "PageSetupDialog",
        "PrintSetupDialog",
    )
    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        for class_name in class_names:
            cls = getattr(module, class_name, None)
            if cls is not None:
                _patch_dialog_class(cls)


def apply_project_dialog_style_cursor_patch() -> None:
    _install_shared_arrow_styles()
    _patch_known_dialogs()

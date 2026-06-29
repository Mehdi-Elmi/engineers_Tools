"""Final workspace scale and approved icon wiring."""

from __future__ import annotations

import logging

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap

from .interaction_ui_patch import _paint_asset_icon


WORKSPACE_SIZE_MM = (400.0, 220.0)


def _paint_first_asset(painter: QPainter, names: tuple[str, ...], rect: QRectF) -> bool:
    for name in names:
        if _paint_asset_icon(painter, name, rect):
            return True
    return False


def _paint_rotate_asset(painter: QPainter, center: QPointF, radius: float, color: QColor) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    icon_rect = QRectF(center.x() - radius * 1.45, center.y() - radius * 1.45, radius * 2.9, radius * 2.9)
    if _paint_first_asset(painter, ("rotate.svg", "rotate_arrow.svg", "layer_rotate.svg"), icon_rect):
        painter.restore()
        return
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(color, 2.1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawArc(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), 45 * 16, 280 * 16)
    painter.setBrush(color)
    painter.drawEllipse(QPointF(center.x() + radius * 0.72, center.y() - radius * 0.70), max(2.0, radius * 0.22), max(2.0, radius * 0.22))
    painter.restore()


def _layer_icon(kind: str, active: bool = True) -> QIcon:
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
    if kind in {"rotate", "rotation"} and _paint_first_asset(painter, ("rotate.svg", "layer_rotate.svg", "rotate_arrow.svg"), QRectF(5.5, 5.5, 23, 23)):
        painter.end()
        return QIcon(pixmap)
    if kind == "eye" and _paint_first_asset(painter, ("layer_eye.svg",), QRectF(5.5, 5.5, 23, 23)):
        painter.end()
        return QIcon(pixmap)
    if kind == "lock" and _paint_first_asset(painter, ("layer_lock_closed.svg",) if active else ("layer_lock_open.svg",), QRectF(5.5, 5.5, 23, 23)):
        painter.end()
        return QIcon(pixmap)
    ink = QColor("#132238")
    painter.setPen(QPen(ink, 2.05, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if kind == "eye":
        eye = QPainterPath()
        eye.moveTo(5.8, 17)
        eye.cubicTo(10.0, 8.8, 24.0, 8.8, 28.2, 17)
        eye.cubicTo(24.0, 25.2, 10.0, 25.2, 5.8, 17)
        painter.setBrush(QColor(255, 255, 255, 205))
        painter.drawPath(eye)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2f7df6" if active else "#8b98a8"))
        painter.drawEllipse(QPointF(17, 17), 4.8, 4.8)
        painter.setBrush(QColor("#07192f"))
        painter.drawEllipse(QPointF(17, 17), 2.1, 2.1)
    elif kind == "lock":
        lock_gradient = QLinearGradient(8, 8, 26, 27)
        lock_gradient.setColorAt(0.0, QColor("#fff7d8"))
        lock_gradient.setColorAt(0.55, QColor("#ffbe4a" if active else "#f2f7fb"))
        lock_gradient.setColorAt(1.0, QColor("#dc7a17" if active else "#91a1b5"))
        painter.setBrush(lock_gradient)
        painter.drawArc(QRectF(10, 7, 14, 14), 0, 180 * 16)
        body = QPainterPath()
        body.addRoundedRect(QRectF(8.2, 15, 17.6, 11.5), 3.8, 3.8)
        painter.drawPath(body)
    else:
        _paint_rotate_asset(painter, QPointF(17, 17), 8.7, ink)
    if not active:
        painter.setPen(QPen(QColor("#d44777"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(8, 26), QPointF(26, 8))
    painter.end()
    return QIcon(pixmap)


def apply_engineering_workspace_finalize_patch() -> None:
    from . import module_window as mw
    from . import runtime_ui_patch as rtp

    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_workspace_finalize_patch: workspace import failed")
        return

    if getattr(edw.EngineeringDesignWorkspace, "_workspace_finalize_patch_applied", False):
        return

    rtp.PageSetupDialog.PAPER_SIZES["Workspace"] = WORKSPACE_SIZE_MM
    rtp.PageSetupDialog.PAPER_SIZES["Custom"] = WORKSPACE_SIZE_MM
    rtp._paint_rotation_glyph = _paint_rotate_asset
    mw._paint_rotation_glyph = _paint_rotate_asset
    edw._layer_icon = _layer_icon

    original_canvas_init = getattr(edw.EngineeringCanvas, "__init__", None)
    original_choose_paper = getattr(rtp.PageSetupDialog, "_choose_paper", None)
    original_dialog_init = getattr(rtp.PageSetupDialog, "__init__", None)
    original_layer_button = getattr(edw.EngineeringDesignWorkspace, "_layer_button", None)

    def _set_size_spins(dialog, name: str) -> None:
        size = dialog.PAPER_SIZES.get(name, WORKSPACE_SIZE_MM)
        for key, value in (("width", size[0]), ("height", size[1])):
            spin = getattr(dialog, "_custom_size_spins", {}).get(key)
            if spin is None:
                continue
            spin.blockSignals(True)
            spin.setValue(float(value))
            spin.setEnabled(name == "Custom")
            spin.blockSignals(False)

    def canvas_init(self, *args, **kwargs):
        if callable(original_canvas_init):
            original_canvas_init(self, *args, **kwargs)
        self._page_setup_size_mm = WORKSPACE_SIZE_MM
        self._page_setup_landscape = True

    def dialog_init(self, *args, **kwargs):
        if callable(original_dialog_init):
            original_dialog_init(self, *args, **kwargs)
        self._paper_name = "Workspace"
        _set_size_spins(self, "Workspace")
        if hasattr(self, "_update_preview"):
            self._update_preview()

    def choose_paper(self, name: str) -> None:
        if callable(original_choose_paper):
            original_choose_paper(self, name)
        else:
            self._paper_name = name
        _set_size_spins(self, name)
        if hasattr(self, "_update_preview"):
            self._update_preview()

    def page_rect(self):
        width, height = getattr(self, "_page_setup_size_mm", WORKSPACE_SIZE_MM)
        available = QRectF(6, 3, max(80, self.width() - 12), max(80, self.height() - 8))
        ratio = max(0.01, float(height) / float(width))
        page_width = min(available.width(), available.height() / ratio)
        page_height = page_width * ratio
        if page_height > available.height():
            page_height = available.height()
            page_width = page_height / ratio
        return QRectF(available.center().x() - page_width / 2, available.center().y() - page_height / 2, page_width, page_height)

    def draw_arc_arrow(painter, center, radius, color, reverse=False):
        _paint_rotate_asset(painter, center, radius, color)

    def layer_button(self, kind: str, active: bool, tooltip: str, callback):
        if callable(original_layer_button):
            button = original_layer_button(self, kind, active, tooltip, callback)
        else:
            from PySide6.QtWidgets import QPushButton
            button = QPushButton()
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
        button.setIcon(_layer_icon(kind, active))
        button.setIconSize(QSize(23, 23))
        return button

    edw.EngineeringCanvas.__init__ = canvas_init
    edw.EngineeringCanvas._page_rect = page_rect
    edw._draw_arc_arrow = draw_arc_arrow
    edw.EngineeringDesignWorkspace._layer_button = layer_button
    rtp.PageSetupDialog.__init__ = dialog_init
    rtp.PageSetupDialog._choose_paper = choose_paper
    edw.EngineeringDesignWorkspace._workspace_finalize_patch_applied = True
    logging.info("engineering_workspace_finalize_patch: installed")

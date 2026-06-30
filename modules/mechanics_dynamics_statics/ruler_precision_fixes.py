"""Ruler precision fixes for unit labels and zoom-aware origins."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

PATCH_VERSION = "engineering-ruler-precision-2026-06-30-a"


def _scene_axis_to_view(canvas, value: float, axis: str) -> float:
    zoom = max(0.01, float(getattr(canvas, "_zoom", 1.0)))
    center = canvas.width() / 2.0 if axis == "x" else canvas.height() / 2.0
    return center + (value - center) * zoom


def apply_ruler_precision_fixes() -> None:
    from src.engineers_tools.ui import start_bar as sb

    if getattr(sb.StartBar, "_engineering_ruler_precision_patch", "") == PATCH_VERSION:
        return

    def overlay_paint(self, event) -> None:
        super(sb._RulerOverlay, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(20, 37, 58, 230))
        font = painter.font()
        font.setPointSize(7)
        font.setBold(True)
        font.setItalic(False)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff"), 1.0))

        canvas = self.parentWidget()
        unit = self._start_bar._unit
        zoom = max(0.01, float(getattr(canvas, "_zoom", 1.0))) if canvas is not None else 1.0
        spacing = max(1.0, self._start_bar._unit_to_canvas_px(1.0, unit) * zoom)
        length = self.width() if self._orientation == "top" else self.height()

        if canvas is not None and self._orientation == "top":
            zero = _scene_axis_to_view(canvas, self._start_bar._ruler_origin.x(), "x") - self.x()
        elif canvas is not None:
            zero = _scene_axis_to_view(canvas, self._start_bar._ruler_origin.y(), "y") - self.y()
        else:
            zero = self._start_bar._ruler_origin.x() - self.x() if self._orientation == "top" else self._start_bar._ruler_origin.y() - self.y()

        label_step = 10 if unit == "mm" else 1
        index = int(-zero / spacing) - 2
        while True:
            position = zero + index * spacing
            if position > length + spacing:
                break
            if position >= 0:
                abs_index = abs(index)
                is_label = abs_index % label_step == 0
                tick = 23 if is_label else 16 if unit == "mm" and abs_index % 5 == 0 else 8
                if self._orientation == "top":
                    painter.drawLine(QPointF(position, self.height()), QPointF(position, self.height() - tick))
                    if is_label:
                        painter.drawText(QRectF(position + 2, 1, 46, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
                else:
                    painter.drawLine(QPointF(self.width(), position), QPointF(self.width() - tick, position))
                    if is_label:
                        painter.drawText(QRectF(2, position + 1, self.width() - 4, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(index))
            index += 1
        painter.end()

    sb._RulerOverlay.paintEvent = overlay_paint
    sb.StartBar._engineering_ruler_precision_patch = PATCH_VERSION

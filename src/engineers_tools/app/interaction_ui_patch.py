"""Focused interaction refinements layered after the main runtime UI patch."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QWidget


def _triangle_arrow_head(painter: QPainter, tip: QPointF, tail: QPointF, color: QColor, size: float = 7.0) -> None:
    direction = tip - tail
    length = max(0.01, (direction.x() ** 2 + direction.y() ** 2) ** 0.5)
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    base = QPointF(tip.x() - unit.x() * size, tip.y() - unit.y() * size)
    left = QPointF(base.x() + normal.x() * size * 0.58, base.y() + normal.y() * size * 0.58)
    right = QPointF(base.x() - normal.x() * size * 0.58, base.y() - normal.y() * size * 0.58)
    painter.setBrush(color)
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(QPolygonF([tip, left, right]))


def _solid_arrow_head(painter: QPainter, tip: QPointF, back: QPointF, size: float = 6.0) -> None:
    _triangle_arrow_head(painter, tip, back, painter.pen().color(), size)


def _paint_rotation_glyph(painter: QPainter, center: QPointF, radius: float, color: QColor) -> None:
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(color, 2.15, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawArc(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), 46 * 16, 280 * 16)
    tip = QPointF(center.x() + radius * 0.77, center.y() - radius * 0.63)
    tail = QPointF(center.x() + radius * 0.06, center.y() - radius * 0.96)
    _triangle_arrow_head(painter, tip, tail, color, max(7.4, radius * 0.88))
    painter.restore()


def _hand_cursor(closed: bool = False) -> QCursor:
    cache = getattr(_hand_cursor, "_cache", {})
    if closed in cache:
        return cache[closed]
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    skin = QColor("#fff4dc")
    outline = QColor("#132238")
    painter.setPen(QPen(outline, 1.45, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(skin)
    if closed:
        palm = QPainterPath()
        palm.addRoundedRect(QRectF(8, 11, 17, 14), 6, 6)
        painter.fillPath(palm, skin)
        painter.drawPath(palm)
        for x in (9.5, 13.5, 17.5, 21.0):
            painter.drawRoundedRect(QRectF(x, 7.0, 4.3, 10.0), 2.0, 2.0)
        painter.drawLine(QPointF(12, 22), QPointF(22, 22))
    else:
        painter.drawRoundedRect(QRectF(12, 8, 5, 16), 2.4, 2.4)
        painter.drawRoundedRect(QRectF(7, 13, 5, 12), 2.4, 2.4)
        painter.drawRoundedRect(QRectF(17, 10, 5, 14), 2.4, 2.4)
        painter.drawRoundedRect(QRectF(22, 13, 5, 11), 2.4, 2.4)
        painter.drawRoundedRect(QRectF(9, 20, 16, 7), 4.0, 4.0)
    painter.end()
    cursor = QCursor(pixmap, 15, 15)
    cache[closed] = cursor
    _hand_cursor._cache = cache
    return cursor


def _style_numeric_spin(spin: QDoubleSpinBox) -> None:
    spin.setStyleSheet(
        """
        QDoubleSpinBox#FileNameInput {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:8px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:4px 23px 4px 7px;
        }
        QDoubleSpinBox#FileNameInput::up-button, QDoubleSpinBox#FileNameInput::down-button {
            width:20px; border:0;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.48 #fff2b8, stop:1 #5ed7c4);
            subcontrol-origin:border;
        }
        QDoubleSpinBox#FileNameInput::up-button { subcontrol-position:top right; border-top-right-radius:7px; }
        QDoubleSpinBox#FileNameInput::down-button { subcontrol-position:bottom right; border-bottom-right-radius:7px; }
        QDoubleSpinBox#FileNameInput::up-arrow {
            width:0; height:0; border-left:6px solid transparent; border-right:6px solid transparent; border-bottom:8px solid #132238;
        }
        QDoubleSpinBox#FileNameInput::down-arrow {
            width:0; height:0; border-left:6px solid transparent; border-right:6px solid transparent; border-top:8px solid #132238;
        }
        """
    )


def _style_combo_arrow(combo: QComboBox) -> None:
    combo.setStyleSheet(
        """
        QComboBox#FileTypeCombo {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:8px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:5px 30px 5px 8px;
        }
        QComboBox#FileTypeCombo::drop-down {
            width:26px; border:0;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.48 #fff2b8, stop:1 #5ed7c4);
            border-top-right-radius:7px; border-bottom-right-radius:7px;
        }
        QComboBox#FileTypeCombo::down-arrow {
            width:0; height:0; border-left:7px solid transparent; border-right:7px solid transparent; border-top:9px solid #132238;
        }
        QComboBox#FileTypeCombo QAbstractItemView {
            background:#ffffff; border:1px solid #8fa2bb; border-radius:8px; selection-background-color:#cfe7ff;
        }
        """
    )


def apply_interaction_ui_patch() -> None:
    from . import module_window as mw
    from . import runtime_ui_patch as rtp
    from ..ui import start_bar as sb

    rtp._paint_rotation_glyph = _paint_rotation_glyph
    rtp._style_numeric_spin = _style_numeric_spin
    rtp._style_combo_arrow = _style_combo_arrow
    mw._paint_rotation_glyph = _paint_rotation_glyph
    sb._arrow_head = _solid_arrow_head

    def canvas_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            point = self._to_canvas_coordinates(event.position())
            action = self._hit_test(point)
            if action is not None and self._object_rect is not None:
                self._drag_action = action
                self._drag_start = point
                self._drag_start_rect = QRectF(self._object_rect)
                self._drag_start_rotation = self._rotation_degrees
                if action in {"move", "rotate"}:
                    self.setCursor(_hand_cursor(True))
                event.accept()
                return
        QWidget.mousePressEvent(self, event)

    def canvas_mouse_move(self, event):
        point = self._to_canvas_coordinates(event.position())
        self.mouse_position_changed.emit(point.x(), point.y())
        if self._drag_action is not None:
            self._apply_drag(point)
            if self._drag_action in {"move", "rotate"}:
                self.setCursor(_hand_cursor(True))
            event.accept()
            return
        hover = self._hit_test(point)
        if hover in {"move", "rotate"}:
            self.setCursor(_hand_cursor(False))
        elif hover in {"resize_n", "resize_s"}:
            self.setCursor(Qt.SizeVerCursor)
        elif hover in {"resize_e", "resize_w"}:
            self.setCursor(Qt.SizeHorCursor)
        elif hover in {"resize_ne", "resize_sw"}:
            self.setCursor(Qt.SizeBDiagCursor)
        elif hover in {"resize_nw", "resize_se"}:
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.unsetCursor()
        QWidget.mouseMoveEvent(self, event)

    def canvas_mouse_release(self, event):
        self._drag_action = None
        point = self._to_canvas_coordinates(event.position())
        hover = self._hit_test(point)
        if hover in {"move", "rotate"}:
            self.setCursor(_hand_cursor(False))
        else:
            self.unsetCursor()
        QWidget.mouseReleaseEvent(self, event)

    mw.GridCanvas.mousePressEvent = canvas_mouse_press
    mw.GridCanvas.mouseMoveEvent = canvas_mouse_move
    mw.GridCanvas.mouseReleaseEvent = canvas_mouse_release

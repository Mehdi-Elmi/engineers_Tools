"""Unified cursor style for Engineering Design Tools.

Window resize, canvas resize, guide movement, and the default pointer must come
from one visual family. Resize cursors use the approved two-arrow glyph with the
small yellow center node.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QCursor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

PATCH_VERSION = "engineering-cursor-unification-2026-06-30-a"


def _arrow_head(painter: QPainter, tip: QPointF, tail: QPointF, size: float = 5.2) -> None:
    direction = tip - tail
    length = max(0.01, math.hypot(direction.x(), direction.y()))
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    base = QPointF(tip.x() - unit.x() * size, tip.y() - unit.y() * size)
    left = QPointF(base.x() + normal.x() * size * 0.48, base.y() + normal.y() * size * 0.48)
    right = QPointF(base.x() - normal.x() * size * 0.48, base.y() - normal.y() * size * 0.48)
    painter.drawPolygon(QPolygonF([tip, left, right]))


def _paint_resize_line(painter: QPainter, a: QPointF, b: QPointF) -> None:
    painter.setPen(QPen(QColor("#ffffff"), 4.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawLine(a, b)
    painter.setPen(QPen(QColor("#132238"), 2.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawLine(a, b)
    painter.setBrush(QColor("#132238"))
    painter.setPen(Qt.PenStyle.NoPen)
    _arrow_head(painter, a, b)
    _arrow_head(painter, b, a)
    painter.setBrush(QColor("#ffc35a"))
    painter.setPen(QPen(QColor("#132238"), 1.1))
    painter.drawEllipse(QPointF(16, 16), 3.4, 3.4)


def _paint_hand(painter: QPainter, closed: bool) -> None:
    ink = QColor("#132238")
    fill = QLinearGradient(7, 4, 25, 29)
    fill.setColorAt(0.0, QColor("#ffffff"))
    fill.setColorAt(0.54, QColor("#dff4ff"))
    fill.setColorAt(1.0, QColor("#78b8ff" if closed else "#8dc1ff"))
    path = QPainterPath()
    if closed:
        path.addRoundedRect(8, 11, 17, 15, 6, 6)
        path.addRoundedRect(9, 7, 4, 9, 2, 2)
        path.addRoundedRect(13, 6, 4, 10, 2, 2)
        path.addRoundedRect(17, 7, 4, 9, 2, 2)
        path.addRoundedRect(21, 10, 4, 8, 2, 2)
    else:
        path.addRoundedRect(8, 12, 15, 15, 6, 6)
        path.addRoundedRect(8, 5, 4, 13, 2, 2)
        path.addRoundedRect(12, 4, 4, 14, 2, 2)
        path.addRoundedRect(16, 5, 4, 13, 2, 2)
        path.addRoundedRect(20, 8, 4, 11, 2, 2)
    painter.fillPath(path, fill)
    painter.setPen(QPen(QColor("#ffffff"), 3.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)
    painter.setPen(QPen(ink, 1.35, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)


def project_cursor(kind: str) -> QCursor:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    if kind in {"resize_h", "guide_v"}:
        _paint_resize_line(painter, QPointF(6, 16), QPointF(26, 16))
    elif kind in {"resize_v", "guide_h"}:
        _paint_resize_line(painter, QPointF(16, 6), QPointF(16, 26))
    elif kind == "resize_fdiag":
        _paint_resize_line(painter, QPointF(8, 8), QPointF(24, 24))
    elif kind == "resize_bdiag":
        _paint_resize_line(painter, QPointF(24, 8), QPointF(8, 24))
    elif kind == "move":
        for tip, tail in ((QPointF(16, 5), QPointF(16, 15)), (QPointF(27, 16), QPointF(17, 16)), (QPointF(16, 27), QPointF(16, 17)), (QPointF(5, 16), QPointF(15, 16))):
            painter.setPen(QPen(QColor("#ffffff"), 3.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(tail, tip)
            painter.setPen(QPen(QColor("#132238"), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(tail, tip)
            painter.setBrush(QColor("#132238"))
            _arrow_head(painter, tip, tail, 4.8)
        painter.setBrush(QColor("#ffc35a"))
        painter.setPen(QPen(QColor("#132238"), 1.0))
        painter.drawEllipse(QPointF(16, 16), 2.8, 2.8)
    elif kind in {"rotate", "hand_open"}:
        _paint_hand(painter, closed=False)
    elif kind == "hand_closed":
        _paint_hand(painter, closed=True)
    elif kind == "origin":
        painter.setPen(QPen(QColor("#ffffff"), 3.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(8, 16), QPointF(24, 16))
        painter.drawLine(QPointF(16, 8), QPointF(16, 24))
        painter.setPen(QPen(QColor("#132238"), 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(8, 16), QPointF(24, 16))
        painter.drawLine(QPointF(16, 8), QPointF(16, 24))
        painter.setBrush(QColor("#ffc35a"))
        painter.setPen(QPen(QColor("#132238"), 1.0))
        painter.drawEllipse(QPointF(16, 16), 2.8, 2.8)
    else:
        path = QPainterPath()
        path.moveTo(7, 5)
        path.lineTo(24, 17)
        path.lineTo(16.5, 18.4)
        path.lineTo(21.5, 28)
        path.lineTo(16.2, 29)
        path.lineTo(11.8, 19.5)
        path.lineTo(7, 24)
        path.closeSubpath()
        grad = QLinearGradient(6, 5, 24, 28)
        grad.setColorAt(0.0, QColor("#ffffff"))
        grad.setColorAt(0.58, QColor("#dff4ff"))
        grad.setColorAt(1.0, QColor("#8dc1ff"))
        painter.fillPath(path, grad)
        painter.setPen(QPen(QColor("#132238"), 1.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)
    painter.end()
    return QCursor(pixmap, 16, 16)


def apply_cursor_unification_fixes() -> None:
    from . import interaction_fixes
    from . import ui_refinement_fixes
    from . import window_resize_fixes

    if getattr(interaction_fixes, "_engineering_cursor_unification_patch", "") == PATCH_VERSION:
        return

    interaction_fixes.project_cursor = project_cursor
    ui_refinement_fixes._refined_project_cursor = project_cursor
    window_resize_fixes._window_cursor = project_cursor
    interaction_fixes._engineering_cursor_unification_patch = PATCH_VERSION

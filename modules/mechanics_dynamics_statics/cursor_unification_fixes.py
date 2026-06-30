"""Unified cursor style for Engineering Design Tools.

Window resize, canvas resize, guide movement, and the default pointer must come
from one visual family. Resize cursors use the approved two-arrow glyph with the
small yellow center node.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

PATCH_VERSION = "engineering-cursor-unification-2026-06-30-e"


def _arrow_head(painter: QPainter, tip: QPointF, tail: QPointF, size: float = 5.2) -> None:
    direction = tip - tail
    length = max(0.01, math.hypot(direction.x(), direction.y()))
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    base = QPointF(tip.x() - unit.x() * size, tip.y() - unit.y() * size)
    left = QPointF(base.x() + normal.x() * size * 0.48, base.y() + normal.y() * size * 0.48)
    right = QPointF(base.x() - normal.x() * size * 0.48, base.y() - normal.y() * size * 0.48)
    painter.drawPolygon(QPolygonF([tip, left, right]))


def _paint_stroked_line(painter: QPainter, a: QPointF, b: QPointF, ink: QColor) -> None:
    painter.setPen(QPen(QColor("#ffffff"), 4.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawLine(a, b)
    painter.setPen(QPen(ink, 2.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawLine(a, b)


def _paint_resize_line(painter: QPainter, a: QPointF, b: QPointF) -> None:
    ink = QColor("#132238")
    direction = b - a
    length = max(0.01, math.hypot(direction.x(), direction.y()))
    unit = QPointF(direction.x() / length, direction.y() / length)
    center = QPointF((a.x() + b.x()) / 2.0, (a.y() + b.y()) / 2.0)
    gap = 5.2
    left_inner = QPointF(center.x() - unit.x() * gap, center.y() - unit.y() * gap)
    right_inner = QPointF(center.x() + unit.x() * gap, center.y() + unit.y() * gap)

    _paint_stroked_line(painter, a, left_inner, ink)
    _paint_stroked_line(painter, right_inner, b, ink)
    painter.setBrush(ink)
    painter.setPen(Qt.PenStyle.NoPen)
    _arrow_head(painter, a, left_inner, 5.8)
    _arrow_head(painter, b, right_inner, 5.8)
    painter.setBrush(QColor("#ffc35a"))
    painter.setPen(QPen(ink, 1.1))
    painter.drawEllipse(center, 3.4, 3.4)


def _paint_hand(painter: QPainter, closed: bool) -> None:
    ink = QColor("#132238")
    fill = QLinearGradient(7, 4, 25, 29)
    fill.setColorAt(0.0, QColor("#ffffff"))
    fill.setColorAt(0.48, QColor("#fff1bf" if closed else "#dff4ff"))
    fill.setColorAt(1.0, QColor("#ff8a35" if closed else "#7bc7ff"))
    path = QPainterPath()
    if closed:
        path.addRoundedRect(QRectF(8.0, 11.0, 17.2, 15.0), 6.0, 6.0)
        path.addRoundedRect(QRectF(8.6, 7.2, 4.4, 9.3), 2.1, 2.1)
        path.addRoundedRect(QRectF(12.8, 5.8, 4.4, 10.8), 2.1, 2.1)
        path.addRoundedRect(QRectF(17.0, 6.9, 4.4, 9.5), 2.1, 2.1)
        path.addRoundedRect(QRectF(21.0, 9.8, 4.2, 8.2), 2.0, 2.0)
    else:
        path.addRoundedRect(QRectF(8.0, 12.2, 15.6, 14.8), 6.0, 6.0)
        path.addRoundedRect(QRectF(7.6, 5.0, 4.2, 13.4), 2.0, 2.0)
        path.addRoundedRect(QRectF(11.8, 3.8, 4.2, 14.7), 2.0, 2.0)
        path.addRoundedRect(QRectF(16.0, 4.9, 4.2, 13.6), 2.0, 2.0)
        path.addRoundedRect(QRectF(20.0, 7.8, 4.2, 11.2), 2.0, 2.0)
    painter.fillPath(path, fill)
    painter.setPen(QPen(QColor("#ffffff"), 3.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)
    painter.setPen(QPen(ink, 1.35, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)


def project_cursor(kind: str) -> QCursor:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    if kind in {"resize_h", "guide_v"}:
        _paint_resize_line(painter, QPointF(5, 16), QPointF(27, 16))
    elif kind in {"resize_v", "guide_h"}:
        _paint_resize_line(painter, QPointF(16, 5), QPointF(16, 27))
    elif kind == "resize_fdiag":
        _paint_resize_line(painter, QPointF(7, 7), QPointF(25, 25))
    elif kind == "resize_bdiag":
        _paint_resize_line(painter, QPointF(25, 7), QPointF(7, 25))
    elif kind == "move":
        ink = QColor("#145f8f")
        for tip, tail in ((QPointF(16, 5), QPointF(16, 15)), (QPointF(27, 16), QPointF(17, 16)), (QPointF(16, 27), QPointF(16, 17)), (QPointF(5, 16), QPointF(15, 16))):
            _paint_stroked_line(painter, tail, tip, ink)
            painter.setBrush(ink)
            painter.setPen(Qt.PenStyle.NoPen)
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

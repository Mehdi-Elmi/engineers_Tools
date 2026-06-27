"""Painted launcher card button."""

from __future__ import annotations

import math

from PySide6.QtCore import QLineF, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QPushButton

from ..app.modules import LauncherModule


class LauncherButton(QPushButton):
    def __init__(self, module: LauncherModule) -> None:
        super().__init__()
        self.module = module
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(186)
        self.setCheckable(False)
        self.setText("")

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(260, 204)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(5, 4, self.width() - 10, self.height() - 10)
        pressed_offset = 3 if self.isDown() else 0
        body = rect.translated(0, pressed_offset)
        shadow = QPainterPath()
        shadow.addRoundedRect(rect.translated(0, 9), 12, 12)
        painter.fillPath(shadow, QColor(57, 75, 102, 68 if not self.isDown() else 28))
        gradient = QLinearGradient(body.topLeft(), body.bottomRight())
        gradient.setColorAt(0.0, QColor("#ffffff"))
        gradient.setColorAt(0.55, QColor("#eef4fb"))
        gradient.setColorAt(1.0, QColor("#d6e2f0"))
        path = QPainterPath()
        path.addRoundedRect(body, 12, 12)
        painter.fillPath(path, gradient)
        painter.setPen(QPen(QColor(self.module.accent) if self.underMouse() else QColor("#b8c5d4"), 1.3))
        painter.drawPath(path)
        accent = QColor(self.module.accent)
        painter.fillRect(QRectF(body.left() + 18, body.top() + 15, body.width() - 36, 4), accent)
        self._paint_icon(painter, body, accent)
        self._paint_text(painter, body)

    def _paint_text(self, painter: QPainter, body: QRectF) -> None:
        title_rect = QRectF(body.left() + 18, body.bottom() - 54, body.width() - 36, 25)
        hint_rect = QRectF(body.left() + 18, body.bottom() - 29, body.width() - 36, 20)
        painter.setPen(QColor("#182638"))
        title_font = QFont("Times New Roman", 12, QFont.Bold)
        title_font.setItalic(True)
        painter.setFont(title_font)
        painter.drawText(title_rect, Qt.AlignCenter, self.module.label)
        painter.setPen(QColor("#617082"))
        hint_font = QFont("Times New Roman", 8, QFont.Bold)
        hint_font.setItalic(True)
        painter.setFont(hint_font)
        painter.drawText(hint_rect, Qt.AlignCenter, self.module.description)

    def _paint_icon(self, painter: QPainter, body: QRectF, accent: QColor) -> None:
        icon_size = 94
        icon_rect = QRectF(body.center().x() - icon_size / 2, body.top() + 38, icon_size, icon_size)
        icon_gradient = QLinearGradient(icon_rect.topLeft(), icon_rect.bottomRight())
        icon_gradient.setColorAt(0, accent.lighter(185))
        icon_gradient.setColorAt(1, accent.darker(125))
        icon_path = QPainterPath()
        icon_path.addRoundedRect(icon_rect, 24, 24)
        painter.fillPath(icon_path, icon_gradient)
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        painter.drawPath(icon_path)
        painter.setPen(QPen(QColor("#ffffff"), 3.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        if self.module.icon_kind == "engineering":
            self._paint_engineering_icon(painter, icon_rect)
        elif self.module.icon_kind == "circuits":
            self._paint_circuit_icon(painter, icon_rect)
        elif self.module.icon_kind == "flowcharts":
            self._paint_flowchart_icon(painter, icon_rect)
        elif self.module.icon_kind == "barcode":
            self._paint_barcode_icon(painter, icon_rect)
        else:
            self._paint_background_icon(painter, icon_rect)

    def _paint_engineering_icon(self, painter: QPainter, rect: QRectF) -> None:
        origin = QPointF(rect.left() + 24, rect.bottom() - 22)
        x_end = QPointF(rect.right() - 18, origin.y())
        y_end = QPointF(origin.x(), rect.top() + 18)
        vector_end = QPointF(rect.right() - 24, rect.top() + 31)
        painter.drawLine(QLineF(origin, x_end))
        painter.drawLine(QLineF(origin, y_end))
        painter.drawLine(QLineF(origin, vector_end))
        painter.setBrush(QColor("#ffffff"))
        painter.drawPolygon(QPolygonF([x_end, QPointF(x_end.x() - 9, x_end.y() - 5), QPointF(x_end.x() - 9, x_end.y() + 5)]))
        painter.drawPolygon(QPolygonF([y_end, QPointF(y_end.x() - 5, y_end.y() + 9), QPointF(y_end.x() + 5, y_end.y() + 9)]))
        line = QLineF(origin, vector_end)
        angle = math.atan2(line.dy(), line.dx())
        back_x = math.cos(angle)
        back_y = math.sin(angle)
        normal_x = -back_y
        normal_y = back_x
        painter.drawPolygon(QPolygonF([vector_end, QPointF(vector_end.x() - back_x * 13 + normal_x * 5, vector_end.y() - back_y * 13 + normal_y * 5), QPointF(vector_end.x() - back_x * 13 - normal_x * 5, vector_end.y() - back_y * 13 - normal_y * 5)]))
        painter.setBrush(Qt.NoBrush)
        angle_degrees = math.degrees(math.atan2(origin.y() - vector_end.y(), vector_end.x() - origin.x()))
        radius = 28
        painter.drawArc(QRectF(origin.x() - radius, origin.y() - radius, radius * 2, radius * 2), 0, int(angle_degrees * 16))
        painter.setFont(QFont("Times New Roman", 10, QFont.Bold))
        painter.drawText(QRectF(origin.x() + 24, origin.y() - 31, 16, 14), Qt.AlignCenter, "θ")
        painter.drawText(QRectF(x_end.x() - 2, x_end.y() + 3, 12, 12), Qt.AlignCenter, "x")
        painter.drawText(QRectF(y_end.x() - 15, y_end.y() - 4, 12, 12), Qt.AlignCenter, "y")

    def _paint_circuit_icon(self, painter: QPainter, rect: QRectF) -> None:
        painter.save()
        shadow_pen = QPen(QColor(19, 34, 56, 95), 5.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        trace_pen = QPen(QColor("#ffffff"), 3.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        chip_rect = QRectF(rect.center().x() - 20, rect.center().y() - 22, 40, 44)

        def draw_traces(pen: QPen) -> None:
            painter.setPen(pen)
            left_x = rect.left() + 13
            right_x = rect.right() - 13
            top_y = rect.top() + 16
            mid_y = rect.center().y()
            low_y = rect.bottom() - 17
            painter.drawLine(QLineF(left_x, top_y, chip_rect.left(), chip_rect.top() + 8))
            painter.drawLine(QLineF(left_x, mid_y, chip_rect.left(), chip_rect.center().y()))
            painter.drawLine(QLineF(left_x, low_y, chip_rect.left(), chip_rect.bottom() - 8))
            painter.drawLine(QLineF(chip_rect.right(), chip_rect.top() + 8, right_x, top_y))
            painter.drawLine(QLineF(chip_rect.right(), chip_rect.center().y(), right_x, mid_y))
            painter.drawLine(QLineF(chip_rect.right(), chip_rect.bottom() - 8, right_x, low_y))
            painter.drawLine(QLineF(left_x, top_y, left_x, mid_y))
            painter.drawLine(QLineF(right_x, mid_y, right_x, low_y))

        draw_traces(shadow_pen)
        draw_traces(trace_pen)

        painter.setPen(QPen(QColor("#ffffff"), 2.2, Qt.SolidLine, Qt.RoundCap))
        for y_offset in (8, 18, 28, 38):
            painter.drawLine(QLineF(chip_rect.left() - 7, chip_rect.top() + y_offset, chip_rect.left(), chip_rect.top() + y_offset))
            painter.drawLine(QLineF(chip_rect.right(), chip_rect.top() + y_offset, chip_rect.right() + 7, chip_rect.top() + y_offset))

        chip_path = QPainterPath()
        chip_path.addRoundedRect(chip_rect, 8, 8)
        chip_gradient = QLinearGradient(chip_rect.topLeft(), chip_rect.bottomRight())
        chip_gradient.setColorAt(0.0, QColor(255, 255, 255, 68))
        chip_gradient.setColorAt(1.0, QColor(19, 34, 56, 90))
        painter.fillPath(chip_path, chip_gradient)
        painter.setPen(QPen(QColor("#ffffff"), 2.4))
        painter.drawPath(chip_path)

        painter.setPen(QPen(QColor("#ffffff"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QLineF(chip_rect.left() + 9, chip_rect.center().y() - 5, chip_rect.left() + 16, chip_rect.center().y() + 5))
        painter.drawLine(QLineF(chip_rect.left() + 16, chip_rect.center().y() + 5, chip_rect.left() + 23, chip_rect.center().y() - 5))
        painter.drawLine(QLineF(chip_rect.left() + 23, chip_rect.center().y() - 5, chip_rect.left() + 31, chip_rect.center().y() + 5))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffffff"))
        for point in (
            QPointF(rect.left() + 13, rect.top() + 16), QPointF(rect.left() + 13, rect.center().y()), QPointF(rect.left() + 13, rect.bottom() - 17),
            QPointF(rect.right() - 13, rect.top() + 16), QPointF(rect.right() - 13, rect.center().y()), QPointF(rect.right() - 13, rect.bottom() - 17),
        ):
            painter.drawEllipse(point, 3.6, 3.6)
        painter.restore()

    def _paint_flowchart_icon(self, painter: QPainter, rect: QRectF) -> None:
        top_box = QRectF(rect.center().x() - 28, rect.top() + 8, 56, 17)
        diamond = QPolygonF([QPointF(rect.center().x(), rect.top() + 34), QPointF(rect.right() - 10, rect.top() + 49), QPointF(rect.center().x(), rect.top() + 64), QPointF(rect.left() + 10, rect.top() + 49)])
        bottom_left = QRectF(rect.left() + 7, rect.bottom() - 17, 31, 15)
        bottom_right = QRectF(rect.right() - 38, rect.bottom() - 17, 31, 15)
        painter.setBrush(QColor(255, 255, 255, 42))
        painter.drawRoundedRect(top_box, 7, 7)
        painter.drawPolygon(diamond)
        painter.drawRoundedRect(bottom_left, 4, 4)
        painter.drawRoundedRect(bottom_right, 4, 4)
        painter.setBrush(Qt.NoBrush)
        split_y = rect.bottom() - 23
        painter.drawLine(QLineF(rect.center().x(), top_box.bottom(), rect.center().x(), rect.top() + 34))
        painter.drawLine(QLineF(rect.center().x(), rect.top() + 64, rect.center().x(), split_y))
        painter.drawLine(QLineF(rect.center().x(), split_y, bottom_left.center().x(), split_y))
        painter.drawLine(QLineF(rect.center().x(), split_y, bottom_right.center().x(), split_y))
        painter.drawLine(QLineF(bottom_left.center().x(), split_y, bottom_left.center().x(), bottom_left.top()))
        painter.drawLine(QLineF(bottom_right.center().x(), split_y, bottom_right.center().x(), bottom_right.top()))

    def _paint_barcode_icon(self, painter: QPainter, rect: QRectF) -> None:
        barcode = rect.adjusted(15, 17, -15, -18)
        painter.drawRoundedRect(barcode.adjusted(-5, -5, 5, 5), 5, 5)
        painter.save()
        painter.setClipRect(barcode)
        x = barcode.left() + 3
        for width in (4, 1, 2, 5, 1, 3, 2, 6, 1, 2, 4):
            painter.setPen(QPen(QColor("#ffffff"), width, Qt.SolidLine, Qt.FlatCap))
            painter.drawLine(int(x), int(barcode.top()), int(x), int(barcode.bottom()))
            x += width + 2.5
        painter.restore()

    def _paint_background_icon(self, painter: QPainter, rect: QRectF) -> None:
        frame = QRectF(rect.left() + 15, rect.top() + 16, 48, 37)
        painter.setBrush(QColor(255, 255, 255, 35))
        painter.drawRoundedRect(frame, 6, 6)
        painter.setBrush(Qt.NoBrush)
        for row in range(3):
            for col in range(4):
                if (row + col) % 2 == 0:
                    painter.fillRect(QRectF(frame.left() + 5 + col * 6, frame.top() + 6 + row * 6, 6, 6), QColor(255, 255, 255, 54))
        painter.drawLine(QLineF(frame.left() + 8, frame.bottom() - 9, frame.left() + 20, frame.top() + 19))
        painter.drawLine(QLineF(frame.left() + 20, frame.top() + 19, frame.left() + 31, frame.bottom() - 12))
        painter.drawLine(QLineF(frame.left() + 31, frame.bottom() - 12, frame.right() - 6, frame.top() + 11))
        painter.setPen(QPen(QColor("#ffffff"), 4.2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QLineF(rect.left() + 20, rect.bottom() - 13, rect.right() - 14, rect.top() + 18))

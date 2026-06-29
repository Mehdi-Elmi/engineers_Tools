"""Final engineering canvas sizing and export rendering patch."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QMarginsF, QPointF, QRectF, QSize, QSizeF, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QDialog

from .interaction_ui_patch import _paint_asset_icon


def _better_layer_icon(kind: str, active: bool = True) -> QIcon:
    pixmap = QPixmap(34, 34)
    pixmap.fill(Qt.transparent)
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

    asset_name = {
        "eye": "layer_eye.svg",
        "lock": "layer_lock_closed.svg" if active else "layer_lock_open.svg",
        "rotation": "layer_rotate.svg",
        "rotate": "layer_rotate.svg",
    }.get(kind)
    if asset_name and _paint_asset_icon(painter, asset_name, QRectF(6, 6, 22, 22)):
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
        painter.setPen(QPen(QColor("#0d2745"), 1.2))
        painter.drawArc(QRectF(10.4, 10.4, 13.2, 13.2), 25 * 16, 310 * 16)
        painter.setPen(Qt.PenStyle.NoPen)
        iris = QLinearGradient(12, 12, 22, 22)
        iris.setColorAt(0.0, QColor("#7be7ff" if active else "#c5ced8"))
        iris.setColorAt(0.55, QColor("#2f7df6" if active else "#8b98a8"))
        iris.setColorAt(1.0, QColor("#143f86" if active else "#657385"))
        painter.setBrush(iris)
        painter.drawEllipse(QPointF(17, 17), 4.8, 4.8)
        painter.setBrush(QColor("#07192f"))
        painter.drawEllipse(QPointF(17, 17), 2.2, 2.2)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QPointF(18.9, 15.1), 1.2, 1.2)
    elif kind == "lock":
        lock_gradient = QLinearGradient(8, 8, 26, 27)
        lock_gradient.setColorAt(0.0, QColor("#fff7d8"))
        lock_gradient.setColorAt(0.55, QColor("#ffbe4a" if active else "#f2f7fb"))
        lock_gradient.setColorAt(1.0, QColor("#dc7a17" if active else "#91a1b5"))
        if active:
            painter.drawArc(QRectF(10, 7, 14, 14), 0, 180 * 16)
            painter.drawLine(QPointF(10, 14), QPointF(10, 16))
            painter.drawLine(QPointF(24, 14), QPointF(24, 16))
        else:
            painter.drawArc(QRectF(11, 7, 14, 14), 35 * 16, 145 * 16)
            painter.drawLine(QPointF(22, 11), QPointF(26, 8.4))
        body = QPainterPath()
        body.addRoundedRect(QRectF(8.2, 15, 17.6, 11.5), 3.8, 3.8)
        painter.setBrush(lock_gradient)
        painter.drawPath(body)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(ink)
        painter.drawEllipse(QPointF(17, 20.1), 1.9, 1.9)
        painter.drawRoundedRect(QRectF(16.2, 20.0, 1.6, 4.6), 0.8, 0.8)
    else:
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(ink, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawArc(QRectF(8.5, 8.5, 17, 17), 45 * 16, 280 * 16)
        painter.setBrush(ink)
        painter.drawEllipse(QPointF(23.2, 12.4), 2.6, 2.6)

    if not active:
        painter.setPen(QPen(QColor("#d44777"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(8, 26), QPointF(26, 8))
    painter.end()
    return QIcon(pixmap)


def _page_size_mm(canvas) -> tuple[float, float]:
    width, height = getattr(canvas, "_page_setup_size_mm", (400.0, 220.0))
    return max(1.0, float(width)), max(1.0, float(height))


def _dpi(canvas) -> int:
    return max(72, min(2400, int(getattr(canvas, "_page_setup_dpi", 600))))


def _pixel_size(width_mm: float, height_mm: float, dpi: int) -> tuple[int, int]:
    width_px = max(1, round(width_mm / 25.4 * dpi))
    height_px = max(1, round(height_mm / 25.4 * dpi))
    max_side = 12000
    if max(width_px, height_px) > max_side:
        scale = max_side / max(width_px, height_px)
        logging.info("engineering_export_patch: capped export pixels from %sx%s with scale %.3f", width_px, height_px, scale)
        width_px = max(1, round(width_px * scale))
        height_px = max(1, round(height_px * scale))
    return width_px, height_px


def _visible_objects(canvas) -> list:
    return [obj for obj in getattr(canvas, "objects", []) if getattr(obj, "visible", True)]


def _bounds(canvas, objects: list) -> QRectF:
    output = QRectF()
    for obj in objects:
        rect = canvas._object_scene_bounds(obj) if hasattr(canvas, "_object_scene_bounds") else QRectF(getattr(obj, "rect", QRectF()))
        output = QRectF(rect) if output.isNull() else output.united(rect)
    if output.isNull():
        return canvas._page_rect() if hasattr(canvas, "_page_rect") else QRectF(0, 0, max(1, canvas.width()), max(1, canvas.height()))
    return output.adjusted(-4, -4, 4, 4)


def _printable(target: QRectF, page_size: tuple[float, float], margins) -> QRectF:
    width_mm, height_mm = page_size
    top, right, bottom, left = margins or (0.0, 0.0, 0.0, 0.0)
    rect = target.adjusted(
        target.width() * max(0.0, float(left)) / width_mm,
        target.height() * max(0.0, float(top)) / height_mm,
        -target.width() * max(0.0, float(right)) / width_mm,
        -target.height() * max(0.0, float(bottom)) / height_mm,
    )
    return rect if rect.width() >= 16 and rect.height() >= 16 else target.adjusted(8, 8, -8, -8)


def _draw_grid(painter: QPainter, target: QRectF, page_size: tuple[float, float]) -> None:
    width_mm, height_mm = page_size
    x_step = max(2.0, target.width() * 10.0 / width_mm)
    y_step = max(2.0, target.height() * 10.0 / height_mm)
    painter.save()
    painter.setPen(QPen(QColor(70, 96, 130, 48), 1))
    x = target.left()
    while x <= target.right() + 0.5:
        painter.drawLine(QPointF(x, target.top()), QPointF(x, target.bottom()))
        x += x_step
    y = target.top()
    while y <= target.bottom() + 0.5:
        painter.drawLine(QPointF(target.left(), y), QPointF(target.right(), y))
        y += y_step
    painter.restore()


def _draw_objects(painter: QPainter, canvas, objects: list, source: QRectF, target: QRectF) -> None:
    if not objects or source.width() <= 0 or source.height() <= 0:
        return
    scale = min(target.width() / source.width(), target.height() / source.height())
    offset = QPointF(target.center().x() - source.center().x() * scale, target.center().y() - source.center().y() * scale)
    for obj in objects:
        rect = QRectF(getattr(obj, "rect", QRectF()))
        center = QPointF(rect.center().x() * scale + offset.x(), rect.center().y() * scale + offset.y())
        local = QRectF(-rect.width() * scale / 2, -rect.height() * scale / 2, rect.width() * scale, rect.height() * scale)
        painter.save()
        painter.translate(center)
        painter.rotate(float(getattr(obj, "rotation", 0.0)))
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        pixmap = getattr(obj, "pixmap", QPixmap())
        if isinstance(pixmap, QPixmap) and not pixmap.isNull():
            painter.drawPixmap(local.toRect(), pixmap)
        else:
            painter.setPen(QPen(QColor("#465d78"), 1.2))
            painter.setBrush(QColor("#ffffff"))
            painter.drawRect(local)
            painter.drawText(local, Qt.AlignmentFlag.AlignCenter, str(getattr(obj, "name", "Object")))
        painter.restore()


def _render(window, painter: QPainter, target: QRectF, transparent: bool = False) -> None:
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return
    page_size = _page_size_mm(canvas)
    options = getattr(window, "_save_options", {}) or {}
    if not transparent:
        painter.fillRect(target, QColor("#ffffff"))
    if options.get("save_grid", False):
        _draw_grid(painter, target, page_size)
    objects = _visible_objects(canvas)
    _draw_objects(painter, canvas, objects, _bounds(canvas, objects), _printable(target, page_size, getattr(canvas, "_page_setup_margins", None)))


def _write_image(window, path: Path) -> bool:
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return False
    width_mm, height_mm = _page_size_mm(canvas)
    width_px, height_px = _pixel_size(width_mm, height_mm, _dpi(canvas))
    transparent = bool((getattr(window, "_save_options", {}) or {}).get("remove_white_background", False))
    image = QImage(width_px, height_px, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent if transparent else QColor("#ffffff"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    _render(window, painter, QRectF(0, 0, width_px, height_px), transparent)
    painter.end()
    return bool(image.save(str(path)))


def _write_pdf(window, path: Path) -> bool:
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return False
    try:
        from PySide6.QtGui import QPageLayout, QPageSize, QPdfWriter
    except Exception:
        return False
    width_mm, height_mm = _page_size_mm(canvas)
    writer = QPdfWriter(str(path))
    writer.setResolution(_dpi(canvas))
    writer.setPageSize(QPageSize(QSizeF(width_mm, height_mm), QPageSize.Unit.Millimeter))
    writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
    painter = QPainter(writer)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    _render(window, painter, QRectF(0, 0, writer.width(), writer.height()), False)
    painter.end()
    return True


def _write_svg(window, path: Path) -> bool:
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return False
    width_mm, height_mm = _page_size_mm(canvas)
    options = getattr(window, "_save_options", {}) or {}
    objects = _visible_objects(canvas)
    background = "" if options.get("remove_white_background", False) else f'<rect width="{width_mm:.3f}" height="{height_mm:.3f}" fill="white"/>'
    grid = ""
    if options.get("save_grid", False):
        lines = []
        x = 0.0
        while x <= width_mm + 0.001:
            lines.append(f'<line x1="{x:.3f}" y1="0" x2="{x:.3f}" y2="{height_mm:.3f}" stroke="#d8e3ef" stroke-width="0.2"/>')
            x += 10.0
        y = 0.0
        while y <= height_mm + 0.001:
            lines.append(f'<line x1="0" y1="{y:.3f}" x2="{width_mm:.3f}" y2="{y:.3f}" stroke="#d8e3ef" stroke-width="0.2"/>')
            y += 10.0
        grid = "\n".join(lines)
    source = _bounds(canvas, objects)
    printable = _printable(QRectF(0, 0, width_mm, height_mm), (width_mm, height_mm), getattr(canvas, "_page_setup_margins", None))
    scale = min(printable.width() / max(1.0, source.width()), printable.height() / max(1.0, source.height())) if objects else 1.0
    offset = QPointF(printable.center().x() - source.center().x() * scale, printable.center().y() - source.center().y() * scale)
    object_markup = []
    for obj in objects:
        rect = QRectF(getattr(obj, "rect", QRectF()))
        x = rect.left() * scale + offset.x()
        y = rect.top() * scale + offset.y()
        width = rect.width() * scale
        height = rect.height() * scale
        name = str(getattr(obj, "name", "Object")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        object_markup.append(
            f'<rect x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" '
            f'fill="#ffffff" stroke="#465d78" stroke-width="0.35"/>'
            f'<text x="{x + width / 2:.3f}" y="{y + height / 2:.3f}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="4" fill="#132238">{name}</text>'
        )
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:.3f}mm" height="{height_mm:.3f}mm" viewBox="0 0 {width_mm:.3f} {height_mm:.3f}">{background}{grid}{"".join(object_markup)}</svg>\n', encoding="utf-8")
    return True


def apply_engineering_export_patch() -> None:
    from . import runtime_ui_patch as rtp

    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_export_patch: engineering workspace import failed")
        return

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_export_patch_applied", False):
        return

    edw._layer_icon = _better_layer_icon
    rtp.PageSetupDialog.PAPER_SIZES["Workspace"] = (400.0, 220.0)

    original_write_document = edw.EngineeringDesignWorkspace._write_document
    original_layer_button = getattr(edw.EngineeringDesignWorkspace, "_layer_button", None)

    def page_rect(self):
        width, height = getattr(self, "_page_setup_size_mm", (400.0, 220.0))
        available = QRectF(8, 4, max(80, self.width() - 16), max(80, self.height() - 10))
        ratio = max(0.01, height / width)
        page_width = min(available.width(), available.height() / ratio)
        page_height = page_width * ratio
        if page_height > available.height():
            page_height = available.height()
            page_width = page_height / ratio
        return QRectF(available.center().x() - page_width / 2, available.center().y() - page_height / 2, page_width, page_height)

    def page_setup(self):
        dialog = rtp.PageSetupDialog(self)
        if dialog.exec() == QDialog.Accepted:
            paper_size = dialog._current_paper_size()
            landscape = bool(getattr(dialog, "_landscape", True))
            margins = (
                dialog._margin_spins.get("top").value() if "top" in dialog._margin_spins else 0.0,
                dialog._margin_spins.get("right").value() if "right" in dialog._margin_spins else 0.0,
                dialog._margin_spins.get("bottom").value() if "bottom" in dialog._margin_spins else 0.0,
                dialog._margin_spins.get("left").value() if "left" in dialog._margin_spins else 0.0,
            )
            canvas = getattr(self, "_canvas", None)
            if isinstance(canvas, edw.EngineeringCanvas):
                canvas.set_page_setup(paper_size, landscape, margins)
                canvas._page_setup_dpi = int(dialog._custom_dpi.value()) if hasattr(dialog, "_custom_dpi") else 600
                canvas._page_setup_position = getattr(dialog, "_position", (1, 1))
            self._set_status("Page Setup applied: " + ("Landscape" if landscape else "Portrait"))
        else:
            self._set_status("Page Setup canceled")

    def write_document(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        suffix = path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".webp"} and _write_image(self, path):
            logging.info("engineering_export_patch: rendered image export path=%s", path)
            return
        if suffix == ".pdf" and _write_pdf(self, path):
            logging.info("engineering_export_patch: rendered pdf export path=%s", path)
            return
        if suffix == ".svg" and _write_svg(self, path):
            logging.info("engineering_export_patch: rendered svg export path=%s", path)
            return
        original_write_document(self, path)

    def layer_button(self, kind: str, active: bool, tooltip: str, callback):
        if callable(original_layer_button):
            button = original_layer_button(self, kind, active, tooltip, callback)
        else:
            from PySide6.QtWidgets import QPushButton
            button = QPushButton()
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
        button.setIcon(_better_layer_icon(kind, active))
        button.setIconSize(QSize(23, 23))
        return button

    edw.EngineeringCanvas._page_rect = page_rect
    edw.EngineeringDesignWorkspace._page_setup = page_setup
    edw.EngineeringDesignWorkspace._write_document = write_document
    edw.EngineeringDesignWorkspace._layer_button = layer_button
    edw.EngineeringDesignWorkspace._engineering_export_patch_applied = True
    logging.info("engineering_export_patch: installed")

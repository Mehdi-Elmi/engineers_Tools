"""Project file, export, clipboard, and render quality fixes for Engineering Design Tools."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QMarginsF, QMimeData, QPointF, QRectF, QSizeF, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPageLayout, QPageSize, QPdfWriter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

PATCH_VERSION = "engineering-file-export-project-fixes-2026-06-30-d"
PROJECT_SUFFIXES = {".etools", ".etool"}
CLIPBOARD_MIME = "application/x-engineer-tools-objects+json"
PAPER_SIZES_MM = {
    "Workspace": (400.0, 220.0),
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "A2": (420.0, 594.0),
    "A1": (594.0, 841.0),
    "A0": (841.0, 1189.0),
    "Letter": (215.9, 279.4),
}
UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "px": 25.4 / 96.0, "in": 25.4, "pt": 25.4 / 72.0}
MM_TO_UNIT = {unit: 1.0 / factor for unit, factor in UNIT_TO_MM.items()}


def _rect_to_list(rect: QRectF) -> list[float]:
    return [float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height())]


def _rect_from_list(values: object) -> QRectF:
    if isinstance(values, (list, tuple)) and len(values) >= 4:
        try:
            return QRectF(float(values[0]), float(values[1]), float(values[2]), float(values[3]))
        except (TypeError, ValueError):
            pass
    return QRectF(80.0, 80.0, 240.0, 160.0)


def _png_bytes_from_image(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def _png_base64_from_image(image: QImage) -> str:
    return bytes(QByteArray(_png_bytes_from_image(image)).toBase64()).decode("ascii")


def _pixmap_to_base64(pixmap: QPixmap) -> str:
    if pixmap.isNull():
        return ""
    return _png_base64_from_image(pixmap.toImage())


def _pixmap_from_base64(value: object) -> QPixmap:
    pixmap = QPixmap()
    if isinstance(value, str) and value:
        pixmap.loadFromData(QByteArray.fromBase64(value.encode("ascii")), "PNG")
    return pixmap


def _white_to_transparent_image(pixmap: QPixmap, threshold: int = 248) -> QImage:
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    for y in range(image.height()):
        for x in range(image.width()):
            color = image.pixelColor(x, y)
            if color.red() >= threshold and color.green() >= threshold and color.blue() >= threshold:
                color.setAlpha(0)
                image.setPixelColor(x, y, color)
    return image


def _object_to_data(obj) -> dict[str, object]:
    return {
        "path": str(getattr(obj, "path", "")),
        "name": str(getattr(obj, "name", "Object")),
        "rect": _rect_to_list(QRectF(getattr(obj, "rect", QRectF()))),
        "rotation": float(getattr(obj, "rotation", 0.0)),
        "visible": bool(getattr(obj, "visible", True)),
        "locked": bool(getattr(obj, "locked", False)),
        "rotation_handle_visible": bool(getattr(obj, "rotation_handle_visible", True)),
        "group_id": getattr(obj, "group_id", None),
        "image_png": _pixmap_to_base64(getattr(obj, "pixmap", QPixmap())),
    }


def _data_to_object(edw, item: dict[str, object]):
    file_path = Path(str(item.get("path", "")))
    pixmap = _pixmap_from_base64(item.get("image_png"))
    if pixmap.isNull() and file_path.exists():
        pixmap = QPixmap(str(file_path))
    return edw.CanvasObject(
        path=file_path,
        pixmap=pixmap,
        rect=_rect_from_list(item.get("rect")),
        rotation=float(item.get("rotation", 0.0) or 0.0),
        name=str(item.get("name", file_path.stem or "Object")),
        visible=bool(item.get("visible", True)),
        locked=bool(item.get("locked", False)),
        rotation_handle_visible=bool(item.get("rotation_handle_visible", True)),
        group_id=item.get("group_id"),
    )


def _default_page_setup() -> dict[str, object]:
    return {
        "paper": "Workspace",
        "orientation": "Landscape",
        "width_mm": 400.0,
        "height_mm": 220.0,
        "dpi": 600,
        "unit": "mm",
        "margins_mm": {"top": 10.0, "right": 10.0, "bottom": 10.0, "left": 10.0},
        "position": "Center",
    }


def _normalize_page_setup(data: object | None = None) -> dict[str, object]:
    state = _default_page_setup()
    if isinstance(data, dict):
        state.update(data)
    paper = str(state.get("paper", "Workspace"))
    if paper not in PAPER_SIZES_MM:
        paper = "Workspace"
    orientation = str(state.get("orientation", "Landscape"))
    if orientation not in {"Portrait", "Landscape"}:
        orientation = "Landscape"
    base_w, base_h = PAPER_SIZES_MM[paper]
    if orientation == "Landscape" and base_h > base_w:
        base_w, base_h = base_h, base_w
    if orientation == "Portrait" and base_w > base_h:
        base_w, base_h = base_h, base_w
    if paper == "Workspace":
        base_w, base_h = 400.0, 220.0
    margins = state.get("margins_mm")
    if not isinstance(margins, dict):
        margins = {}
    unit = str(state.get("unit", "mm"))
    if unit not in UNIT_TO_MM:
        unit = "mm"
    position = str(state.get("position", "Center"))
    if position not in {"Top Left", "Top", "Top Right", "Left", "Center", "Right", "Bottom Left", "Bottom", "Bottom Right"}:
        position = "Center"
    return {
        "paper": paper,
        "orientation": orientation,
        "width_mm": float(base_w),
        "height_mm": float(base_h),
        "dpi": max(72, min(2400, int(float(state.get("dpi", 600) or 600)))),
        "unit": unit,
        "margins_mm": {
            "top": max(0.0, float(margins.get("top", 10.0) or 0.0)),
            "right": max(0.0, float(margins.get("right", 10.0) or 0.0)),
            "bottom": max(0.0, float(margins.get("bottom", 10.0) or 0.0)),
            "left": max(0.0, float(margins.get("left", 10.0) or 0.0)),
        },
        "position": position,
    }


def _apply_page_setup_to_canvas(workspace, state: dict[str, object] | None = None) -> dict[str, object]:
    state = _normalize_page_setup(state or getattr(workspace, "_page_setup", None))
    workspace._page_setup = state
    canvas = getattr(workspace, "_canvas", None)
    if canvas is not None:
        canvas._page_setup_size_mm = (float(state["width_mm"]), float(state["height_mm"]))
        canvas._page_setup_dpi = int(state["dpi"])
        canvas._page_setup_position = str(state["position"])
        canvas._page_setup_margins_mm = dict(state["margins_mm"])
        canvas._page_setup_unit = str(state["unit"])
    return state


def _page_size_mm(canvas) -> tuple[float, float]:
    size = getattr(canvas, "_page_setup_size_mm", None)
    if isinstance(size, (tuple, list)) and len(size) >= 2:
        try:
            return max(1.0, float(size[0])), max(1.0, float(size[1]))
        except (TypeError, ValueError):
            pass
    return 400.0, 220.0


def _page_margins_mm(canvas) -> dict[str, float]:
    margins = getattr(canvas, "_page_setup_margins_mm", None)
    if not isinstance(margins, dict):
        margins = {}
    return {key: max(0.0, float(margins.get(key, 10.0) or 0.0)) for key in ("top", "right", "bottom", "left")}


def _dpi(canvas) -> int:
    try:
        return max(72, min(2400, int(getattr(canvas, "_page_setup_dpi", 600))))
    except (TypeError, ValueError):
        return 600


def _pixel_size(canvas) -> tuple[int, int]:
    width_mm, height_mm = _page_size_mm(canvas)
    dpi = _dpi(canvas)
    width_px = max(1, round(width_mm / 25.4 * dpi))
    height_px = max(1, round(height_mm / 25.4 * dpi))
    max_side = 16000
    if max(width_px, height_px) > max_side:
        scale = max_side / max(width_px, height_px)
        width_px = max(1, round(width_px * scale))
        height_px = max(1, round(height_px * scale))
    return width_px, height_px


def _visible_objects(canvas) -> list:
    return [obj for obj in getattr(canvas, "objects", []) if getattr(obj, "visible", True)]


def _selected_or_visible_objects(canvas) -> list:
    selected = [canvas.objects[index] for index in sorted(getattr(canvas, "selected_indices", set())) if 0 <= index < len(canvas.objects)]
    return selected or _visible_objects(canvas)


def _content_bounds(canvas, objects: list) -> QRectF:
    output = QRectF()
    for obj in objects:
        rect = canvas._object_scene_bounds(obj) if hasattr(canvas, "_object_scene_bounds") else QRectF(getattr(obj, "rect", QRectF()))
        output = QRectF(rect) if output.isNull() else output.united(rect)
    if output.isNull():
        return QRectF(0, 0, max(1, canvas.width()), max(1, canvas.height()))
    return output.adjusted(-4, -4, 4, 4)


def _placed_target(printable: QRectF, source: QRectF, placement: str) -> QRectF:
    scale = min(printable.width() / max(1.0, source.width()), printable.height() / max(1.0, source.height()))
    width = source.width() * scale
    height = source.height() * scale
    if "Left" in placement:
        x = printable.left()
    elif "Right" in placement:
        x = printable.right() - width
    else:
        x = printable.center().x() - width / 2.0
    if "Top" in placement:
        y = printable.top()
    elif "Bottom" in placement:
        y = printable.bottom() - height
    else:
        y = printable.center().y() - height / 2.0
    return QRectF(x, y, width, height)


def _printable_rect(canvas, target: QRectF) -> QRectF:
    width_mm, height_mm = _page_size_mm(canvas)
    margins = _page_margins_mm(canvas)
    left = target.left() + target.width() * margins["left"] / max(width_mm, 1.0)
    right = target.right() - target.width() * margins["right"] / max(width_mm, 1.0)
    top = target.top() + target.height() * margins["top"] / max(height_mm, 1.0)
    bottom = target.bottom() - target.height() * margins["bottom"] / max(height_mm, 1.0)
    if right <= left or bottom <= top:
        return target.adjusted(2, 2, -2, -2)
    return QRectF(QPointF(left, top), QPointF(right, bottom))


def _draw_source_grid(painter: QPainter, source: QRectF) -> None:
    spacing = 24.0
    painter.save()
    painter.setPen(QPen(QColor(70, 96, 130, 46), 1.0))
    x = source.left() - (source.left() % spacing)
    while x <= source.right():
        painter.drawLine(QPointF(x, source.top()), QPointF(x, source.bottom()))
        x += spacing
    y = source.top() - (source.top() % spacing)
    while y <= source.bottom():
        painter.drawLine(QPointF(source.left(), y), QPointF(source.right(), y))
        y += spacing
    painter.restore()


def _draw_export_object(painter: QPainter, obj, remove_white: bool) -> None:
    rect = QRectF(getattr(obj, "rect", QRectF()))
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    painter.translate(rect.center())
    painter.rotate(float(getattr(obj, "rotation", 0.0)))
    local = QRectF(-rect.width() / 2, -rect.height() / 2, rect.width(), rect.height())
    pixmap = getattr(obj, "pixmap", QPixmap())
    if isinstance(pixmap, QPixmap) and not pixmap.isNull():
        if remove_white:
            painter.drawImage(local, _white_to_transparent_image(pixmap), QRectF(pixmap.rect()))
        else:
            painter.setPen(QPen(QColor("#d6e2f0"), 1.2))
            painter.setBrush(QColor("#ffffff"))
            painter.drawRect(local)
            painter.drawPixmap(local, pixmap, QRectF(pixmap.rect()))
    else:
        if not remove_white:
            painter.setPen(QPen(QColor("#d6e2f0"), 1.2))
            painter.setBrush(QColor("#ffffff"))
            painter.drawRect(local)
        painter.setPen(QPen(QColor("#465d78"), 1.2))
        painter.drawText(local.adjusted(10, 10, -10, -10), Qt.AlignmentFlag.AlignCenter, getattr(obj, "path", Path("Object")).name)
    painter.restore()


def _draw_export(canvas, painter: QPainter, target: QRectF, options: dict[str, object], objects: list | None = None) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    remove_white = bool(options.get("remove_white_background", False))
    if not remove_white:
        painter.fillRect(target, QColor("#ffffff"))
    objects = objects if objects is not None else _visible_objects(canvas)
    source = _content_bounds(canvas, objects)
    placement = str(getattr(canvas, "_page_setup_position", None) or "Center")
    printable = _printable_rect(canvas, target)
    placed = _placed_target(printable, source, placement)
    scale = placed.width() / max(1.0, source.width())
    painter.translate(placed.topLeft())
    painter.scale(scale, scale)
    painter.translate(-source.topLeft())
    if options.get("save_grid", False):
        _draw_source_grid(painter, source)
    for obj in objects:
        _draw_export_object(painter, obj, remove_white)
    painter.restore()


def _render_page_image(workspace, transparent_allowed: bool = False) -> QImage | None:
    canvas = getattr(workspace, "_canvas", None)
    if canvas is None:
        return None
    _apply_page_setup_to_canvas(workspace)
    width_px, height_px = _pixel_size(canvas)
    options = getattr(workspace, "_save_options", {}) or {}
    transparent = transparent_allowed and bool(options.get("remove_white_background", False))
    image = QImage(width_px, height_px, QImage.Format.Format_ARGB32)
    image.setDotsPerMeterX(round(_dpi(canvas) / 25.4 * 1000))
    image.setDotsPerMeterY(round(_dpi(canvas) / 25.4 * 1000))
    image.fill(Qt.GlobalColor.transparent if transparent else QColor("#ffffff"))
    painter = QPainter(image)
    _draw_export(canvas, painter, QRectF(0, 0, width_px, height_px), options)
    painter.end()
    return image


def _save_image(workspace, path: Path) -> bool:
    transparent_allowed = path.suffix.lower() in {".png", ".webp"}
    image = _render_page_image(workspace, transparent_allowed=transparent_allowed)
    return bool(image is not None and image.save(str(path)))


def _save_pdf(workspace, path: Path) -> bool:
    canvas = getattr(workspace, "_canvas", None)
    if canvas is None:
        return False
    _apply_page_setup_to_canvas(workspace)
    width_mm, height_mm = _page_size_mm(canvas)
    writer = QPdfWriter(str(path))
    writer.setResolution(_dpi(canvas))
    writer.setPageSize(QPageSize(QSizeF(width_mm, height_mm), QPageSize.Unit.Millimeter))
    writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
    painter = QPainter(writer)
    _draw_export(canvas, painter, QRectF(0, 0, writer.width(), writer.height()), getattr(workspace, "_save_options", {}) or {})
    painter.end()
    return True


def _svg_escape(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _build_svg(workspace, objects: list | None = None) -> str:
    canvas = getattr(workspace, "_canvas", None)
    if canvas is None:
        return '<svg xmlns="http://www.w3.org/2000/svg"/>'
    _apply_page_setup_to_canvas(workspace)
    width_mm, height_mm = _page_size_mm(canvas)
    options = getattr(workspace, "_save_options", {}) or {}
    remove_white = bool(options.get("remove_white_background", False))
    objects = objects if objects is not None else _visible_objects(canvas)
    source = _content_bounds(canvas, objects)
    margins = _page_margins_mm(canvas)
    printable = QRectF(margins["left"], margins["top"], max(1.0, width_mm - margins["left"] - margins["right"]), max(1.0, height_mm - margins["top"] - margins["bottom"]))
    placed = _placed_target(printable, source, str(getattr(canvas, "_page_setup_position", None) or "Center"))
    scale = placed.width() / max(1.0, source.width())
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:.3f}mm" height="{height_mm:.3f}mm" viewBox="0 0 {width_mm:.3f} {height_mm:.3f}">']
    if not remove_white:
        parts.append(f'<rect x="0" y="0" width="{width_mm:.3f}" height="{height_mm:.3f}" fill="white"/>')
    if options.get("save_grid", False):
        x = 0.0
        while x <= width_mm + 0.001:
            parts.append(f'<line x1="{x:.3f}" y1="0" x2="{x:.3f}" y2="{height_mm:.3f}" stroke="#d8e3ef" stroke-width="0.15"/>')
            x += 10.0
        y = 0.0
        while y <= height_mm + 0.001:
            parts.append(f'<line x1="0" y1="{y:.3f}" x2="{width_mm:.3f}" y2="{y:.3f}" stroke="#d8e3ef" stroke-width="0.15"/>')
            y += 10.0
    for obj in objects:
        rect = QRectF(getattr(obj, "rect", QRectF()))
        x = placed.left() + (rect.left() - source.left()) * scale
        y = placed.top() + (rect.top() - source.top()) * scale
        width = rect.width() * scale
        height = rect.height() * scale
        cx = x + width / 2.0
        cy = y + height / 2.0
        angle = float(getattr(obj, "rotation", 0.0))
        parts.append(f'<g transform="rotate({angle:.6f} {cx:.6f} {cy:.6f})">')
        pixmap = getattr(obj, "pixmap", QPixmap())
        if isinstance(pixmap, QPixmap) and not pixmap.isNull():
            image = _white_to_transparent_image(pixmap) if remove_white else pixmap.toImage()
            encoded = _png_base64_from_image(image)
            if not remove_white:
                parts.append(f'<rect x="{x:.6f}" y="{y:.6f}" width="{width:.6f}" height="{height:.6f}" fill="white" stroke="#d6e2f0" stroke-width="0.2"/>')
            parts.append(f'<image x="{x:.6f}" y="{y:.6f}" width="{width:.6f}" height="{height:.6f}" href="data:image/png;base64,{encoded}" preserveAspectRatio="none"/>')
        else:
            if not remove_white:
                parts.append(f'<rect x="{x:.6f}" y="{y:.6f}" width="{width:.6f}" height="{height:.6f}" fill="white" stroke="#465d78" stroke-width="0.35"/>')
            parts.append(f'<text x="{cx:.6f}" y="{cy:.6f}" text-anchor="middle" dominant-baseline="middle" font-size="4" fill="#132238">{_svg_escape(getattr(obj, "name", "Object"))}</text>')
        parts.append("</g>")
    parts.append("</svg>\n")
    return "".join(parts)


def _render_objects_image(canvas, objects: list, scale: float = 2.0) -> QImage:
    source = _content_bounds(canvas, objects)
    width = max(1, round(source.width() * scale))
    height = max(1, round(source.height() * scale))
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    painter.scale(scale, scale)
    painter.translate(-source.topLeft())
    for obj in objects:
        _draw_export_object(painter, obj, True)
    painter.end()
    return image


def _selected_payload(canvas, objects: list) -> dict[str, object]:
    return {"format": "EngineerToolsClipboard", "version": 1, "objects": [_object_to_data(obj) for obj in objects]}


def _copy_canvas_selection(canvas) -> bool:
    objects = _selected_or_visible_objects(canvas)
    if not objects:
        return False
    image = _render_objects_image(canvas, objects, scale=2.0)
    encoded = _png_base64_from_image(image)
    mime = QMimeData()
    mime.setImageData(image)
    mime.setHtml(f'<img src="data:image/png;base64,{encoded}" />')
    mime.setData("image/png", QByteArray(_png_bytes_from_image(image)))
    mime.setData("image/svg+xml", QByteArray(_build_clipboard_svg(canvas, objects).encode("utf-8")))
    mime.setData(CLIPBOARD_MIME, QByteArray(json.dumps(_selected_payload(canvas, objects)).encode("utf-8")))
    QApplication.clipboard().setMimeData(mime)
    canvas._clipboard = [obj.clone() for obj in objects]
    canvas._last_action = "copy"
    return True


def _build_clipboard_svg(canvas, objects: list) -> str:
    source = _content_bounds(canvas, objects)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{source.width():.3f}" height="{source.height():.3f}" viewBox="{source.left():.3f} {source.top():.3f} {source.width():.3f} {source.height():.3f}">']
    for obj in objects:
        rect = QRectF(getattr(obj, "rect", QRectF()))
        pixmap = getattr(obj, "pixmap", QPixmap())
        if isinstance(pixmap, QPixmap) and not pixmap.isNull():
            encoded = _png_base64_from_image(_white_to_transparent_image(pixmap))
            parts.append(f'<image x="{rect.x():.6f}" y="{rect.y():.6f}" width="{rect.width():.6f}" height="{rect.height():.6f}" transform="rotate({float(getattr(obj, "rotation", 0.0)):.6f} {rect.center().x():.6f} {rect.center().y():.6f})" href="data:image/png;base64,{encoded}" preserveAspectRatio="none"/>')
    parts.append("</svg>")
    return "".join(parts)


def _paste_objects(canvas, objects: list, offset: QPointF) -> bool:
    if not objects:
        return False
    canvas._push_undo()
    start = len(canvas.objects)
    for obj in objects:
        clone = obj.clone(offset)
        clone.name = canvas._next_object_name(obj.name)
        clone.group_id = None
        canvas.objects.append(clone)
    canvas.selected_indices = set(range(start, len(canvas.objects)))
    canvas._active_group_edit = None
    canvas._last_action = "paste"
    canvas._emit_object_changes()
    canvas.update()
    return True


def _text_to_pixmap(text: str) -> QPixmap:
    image = QImage(760, 280, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setPen(QPen(QColor("#132238"), 1.0))
    font = QFont("Arial", 18)
    painter.setFont(font)
    painter.drawText(QRectF(18, 18, 724, 244), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, text[:2000])
    painter.end()
    return QPixmap.fromImage(image)


def _paste_from_clipboard(canvas, edw) -> bool:
    mime = QApplication.clipboard().mimeData()
    if mime is None:
        return False
    if mime.hasFormat(CLIPBOARD_MIME):
        try:
            data = json.loads(bytes(mime.data(CLIPBOARD_MIME)).decode("utf-8"))
            objects = [_data_to_object(edw, item) for item in data.get("objects", []) if isinstance(item, dict)]
            return _paste_objects(canvas, objects, QPointF(24, 24))
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
            pass
    if mime.hasUrls():
        loaded = False
        for url in mime.urls():
            if isinstance(url, QUrl) and url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.exists():
                    canvas.load_file(path)
                    loaded = True
        if loaded:
            return True
    if mime.hasImage():
        data = mime.imageData()
        image = data if isinstance(data, QImage) else QImage(data)
        pixmap = QPixmap.fromImage(image)
        if not pixmap.isNull():
            canvas._push_undo()
            width = min(float(pixmap.width()), max(180.0, canvas.width() * 0.6))
            scale = width / max(1.0, float(pixmap.width()))
            height = max(1.0, pixmap.height() * scale)
            rect = QRectF((canvas.width() - width) / 2.0, (canvas.height() - height) / 2.0, width, height)
            canvas.objects.append(edw.CanvasObject(path=Path("Clipboard Image"), pixmap=pixmap, rect=rect, name="Clipboard Image"))
            canvas._select_only(len(canvas.objects) - 1)
            canvas._emit_object_changes()
            canvas.update()
            return True
    if mime.hasText():
        text = mime.text().strip()
        path = Path(text.strip('"'))
        if path.exists():
            canvas.load_file(path)
            return True
        if text:
            pixmap = _text_to_pixmap(text)
            canvas._push_undo()
            rect = QRectF(70.0, 70.0, 380.0, 140.0)
            canvas.objects.append(edw.CanvasObject(path=Path("Clipboard Text"), pixmap=pixmap, rect=rect, name="Clipboard Text"))
            canvas._select_only(len(canvas.objects) - 1)
            canvas._emit_object_changes()
            canvas.update()
            return True
    return False


def _office_text_from_zip(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            text_parts: list[str] = []
            for name in names:
                if name.endswith(".xml") and any(prefix in name for prefix in ("word/", "ppt/slides/", "xl/worksheets/", "xl/sharedStrings")):
                    raw = archive.read(name)
                    try:
                        root = ET.fromstring(raw)
                    except ET.ParseError:
                        continue
                    for node in root.iter():
                        if node.text and node.text.strip():
                            text_parts.append(node.text.strip())
            return "\n".join(text_parts[:160])
    except (OSError, zipfile.BadZipFile, KeyError):
        return ""
    return ""


def _import_office_file(canvas, edw, path: Path) -> bool:
    text = _office_text_from_zip(path) or f"Imported Office document:\n{path.name}"
    pixmap = _text_to_pixmap(text)
    canvas._push_undo()
    rect = QRectF(70.0, 70.0, min(520.0, max(260.0, canvas.width() * 0.5)), 220.0)
    canvas.objects.append(edw.CanvasObject(path=path, pixmap=pixmap, rect=rect, name=path.stem or "Office Import"))
    canvas._select_only(len(canvas.objects) - 1)
    canvas._emit_object_changes()
    canvas.update()
    return True


def _write_docx_with_image(workspace, path: Path) -> bool:
    image = _render_page_image(workspace, transparent_allowed=True)
    if image is None:
        return False
    png_data = _png_bytes_from_image(image)
    canvas = getattr(workspace, "_canvas", None)
    width_mm, height_mm = _page_size_mm(canvas)
    margins = _page_margins_mm(canvas)
    printable_w_mm = max(10.0, width_mm - margins["left"] - margins["right"])
    printable_h_mm = max(10.0, height_mm - margins["top"] - margins["bottom"])
    extent_cx = round(printable_w_mm * 36000)
    extent_cy = round(printable_h_mm * 36000)
    page_w_twip = round(width_mm * 56.6929134)
    page_h_twip = round(height_mm * 56.6929134)
    margin_twips = {key: round(value * 56.6929134) for key, value in margins.items()}
    document_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
  <w:body>
    <w:p><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{extent_cx}" cy="{extent_cy}"/><wp:docPr id="1" name="Engineer Tools Export"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="engineer-tools.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rIdImage1"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{extent_cx}" cy="{extent_cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>
    <w:sectPr><w:pgSz w:w="{page_w_twip}" w:h="{page_h_twip}"/><w:pgMar w:top="{margin_twips['top']}" w:right="{margin_twips['right']}" w:bottom="{margin_twips['bottom']}" w:left="{margin_twips['left']}" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr>
  </w:body>
</w:document>'''
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        archive.writestr("word/_rels/document.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdImage1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/engineer-tools.png"/></Relationships>')
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/media/engineer-tools.png", png_data)
    return True


def _show_page_setup_dialog(workspace) -> None:
    state = _apply_page_setup_to_canvas(workspace)
    unit = str(state["unit"])
    factor = MM_TO_UNIT[unit]
    dialog = QDialog(workspace)
    dialog.setObjectName("PageSetupDialog")
    dialog.setWindowTitle("Page Setup")
    dialog.setModal(True)
    dialog.setMinimumWidth(360)
    root = QVBoxLayout(dialog)
    form = QFormLayout()
    paper = QComboBox()
    paper.addItems(tuple(PAPER_SIZES_MM.keys()))
    paper.setCurrentText(str(state["paper"]))
    orientation = QComboBox()
    orientation.addItems(("Portrait", "Landscape"))
    orientation.setCurrentText(str(state["orientation"]))
    unit_box = QComboBox()
    unit_box.addItems(tuple(UNIT_TO_MM.keys()))
    unit_box.setCurrentText(unit)
    dpi = QDoubleSpinBox()
    dpi.setRange(72, 2400)
    dpi.setDecimals(0)
    dpi.setSingleStep(50)
    dpi.setValue(float(state["dpi"]))
    position = QComboBox()
    position.addItems(("Top Left", "Top", "Top Right", "Left", "Center", "Right", "Bottom Left", "Bottom", "Bottom Right"))
    position.setCurrentText(str(state["position"]))

    def spin(value_mm: float) -> QDoubleSpinBox:
        box = QDoubleSpinBox()
        box.setRange(0, 1000000)
        box.setDecimals(3)
        box.setSingleStep(1)
        box.setValue(value_mm * factor)
        box.setSuffix(f" {unit_box.currentText()}")
        return box

    width = spin(float(state["width_mm"]))
    height = spin(float(state["height_mm"]))
    margins = state["margins_mm"]
    top = spin(float(margins["top"]))
    right = spin(float(margins["right"]))
    bottom = spin(float(margins["bottom"]))
    left = spin(float(margins["left"]))

    def refresh_size() -> None:
        paper_name = paper.currentText()
        w_mm, h_mm = PAPER_SIZES_MM.get(paper_name, PAPER_SIZES_MM["Workspace"])
        if orientation.currentText() == "Landscape" and h_mm > w_mm:
            w_mm, h_mm = h_mm, w_mm
        if orientation.currentText() == "Portrait" and w_mm > h_mm:
            w_mm, h_mm = h_mm, w_mm
        factor_now = MM_TO_UNIT[unit_box.currentText()]
        width.setValue(w_mm * factor_now)
        height.setValue(h_mm * factor_now)

    def refresh_unit() -> None:
        old_unit = getattr(dialog, "_last_unit", unit)
        old_factor = UNIT_TO_MM.get(old_unit, 1.0)
        new_unit = unit_box.currentText()
        for box in (width, height, top, right, bottom, left):
            value_mm = box.value() * old_factor
            box.setSuffix(f" {new_unit}")
            box.setValue(value_mm * MM_TO_UNIT[new_unit])
        dialog._last_unit = new_unit

    paper.currentTextChanged.connect(lambda _text: refresh_size())
    orientation.currentTextChanged.connect(lambda _text: refresh_size())
    unit_box.currentTextChanged.connect(lambda _text: refresh_unit())
    form.addRow("Paper", paper)
    form.addRow("Orientation", orientation)
    form.addRow("Unit", unit_box)
    form.addRow("Width", width)
    form.addRow("Height", height)
    form.addRow("Quality DPI", dpi)
    form.addRow("Top", top)
    form.addRow("Right", right)
    form.addRow("Bottom", bottom)
    form.addRow("Left", left)
    form.addRow("Object Position", position)
    root.addLayout(form)
    buttons = QHBoxLayout()
    buttons.addStretch(1)
    apply_button = QPushButton("Apply")
    cancel_button = QPushButton("Cancel")
    buttons.addWidget(apply_button)
    buttons.addWidget(cancel_button)
    root.addLayout(buttons)
    cancel_button.clicked.connect(dialog.reject)

    def apply() -> None:
        selected_unit = unit_box.currentText()
        factor_to_mm = UNIT_TO_MM[selected_unit]
        new_state = _normalize_page_setup({
            "paper": paper.currentText(),
            "orientation": orientation.currentText(),
            "dpi": int(dpi.value()),
            "unit": selected_unit,
            "margins_mm": {
                "top": top.value() * factor_to_mm,
                "right": right.value() * factor_to_mm,
                "bottom": bottom.value() * factor_to_mm,
                "left": left.value() * factor_to_mm,
            },
            "position": position.currentText(),
        })
        workspace._page_setup = new_state
        _apply_page_setup_to_canvas(workspace, new_state)
        workspace._set_status(f"Page Setup {new_state['paper']} {new_state['orientation']} | {new_state['dpi']} DPI")
        dialog.accept()

    apply_button.clicked.connect(apply)
    dialog.setStyleSheet("QDialog#PageSetupDialog {background:#eaf4ff;} QLabel {font-style:normal; font-weight:700; color:#132238;} QComboBox, QDoubleSpinBox {background:#fff9de; border:1px solid #b38621; border-radius:6px; padding:3px 6px; font-style:normal;} QPushButton {background:#fff9de; border:1px solid #b38621; border-radius:8px; padding:5px 12px; font-style:normal; font-weight:800;}")
    dialog.exec()


def apply_file_export_project_fixes() -> None:
    from . import workspace as edw
    from . import cursor_unification_fixes as cursors
    from src.engineers_tools.app.project_file_dialog import ProjectFileDialog
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_file_export_project_patch", "") == PATCH_VERSION:
        return

    original_write_document = edw.EngineeringDesignWorkspace._write_document
    original_mouse_press = edw.EngineeringCanvas.mousePressEvent
    original_mouse_move = edw.EngineeringCanvas.mouseMoveEvent
    original_mouse_release = edw.EngineeringCanvas.mouseReleaseEvent
    original_workspace_init = edw.EngineeringDesignWorkspace.__init__
    original_start_set_unit = sb.StartBar._set_unit

    def workspace_init(self, module) -> None:
        self._page_setup = _default_page_setup()
        original_workspace_init(self, module)
        _apply_page_setup_to_canvas(self, self._page_setup)

    def paint_object(self, painter: QPainter, obj) -> None:
        _draw_export_object(painter, obj, False)

    def save_project(self, path: Path) -> None:
        canvas = getattr(self, "_canvas", None)
        _apply_page_setup_to_canvas(self)
        payload = {
            "format": "EngineerToolsProject",
            "version": 3,
            "save_options": getattr(self, "_save_options", {}) or {},
            "page_setup": getattr(self, "_page_setup", _default_page_setup()),
            "objects": [_object_to_data(obj) for obj in getattr(canvas, "objects", [])],
            "selected_indices": sorted(getattr(canvas, "selected_indices", set())),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def restore_project(self, path: Path) -> bool:
        canvas = getattr(self, "_canvas", None)
        if canvas is None:
            return False
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("format") not in {"EngineerToolsProject", "EngineeringDesignTools"}:
            return False
        canvas.objects = []
        for item in data.get("objects", []):
            if isinstance(item, dict):
                canvas.objects.append(_data_to_object(edw, item))
        selected = data.get("selected_indices", [])
        canvas.selected_indices = {int(index) for index in selected if isinstance(index, int) and 0 <= index < len(canvas.objects)}
        canvas._undo_stack = []
        canvas._redo_stack = []
        canvas._emit_object_changes()
        canvas.update()
        self._current_file_path = path
        self._last_file_dir = path.parent
        self._save_options = dict(data.get("save_options", {}) or {})
        _apply_page_setup_to_canvas(self, data.get("page_setup"))
        self._set_status(f"Opened {path.name}")
        return True

    def load_regular_file(self, path: Path, verb: str) -> None:
        if self._canvas is not None:
            if path.suffix.lower() in {".docx", ".pptx", ".xlsx", ".rtf", ".csv"}:
                _import_office_file(self._canvas, edw, path)
            else:
                self._canvas.load_file(path)
            self._last_file_dir = path.parent
            self._set_status(f"{verb} {path.name}")

    def open_file(self):
        result = ProjectFileDialog.get_open_file(self, self._last_file_dir)
        if result is None:
            self._set_status("Open canceled")
            return
        if result.path.suffix.lower() in PROJECT_SUFFIXES and restore_project(self, result.path):
            return
        load_regular_file(self, result.path, "Opened")

    def import_file(self):
        result = ProjectFileDialog.get_import_file(self, self._last_file_dir)
        if result is None:
            self._set_status("Import canceled")
            return
        if result.path.suffix.lower() in PROJECT_SUFFIXES and restore_project(self, result.path):
            return
        load_regular_file(self, result.path, "Imported")

    def write_document(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        _apply_page_setup_to_canvas(self)
        suffix = path.suffix.lower()
        if suffix in PROJECT_SUFFIXES:
            save_project(self, path)
        elif suffix in {".png", ".jpg", ".jpeg", ".bmp", ".webp"} and _save_image(self, path):
            return
        elif suffix == ".pdf" and _save_pdf(self, path):
            return
        elif suffix == ".svg":
            path.write_text(_build_svg(self), encoding="utf-8")
        elif suffix == ".docx" and _write_docx_with_image(self, path):
            return
        else:
            original_write_document(self, path)

    def set_cursor_for_action(canvas, action: str | None, dragging: bool = False) -> None:
        mapping = {
            "move": "move",
            "rotate": "hand_closed" if dragging else "hand_open",
            "resize_n": "resize_v", "resize_s": "resize_v",
            "resize_e": "resize_h", "resize_w": "resize_h",
            "resize_nw": "resize_fdiag", "resize_se": "resize_fdiag",
            "resize_ne": "resize_bdiag", "resize_sw": "resize_bdiag",
        }
        name = mapping.get(action or "")
        if name:
            canvas.setCursor(cursors.project_cursor(name))

    def mouse_press(self, event) -> None:
        original_mouse_press(self, event)
        set_cursor_for_action(self, getattr(self, "_drag_action", None), dragging=True)

    def mouse_move(self, event) -> None:
        original_mouse_move(self, event)
        drag_action = getattr(self, "_drag_action", None)
        if drag_action is not None:
            set_cursor_for_action(self, drag_action, dragging=True)
            return
        point = self._to_canvas_point(event.position()) if hasattr(self, "_to_canvas_point") else event.position()
        _index, hover = self._hit_test_object(point) if hasattr(self, "_hit_test_object") else (None, None)
        set_cursor_for_action(self, hover, dragging=False)

    def mouse_release(self, event) -> None:
        original_mouse_release(self, event)
        point = self._to_canvas_point(event.position()) if hasattr(self, "_to_canvas_point") else event.position()
        _index, hover = self._hit_test_object(point) if hasattr(self, "_hit_test_object") else (None, None)
        set_cursor_for_action(self, hover, dragging=False)

    def copy_selection(self) -> bool:
        return _copy_canvas_selection(self)

    def cut_selection(self) -> bool:
        if not _copy_canvas_selection(self):
            return False
        self._push_undo()
        self._delete_selected_objects()
        self._last_action = "cut"
        return True

    def paste_selection(self) -> bool:
        if _paste_from_clipboard(self, edw):
            return True
        if not self._clipboard:
            return False
        return _paste_objects(self, self._clipboard, QPointF(24, 24))

    def page_setup(self) -> None:
        _show_page_setup_dialog(self)

    def start_set_unit(self, unit: str) -> None:
        original_start_set_unit(self, unit)
        host = self.window()
        if hasattr(host, "_page_setup"):
            state = _normalize_page_setup(getattr(host, "_page_setup", None))
            state["unit"] = unit
            host._page_setup = state
            _apply_page_setup_to_canvas(host, state)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringCanvas._paint_object = paint_object
    edw.EngineeringCanvas.mousePressEvent = mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    edw.EngineeringCanvas.copy_selection = copy_selection
    edw.EngineeringCanvas.cut_selection = cut_selection
    edw.EngineeringCanvas.paste_selection = paste_selection
    edw.EngineeringDesignWorkspace._open_file = open_file
    edw.EngineeringDesignWorkspace._import_file = import_file
    edw.EngineeringDesignWorkspace._write_document = write_document
    edw.EngineeringDesignWorkspace._page_setup = page_setup
    sb.StartBar._set_unit = start_set_unit
    edw.EngineeringDesignWorkspace._engineering_file_export_project_patch = PATCH_VERSION

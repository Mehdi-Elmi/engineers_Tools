"""Project file, export, and render quality fixes for Engineering Design Tools."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QMarginsF, QPointF, QRectF, QSizeF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPageLayout, QPageSize, QPdfWriter, QPen, QPixmap

PATCH_VERSION = "engineering-file-export-project-fixes-2026-06-30-c"
PROJECT_SUFFIXES = {".etools", ".etool"}


def _rect_to_list(rect: QRectF) -> list[float]:
    return [float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height())]


def _rect_from_list(values: object) -> QRectF:
    if isinstance(values, (list, tuple)) and len(values) >= 4:
        try:
            return QRectF(float(values[0]), float(values[1]), float(values[2]), float(values[3]))
        except (TypeError, ValueError):
            pass
    return QRectF(80.0, 80.0, 240.0, 160.0)


def _png_base64_from_image(image: QImage) -> str:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(data.toBase64()).decode("ascii")


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


def _page_size_mm(canvas) -> tuple[float, float]:
    size = getattr(canvas, "_page_setup_size_mm", None)
    if isinstance(size, (tuple, list)) and len(size) >= 2:
        try:
            return max(1.0, float(size[0])), max(1.0, float(size[1]))
        except (TypeError, ValueError):
            pass
    return 400.0, 220.0


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
    max_side = 12000
    if max(width_px, height_px) > max_side:
        scale = max_side / max(width_px, height_px)
        width_px = max(1, round(width_px * scale))
        height_px = max(1, round(height_px * scale))
    return width_px, height_px


def _visible_objects(canvas) -> list:
    return [obj for obj in getattr(canvas, "objects", []) if getattr(obj, "visible", True)]


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


def _draw_export(canvas, painter: QPainter, target: QRectF, options: dict[str, object]) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    remove_white = bool(options.get("remove_white_background", False))
    if not remove_white:
        painter.fillRect(target, QColor("#ffffff"))
    objects = _visible_objects(canvas)
    source = _content_bounds(canvas, objects)
    placement = str(getattr(canvas, "_page_setup_position", None) or "Center")
    printable = target.adjusted(8, 8, -8, -8)
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


def _save_image(workspace, path: Path) -> bool:
    canvas = getattr(workspace, "_canvas", None)
    if canvas is None:
        return False
    width_px, height_px = _pixel_size(canvas)
    options = getattr(workspace, "_save_options", {}) or {}
    transparent = bool(options.get("remove_white_background", False)) and path.suffix.lower() in {".png", ".webp"}
    image = QImage(width_px, height_px, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent if transparent else QColor("#ffffff"))
    painter = QPainter(image)
    _draw_export(canvas, painter, QRectF(0, 0, width_px, height_px), options)
    painter.end()
    return bool(image.save(str(path)))


def _save_pdf(workspace, path: Path) -> bool:
    canvas = getattr(workspace, "_canvas", None)
    if canvas is None:
        return False
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


def _build_svg(workspace) -> str:
    canvas = getattr(workspace, "_canvas", None)
    if canvas is None:
        return '<svg xmlns="http://www.w3.org/2000/svg"/>'
    width_mm, height_mm = _page_size_mm(canvas)
    options = getattr(workspace, "_save_options", {}) or {}
    remove_white = bool(options.get("remove_white_background", False))
    objects = _visible_objects(canvas)
    source = _content_bounds(canvas, objects)
    printable = QRectF(0, 0, width_mm, height_mm).adjusted(2, 2, -2, -2)
    placed = _placed_target(printable, source, str(getattr(canvas, "_page_setup_position", None) or "Center"))
    scale = placed.width() / max(1.0, source.width())
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:.3f}mm" height="{height_mm:.3f}mm" viewBox="0 0 {width_mm:.3f} {height_mm:.3f}">']
    if not remove_white:
        parts.append(f'<rect x="0" y="0" width="{width_mm:.3f}" height="{height_mm:.3f}" fill="white"/>')
    if options.get("save_grid", False):
        grid = []
        x = 0.0
        while x <= width_mm + 0.001:
            grid.append(f'<line x1="{x:.3f}" y1="0" x2="{x:.3f}" y2="{height_mm:.3f}" stroke="#d8e3ef" stroke-width="0.15"/>')
            x += 10.0
        y = 0.0
        while y <= height_mm + 0.001:
            grid.append(f'<line x1="0" y1="{y:.3f}" x2="{width_mm:.3f}" y2="{y:.3f}" stroke="#d8e3ef" stroke-width="0.15"/>')
            y += 10.0
        parts.extend(grid)
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


def apply_file_export_project_fixes() -> None:
    from . import workspace as edw
    from . import cursor_unification_fixes as cursors
    from src.engineers_tools.app.project_file_dialog import ProjectFileDialog

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_file_export_project_patch", "") == PATCH_VERSION:
        return

    original_write_document = edw.EngineeringDesignWorkspace._write_document
    original_mouse_press = edw.EngineeringCanvas.mousePressEvent
    original_mouse_move = edw.EngineeringCanvas.mouseMoveEvent
    original_mouse_release = edw.EngineeringCanvas.mouseReleaseEvent

    def paint_object(self, painter: QPainter, obj) -> None:
        _draw_export_object(painter, obj, False)

    def save_project(self, path: Path) -> None:
        canvas = getattr(self, "_canvas", None)
        payload = {
            "format": "EngineerToolsProject",
            "version": 2,
            "save_options": getattr(self, "_save_options", {}) or {},
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
            if not isinstance(item, dict):
                continue
            file_path = Path(str(item.get("path", "")))
            pixmap = _pixmap_from_base64(item.get("image_png"))
            if pixmap.isNull() and file_path.exists():
                pixmap = QPixmap(str(file_path))
            canvas.objects.append(edw.CanvasObject(
                path=file_path,
                pixmap=pixmap,
                rect=_rect_from_list(item.get("rect")),
                rotation=float(item.get("rotation", 0.0) or 0.0),
                name=str(item.get("name", file_path.stem or "Object")),
                visible=bool(item.get("visible", True)),
                locked=bool(item.get("locked", False)),
                rotation_handle_visible=bool(item.get("rotation_handle_visible", True)),
                group_id=item.get("group_id"),
            ))
        selected = data.get("selected_indices", [])
        canvas.selected_indices = {int(index) for index in selected if isinstance(index, int) and 0 <= index < len(canvas.objects)}
        canvas._undo_stack = []
        canvas._redo_stack = []
        canvas._emit_object_changes()
        canvas.update()
        self._current_file_path = path
        self._last_file_dir = path.parent
        self._save_options = dict(data.get("save_options", {}) or {})
        self._set_status(f"Opened {path.name}")
        return True

    def load_regular_file(self, path: Path, verb: str) -> None:
        if self._canvas is not None:
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
        suffix = path.suffix.lower()
        if suffix in PROJECT_SUFFIXES:
            save_project(self, path)
        elif suffix in {".png", ".jpg", ".jpeg", ".bmp", ".webp"} and _save_image(self, path):
            return
        elif suffix == ".pdf" and _save_pdf(self, path):
            return
        elif suffix == ".svg":
            path.write_text(_build_svg(self), encoding="utf-8")
        else:
            original_write_document(self, path)

    def set_rotate_cursor(canvas) -> None:
        canvas.setCursor(cursors.project_cursor("hand_closed"))

    def mouse_press(self, event) -> None:
        original_mouse_press(self, event)
        if getattr(self, "_drag_action", None) == "rotate":
            set_rotate_cursor(self)

    def mouse_move(self, event) -> None:
        original_mouse_move(self, event)
        if getattr(self, "_drag_action", None) == "rotate":
            set_rotate_cursor(self)
            return
        point = self._to_canvas_point(event.position()) if hasattr(self, "_to_canvas_point") else event.position()
        _index, hover = self._hit_test_object(point) if hasattr(self, "_hit_test_object") else (None, None)
        if hover == "rotate":
            self.setCursor(cursors.project_cursor("hand_open"))

    def mouse_release(self, event) -> None:
        original_mouse_release(self, event)
        point = self._to_canvas_point(event.position()) if hasattr(self, "_to_canvas_point") else event.position()
        _index, hover = self._hit_test_object(point) if hasattr(self, "_hit_test_object") else (None, None)
        if hover == "rotate":
            self.setCursor(cursors.project_cursor("hand_open"))

    edw.EngineeringCanvas._paint_object = paint_object
    edw.EngineeringCanvas.mousePressEvent = mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    edw.EngineeringDesignWorkspace._open_file = open_file
    edw.EngineeringDesignWorkspace._import_file = import_file
    edw.EngineeringDesignWorkspace._write_document = write_document
    edw.EngineeringDesignWorkspace._engineering_file_export_project_patch = PATCH_VERSION

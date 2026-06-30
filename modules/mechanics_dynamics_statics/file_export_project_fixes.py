"""Project file, export, and render quality fixes for Engineering Design Tools."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPoint, QPointF, QRect, QRectF, QSize, QSizeF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPageLayout, QPageSize, QPdfWriter, QPixmap

PATCH_VERSION = "engineering-file-export-project-fixes-2026-06-30-a"
PROJECT_SUFFIXES = {".etools", ".etool"}


def _rect_to_list(rect: QRectF) -> list[float]:
    return [float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height())]


def _rect_from_list(values: object) -> QRectF:
    if isinstance(values, list | tuple) and len(values) >= 4:
        try:
            return QRectF(float(values[0]), float(values[1]), float(values[2]), float(values[3]))
        except (TypeError, ValueError):
            pass
    return QRectF(80.0, 80.0, 240.0, 160.0)


def _pixmap_to_base64(pixmap: QPixmap) -> str:
    if pixmap.isNull():
        return ""
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    buffer.close()
    return bytes(data.toBase64()).decode("ascii")


def _pixmap_from_base64(value: object) -> QPixmap:
    pixmap = QPixmap()
    if isinstance(value, str) and value:
        pixmap.loadFromData(QByteArray.fromBase64(value.encode("ascii")), "PNG")
    return pixmap


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
    if isinstance(size, tuple | list) and len(size) >= 2:
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


def _draw_export(canvas, painter: QPainter, target: QRectF, options: dict[str, object]) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    if not options.get("remove_white_background", False):
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
        canvas.render(painter, QPoint(0, 0), QRect(0, 0, canvas.width(), canvas.height()))
    else:
        for obj in objects:
            canvas._paint_object(painter, obj)
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


def apply_file_export_project_fixes() -> None:
    from . import workspace as edw
    from src.engineers_tools.app.project_file_dialog import ProjectFileDialog

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_file_export_project_patch", "") == PATCH_VERSION:
        return

    original_open_file = edw.EngineeringDesignWorkspace._open_file
    original_import_file = edw.EngineeringDesignWorkspace._import_file
    original_write_document = edw.EngineeringDesignWorkspace._write_document
    original_paint_object = edw.EngineeringCanvas._paint_object

    def paint_object(self, painter: QPainter, obj) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        rect = obj.rect
        painter.translate(rect.center())
        painter.rotate(float(getattr(obj, "rotation", 0.0)))
        local = QRectF(-rect.width() / 2, -rect.height() / 2, rect.width(), rect.height())
        painter.setPen(QPen(QColor("#d6e2f0"), 1.2))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(local)
        pixmap = getattr(obj, "pixmap", QPixmap())
        if isinstance(pixmap, QPixmap) and not pixmap.isNull():
            painter.drawPixmap(local, pixmap, QRectF(pixmap.rect()))
        else:
            painter.setPen(QPen(QColor("#465d78"), 1.2))
            painter.drawText(local.adjusted(10, 10, -10, -10), Qt.AlignmentFlag.AlignCenter, obj.path.name)
        painter.restore()

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

    def open_file(self):
        result = ProjectFileDialog.get_open_file(self, self._last_file_dir)
        if result is None:
            self._set_status("Open canceled")
            return
        if result.path.suffix.lower() in PROJECT_SUFFIXES and restore_project(self, result.path):
            return
        original_open_file(self)

    def import_file(self):
        result = ProjectFileDialog.get_import_file(self, self._last_file_dir)
        if result is None:
            self._set_status("Import canceled")
            return
        if result.path.suffix.lower() in PROJECT_SUFFIXES and restore_project(self, result.path):
            return
        if self._canvas is not None:
            self._canvas.load_file(result.path)
            self._last_file_dir = result.path.parent
            self._set_status(f"Imported {result.path.name}")

    def write_document(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        suffix = path.suffix.lower()
        if suffix in PROJECT_SUFFIXES:
            save_project(self, path)
        elif suffix in {".png", ".jpg", ".jpeg", ".bmp", ".webp"} and _save_image(self, path):
            return
        elif suffix == ".pdf" and _save_pdf(self, path):
            return
        else:
            original_write_document(self, path)

    edw.EngineeringCanvas._paint_object = paint_object
    edw.EngineeringDesignWorkspace._open_file = open_file
    edw.EngineeringDesignWorkspace._import_file = import_file
    edw.EngineeringDesignWorkspace._write_document = write_document
    edw.EngineeringDesignWorkspace._engineering_file_export_project_patch = PATCH_VERSION

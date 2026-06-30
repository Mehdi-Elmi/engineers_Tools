"""Strict fixed-page viewport behavior for Engineering Design Tools."""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import QCursor, QPixmap


VERSION = "fixed-viewport-v5"
WORKSPACE_SIZE_MM = (400.0, 220.0)
EDGE_MARGIN = 0
NATIVE_PROJECT_SUFFIXES = {".etools", ".etool"}


def _usable_area(canvas) -> QRectF:
    ruler_left = 0
    ruler_top = 0
    try:
        start_bar = getattr(canvas.window(), "_start_bar_widget", None)
        if start_bar is not None and getattr(start_bar, "_ruler_enabled", False):
            from src.engineers_tools.ui import start_bar as sb

            ruler_left = sb.RULER_THICKNESS
            ruler_top = sb.RULER_THICKNESS
    except Exception:
        ruler_left = 0
        ruler_top = 0
    return QRectF(
        ruler_left + 6,
        ruler_top + 3,
        max(80.0, float(canvas.width() - ruler_left - 12)),
        max(80.0, float(canvas.height() - ruler_top - 8)),
    )


def _fit_page_in(area: QRectF) -> QRectF:
    ratio = WORKSPACE_SIZE_MM[1] / WORKSPACE_SIZE_MM[0]
    page_width = min(area.width(), area.height() / ratio)
    page_height = page_width * ratio
    if page_height > area.height():
        page_height = area.height()
        page_width = page_height / ratio
    return QRectF(
        area.center().x() - page_width / 2.0,
        area.center().y() - page_height / 2.0,
        page_width,
        page_height,
    )


def _baseline_size(canvas, candidate: QRectF) -> tuple[float, float]:
    """Lock the approved page display size; never grow past it during resize."""
    window = canvas.window()
    is_maximized = bool(getattr(window, "_is_manually_maximized", False) or window.isMaximized())
    baseline = getattr(canvas, "_fixed_viewport_page_px", None)
    locked = bool(getattr(canvas, "_fixed_viewport_page_locked", False))

    if baseline is None:
        baseline = (candidate.width(), candidate.height())
        canvas._fixed_viewport_page_px = baseline
        canvas._fixed_viewport_page_locked = is_maximized
        return baseline

    if is_maximized and not locked:
        baseline = (candidate.width(), candidate.height())
        canvas._fixed_viewport_page_px = baseline
        canvas._fixed_viewport_page_locked = True
        return baseline

    return float(baseline[0]), float(baseline[1])


def _page_rect(canvas) -> QRectF:
    """Return a fixed approved page rect; window resize changes viewport fit only."""
    area = _usable_area(canvas)
    candidate = _fit_page_in(area)
    baseline_w, baseline_h = _baseline_size(canvas, candidate)

    scale = min(1.0, candidate.width() / max(1.0, baseline_w), candidate.height() / max(1.0, baseline_h))
    width = max(1.0, baseline_w * scale)
    height = max(1.0, baseline_h * scale)
    return QRectF(area.center().x() - width / 2.0, area.center().y() - height / 2.0, width, height)


def _unit_to_canvas_px(start_bar, value: float, unit: str, orientation: str = "top") -> float:
    try:
        from src.engineers_tools.ui import start_bar as sb
    except Exception:
        return max(1.0, float(value))
    canvas = start_bar._canvas() if hasattr(start_bar, "_canvas") else None
    if canvas is None:
        return max(1.0, float(value) * sb.UNIT_TO_MM[unit] * sb.MM_TO_SCREEN_PX)
    page = _page_rect(canvas)
    mm_value = float(value) * sb.UNIT_TO_MM[unit]
    if orientation in {"left", "vertical", "y"}:
        return max(1.0, mm_value * page.height() / WORKSPACE_SIZE_MM[1])
    return max(1.0, mm_value * page.width() / WORKSPACE_SIZE_MM[0])


def _asset_cursor(file_name: str, fallback: QCursor, hot_x: int = 12, hot_y: int = 12, size: int = 24) -> QCursor:
    try:
        from . import engineering_ui_small_fixes_patch as small

        return small._asset_cursor(file_name, fallback, hot_x, hot_y, size)
    except Exception:
        return fallback


def _resize_cursor(edges: set[str]) -> QCursor:
    if {"left", "top"} <= edges or {"right", "bottom"} <= edges:
        return _asset_cursor("corner_resize_a.svg", QCursor(Qt.CursorShape.SizeFDiagCursor))
    if {"right", "top"} <= edges or {"left", "bottom"} <= edges:
        return _asset_cursor("corner_resize_b.svg", QCursor(Qt.CursorShape.SizeBDiagCursor))
    if "left" in edges or "right" in edges:
        return _asset_cursor("resize_horizontal.svg", QCursor(Qt.CursorShape.SizeHorCursor))
    if "top" in edges or "bottom" in edges:
        return _asset_cursor("resize_vertical.svg", QCursor(Qt.CursorShape.SizeVerCursor))
    return QCursor(Qt.CursorShape.ArrowCursor)


def _disable_shell_edge_resize(patch_module) -> None:
    """Keep the main shell move-only; canvas object resize remains separate."""
    patch_module.EDGE_MARGIN = 0
    patch_module._window_edges = lambda _window, _pos: set()

    def no_window_resize(window, _global_pos) -> None:
        window._fixed_resize_edges = set()
        window._fixed_resize_start_global = None
        window._fixed_resize_start_geometry = None
        window._window_resize_edges = set()
        window._window_resize_start_global = None
        window._window_resize_start_geometry = None
        try:
            window.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        except Exception:
            pass

    patch_module._apply_window_resize = no_window_resize


def _rect_to_list(rect: QRectF) -> list[float]:
    return [float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height())]


def _rect_from_list(values) -> QRectF:
    values = list(values or [0, 0, 80, 80])
    while len(values) < 4:
        values.append(0)
    return QRectF(float(values[0]), float(values[1]), max(1.0, float(values[2])), max(1.0, float(values[3])))


def _pixmap_to_base64(pixmap: QPixmap) -> str:
    if not isinstance(pixmap, QPixmap) or pixmap.isNull():
        return ""
    data = QByteArray()
    buffer = QBuffer(data)
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        return ""
    pixmap.save(buffer, "PNG")
    buffer.close()
    return base64.b64encode(bytes(data)).decode("ascii")


def _pixmap_from_base64(payload: str) -> QPixmap:
    pixmap = QPixmap()
    if not payload:
        return pixmap
    try:
        pixmap.loadFromData(base64.b64decode(payload.encode("ascii")), "PNG")
    except Exception:
        return QPixmap()
    return pixmap


def _page_setup_state(window, canvas) -> dict:
    existing = dict(getattr(window, "_page_setup_state", {}) or {})
    size = tuple(getattr(canvas, "_page_setup_size_mm", existing.get("paper_size", WORKSPACE_SIZE_MM)))
    margins = tuple(getattr(canvas, "_page_setup_margins", existing.get("margins", (0.0, 0.0, 0.0, 0.0))) or (0.0, 0.0, 0.0, 0.0))
    state = {
        "paper_name": existing.get("paper_name", getattr(canvas, "_page_setup_paper_name", "Workspace")),
        "paper_size": [float(size[0]), float(size[1])],
        "landscape": bool(getattr(canvas, "_page_setup_landscape", existing.get("landscape", True))),
        "margins": [float(value) for value in margins],
        "position": list(getattr(canvas, "_page_setup_position", existing.get("position", (1, 1))) or (1, 1)),
        "dpi": int(getattr(canvas, "_page_setup_dpi", existing.get("dpi", 600))),
    }
    return state


def _apply_page_setup_state(window, canvas, state: dict) -> None:
    paper_size = tuple(state.get("paper_size", WORKSPACE_SIZE_MM))
    landscape = bool(state.get("landscape", True))
    margins = tuple(state.get("margins", (0.0, 0.0, 0.0, 0.0)))
    setter = getattr(canvas, "set_page_setup", None)
    if callable(setter):
        setter(paper_size, landscape, margins)
    else:
        canvas._page_setup_size_mm = paper_size
        canvas._page_setup_landscape = landscape
        canvas._page_setup_margins = margins
    canvas._page_setup_paper_name = state.get("paper_name", "Workspace")
    canvas._page_setup_dpi = int(state.get("dpi", 600))
    canvas._page_setup_position = tuple(state.get("position", (1, 1)))
    window._page_setup_state = dict(state)


def _serialize_project(window) -> dict:
    canvas = getattr(window, "_canvas", None)
    objects = []
    if canvas is not None:
        for obj in getattr(canvas, "objects", []):
            source = str(getattr(obj, "path", ""))
            pixmap = getattr(obj, "pixmap", QPixmap())
            objects.append(
                {
                    "path": source,
                    "name": str(getattr(obj, "name", Path(source).stem or "Object")),
                    "rect": _rect_to_list(getattr(obj, "rect", QRectF(0, 0, 80, 80))),
                    "rotation": float(getattr(obj, "rotation", 0.0)),
                    "visible": bool(getattr(obj, "visible", True)),
                    "locked": bool(getattr(obj, "locked", False)),
                    "rotation_handle_visible": bool(getattr(obj, "rotation_handle_visible", True)),
                    "group_id": getattr(obj, "group_id", None),
                    "image_png": _pixmap_to_base64(pixmap),
                }
            )
    return {
        "format": "EngineerToolsProject",
        "version": 1,
        "page_setup": _page_setup_state(window, canvas) if canvas is not None else {},
        "save_options": dict(getattr(window, "_save_options", {}) or {}),
        "pages": list(getattr(window, "_pages", ["Page 1"])),
        "active_page_index": int(getattr(window, "_active_page_index", 0)),
        "objects": objects,
        "selected_indices": sorted(int(index) for index in getattr(canvas, "selected_indices", set())) if canvas is not None else [],
    }


def _restore_project(window, path: Path, data: dict, edw) -> bool:
    if data.get("format") != "EngineerToolsProject":
        return False
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return False
    canvas.objects = []
    for item in data.get("objects", []):
        source_path = Path(item.get("path") or item.get("name") or "Object")
        pixmap = _pixmap_from_base64(item.get("image_png", ""))
        if pixmap.isNull() and source_path.exists():
            pixmap = QPixmap(str(source_path))
        canvas.objects.append(
            edw.CanvasObject(
                path=source_path,
                pixmap=pixmap,
                rect=_rect_from_list(item.get("rect")),
                rotation=float(item.get("rotation", 0.0)),
                name=str(item.get("name") or source_path.stem or "Object"),
                visible=bool(item.get("visible", True)),
                locked=bool(item.get("locked", False)),
                rotation_handle_visible=bool(item.get("rotation_handle_visible", True)),
                group_id=item.get("group_id"),
            )
        )
    selected = {int(index) for index in data.get("selected_indices", []) if 0 <= int(index) < len(canvas.objects)}
    canvas.selected_indices = selected
    canvas._undo_stack = []
    canvas._redo_stack = []
    group_ids = [int(obj.group_id) for obj in canvas.objects if getattr(obj, "group_id", None) is not None]
    canvas._next_group_id = max(group_ids, default=0) + 1
    _apply_page_setup_state(window, canvas, data.get("page_setup", {}))
    window._save_options = dict(data.get("save_options", {}) or {})
    window._pages = list(data.get("pages", ["Page 1"])) or ["Page 1"]
    window._active_page_index = max(0, min(int(data.get("active_page_index", 0)), len(window._pages) - 1))
    window._current_file_path = path
    window._last_file_dir = path.parent
    refresh_pages = getattr(window, "_refresh_page_buttons", None)
    if callable(refresh_pages):
        refresh_pages()
    refresh_layers = getattr(window, "_refresh_layers", None)
    if callable(refresh_layers):
        refresh_layers()
    emit = getattr(canvas, "_emit_object_changes", None)
    if callable(emit):
        emit()
    canvas.update()
    return True


def _write_native_project(window, path: Path) -> None:
    path.write_text(json.dumps(_serialize_project(window), ensure_ascii=False, indent=2), encoding="utf-8")


def _read_native_project(window, path: Path, edw) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logging.exception("engineering_fixed_viewport_patch: failed to read native project %s", path)
        return False
    return _restore_project(window, path, data, edw)


def _set_dialog_paper_size(dialog, paper_name: str | None = None) -> None:
    if paper_name:
        index = dialog._paper_combo.findData(paper_name)
        if index >= 0:
            dialog._paper_combo.blockSignals(True)
            dialog._paper_combo.setCurrentIndex(index)
            dialog._paper_combo.blockSignals(False)
            dialog._paper_name = paper_name
    size = dialog.PAPER_SIZES.get(dialog._paper_name, dialog.PAPER_SIZES.get("Workspace", WORKSPACE_SIZE_MM))
    if hasattr(dialog, "_custom_size_spins"):
        for key, value in (("width", size[0]), ("height", size[1])):
            spin = dialog._custom_size_spins.get(key)
            if spin is None:
                continue
            spin.blockSignals(True)
            spin.setValue(float(value))
            spin.setEnabled(dialog._paper_name == "Custom")
            spin.blockSignals(False)
    if hasattr(dialog, "_update_preview"):
        dialog._update_preview()


def _apply_state_to_page_setup_dialog(dialog, state: dict) -> None:
    paper_name = state.get("paper_name", "Workspace")
    if paper_name == "Custom" and "paper_size" in state:
        dialog.PAPER_SIZES["Custom"] = tuple(state["paper_size"])
    _set_dialog_paper_size(dialog, paper_name)
    landscape = bool(state.get("landscape", True))
    if hasattr(dialog, "_set_orientation"):
        dialog._set_orientation(landscape)
    for key, value in zip(("top", "right", "bottom", "left"), state.get("margins", (0.0, 0.0, 0.0, 0.0)), strict=False):
        spin = getattr(dialog, "_margin_spins", {}).get(key)
        if spin is not None:
            spin.setValue(float(value))
    position = tuple(state.get("position", (1, 1)))
    if hasattr(dialog, "_set_position") and len(position) == 2:
        dialog._set_position(int(position[0]), int(position[1]))
    dpi = str(int(state.get("dpi", 600)))
    if dpi in getattr(dialog, "DPI_VALUES", ()) and dpi != "Custom":
        dialog._set_dpi(dpi)
    else:
        dialog._set_dpi("Custom")
        dialog._custom_dpi.setValue(float(state.get("dpi", 600)))
    dialog._update_preview()


def _install_page_setup_state_patch(edw) -> None:
    from . import runtime_ui_patch as rtp

    if getattr(rtp.PageSetupDialog, "_engineering_page_setup_state_patch", "") == VERSION:
        return
    original_combo_changed = rtp.PageSetupDialog._paper_combo_changed

    def paper_combo_changed(self, index: int = 0) -> None:
        original_combo_changed(self, index)
        _set_dialog_paper_size(self)

    def page_setup(self) -> None:
        canvas = getattr(self, "_canvas", None)
        dialog = rtp.PageSetupDialog(self)
        if canvas is not None:
            _apply_state_to_page_setup_dialog(dialog, _page_setup_state(self, canvas))
        if dialog.exec() == dialog.DialogCode.Accepted:
            state = {
                "paper_name": dialog._paper_name,
                "paper_size": list(dialog._current_paper_size()),
                "landscape": bool(dialog._landscape),
                "margins": [
                    dialog._margin_spins.get("top").value() if "top" in dialog._margin_spins else 0.0,
                    dialog._margin_spins.get("right").value() if "right" in dialog._margin_spins else 0.0,
                    dialog._margin_spins.get("bottom").value() if "bottom" in dialog._margin_spins else 0.0,
                    dialog._margin_spins.get("left").value() if "left" in dialog._margin_spins else 0.0,
                ],
                "position": list(getattr(dialog, "_position", (1, 1))),
                "dpi": int(dialog._custom_dpi.value()) if hasattr(dialog, "_custom_dpi") else 600,
            }
            if canvas is not None:
                _apply_page_setup_state(self, canvas, state)
                canvas.update()
            self._set_status(f"Page Setup applied: {state['paper_name']} {state['dpi']} DPI")
            return
        self._set_status("Page Setup canceled")

    rtp.PageSetupDialog._paper_combo_changed = paper_combo_changed
    edw.EngineeringDesignWorkspace._page_setup = page_setup
    rtp.PageSetupDialog._engineering_page_setup_state_patch = VERSION


def _install_native_project_patch(edw) -> None:
    from .project_file_dialog import ProjectFileDialog

    if getattr(edw.EngineeringDesignWorkspace, "_native_project_patch_version", "") == VERSION:
        return
    original_write_document = edw.EngineeringDesignWorkspace._write_document

    def write_document(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() in NATIVE_PROJECT_SUFFIXES:
            _write_native_project(self, path)
            return
        original_write_document(self, path)

    def open_file(self) -> None:
        result = ProjectFileDialog.get_open_file(self, getattr(self, "_last_file_dir", None))
        if result is None:
            self._set_status("Open canceled")
            return
        path = result.path
        if path.suffix.lower() in NATIVE_PROJECT_SUFFIXES:
            if _read_native_project(self, path, edw):
                self._set_status(f"Opened project {path.name}")
            else:
                self._set_status("Open project failed")
            return
        canvas = getattr(self, "_canvas", None)
        if canvas is not None:
            canvas.load_file(path)
        self._last_file_dir = path.parent
        self._set_status(f"Opened {path.name}")

    def import_file(self) -> None:
        result = ProjectFileDialog.get_import_file(self, getattr(self, "_last_file_dir", None))
        if result is None:
            self._set_status("Import canceled")
            return
        path = result.path
        if path.suffix.lower() in NATIVE_PROJECT_SUFFIXES:
            if _read_native_project(self, path, edw):
                self._set_status(f"Imported project {path.name}")
            else:
                self._set_status("Import project failed")
            return
        canvas = getattr(self, "_canvas", None)
        if canvas is not None:
            canvas.load_file(path)
        self._last_file_dir = path.parent
        self._set_status(f"Imported {path.name}")

    edw.EngineeringDesignWorkspace._write_document = write_document
    edw.EngineeringDesignWorkspace._open_file = open_file
    edw.EngineeringDesignWorkspace._import_file = import_file
    edw.EngineeringDesignWorkspace._native_project_patch_version = VERSION


def _sync_open_rulers(start_bar, canvas) -> None:
    try:
        if not hasattr(canvas, "_page_setup_size_mm"):
            canvas._page_setup_size_mm = WORKSPACE_SIZE_MM
        if getattr(start_bar, "_ruler_enabled", False):
            page = _page_rect(canvas)
            if getattr(start_bar, "_ruler_corner_origin_active", False):
                start_bar._set_ruler_origin(QPointF(page.topLeft()), custom=True)
            elif not getattr(start_bar, "_ruler_origin_custom", False):
                start_bar._set_ruler_origin(QPointF(page.center()), custom=False)
            if hasattr(start_bar, "_position_rulers"):
                start_bar._position_rulers()
        canvas.update()
    except Exception:
        logging.exception("engineering_fixed_viewport_patch: ruler sync failed")


def _install_rotation_drag_cursor() -> None:
    try:
        from modules.mechanics_dynamics_statics import workspace as edw
    except Exception:
        logging.exception("engineering_fixed_viewport_patch: canvas import failed")
        return
    if getattr(edw.EngineeringCanvas, "_fixed_viewport_cursor_version", "") == VERSION:
        return
    original_press = edw.EngineeringCanvas.mousePressEvent
    original_move = edw.EngineeringCanvas.mouseMoveEvent

    def set_closed_hand(canvas) -> None:
        canvas.setCursor(_asset_cursor("hand_closed.svg", QCursor(Qt.CursorShape.ClosedHandCursor), 11, 8, 23))

    def mouse_press(self, event) -> None:
        original_press(self, event)
        if getattr(self, "_drag_action", None) == "rotate":
            set_closed_hand(self)

    def mouse_move(self, event) -> None:
        original_move(self, event)
        if getattr(self, "_drag_action", None) == "rotate":
            set_closed_hand(self)

    edw.EngineeringCanvas.mousePressEvent = mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas._fixed_viewport_cursor_version = VERSION


def apply_engineering_fixed_viewport_patch() -> None:
    try:
        from . import engineering_fixed_page_rotation_patch as fixed
        from . import engineering_window_geometry_patch as geometry
        from .module_window import ModuleWindow
        from modules.mechanics_dynamics_statics import workspace as edw
        from src.engineers_tools.ui import start_bar as sb
    except Exception:
        logging.exception("engineering_fixed_viewport_patch: imports failed")
        return

    if getattr(ModuleWindow, "_fixed_viewport_patch_version", "") == VERSION:
        return

    fixed.WORKSPACE_SIZE_MM = WORKSPACE_SIZE_MM
    fixed._fixed_page_size = lambda _canvas=None: WORKSPACE_SIZE_MM
    fixed._page_rect = _page_rect
    fixed._unit_to_canvas_px = _unit_to_canvas_px
    fixed._resize_cursor = _resize_cursor
    _disable_shell_edge_resize(geometry)
    _disable_shell_edge_resize(fixed)
    _install_native_project_patch(edw)
    _install_page_setup_state_patch(edw)
    edw.EngineeringCanvas._page_rect = _page_rect
    sb.StartBar._unit_to_canvas_px = _unit_to_canvas_px

    original_resize = getattr(ModuleWindow, "resizeEvent", None)

    def resize_event(self, event) -> None:
        if callable(original_resize):
            original_resize(self, event)
        canvas = getattr(self, "_canvas", None)
        start_bar = getattr(self, "_start_bar_widget", None)
        if canvas is not None and start_bar is not None:
            _sync_open_rulers(start_bar, canvas)

    ModuleWindow.resizeEvent = resize_event
    _install_rotation_drag_cursor()
    ModuleWindow._fixed_viewport_patch_version = VERSION
    logging.info("engineering_fixed_viewport_patch: installed version=%s", VERSION)

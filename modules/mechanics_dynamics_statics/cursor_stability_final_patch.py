"""Final cursor stability for move, resize, rotate and empty-canvas reset."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt

PATCH_VERSION = "engineering-cursor-stability-final-2026-06-30-b"


def _kind(hover: str | None, action: str | None = None) -> str:
    mapping = {
        "move": "move",
        "rotate": "rotate",
        "resize_n": "resize_n",
        "resize_s": "resize_s",
        "resize_e": "resize_e",
        "resize_w": "resize_w",
        "resize_ne": "resize_ne",
        "resize_sw": "resize_sw",
        "resize_nw": "resize_nw",
        "resize_se": "resize_se",
    }
    return mapping.get(action or str(hover), "default")


def apply_cursor_stability_final_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_cursor_stability_final_patch", "") == PATCH_VERSION:
        return

    for key in (
        "resize_h", "resize_v", "resize_horizontal", "resize_vertical", "resize_n", "resize_s", "resize_e", "resize_w",
        "resize_ne", "resize_sw", "resize_nw", "resize_se", "resize_diag_f", "resize_diag_b", "resize_fdiag", "resize_bdiag",
        "rotate", "rotate_drag", "move", "default",
    ):
        file_name, hot_x, hot_y, _side = svg._CURSOR_ASSET_MAP.get(key, ("mouse_cursor.svg", 12, 12, 24))
        svg._CURSOR_ASSET_MAP[key] = (file_name, hot_x, hot_y, 24)
    svg._CURSOR_ASSET_MAP["rotate"] = ("rotate_cursor.svg", 12, 12, 24)
    svg._CURSOR_ASSET_MAP["rotate_drag"] = ("rotate_cursor.svg", 12, 12, 24)
    svg._CURSOR_ASSET_MAP["move"] = ("move_cursor.svg", 12, 12, 24)
    svg._CURSOR_CACHE.clear()

    old_press = edw.EngineeringCanvas.mousePressEvent
    old_release = edw.EngineeringCanvas.mouseReleaseEvent
    old_delete = edw.EngineeringCanvas._delete_selected_objects
    old_restore = edw.EngineeringCanvas._restore_snapshot

    def set_kind(canvas, kind: str) -> None:
        setter = getattr(svg, "_set_cursor_kind", None)
        if callable(setter):
            setter(canvas, kind)
            return
        if getattr(canvas, "_svg_cursor_kind", None) == kind:
            return
        canvas._svg_cursor_kind = kind
        canvas.setCursor(svg.project_cursor(kind))

    def reset(canvas) -> None:
        canvas._drag_action = None
        canvas._selection_origin = None
        canvas._selection_rect = None
        set_kind(canvas, "default")
        canvas.update()

    def press(self, event) -> None:
        old_press(self, event)
        if not getattr(self, "objects", None):
            reset(self)
            return
        set_kind(self, _kind(None, getattr(self, "_drag_action", None)))

    def move(self, event) -> None:
        point = self._to_canvas_point(event.position())
        self.mouse_position_changed.emit(point.x(), point.y())
        if not getattr(self, "objects", None):
            set_kind(self, "default")
            event.accept()
            return
        action = getattr(self, "_drag_action", None)
        if action is not None:
            set_kind(self, _kind(None, action))
            self._apply_drag(point)
            event.accept()
            return
        if getattr(self, "_selection_origin", None) is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._selection_rect = QRectF(self._selection_origin, point).normalized()
            self.update()
            event.accept()
            return
        _index, hover = self._hit_test_object(point)
        set_kind(self, _kind(hover))
        event.accept()

    def release(self, event) -> None:
        old_release(self, event)
        if not getattr(self, "objects", None):
            reset(self)
            return
        try:
            point = self._to_canvas_point(event.position())
            _index, hover = self._hit_test_object(point)
            set_kind(self, _kind(hover))
        except Exception:
            set_kind(self, "default")

    def delete_selected(self) -> None:
        old_delete(self)
        reset(self)

    def restore_snapshot(self, snapshot) -> None:
        old_restore(self, snapshot)
        reset(self)

    edw.EngineeringCanvas.mousePressEvent = press
    edw.EngineeringCanvas.mouseMoveEvent = move
    edw.EngineeringCanvas.mouseReleaseEvent = release
    edw.EngineeringCanvas._delete_selected_objects = delete_selected
    edw.EngineeringCanvas._restore_snapshot = restore_snapshot
    edw.EngineeringDesignWorkspace._engineering_cursor_stability_final_patch = PATCH_VERSION

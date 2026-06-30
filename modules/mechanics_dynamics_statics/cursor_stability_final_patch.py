"""Final cursor stability for move, resize and rotate."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt

PATCH_VERSION = "engineering-cursor-stability-final-2026-06-30-a"


def _kind(hover: str | None, action: str | None = None) -> str:
    mapping = {"move": "move", "rotate": "rotate", "resize_n": "resize_n", "resize_s": "resize_s", "resize_e": "resize_e", "resize_w": "resize_w", "resize_ne": "resize_ne", "resize_sw": "resize_sw", "resize_nw": "resize_nw", "resize_se": "resize_se"}
    return mapping.get(action or str(hover), "default")


def apply_cursor_stability_final_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_cursor_stability_final_patch", "") == PATCH_VERSION:
        return

    for key in ("resize_h", "resize_v", "resize_horizontal", "resize_vertical", "resize_n", "resize_s", "resize_e", "resize_w", "resize_ne", "resize_sw", "resize_nw", "resize_se", "resize_diag_f", "resize_diag_b", "resize_fdiag", "resize_bdiag", "rotate", "rotate_drag"):
        file_name, hot_x, hot_y, _side = svg._CURSOR_ASSET_MAP.get(key, ("mouse_cursor.svg", 12, 12, 24))
        svg._CURSOR_ASSET_MAP[key] = (file_name, hot_x, hot_y, 26)
    svg._CURSOR_ASSET_MAP["rotate"] = ("rotate_cursor.svg", 12, 12, 26)
    svg._CURSOR_ASSET_MAP["rotate_drag"] = ("rotate_cursor.svg", 12, 12, 26)
    svg._CURSOR_CACHE.clear()

    old_press = edw.EngineeringCanvas.mousePressEvent
    old_release = edw.EngineeringCanvas.mouseReleaseEvent

    def press(self, event) -> None:
        old_press(self, event)
        self.setCursor(svg.project_cursor(_kind(None, getattr(self, "_drag_action", None))))

    def move(self, event) -> None:
        point = self._to_canvas_point(event.position())
        self.mouse_position_changed.emit(point.x(), point.y())
        action = getattr(self, "_drag_action", None)
        if action is not None:
            self.setCursor(svg.project_cursor(_kind(None, action)))
            self._apply_drag(point)
            self.setCursor(svg.project_cursor(_kind(None, action)))
            event.accept()
            return
        if getattr(self, "_selection_origin", None) is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._selection_rect = QRectF(self._selection_origin, point).normalized()
            self.update()
            event.accept()
            return
        _index, hover = self._hit_test_object(point)
        self.setCursor(svg.project_cursor(_kind(hover)))
        event.accept()

    def release(self, event) -> None:
        old_release(self, event)
        try:
            point = self._to_canvas_point(event.position())
            _index, hover = self._hit_test_object(point)
            self.setCursor(svg.project_cursor(_kind(hover)))
        except Exception:
            self.setCursor(svg.project_cursor("default"))

    edw.EngineeringCanvas.mousePressEvent = press
    edw.EngineeringCanvas.mouseMoveEvent = move
    edw.EngineeringCanvas.mouseReleaseEvent = release
    edw.EngineeringDesignWorkspace._engineering_cursor_stability_final_patch = PATCH_VERSION

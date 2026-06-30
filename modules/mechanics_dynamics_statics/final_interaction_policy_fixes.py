"""Final interaction policy for the current Engineering Design Tools shell.

For this stage the main window can be moved and maximized/restored, but manual
border and corner resize is disabled. Object resize/rotate remains available
inside the canvas. This file also forces rotate press/release cursors to use the
project cursor family instead of Qt defaults.
"""

from __future__ import annotations

from PySide6.QtCore import Qt

PATCH_VERSION = "engineering-final-interaction-policy-2026-06-30-b"


def apply_final_interaction_policy_fixes() -> None:
    from src.engineers_tools.app.module_window import ModuleWindow
    from . import cursor_unification_fixes as cursors
    from . import window_resize_fixes
    from . import workspace as edw

    if getattr(ModuleWindow, "_engineering_final_interaction_policy_patch", "") == PATCH_VERSION:
        return

    # Disable only the manual edge/corner resize surface. The window controls
    # still keep their normal minimize/maximize/restore behavior.
    window_resize_fixes._window_edges = lambda _window, _pos: frozenset()
    window_resize_fixes._cursor_kind = lambda _edges: None

    original_canvas_press = edw.EngineeringCanvas.mousePressEvent
    original_canvas_release = edw.EngineeringCanvas.mouseReleaseEvent

    def canvas_mouse_press(self, event) -> None:
        original_canvas_press(self, event)
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, "_drag_action", None) == "rotate":
            self.setCursor(cursors.project_cursor("hand_closed"))

    def canvas_mouse_release(self, event) -> None:
        was_rotate = getattr(self, "_drag_action", None) == "rotate"
        original_canvas_release(self, event)
        if was_rotate:
            self.setCursor(cursors.project_cursor("hand_open"))

    edw.EngineeringCanvas.mousePressEvent = canvas_mouse_press
    edw.EngineeringCanvas.mouseReleaseEvent = canvas_mouse_release
    ModuleWindow._engineering_final_interaction_policy_patch = PATCH_VERSION

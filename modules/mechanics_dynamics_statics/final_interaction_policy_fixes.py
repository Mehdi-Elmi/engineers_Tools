"""Final interaction policy for the current Engineering Design Tools shell.

For this stage the main window opens maximized by default. It can be restored and
moved from the top bar, but manual border/corner resize is disabled. Object
resize/rotate remains available inside the canvas.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt

PATCH_VERSION = "engineering-final-interaction-policy-2026-06-30-c"


def apply_final_interaction_policy_fixes() -> None:
    from src.engineers_tools.app.module_window import ModuleWindow
    from . import cursor_unification_fixes as cursors
    from . import window_resize_fixes
    from . import workspace as edw

    if getattr(ModuleWindow, "_engineering_final_interaction_policy_patch", "") == PATCH_VERSION:
        return

    # Keep the old resize API inert for any code path that still asks for it.
    window_resize_fixes._window_edges = lambda _window, _pos: frozenset()
    window_resize_fixes._cursor_kind = lambda _edges: None

    original_init = ModuleWindow.__init__
    original_canvas_press = edw.EngineeringCanvas.mousePressEvent
    original_canvas_release = edw.EngineeringCanvas.mouseReleaseEvent

    def init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        self._engineering_open_maximized_pending = True

        def open_maximized() -> None:
            if not getattr(self, "_engineering_open_maximized_pending", False):
                return
            self._engineering_open_maximized_pending = False
            if not getattr(self, "_is_manually_maximized", False):
                self._toggle_maximize()

        QTimer.singleShot(0, open_maximized)

    def canvas_mouse_press(self, event) -> None:
        original_canvas_press(self, event)
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, "_drag_action", None) == "rotate":
            self.setCursor(cursors.project_cursor("hand_closed"))

    def canvas_mouse_release(self, event) -> None:
        was_rotate = getattr(self, "_drag_action", None) == "rotate"
        original_canvas_release(self, event)
        if was_rotate:
            self.setCursor(cursors.project_cursor("hand_open"))

    ModuleWindow.__init__ = init
    edw.EngineeringCanvas.mousePressEvent = canvas_mouse_press
    edw.EngineeringCanvas.mouseReleaseEvent = canvas_mouse_release
    ModuleWindow._engineering_final_interaction_policy_patch = PATCH_VERSION

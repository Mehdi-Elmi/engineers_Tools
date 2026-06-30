"""Final interaction policy for the current Engineering Design Tools shell.

For this stage the main window is intentionally movable but not resizable. Object
resize/rotate remains available inside the canvas. This file also forces rotate
press/release cursors to use the project cursor family instead of Qt defaults.
"""

from __future__ import annotations

from PySide6.QtCore import Qt

PATCH_VERSION = "engineering-final-interaction-policy-2026-06-30-a"


def apply_final_interaction_policy_fixes() -> None:
    from src.engineers_tools.app.module_window import ModuleWindow
    from . import cursor_unification_fixes as cursors
    from . import window_resize_fixes
    from . import workspace as edw

    if getattr(ModuleWindow, "_engineering_final_interaction_policy_patch", "") == PATCH_VERSION:
        return

    # The main shell can move, but its border/corner resize is disabled here.
    window_resize_fixes._window_edges = lambda _window, _pos: frozenset()
    window_resize_fixes._cursor_kind = lambda _edges: None

    original_init = ModuleWindow.__init__
    original_build_top_bar = ModuleWindow._build_top_bar
    original_toggle_maximize = ModuleWindow._toggle_maximize
    original_canvas_press = edw.EngineeringCanvas.mousePressEvent
    original_canvas_release = edw.EngineeringCanvas.mouseReleaseEvent

    def init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        self.setFixedSize(self.size())
        self._is_manually_maximized = False
        if self._maximize_button is not None:
            self._maximize_button.setEnabled(False)
            self._maximize_button.setToolTip("Window size is locked")

    def build_top_bar(self):
        bar = original_build_top_bar(self)
        if self._maximize_button is not None:
            self._maximize_button.setEnabled(False)
            self._maximize_button.setToolTip("Window size is locked")
        return bar

    def toggle_maximize(self) -> None:
        self._is_manually_maximized = False
        if self._maximize_button is not None:
            self._maximize_button.setEnabled(False)
            self._maximize_button.setToolTip("Window size is locked")
        setter = getattr(self, "_set_status", None)
        if callable(setter):
            setter("Window size locked")

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
    ModuleWindow._build_top_bar = build_top_bar
    ModuleWindow._toggle_maximize = toggle_maximize
    ModuleWindow._restore_from_maximize = toggle_maximize
    edw.EngineeringCanvas.mousePressEvent = canvas_mouse_press
    edw.EngineeringCanvas.mouseReleaseEvent = canvas_mouse_release
    ModuleWindow._engineering_final_interaction_policy_patch = PATCH_VERSION

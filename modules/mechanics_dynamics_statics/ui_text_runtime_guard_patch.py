"""Final guard for Text runtime menus and font choices.

Runs after the runtime Text patch and before the workspace is created. It keeps
font choices consistent across the Text bar and File Properties, and makes menu
actions ignore the QAction ``checked`` argument so Bullet/Number/Color commands
operate on the active window instead of receiving a boolean.
"""

from __future__ import annotations

PATCH_VERSION = "engineering-ui-text-runtime-guard-2026-07-01-a"

FONT_CHOICES = (
    "Times New Roman",
    "Arial",
    "Calibri",
    "Cambria",
    "Cambria Math",
    "Segoe UI",
    "Tahoma",
    "Verdana",
    "Georgia",
    "Courier New",
    "Consolas",
    "Symbol",
)


def apply_ui_text_runtime_guard_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from . import ui_text_tool_final_patch as text_final
    from . import ui_text_tool_runtime_fix_patch as runtime
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_ui_text_runtime_guard_patch", "") == PATCH_VERSION:
        return

    svg.FONT_CHOICES = FONT_CHOICES
    text_final.FONT_CHOICES = FONT_CHOICES
    runtime.FONT_CHOICES = FONT_CHOICES

    def safe_menu_action(menu, text: str, callback) -> None:
        action = menu.addAction(text)
        action.triggered.connect(lambda checked=False, cb=callback: cb())

    runtime._menu_action = safe_menu_action
    edw.EngineeringDesignWorkspace._engineering_ui_text_runtime_guard_patch = PATCH_VERSION

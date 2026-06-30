"""Apply project cursor family to Start Bar hover states."""

from __future__ import annotations

PATCH_VERSION = "engineering-startbar-cursor-fixes-2026-06-30-a"


def apply_startbar_cursor_fixes() -> None:
    from .cursor_unification_fixes import project_cursor
    from src.engineers_tools.ui import start_bar as sb

    if getattr(sb.StartBar, "_engineering_startbar_cursor_patch", "") == PATCH_VERSION:
        return

    original_init = sb.StartBar.__init__

    def init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        for button in getattr(self, "_buttons", {}).values():
            button.setCursor(project_cursor("hand_open"))
        popup = getattr(self, "_popup", None)
        if popup is not None:
            popup.setCursor(project_cursor("hand_open"))

    sb.StartBar.__init__ = init
    sb.StartBar._engineering_startbar_cursor_patch = PATCH_VERSION

"""Legacy TextSubBar patch disabled.

The current text tool uses the fixed top InlineTextBar installed by
ui_text_tool_final_patch. This module is kept as a no-op because module_entry
still imports it for compatibility with older patch chains.
"""

from __future__ import annotations

PATCH_VERSION = "engineering-text-toolbar-toggle-disabled-2026-07-01-a"


def apply_text_toolbar_toggle_patch() -> None:
    from . import workspace as edw

    edw.EngineeringDesignWorkspace._engineering_text_toolbar_toggle_patch = PATCH_VERSION

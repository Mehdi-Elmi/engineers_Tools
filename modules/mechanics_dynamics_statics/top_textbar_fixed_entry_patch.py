"""Apply the fixed top Text Bar patch from module entry compatible chains."""

from __future__ import annotations

PATCH_VERSION = "engineering-top-textbar-entry-2026-06-30-a"


def apply_top_textbar_fixed_entry_patch() -> None:
    from .top_textbar_fixed_patch_3 import apply_top_textbar_fixed_patch_3
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_top_textbar_entry_patch", "") == PATCH_VERSION:
        return
    apply_top_textbar_fixed_patch_3()
    edw.EngineeringDesignWorkspace._engineering_top_textbar_entry_patch = PATCH_VERSION

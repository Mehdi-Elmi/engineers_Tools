"""Keep text tools visible as a fixed workspace strip."""

from __future__ import annotations

PATCH_VERSION = "engineering-top-textbar-fixed-2026-06-30-c"


def apply_top_textbar_fixed_patch_3() -> None:
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_top_textbar_fixed_patch_3", "") == PATCH_VERSION:
        return

    original_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        original_init(self, module)
        start_bar = getattr(self, "_start_bar_widget", None)
        setter = getattr(start_bar, "_set_text_toolbar_visible", None) if start_bar is not None else None
        if callable(setter):
            setter(True)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_top_textbar_fixed_patch_3 = PATCH_VERSION

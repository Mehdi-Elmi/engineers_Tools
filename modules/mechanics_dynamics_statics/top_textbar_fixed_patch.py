"""Keep the Text tools fixed near the top menu area instead of using a Start Bar popup."""

from __future__ import annotations

PATCH_VERSION = "engineering-top-textbar-fixed-2026-06-30-a"


def apply_top_textbar_fixed_patch() -> None:
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_top_textbar_fixed_patch", "") == PATCH_VERSION:
        return

    original_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        original_init(self, module)
        start_bar = getattr(self, "_start_bar_widget", None)
        setter = getattr(start_bar, "_set_text_toolbar_visible", None) if start_bar is not None else None
        if callable(setter):
            setter(True)

    def show_view_menu(self, anchor) -> None:
        items = [edw.MenuItemSpec("Start Bar", self._toggle_start_bar, checkable=True, checked=self._view_state["start_bar"])]
        for tool in self.get_start_bar_tools():
            items.append(edw.MenuItemSpec(tool.label, lambda key=tool.key: self._toggle_start_bar_tool(key), checkable=True, checked=self._start_bar_tool_state.get(tool.key, True)))
        start_bar = getattr(self, "_start_bar_widget", None)
        active = True if start_bar is None else bool(getattr(start_bar, "_text_toolbar_enabled", True))
        items.append(edw.MenuItemSpec("Text Bar", lambda: getattr(start_bar, "_set_text_toolbar_visible", lambda value: None)(not active), checkable=True, checked=active))
        self._show_menu("View", tuple(items), anchor)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._show_view_menu = show_view_menu
    edw.EngineeringDesignWorkspace._engineering_top_textbar_fixed_patch = PATCH_VERSION

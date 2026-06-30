"""Add Text Bar toggle to the workspace View menu."""

from __future__ import annotations

PATCH_VERSION = "engineering-view-textbar-menu-2026-06-30-a"


def apply_view_textbar_menu_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_view_textbar_menu_patch", "") == PATCH_VERSION:
        return

    def toggle_text_bar(workspace) -> None:
        start_bar = getattr(workspace, "_start_bar_widget", None)
        if start_bar is None:
            return
        setter = getattr(start_bar, "_set_text_toolbar_visible", None)
        if callable(setter):
            setter(not bool(getattr(start_bar, "_text_toolbar_enabled", False)))

    def show_view_menu(self, anchor) -> None:
        items = [edw.MenuItemSpec("Start Bar", self._toggle_start_bar, checkable=True, checked=self._view_state["start_bar"])]
        for tool in self.get_start_bar_tools():
            items.append(edw.MenuItemSpec(tool.label, lambda key=tool.key: self._toggle_start_bar_tool(key), checkable=True, checked=self._start_bar_tool_state.get(tool.key, True)))
        start_bar = getattr(self, "_start_bar_widget", None)
        active = bool(getattr(start_bar, "_text_toolbar_enabled", False)) if start_bar is not None else False
        items.append(edw.MenuItemSpec("Text Bar", lambda: toggle_text_bar(self), checkable=True, checked=active))
        self._show_menu("View", tuple(items), anchor)

    edw.EngineeringDesignWorkspace._show_view_menu = show_view_menu
    edw.EngineeringDesignWorkspace._engineering_view_textbar_menu_patch = PATCH_VERSION

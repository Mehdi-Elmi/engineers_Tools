"""Entry point for Engineering Design Tools."""

from __future__ import annotations

from src.engineers_tools.app.module_window import ModuleWindow
from src.engineers_tools.app.modules import LauncherModule

from .interaction_fixes import apply_interaction_fixes
from .ui_refinement_fixes import apply_ui_refinement_fixes
from .window_resize_fixes import apply_window_resize_fixes
from .workspace import EngineeringDesignWorkspace


def create_window(module: LauncherModule) -> ModuleWindow:
    apply_window_resize_fixes()
    apply_interaction_fixes()
    apply_ui_refinement_fixes()
    return EngineeringDesignWorkspace(module)

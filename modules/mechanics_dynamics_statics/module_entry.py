"""Entry point for Engineering Design Tools."""

from __future__ import annotations

from src.engineers_tools.app.module_window import ModuleWindow
from src.engineers_tools.app.modules import LauncherModule

from .current_interaction_cleanup_fixes import apply_current_interaction_cleanup_fixes
from .cursor_unification_fixes import apply_cursor_unification_fixes
from .file_export_project_fixes import apply_file_export_project_fixes
from .final_interaction_policy_fixes import apply_final_interaction_policy_fixes
from .fixed_workspace_dimension_fixes import apply_fixed_workspace_dimension_fixes
from .interaction_fixes import apply_interaction_fixes
from .ruler_precision_fixes import apply_ruler_precision_fixes
from .startbar_cursor_fixes import apply_startbar_cursor_fixes
from .ui_refinement_fixes import apply_ui_refinement_fixes
from .window_resize_fixes import apply_window_resize_fixes
from .workspace import EngineeringDesignWorkspace


def create_window(module: LauncherModule) -> ModuleWindow:
    apply_window_resize_fixes()
    apply_interaction_fixes()
    apply_ui_refinement_fixes()
    apply_cursor_unification_fixes()
    apply_startbar_cursor_fixes()
    apply_fixed_workspace_dimension_fixes()
    apply_ruler_precision_fixes()
    apply_final_interaction_policy_fixes()
    apply_current_interaction_cleanup_fixes()
    apply_file_export_project_fixes()
    return EngineeringDesignWorkspace(module)

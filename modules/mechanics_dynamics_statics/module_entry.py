"""Entry point for Engineering Design Tools."""

from __future__ import annotations

from src.engineers_tools.app.module_window import ModuleWindow
from src.engineers_tools.app.modules import LauncherModule

from .current_interaction_cleanup_fixes import apply_current_interaction_cleanup_fixes
from .cursor_stability_final_patch import apply_cursor_stability_final_patch
from .cursor_unification_fixes import apply_cursor_unification_fixes
from .engineering_runtime_audit_final_patch import apply_engineering_runtime_audit_final_patch
from .file_export_project_fixes import apply_file_export_project_fixes
from .file_properties_general_patch import apply_file_properties_general_patch
from .file_properties_view_final_patch import apply_file_properties_view_final_patch
from .final_focus_editing_icons_patch import apply_final_focus_editing_icons_patch
from .final_interaction_policy_fixes import apply_final_interaction_policy_fixes
from .final_ui_repair_fixes import apply_final_ui_repair_fixes
from .fixed_workspace_dimension_fixes import apply_fixed_workspace_dimension_fixes
from .interaction_fixes import apply_interaction_fixes
from .native_cursor_lock_patch import apply_native_cursor_lock_patch
from .page_setup_properties_hotfix import apply_page_setup_properties_hotfix
from .project_dialog_style_cursor_patch import apply_project_dialog_style_cursor_patch
from .properties_grid_cleanup_patch import apply_properties_grid_cleanup_patch
from .ruler_precision_fixes import apply_ruler_precision_fixes
from .ruler_unit_origin_final_patch import apply_ruler_unit_origin_final_patch
from .startbar_cursor_fixes import apply_startbar_cursor_fixes
from .svg_cursor_assets_activation_patch import apply_svg_cursor_assets_activation_patch
from .text_color_inline_palette_patch import apply_text_color_inline_palette_patch
from .text_color_swatch_patch import apply_text_color_swatch_patch
from .text_lag_final_patch import apply_text_lag_final_patch
from .text_line_math_symbols_patch import apply_text_line_math_symbols_patch
from .text_list_settings_final_patch import apply_text_list_settings_final_patch
from .text_list_settings_patch import apply_text_list_settings_patch
from .text_runtime_performance_editing_patch import apply_text_runtime_performance_editing_patch
from .text_toolbar_final_event_safety_patch import apply_text_toolbar_final_event_safety_patch
from .text_toolbar_word_behavior_patch import apply_text_toolbar_word_behavior_patch
from .ui_refinement_fixes import apply_ui_refinement_fixes
from .ui_text_runtime_guard_patch import apply_ui_text_runtime_guard_patch
from .ui_text_tool_final_patch import apply_ui_text_tool_final_patch
from .ui_text_tool_runtime_fix_patch import apply_ui_text_tool_runtime_fix_patch
from .unit_grid_properties_final_patch import apply_unit_grid_properties_final_patch
from .window_resize_fixes import apply_window_resize_fixes
from .windows_cursor_ruler_patch import apply_windows_cursor_ruler_patch
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
    apply_final_ui_repair_fixes()
    apply_page_setup_properties_hotfix()
    apply_unit_grid_properties_final_patch()
    apply_properties_grid_cleanup_patch()
    apply_file_properties_general_patch()
    apply_windows_cursor_ruler_patch()
    apply_ruler_unit_origin_final_patch()
    apply_svg_cursor_assets_activation_patch()
    apply_file_properties_view_final_patch()
    apply_cursor_stability_final_patch()
    apply_ui_text_tool_final_patch()
    apply_ui_text_tool_runtime_fix_patch()
    apply_ui_text_runtime_guard_patch()
    apply_text_list_settings_patch()
    apply_text_color_swatch_patch()
    apply_text_list_settings_final_patch()
    apply_text_color_inline_palette_patch()
    apply_native_cursor_lock_patch()
    apply_project_dialog_style_cursor_patch()
    apply_engineering_runtime_audit_final_patch()
    apply_text_toolbar_word_behavior_patch()
    apply_text_toolbar_final_event_safety_patch()
    apply_text_runtime_performance_editing_patch()
    apply_text_lag_final_patch()
    apply_final_focus_editing_icons_patch()
    apply_text_line_math_symbols_patch()
    return EngineeringDesignWorkspace(module)

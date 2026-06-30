"""Final SVG cursor mapping overrides."""

from __future__ import annotations

PATCH_VERSION = "engineering-svg-cursor-mapping-final-2026-06-30-a"


def apply_svg_cursor_mapping_final_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_svg_cursor_mapping_final_patch", "") == PATCH_VERSION:
        return

    svg._CURSOR_ASSET_MAP.update(
        {
            "rotate": ("rotate_cursor.svg", 12, 12, 24),
            "rotate_drag": ("rotate_cursor.svg", 12, 12, 24),
            "resize_ne": ("corner_resize_b.svg", 12, 12, 24),
            "resize_sw": ("corner_resize_b.svg", 12, 12, 24),
            "resize_nw": ("corner_resize_a.svg", 12, 12, 24),
            "resize_se": ("corner_resize_a.svg", 12, 12, 24),
            "resize_diag_f": ("corner_resize_a.svg", 12, 12, 24),
            "resize_diag_b": ("corner_resize_b.svg", 12, 12, 24),
            "resize_fdiag": ("corner_resize_a.svg", 12, 12, 24),
            "resize_bdiag": ("corner_resize_b.svg", 12, 12, 24),
        }
    )
    svg._CURSOR_CACHE.clear()
    edw.EngineeringDesignWorkspace._engineering_svg_cursor_mapping_final_patch = PATCH_VERSION

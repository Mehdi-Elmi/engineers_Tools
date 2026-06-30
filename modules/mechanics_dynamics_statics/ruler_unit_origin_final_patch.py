"""Final ruler origin behavior while changing units."""

from __future__ import annotations

from PySide6.QtCore import QPointF

PATCH_VERSION = "engineering-ruler-unit-origin-final-2026-06-30-a"
UNITS = {"mm", "cm", "m", "px", "pt", "in"}


def apply_ruler_unit_origin_final_patch() -> None:
    from . import workspace as edw
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_ruler_unit_origin_final_patch", "") == PATCH_VERSION:
        return

    def set_unit(self, unit: str) -> None:
        if unit not in UNITS:
            return
        if unit == getattr(self, "_unit", "mm"):
            popup = getattr(self, "_popup", None)
            if popup is not None:
                popup.close()
            return

        keep_custom = bool(getattr(self, "_ruler_origin_custom", False)) and not bool(getattr(self, "_ruler_corner_origin_active", False))
        custom_origin = QPointF(getattr(self, "_ruler_origin", QPointF(0, 0)))
        corner_active = bool(getattr(self, "_ruler_corner_origin_active", False))

        self._unit = unit
        self._grid_spacing = 1.0
        self._apply_unit_to_host()
        self._ensure_canvas_hooks()
        self._apply_grid_to_host()

        if getattr(self, "_ruler_enabled", False):
            if corner_active:
                self._ruler_origin = QPointF(float(sb.RULER_THICKNESS), float(sb.RULER_THICKNESS))
                self._ruler_origin_custom = True
            elif keep_custom:
                self._ruler_origin = custom_origin
                self._ruler_origin_custom = True
            else:
                self._center_ruler_origin()
            self._sync_rulers()

        self.unit_changed.emit(unit)
        self.grid_changed.emit(self._grid_enabled, self._grid_spacing, self._unit)
        self.tool_requested.emit(f"unit_{unit}")
        self._refresh_tooltips()
        popup = getattr(self, "_popup", None)
        if popup is not None:
            popup.close()

    sb.StartBar._set_unit = set_unit
    edw.EngineeringDesignWorkspace._engineering_ruler_unit_origin_final_patch = PATCH_VERSION

"""Lock native Qt cursors to the Engineering Tools cursor system.

Several older patches and base handlers still call ``setCursor`` with native Qt
cursor shapes such as OpenHandCursor, ClosedHandCursor, and Size*Cursor. This
patch runs last and intercepts those calls on the engineering canvas so drag,
resize, rotate, and move never fall back to Windows cursors.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

PATCH_VERSION = "engineering-native-cursor-lock-2026-07-01-a"

_NATIVE_SHAPE_TO_KIND = {
    Qt.CursorShape.OpenHandCursor: "rotate",
    Qt.CursorShape.ClosedHandCursor: "rotate_drag",
    Qt.CursorShape.SizeAllCursor: "move_drag",
    Qt.CursorShape.SizeHorCursor: "resize_horizontal",
    Qt.CursorShape.SizeVerCursor: "resize_vertical",
    Qt.CursorShape.SizeFDiagCursor: "resize_fdiag",
    Qt.CursorShape.SizeBDiagCursor: "resize_bdiag",
    Qt.CursorShape.CrossCursor: "rotate",
    Qt.CursorShape.ArrowCursor: "default",
}


def _native_kind(cursor) -> str | None:
    shape = None
    if isinstance(cursor, Qt.CursorShape):
        shape = cursor
    elif isinstance(cursor, QCursor):
        try:
            shape = cursor.shape()
        except Exception:
            shape = None
    return _NATIVE_SHAPE_TO_KIND.get(shape)


def apply_native_cursor_lock_patch() -> None:
    from . import final_cursor_properties_textbar_patch as fcp
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw

    if getattr(edw.EngineeringCanvas, "_engineering_native_cursor_lock_patch", "") == PATCH_VERSION:
        return

    svg._CURSOR_ASSET_MAP.update({
        "default": ("mouse_cursor.svg", 3, 3, 24),
        "move": ("move_cursor.svg", 14, 14, 28),
        "move_drag": ("move_cursor.svg", 14, 14, 28),
        "rotate": ("rotate.svg", 14, 14, 28),
        "rotate_drag": ("rotate.svg", 14, 14, 28),
        "resize_horizontal": ("resize_horizontal.svg", 14, 14, 28),
        "resize_vertical": ("resize_vertical.svg", 14, 14, 28),
        "resize_fdiag": ("corner_resize_a.svg", 14, 14, 28),
        "resize_bdiag": ("corner_resize_b.svg", 14, 14, 28),
        "resize_diag_f": ("corner_resize_a.svg", 14, 14, 28),
        "resize_diag_b": ("corner_resize_b.svg", 14, 14, 28),
        "resize_ne": ("corner_resize_b.svg", 14, 14, 28),
        "resize_sw": ("corner_resize_b.svg", 14, 14, 28),
        "resize_nw": ("corner_resize_a.svg", 14, 14, 28),
        "resize_se": ("corner_resize_a.svg", 14, 14, 28),
        "resize_n": ("resize_vertical.svg", 14, 14, 28),
        "resize_s": ("resize_vertical.svg", 14, 14, 28),
        "resize_e": ("resize_horizontal.svg", 14, 14, 28),
        "resize_w": ("resize_horizontal.svg", 14, 14, 28),
    })
    svg._CURSOR_CACHE.clear()
    fcp._CURSOR_ASSET_OVERRIDES.update(svg._CURSOR_ASSET_MAP)
    if hasattr(svg, "_HAND_FILE_REDIRECTS"):
        svg._HAND_FILE_REDIRECTS.update({
            "hand_open.svg": "mouse_cursor.svg",
            "hand_closed.svg": "move_cursor.svg",
            "hand_pointer.svg": "mouse_cursor.svg",
            "rotate_cursor.svg": "rotate.svg",
        })

    original_set_cursor = edw.EngineeringCanvas.setCursor

    def set_cursor(self, cursor) -> None:
        kind = _native_kind(cursor)
        if kind is not None:
            try:
                original_set_cursor(self, svg.project_cursor(kind))
                self._svg_cursor_kind = kind
                return
            except Exception:
                pass
        original_set_cursor(self, cursor)

    edw.EngineeringCanvas.setCursor = set_cursor
    edw.EngineeringCanvas._engineering_native_cursor_lock_patch = PATCH_VERSION

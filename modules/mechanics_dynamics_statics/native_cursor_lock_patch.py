"""Lock native Qt cursors to the Engineering Tools cursor system.

Several older patches and base handlers still call ``setCursor`` or
``unsetCursor`` with native Qt cursor shapes such as OpenHandCursor,
ClosedHandCursor, and Size*Cursor. This patch runs last and intercepts those
calls on both engineering canvases so drag, resize, rotate, and move never fall
back to Windows cursors.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

PATCH_VERSION = "engineering-native-cursor-lock-2026-07-01-b"

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


def _install_for_canvas_class(canvas_cls, svg) -> None:
    if getattr(canvas_cls, "_native_cursor_lock_class_patch", "") == PATCH_VERSION:
        return
    original_set_cursor = canvas_cls.setCursor
    original_unset_cursor = canvas_cls.unsetCursor

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

    def unset_cursor(self) -> None:
        try:
            original_set_cursor(self, svg.project_cursor("default"))
            self._svg_cursor_kind = "default"
            return
        except Exception:
            original_unset_cursor(self)

    canvas_cls.setCursor = set_cursor
    canvas_cls.unsetCursor = unset_cursor
    canvas_cls._native_cursor_lock_class_patch = PATCH_VERSION


def apply_native_cursor_lock_patch() -> None:
    from . import final_cursor_properties_textbar_patch as fcp
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw
    from src.engineers_tools.app import module_window as mw

    if getattr(edw.EngineeringCanvas, "_engineering_native_cursor_lock_patch", "") == PATCH_VERSION:
        return

    cursor_map = {
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
    }
    svg._CURSOR_ASSET_MAP.update(cursor_map)
    svg._CURSOR_CACHE.clear()
    fcp._CURSOR_ASSET_OVERRIDES.update(cursor_map)
    if hasattr(svg, "_HAND_FILE_REDIRECTS"):
        svg._HAND_FILE_REDIRECTS.update({
            "hand_open.svg": "mouse_cursor.svg",
            "hand_closed.svg": "move_cursor.svg",
            "hand_pointer.svg": "mouse_cursor.svg",
            "rotate_cursor.svg": "rotate.svg",
        })

    _install_for_canvas_class(mw.GridCanvas, svg)
    _install_for_canvas_class(edw.EngineeringCanvas, svg)
    edw.EngineeringCanvas._engineering_native_cursor_lock_patch = PATCH_VERSION

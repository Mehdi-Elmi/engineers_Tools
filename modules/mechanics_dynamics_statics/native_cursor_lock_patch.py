"""Lock native Qt cursors to the Engineering Tools cursor system.

Several older patches and base handlers still call ``setCursor``,
``unsetCursor`` or ``QApplication.setOverrideCursor`` with native Qt cursor
shapes such as OpenHandCursor, ClosedHandCursor, and Size*Cursor. This patch
runs last and maps those native cursors to the project's SVG cursor language.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QWidget

PATCH_VERSION = "engineering-native-cursor-lock-2026-07-01-d"

_NATIVE_SHAPE_TO_KIND = {
    Qt.CursorShape.OpenHandCursor: "rotate",
    Qt.CursorShape.ClosedHandCursor: "move_drag",
    Qt.CursorShape.SizeAllCursor: "move_drag",
    Qt.CursorShape.SizeHorCursor: "resize_horizontal",
    Qt.CursorShape.SizeVerCursor: "resize_vertical",
    Qt.CursorShape.SizeFDiagCursor: "resize_fdiag",
    Qt.CursorShape.SizeBDiagCursor: "resize_bdiag",
    Qt.CursorShape.CrossCursor: "rotate",
    Qt.CursorShape.ArrowCursor: "default",
}

_ACTION_TO_KIND = {
    "move": "move_drag",
    "rotate": "rotate_drag",
    "resize_n": "resize_n",
    "resize_s": "resize_s",
    "resize_e": "resize_e",
    "resize_w": "resize_w",
    "resize_ne": "resize_ne",
    "resize_sw": "resize_sw",
    "resize_nw": "resize_nw",
    "resize_se": "resize_se",
}


def _shape(cursor):
    if isinstance(cursor, Qt.CursorShape):
        return cursor
    if isinstance(cursor, QCursor):
        try:
            return cursor.shape()
        except Exception:
            return None
    return None


def _native_kind(cursor, widget=None) -> str | None:
    shape = _shape(cursor)
    action = str(getattr(widget, "_drag_action", "") or "") if widget is not None else ""
    if action in _ACTION_TO_KIND and shape in {
        Qt.CursorShape.OpenHandCursor,
        Qt.CursorShape.ClosedHandCursor,
        Qt.CursorShape.SizeAllCursor,
        Qt.CursorShape.SizeHorCursor,
        Qt.CursorShape.SizeVerCursor,
        Qt.CursorShape.SizeFDiagCursor,
        Qt.CursorShape.SizeBDiagCursor,
    }:
        return _ACTION_TO_KIND[action]
    return _NATIVE_SHAPE_TO_KIND.get(shape)


def _project_cursor(svg, kind: str):
    try:
        return svg.project_cursor(kind)
    except Exception:
        return QCursor(Qt.CursorShape.ArrowCursor)


def _install_for_widget_class(widget_cls, svg) -> None:
    if getattr(widget_cls, "_native_cursor_lock_class_patch", "") == PATCH_VERSION:
        return
    original_set_cursor = widget_cls.setCursor
    original_unset_cursor = widget_cls.unsetCursor

    def set_cursor(self, cursor) -> None:
        kind = _native_kind(cursor, self)
        if kind is not None:
            original_set_cursor(self, _project_cursor(svg, kind))
            self._svg_cursor_kind = kind
            return
        original_set_cursor(self, cursor)

    def unset_cursor(self) -> None:
        original_set_cursor(self, _project_cursor(svg, "default"))
        self._svg_cursor_kind = "default"

    widget_cls.setCursor = set_cursor
    widget_cls.unsetCursor = unset_cursor
    widget_cls._native_cursor_lock_class_patch = PATCH_VERSION


def _install_override_cursor_lock(svg) -> None:
    if getattr(QApplication, "_engineering_override_cursor_lock_patch", "") == PATCH_VERSION:
        return
    original_set_override = QApplication.setOverrideCursor

    def set_override_cursor(cursor) -> None:
        kind = _native_kind(cursor)
        if kind is not None:
            original_set_override(_project_cursor(svg, kind))
            return
        original_set_override(cursor)

    QApplication.setOverrideCursor = staticmethod(set_override_cursor)
    QApplication._engineering_override_cursor_lock_patch = PATCH_VERSION


def apply_native_cursor_lock_patch() -> None:
    from . import final_cursor_properties_textbar_patch as fcp
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw
    from src.engineers_tools.app import module_window as mw

    if getattr(edw.EngineeringCanvas, "_engineering_native_cursor_lock_patch", "") == PATCH_VERSION:
        return

    cursor_map = {
        "default": ("mouse_cursor.svg", 3, 3, 24),
        "select": ("mouse_cursor.svg", 3, 3, 24),
        "pointer": ("mouse_cursor.svg", 3, 3, 24),
        "hand_open": ("mouse_cursor.svg", 3, 3, 24),
        "hand_closed": ("move_cursor.svg", 14, 14, 28),
        "pan_open": ("mouse_cursor.svg", 3, 3, 24),
        "pan_closed": ("move_cursor.svg", 14, 14, 28),
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
    hand_redirects = {
        "hand_open.svg": "mouse_cursor.svg",
        "hand_closed.svg": "move_cursor.svg",
        "hand_pointer.svg": "mouse_cursor.svg",
        "rotate_cursor.svg": "rotate.svg",
    }
    if hasattr(svg, "_HAND_FILE_REDIRECTS"):
        svg._HAND_FILE_REDIRECTS.update(hand_redirects)
    if hasattr(fcp, "_HAND_FILE_REDIRECTS"):
        fcp._HAND_FILE_REDIRECTS.update(hand_redirects)

    _install_for_widget_class(QWidget, svg)
    _install_for_widget_class(mw.GridCanvas, svg)
    _install_for_widget_class(edw.EngineeringCanvas, svg)
    _install_override_cursor_lock(svg)
    edw.EngineeringCanvas._engineering_native_cursor_lock_patch = PATCH_VERSION

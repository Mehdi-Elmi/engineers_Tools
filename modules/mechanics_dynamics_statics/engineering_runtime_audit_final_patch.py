"""Final runtime audit and cursor guard for Engineering Design Tools.

The Text color palette is now built by ui_text_tool_runtime_fix_patch.py only.
This final patch no longer creates any color control, so the toolbar cannot show
two different color palettes.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QWidget

PATCH_VERSION = "engineering-runtime-audit-final-2026-07-01-e"

_CURSOR_SIZE = 28
_CURSOR_MAP = {
    "default": ("mouse_cursor.svg", 3, 3, 24),
    "select": ("mouse_cursor.svg", 3, 3, 24),
    "hand_open": ("mouse_cursor.svg", 3, 3, 24),
    "hand_closed": ("move_cursor.svg", 14, 14, _CURSOR_SIZE),
    "pan_open": ("mouse_cursor.svg", 3, 3, 24),
    "pan_closed": ("move_cursor.svg", 14, 14, _CURSOR_SIZE),
    "move": ("move_cursor.svg", 14, 14, _CURSOR_SIZE),
    "move_drag": ("move_cursor.svg", 14, 14, _CURSOR_SIZE),
    "rotate": ("rotate.svg", 14, 14, _CURSOR_SIZE),
    "rotate_drag": ("rotate.svg", 14, 14, _CURSOR_SIZE),
    "resize_n": ("resize_vertical.svg", 14, 14, _CURSOR_SIZE),
    "resize_s": ("resize_vertical.svg", 14, 14, _CURSOR_SIZE),
    "resize_e": ("resize_horizontal.svg", 14, 14, _CURSOR_SIZE),
    "resize_w": ("resize_horizontal.svg", 14, 14, _CURSOR_SIZE),
    "resize_ne": ("corner_resize_b.svg", 14, 14, _CURSOR_SIZE),
    "resize_sw": ("corner_resize_b.svg", 14, 14, _CURSOR_SIZE),
    "resize_nw": ("corner_resize_a.svg", 14, 14, _CURSOR_SIZE),
    "resize_se": ("corner_resize_a.svg", 14, 14, _CURSOR_SIZE),
    "resize_horizontal": ("resize_horizontal.svg", 14, 14, _CURSOR_SIZE),
    "resize_vertical": ("resize_vertical.svg", 14, 14, _CURSOR_SIZE),
    "resize_diag_f": ("corner_resize_a.svg", 14, 14, _CURSOR_SIZE),
    "resize_diag_b": ("corner_resize_b.svg", 14, 14, _CURSOR_SIZE),
    "resize_fdiag": ("corner_resize_a.svg", 14, 14, _CURSOR_SIZE),
    "resize_bdiag": ("corner_resize_b.svg", 14, 14, _CURSOR_SIZE),
}
_ACTION_TO_CURSOR = {
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
_KNOWN_LOWER_TEXT_BARS = {
    "textsubbar",
    "texttoolbar",
    "texttoolbox",
    "floatingtextbar",
    "lowertextbar",
}
_OLD_COLOR_CONTROLS = {
    "textcolorbutton",
    "inlinecolorpalette",
    "inlinecolorpaletteholder",
    "inlineaddcolorbutton",
    "runtimeauditcolorpalette",
    "runtimeauditcolorpaletteholder",
    "runtimeauditaddcolorbutton",
    "textcolorpalette",
    "textinlinepalette",
    "textcolorswatchpalette",
}


def _is_inside(widget: QWidget, parent: QWidget | None) -> bool:
    current = widget.parentWidget()
    while current is not None:
        if current is parent:
            return True
        current = current.parentWidget()
    return False


def _apply_cursor_maps(svg, fcp=None) -> None:
    svg._CURSOR_ASSET_MAP.update(_CURSOR_MAP)
    if hasattr(svg, "_HAND_FILE_REDIRECTS"):
        svg._HAND_FILE_REDIRECTS.update({
            "hand_open.svg": "mouse_cursor.svg",
            "hand_closed.svg": "move_cursor.svg",
            "hand_pointer.svg": "mouse_cursor.svg",
            "rotate_cursor.svg": "rotate.svg",
        })
    svg._CURSOR_CACHE.clear()
    if fcp is not None:
        if hasattr(fcp, "_CURSOR_ASSET_OVERRIDES"):
            fcp._CURSOR_ASSET_OVERRIDES.update(_CURSOR_MAP)
        if hasattr(fcp, "_HAND_FILE_REDIRECTS"):
            fcp._HAND_FILE_REDIRECTS.update({
                "hand_open.svg": "mouse_cursor.svg",
                "hand_closed.svg": "move_cursor.svg",
                "hand_pointer.svg": "mouse_cursor.svg",
                "rotate_cursor.svg": "rotate.svg",
            })


def _set_cursor(widget: QWidget, svg, kind: str) -> None:
    kind = kind or "default"
    try:
        setter = getattr(svg, "_set_cursor_kind", None)
        if callable(setter):
            setter(widget, kind)
        else:
            widget.setCursor(svg.project_cursor(kind))
    except Exception:
        if kind.startswith("rotate"):
            widget.setCursor(Qt.CursorShape.CrossCursor)
        elif kind.startswith("move"):
            widget.setCursor(Qt.CursorShape.SizeAllCursor)
        elif kind.startswith("resize"):
            widget.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            widget.setCursor(Qt.CursorShape.ArrowCursor)


def _cursor_from_event(canvas, event=None) -> str:
    action = getattr(canvas, "_drag_action", None)
    if str(action) in _ACTION_TO_CURSOR:
        return _ACTION_TO_CURSOR[str(action)]
    if event is None:
        return "default"
    try:
        point = canvas._to_canvas_point(event.position())
        _index, hover = canvas._hit_test_object(point)
        if str(hover) in _ACTION_TO_CURSOR:
            return _ACTION_TO_CURSOR[str(hover)]
    except Exception:
        pass
    return "default"


def _patch_canvas_cursors(edw, svg) -> None:
    canvas_cls = getattr(edw, "EngineeringCanvas", None)
    if canvas_cls is None or getattr(canvas_cls, "_runtime_audit_cursor_patch", "") == PATCH_VERSION:
        return

    old_press = canvas_cls.mousePressEvent
    old_move = canvas_cls.mouseMoveEvent
    old_release = canvas_cls.mouseReleaseEvent
    old_leave = canvas_cls.leaveEvent

    def mouse_press(self, event) -> None:
        old_press(self, event)
        kind = _cursor_from_event(self, event)
        _set_cursor(self, svg, kind)
        QTimer.singleShot(0, lambda c=self, k=kind: _set_cursor(c, svg, k))

    def mouse_move(self, event) -> None:
        old_move(self, event)
        kind = _cursor_from_event(self, event)
        _set_cursor(self, svg, kind)
        QTimer.singleShot(0, lambda c=self, k=kind: _set_cursor(c, svg, k))

    def mouse_release(self, event) -> None:
        old_release(self, event)
        kind = _cursor_from_event(self, event)
        _set_cursor(self, svg, kind)
        QTimer.singleShot(0, lambda c=self, k=kind: _set_cursor(c, svg, k))

    def leave_event(self, event) -> None:
        old_leave(self, event)
        _set_cursor(self, svg, "default")

    canvas_cls.mousePressEvent = mouse_press
    canvas_cls.mouseMoveEvent = mouse_move
    canvas_cls.mouseReleaseEvent = mouse_release
    canvas_cls.leaveEvent = leave_event
    canvas_cls._runtime_audit_cursor_patch = PATCH_VERSION


def _remove_widget(widget: QWidget | None) -> None:
    if widget is None:
        return
    widget.hide()
    widget.setParent(None)
    widget.deleteLater()


def _cleanup_old_color_controls(root: QWidget | None) -> None:
    if root is None:
        return
    for widget in list(root.findChildren(QWidget)):
        name = (widget.objectName() or "").lower()
        if name in _OLD_COLOR_CONTROLS or widget.property("runtimeTextColorControl") and name.startswith("runtimeaudit"):
            _remove_widget(widget)


def _cleanup_lower_text_bars(root: QWidget | None) -> None:
    if root is None:
        return
    command_bar = root.findChild(QWidget, "CommandBar")
    for widget in root.findChildren(QWidget):
        name = (widget.objectName() or "").lower()
        if name == "canvastexteditor":
            continue
        if name == "inlinetextbar":
            if command_bar is not None and not _is_inside(widget, command_bar):
                widget.hide()
            continue
        if name in _KNOWN_LOWER_TEXT_BARS:
            widget.hide()
            continue
        if isinstance(widget, QFrame) and name.startswith("text") and command_bar is not None and not _is_inside(widget, command_bar):
            widget.hide()


def _style_text_bar(root: QWidget | None) -> None:
    if root is None:
        return
    bar = root.findChild(QWidget, "InlineTextBar")
    if bar is None:
        return
    bar.setMinimumWidth(max(bar.minimumWidth(), 960))
    bar.setFixedHeight(max(bar.height(), 52))


def _reapply_visible_runtime(root: QWidget | None) -> None:
    _cleanup_lower_text_bars(root)
    _cleanup_old_color_controls(root)
    _style_text_bar(root)


def apply_engineering_runtime_audit_final_patch() -> None:
    from . import final_cursor_properties_textbar_patch as fcp
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_runtime_audit_final_patch", "") == PATCH_VERSION:
        return

    _apply_cursor_maps(svg, fcp)
    _patch_canvas_cursors(edw, svg)
    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        logging.info("engineering_runtime_audit_final_patch: installed version=%s", PATCH_VERSION)
        _apply_cursor_maps(svg, fcp)
        _reapply_visible_runtime(self)
        for delay in (0, 80, 250, 700, 1500, 2600):
            QTimer.singleShot(delay, lambda root=self: _reapply_visible_runtime(root))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_runtime_audit_final_patch = PATCH_VERSION
    logging.info("engineering_runtime_audit_final_patch: class patch installed version=%s", PATCH_VERSION)

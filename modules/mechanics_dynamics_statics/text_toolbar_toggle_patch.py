"""Legacy lower Text toolbar cleanup and runtime Text wiring.

This module does not create a lower Text toolbar. It removes every legacy Text
bar outside the top CommandBar, keeps Resize/Rotate cursor sizes moderate, and
wires the Start Bar Text button directly to Text Box creation mode.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QWidget

PATCH_VERSION = "engineering-text-toolbar-cleanup-2026-07-01-c"
CURSOR_SIZE = 28


def _inside(widget: QWidget, parent: QWidget | None) -> bool:
    current = widget
    while current is not None:
        if current is parent:
            return True
        current = current.parentWidget()
    return False


def _remove(widget: QWidget) -> None:
    widget.hide()
    widget.setParent(None)
    widget.deleteLater()


def remove_legacy_textbars(root: QWidget | None) -> None:
    if root is None:
        return
    command_bar = root.findChild(QWidget, "CommandBar")
    for widget in root.findChildren(QWidget):
        name = (widget.objectName() or "").lower()
        if name == "canvastexteditor":
            continue
        if name == "inlinetextbar" and not _inside(widget, command_bar):
            _remove(widget)
            continue
        if name in {"textsubbar", "texttoolbar", "texttoolbox", "floatingtextbar"}:
            _remove(widget)
            continue
        if isinstance(widget, QFrame) and name.startswith("text") and not _inside(widget, command_bar):
            _remove(widget)
    start_bar = getattr(root, "_start_bar_widget", None)
    if start_bar is not None:
        widget = getattr(start_bar, "_text_toolbar_widget", None)
        if widget is not None and not _inside(widget, command_bar):
            _remove(widget)
            start_bar._text_toolbar_widget = None


def apply_runtime_cursor_size() -> None:
    try:
        from . import final_cursor_properties_textbar_patch as fcp
        from . import svg_cursor_assets_activation_patch as svg
    except Exception:
        return
    mapping = {
        "rotate": ("rotate.svg", 14, 14, CURSOR_SIZE),
        "rotate_drag": ("rotate.svg", 14, 14, CURSOR_SIZE),
        "resize_n": ("resize_vertical.svg", 14, 14, CURSOR_SIZE),
        "resize_s": ("resize_vertical.svg", 14, 14, CURSOR_SIZE),
        "resize_e": ("resize_horizontal.svg", 14, 14, CURSOR_SIZE),
        "resize_w": ("resize_horizontal.svg", 14, 14, CURSOR_SIZE),
        "resize_ne": ("corner_resize_b.svg", 14, 14, CURSOR_SIZE),
        "resize_sw": ("corner_resize_b.svg", 14, 14, CURSOR_SIZE),
        "resize_nw": ("corner_resize_a.svg", 14, 14, CURSOR_SIZE),
        "resize_se": ("corner_resize_a.svg", 14, 14, CURSOR_SIZE),
        "resize_horizontal": ("resize_horizontal.svg", 14, 14, CURSOR_SIZE),
        "resize_vertical": ("resize_vertical.svg", 14, 14, CURSOR_SIZE),
        "resize_diag_f": ("corner_resize_a.svg", 14, 14, CURSOR_SIZE),
        "resize_diag_b": ("corner_resize_b.svg", 14, 14, CURSOR_SIZE),
        "resize_fdiag": ("corner_resize_a.svg", 14, 14, CURSOR_SIZE),
        "resize_bdiag": ("corner_resize_b.svg", 14, 14, CURSOR_SIZE),
    }
    svg._CURSOR_ASSET_MAP.update(mapping)
    svg._CURSOR_CACHE.clear()
    if hasattr(fcp, "_CURSOR_ASSET_OVERRIDES"):
        fcp._CURSOR_ASSET_OVERRIDES.update(mapping)


def wire_text_button(root: QWidget | None) -> None:
    if root is None:
        return
    start_bar = getattr(root, "_start_bar_widget", None)
    if start_bar is None:
        return
    button = getattr(start_bar, "_buttons", {}).get("text")
    if button is None:
        return
    try:
        from . import ui_text_tool_final_patch as text_final
    except Exception:
        return

    def activate() -> None:
        setter = getattr(start_bar, "_set_text_toolbar_visible", None)
        if callable(setter):
            setter(True, emit=False)
        remove_legacy_textbars(root)
        text_final._activate_text_tool(root)

    if getattr(button, "_text_direct_wire", False):
        return
    button.clicked.connect(lambda checked=False: activate())
    button._text_direct_wire = True
    button.setToolTip("Add Text: click canvas for 5×7 cm box, or drag to draw a custom text box")


def apply_text_toolbar_toggle_patch() -> None:
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_toggle_patch", "") == PATCH_VERSION:
        return

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        apply_runtime_cursor_size()
        remove_legacy_textbars(self)
        wire_text_button(self)
        for delay in (0, 80, 250, 700, 1500):
            QTimer.singleShot(delay, lambda root=self: (apply_runtime_cursor_size(), remove_legacy_textbars(root), wire_text_button(root)))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_toggle_patch = PATCH_VERSION

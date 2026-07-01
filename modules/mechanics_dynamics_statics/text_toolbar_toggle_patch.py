"""Legacy lower Text toolbar cleanup hook.

This module intentionally does not create any Text toolbar. It only removes
legacy Text bars that are outside the top CommandBar.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QWidget

PATCH_VERSION = "engineering-text-toolbar-cleanup-2026-07-01-b"


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


def apply_text_toolbar_toggle_patch() -> None:
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_toggle_patch", "") == PATCH_VERSION:
        return

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        for delay in (0, 80, 250, 700, 1500):
            QTimer.singleShot(delay, lambda root=self: remove_legacy_textbars(root))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_toggle_patch = PATCH_VERSION

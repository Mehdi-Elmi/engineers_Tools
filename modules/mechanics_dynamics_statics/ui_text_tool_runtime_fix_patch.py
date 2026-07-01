"""Runtime fix for the final Text tool UI.

This patch runs after ``ui_text_tool_final_patch``. It deliberately avoids
creating another text system. Instead it tightens the active system so the old
lower TextSubBar is removed, the top text controls are readable, Text activation
is reliable, and Rotate/Resize cursors are smaller while Move stays unchanged.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QPushButton, QSizePolicy, QSpinBox, QWidget

PATCH_VERSION = "engineering-ui-text-runtime-fix-2026-07-01-a"
_SMALL_CURSOR_OVERRIDES = {
    "rotate": ("rotate.svg", 14, 14, 28),
    "rotate_drag": ("rotate.svg", 14, 14, 28),
    "resize_n": ("resize_vertical.svg", 14, 14, 28),
    "resize_s": ("resize_vertical.svg", 14, 14, 28),
    "resize_e": ("resize_horizontal.svg", 14, 14, 28),
    "resize_w": ("resize_horizontal.svg", 14, 14, 28),
    "resize_ne": ("corner_resize_b.svg", 14, 14, 28),
    "resize_sw": ("corner_resize_b.svg", 14, 14, 28),
    "resize_nw": ("corner_resize_a.svg", 14, 14, 28),
    "resize_se": ("corner_resize_a.svg", 14, 14, 28),
    "resize_horizontal": ("resize_horizontal.svg", 14, 14, 28),
    "resize_vertical": ("resize_vertical.svg", 14, 14, 28),
    "resize_diag_f": ("corner_resize_a.svg", 14, 14, 28),
    "resize_diag_b": ("corner_resize_b.svg", 14, 14, 28),
    "resize_fdiag": ("corner_resize_a.svg", 14, 14, 28),
    "resize_bdiag": ("corner_resize_b.svg", 14, 14, 28),
}


def _font(widget: QWidget, size: int = 11) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(False)
    widget.setFont(font)


def _remove_lower_text_bars(root: QWidget | None) -> None:
    if root is None:
        return
    command_bar = root.findChild(QWidget, "CommandBar")
    for child in root.findChildren(QWidget):
        name = child.objectName()
        if name == "TextSubBar":
            child.hide()
            child.setParent(None)
            child.deleteLater()
            continue
        if name == "InlineTextBar" and command_bar is not None:
            parent = child.parentWidget()
            if parent is not command_bar:
                child.hide()
                child.setParent(None)
                child.deleteLater()
    start_bar = getattr(root, "_start_bar_widget", None)
    if start_bar is not None:
        legacy = getattr(start_bar, "_text_toolbar_widget", None)
        if legacy is not None:
            legacy.hide()
            legacy.setParent(None)
            legacy.deleteLater()
            start_bar._text_toolbar_widget = None


def _style_inline_text_bar(bar: QWidget | None) -> None:
    if bar is None:
        return
    bar.setObjectName("InlineTextBar")
    bar.setProperty("runtimeFix", PATCH_VERSION)
    bar.setFixedHeight(42)
    bar.setMinimumWidth(720)
    bar.setMaximumWidth(920)
    bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    bar.setStyleSheet(
        "QFrame#InlineTextBar{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.52 #eef8ff,stop:1 #fff1c8);border:1px solid #7f95b2;border-radius:13px;}"
        "QComboBox{background:#fffdf7;border:1px solid #b98920;border-radius:9px;color:#132238;font-family:'Times New Roman';font-size:12px;font-weight:800;font-style:normal;padding:1px 35px 1px 9px;}"
        "QComboBox::drop-down{width:32px;border:0;subcontrol-origin:border;subcontrol-position:center right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);border-top-right-radius:8px;border-bottom-right-radius:8px;}"
        "QSpinBox{background:#fffdf7;border:1px solid #b98920;border-radius:9px;color:#132238;font-family:'Times New Roman';font-size:12px;font-weight:800;font-style:normal;padding:1px 34px 1px 8px;}"
        "QPushButton{background:#ffffff;border:1px solid #9fb0c5;border-radius:9px;color:#132238;font-family:'Times New Roman';font-size:11px;font-weight:800;font-style:normal;}"
        "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"
        "QPushButton:checked{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffc35a,stop:1 #f18a2a);border-color:#7e5b10;color:#102238;padding-top:2px;}"
        "QPushButton:pressed{background:#d9e9f7;padding-top:2px;}"
    )
    layout = bar.layout()
    if isinstance(layout, QHBoxLayout):
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(6)
    combos = bar.findChildren(QComboBox)
    for index, combo in enumerate(combos):
        combo.setFixedSize(202 if index == 0 else 92, 32)
        combo.setToolTip("Font family" if index == 0 else combo.toolTip())
        _font(combo, 12)
    for spin in bar.findChildren(QSpinBox):
        spin.setFixedSize(118, 32)
        spin.setToolTip("Font size")
        _font(spin, 12)
    for button in bar.findChildren(QPushButton):
        if button.toolTip():
            button.setStatusTip(button.toolTip())
            button.setToolTipDuration(5000)
        _font(button, 11)
        width = max(button.width(), 38 if len(button.text()) <= 2 else 54)
        button.setFixedSize(width, 32)


def _patch_start_bar(sb, text_final) -> None:
    if getattr(sb.StartBar, "_engineering_text_runtime_fix", "") == PATCH_VERSION:
        return
    old_ensure = sb.StartBar._ensure_text_toolbar
    old_set_visible = sb.StartBar._set_text_toolbar_visible
    old_handle = sb.StartBar._handle_tool_click
    old_show = sb.StartBar.showEvent
    old_resize = sb.StartBar.resizeEvent

    def ensure_text_toolbar(self):
        root = self.window()
        _remove_lower_text_bars(root)
        bar = old_ensure(self)
        _style_inline_text_bar(bar)
        _remove_lower_text_bars(root)
        return bar

    def set_text_toolbar_visible(self, visible: bool = True, emit: bool = True) -> None:
        bar = ensure_text_toolbar(self)
        if bar is not None:
            bar.show()
        popup = getattr(self, "_popup", None)
        if popup is not None:
            popup.close()
        self._text_toolbar_enabled = True
        _remove_lower_text_bars(self.window())
        if emit:
            self.tool_requested.emit("text_on")
            self._set_host_status("Text tool ready")
            text_final._activate_text_tool(self.window())

    def handle_tool_click(self, key: str) -> None:
        if key == "text":
            set_text_toolbar_visible(self, True, True)
            return
        old_handle(self, key)
        _remove_lower_text_bars(self.window())

    def show_event(self, event) -> None:
        old_show(self, event)
        QTimer.singleShot(0, lambda s=self: set_text_toolbar_visible(s, True, False))
        QTimer.singleShot(0, lambda s=self: _remove_lower_text_bars(s.window()))

    def resize_event(self, event) -> None:
        old_resize(self, event)
        _remove_lower_text_bars(self.window())

    sb.StartBar._ensure_text_toolbar = ensure_text_toolbar
    sb.StartBar._set_text_toolbar_visible = set_text_toolbar_visible
    sb.StartBar._show_text_toolbar = lambda self, key: set_text_toolbar_visible(self, True, True)
    sb.StartBar._handle_tool_click = handle_tool_click
    sb.StartBar.showEvent = show_event
    sb.StartBar.resizeEvent = resize_event
    sb.StartBar._engineering_text_runtime_fix = PATCH_VERSION


def apply_ui_text_tool_runtime_fix_patch() -> None:
    from . import final_cursor_properties_textbar_patch as fcp
    from . import svg_cursor_assets_activation_patch as svg
    from . import ui_text_tool_final_patch as text_final
    from . import workspace as edw
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_ui_text_runtime_fix_patch", "") == PATCH_VERSION:
        return

    svg._CURSOR_ASSET_MAP.update(_SMALL_CURSOR_OVERRIDES)
    svg._CURSOR_CACHE.clear()
    fcp._CURSOR_ASSET_OVERRIDES.update(_SMALL_CURSOR_OVERRIDES)
    _patch_start_bar(sb, text_final)

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _remove_lower_text_bars(self)
        start_bar = getattr(self, "_start_bar_widget", None)
        if start_bar is not None:
            QTimer.singleShot(0, lambda sb=start_bar: sb._set_text_toolbar_visible(True, emit=False))
            QTimer.singleShot(50, lambda root=self: _remove_lower_text_bars(root))
            QTimer.singleShot(250, lambda root=self: _remove_lower_text_bars(root))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_ui_text_runtime_fix_patch = PATCH_VERSION

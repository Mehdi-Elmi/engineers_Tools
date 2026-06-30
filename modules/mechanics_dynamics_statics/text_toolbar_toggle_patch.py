"""Make Start Bar Text a persistent toggle toolbar, not a popup."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QPushButton, QSpinBox

PATCH_VERSION = "engineering-text-toolbar-toggle-2026-06-30-a"


def _style_font(widget, size: int = 10) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setBold(True)
    font.setPointSize(size)
    widget.setFont(font)


def apply_text_toolbar_toggle_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_toggle_patch", "") == PATCH_VERSION:
        return

    old_click = sb.StartBar._handle_tool_click
    old_show = sb.StartBar.showEvent
    old_resize = sb.StartBar.resizeEvent
    old_ensure = sb.StartBar._ensure_canvas_hooks

    def position_bar(self) -> None:
        bar = getattr(self, "_text_toolbar_widget", None)
        if bar is None or bar.parentWidget() is None:
            return
        parent = bar.parentWidget()
        pos = parent.mapFromGlobal(self.mapToGlobal(QPoint(0, self.height() + 4)))
        width = min(900, max(430, parent.width() - max(pos.x(), 8) - 12))
        bar.setGeometry(max(6, pos.x()), max(6, pos.y()), width, 42)
        bar.raise_()

    def ensure_bar(self):
        bar = getattr(self, "_text_toolbar_widget", None)
        if bar is not None and bar.parentWidget() is not None:
            position_bar(self)
            return bar
        parent = self.parentWidget() or self.window()
        bar = QFrame(parent)
        bar.setObjectName("TextSubBar")
        bar.setFixedHeight(42)
        bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bar.setStyleSheet("QFrame#TextSubBar{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.52 #eef8ff,stop:1 #fff1c8);border:1px solid #8fa2bb;border-radius:12px;} QPushButton{background:#ffffff;border:1px solid #9fb0c5;border-radius:7px;color:#132238;} QComboBox{background:#ffffff;border:1px solid #9fb0c5;border-radius:7px;color:#132238;font-style:italic;font-weight:800;} QSpinBox{background:#fff9de;border:1px solid #b38621;border-radius:7px;color:#132238;font-weight:800;padding-right:22px;}")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(5)
        combo = QComboBox(); combo.addItems(list(getattr(svg, "FONT_CHOICES", ("Times New Roman", "Arial", "Cambria Math")))); combo.setCurrentText("Times New Roman"); combo.setFixedSize(148, 26); layout.addWidget(combo)
        size = QSpinBox(); size.setRange(1, 300); size.setValue(12); size.setSuffix(" pt"); size.setFixedSize(74, 26); layout.addWidget(size)
        for label, tip in (("B", "Bold"), ("I", "Italic"), ("bullet", "Bullet library"), ("1", "Numbering library"), ("AL", "Align left"), ("AC", "Align center"), ("AR", "Align right"), ("J", "Justify"), ("LS", "Line spacing"), ("LTR", "Left to right"), ("RTL", "Right to left"), ("SUM", "Math symbols")):
            button = QPushButton(label); button.setToolTip(tip); button.setFixedSize(38 if len(label) > 2 else 30, 26); button.setCursor(svg.project_cursor("hand_pointer")); _style_font(button, 9); layout.addWidget(button)
        layout.addStretch(1)
        bar.hide()
        self._text_toolbar_widget = bar
        self._text_toolbar_enabled = False
        position_bar(self)
        return bar

    def set_bar(self, visible: bool, emit: bool = True) -> None:
        bar = ensure_bar(self)
        self._text_toolbar_enabled = bool(visible)
        bar.setVisible(bool(visible))
        position_bar(self)
        button = getattr(self, "_buttons", {}).get("text")
        if button is not None:
            button.setCheckable(True)
            button.setChecked(bool(visible))
        if emit:
            self.tool_requested.emit("text_on" if visible else "text_off")
            self._set_host_status("Text environment on" if visible else "Text environment off")

    def click(self, key: str) -> None:
        if key == "text":
            if getattr(self, "_popup", None) is not None:
                self._popup.close()
            set_bar(self, not bool(getattr(self, "_text_toolbar_enabled", False)))
            return
        old_click(self, key)

    def show(self, event) -> None:
        old_show(self, event)
        set_bar(self, bool(getattr(self, "_text_toolbar_enabled", False)), emit=False)

    def resize(self, event) -> None:
        old_resize(self, event)
        position_bar(self)

    def ensure(self) -> None:
        old_ensure(self)
        position_bar(self)

    sb.StartBar._handle_tool_click = click
    sb.StartBar.showEvent = show
    sb.StartBar.resizeEvent = resize
    sb.StartBar._ensure_canvas_hooks = ensure
    sb.StartBar._ensure_text_toolbar = ensure_bar
    sb.StartBar._set_text_toolbar_visible = set_bar
    edw.EngineeringDesignWorkspace._engineering_text_toolbar_toggle_patch = PATCH_VERSION

"""Final text tool and cursor sizing patch.

This patch runs after the phase-2 UI refinements. It keeps the approved Move
cursor unchanged, brings Rotate/Resize back to a moderate size, removes the old
lower TextSubBar, and makes the top Text Bar the active text tool controller.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QFrame, QHBoxLayout, QPushButton, QSizePolicy, QSpinBox, QWidget

PATCH_VERSION = "engineering-ui-text-tool-final-2026-07-01-a"
FONT_CHOICES = ("Times New Roman",)
CURSOR_OVERRIDES = {
    "rotate": ("rotate.svg", 20, 20, 44),
    "rotate_drag": ("rotate.svg", 20, 20, 44),
    "resize_n": ("resize_vertical.svg", 22, 22, 44),
    "resize_s": ("resize_vertical.svg", 22, 22, 44),
    "resize_e": ("resize_horizontal.svg", 22, 22, 44),
    "resize_w": ("resize_horizontal.svg", 22, 22, 44),
    "resize_ne": ("corner_resize_b.svg", 22, 22, 44),
    "resize_sw": ("corner_resize_b.svg", 22, 22, 44),
    "resize_nw": ("corner_resize_a.svg", 22, 22, 44),
    "resize_se": ("corner_resize_a.svg", 22, 22, 44),
    "resize_horizontal": ("resize_horizontal.svg", 22, 22, 44),
    "resize_vertical": ("resize_vertical.svg", 22, 22, 44),
    "resize_diag_f": ("corner_resize_a.svg", 22, 22, 44),
    "resize_diag_b": ("corner_resize_b.svg", 22, 22, 44),
    "resize_fdiag": ("corner_resize_a.svg", 22, 22, 44),
    "resize_bdiag": ("corner_resize_b.svg", 22, 22, 44),
}
TEXT_BUTTONS = (
    ("B", "Bold", 34),
    ("I", "Italic", 34),
    ("•", "Bullet", 34),
    ("1.", "Numbering", 38),
    ("L", "Align left", 34),
    ("C", "Align center", 34),
    ("R", "Align right", 34),
    ("J", "Justify", 34),
    ("LS", "Line spacing", 44),
    ("LTR", "Left to right", 50),
    ("RTL", "Right to left", 50),
    ("Σ", "Math symbols", 36),
)


def _asset_url(svg, name: str) -> str:
    return svg._asset_url(name) if hasattr(svg, "_asset_url") else ""


def _font(widget: QWidget, size: int = 11) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(False)
    widget.setFont(font)


def _style_text_spin(svg, spin: QSpinBox | QDoubleSpinBox) -> None:
    up = _asset_url(svg, "spin_up.svg")
    down = _asset_url(svg, "spin_down.svg")
    spin.setFixedHeight(30)
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffdf6;border:1px solid #c29122;border-radius:9px;color:#132238;font-family:'Times New Roman';font-size:11px;font-weight:800;font-style:normal;padding:1px 34px 1px 8px;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{width:31px;border:0;subcontrol-origin:border;subcontrol-position:top right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);border-top-right-radius:8px;}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{width:31px;border:0;subcontrol-origin:border;subcontrol-position:bottom right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);border-bottom-right-radius:8px;}"
        f"QSpinBox::up-arrow,QDoubleSpinBox::up-arrow{{image:url({up});width:20px;height:12px;}}"
        f"QSpinBox::down-arrow,QDoubleSpinBox::down-arrow{{image:url({down});width:20px;height:12px;}}"
    )


def _style_text_combo(svg, combo: QComboBox) -> None:
    arrow = _asset_url(svg, "combo_down.svg")
    combo.setFixedHeight(30)
    combo.setStyleSheet(
        "QComboBox{background:#ffffff;border:1px solid #9fb0c5;border-radius:9px;color:#132238;font-family:'Times New Roman';font-size:11px;font-weight:800;font-style:normal;padding:1px 35px 1px 9px;}"
        "QComboBox::drop-down{width:32px;border:0;subcontrol-origin:border;subcontrol-position:center right;background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);border-top-right-radius:8px;border-bottom-right-radius:8px;}"
        f"QComboBox::down-arrow{{image:url({arrow});width:20px;height:12px;}}"
    )


def _remove_legacy_text_subbars(root: QWidget | None) -> None:
    if root is None:
        return
    for bar in root.findChildren(QFrame, "TextSubBar"):
        bar.hide()
        bar.setParent(None)
        bar.deleteLater()
    start_bar = getattr(root, "_start_bar_widget", None)
    if start_bar is not None:
        legacy = getattr(start_bar, "_text_toolbar_widget", None)
        if legacy is not None and getattr(legacy, "objectName", lambda: "")() == "TextSubBar":
            legacy.hide()
            legacy.setParent(None)
            legacy.deleteLater()
            start_bar._text_toolbar_widget = None


def _activate_text_tool(window: QWidget | None) -> None:
    if window is None:
        return
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return
    canvas._text_tool_active = True
    canvas._text_box_origin = None
    canvas._text_box_preview = None
    canvas.setCursor(Qt.CursorShape.IBeamCursor)
    status = getattr(window, "_set_status", None)
    if callable(status):
        status("Text: click for 5x7 cm box, or drag to define box")


def _text_button(label: str, tooltip: str, width: int) -> QPushButton:
    button = QPushButton(label)
    button.setToolTip(tooltip)
    button.setStatusTip(tooltip)
    button.setFixedSize(width, 30)
    _font(button, 11)
    button.setStyleSheet("QPushButton{background:#fff;border:1px solid #9fb0c5;border-radius:9px;color:#132238;padding:0;}QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}QPushButton:pressed{background:#d9e9f7;padding-top:1px;}")
    return button


def _install_textbar(sb, svg) -> None:
    def make_textbar(self):
        window = self.window()
        if window is None:
            return None
        _remove_legacy_text_subbars(window)
        command_bar = window.findChild(QWidget, "CommandBar")
        if command_bar is None or command_bar.layout() is None:
            return None
        existing = command_bar.findChild(QFrame, "InlineTextBar")
        if existing is not None and existing.property("phase") != PATCH_VERSION:
            existing.hide()
            existing.setParent(None)
            existing.deleteLater()
            existing = None
        if existing is not None:
            existing.show()
            return existing
        bar = QFrame(command_bar)
        bar.setObjectName("InlineTextBar")
        bar.setProperty("phase", PATCH_VERSION)
        bar.setFixedHeight(38)
        bar.setMinimumWidth(760)
        bar.setMaximumWidth(1020)
        bar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bar.setStyleSheet("QFrame#InlineTextBar{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fff,stop:.52 #eef8ff,stop:1 #fff1c8);border:1px solid #8fa2bb;border-radius:13px;}")
        row = QHBoxLayout(bar)
        row.setContentsMargins(10, 4, 10, 4)
        row.setSpacing(6)
        combo = QComboBox()
        combo.setToolTip("Font family")
        combo.addItems(list(FONT_CHOICES))
        combo.setCurrentText("Times New Roman")
        combo.setFixedSize(198, 30)
        _style_text_combo(svg, combo)
        row.addWidget(combo)
        size = QSpinBox()
        size.setToolTip("Font size")
        size.setRange(1, 300)
        size.setValue(12)
        size.setSuffix(" pt")
        size.setFixedSize(116, 30)
        _style_text_spin(svg, size)
        row.addWidget(size)
        for label, tooltip, width in TEXT_BUTTONS:
            row.addWidget(_text_button(label, tooltip, width))
        command_bar.layout().insertWidget(max(0, command_bar.layout().count() - 1), bar, 0, Qt.AlignmentFlag.AlignVCenter)
        bar.show()
        _remove_legacy_text_subbars(window)
        return bar

    def set_visible(self, visible: bool = True, emit: bool = True) -> None:
        bar = make_textbar(self)
        if bar is not None:
            bar.show()
        popup = getattr(self, "_popup", None)
        if popup is not None:
            popup.close()
        _remove_legacy_text_subbars(self.window())
        self._text_toolbar_enabled = True
        if emit:
            self.tool_requested.emit("text_on")
            self._set_host_status("Text tool ready")
            _activate_text_tool(self.window())

    old_handle = sb.StartBar._handle_tool_click
    old_show = sb.StartBar.showEvent
    old_resize = sb.StartBar.resizeEvent

    def handle(self, key: str) -> None:
        if key == "text":
            set_visible(self, True, True)
            return
        old_handle(self, key)
        _remove_legacy_text_subbars(self.window())

    def show_event(self, event) -> None:
        old_show(self, event)
        QTimer.singleShot(0, lambda s=self: _remove_legacy_text_subbars(s.window()))
        QTimer.singleShot(0, lambda s=self: s._set_text_toolbar_visible(True, emit=False))

    def resize_event(self, event) -> None:
        old_resize(self, event)
        _remove_legacy_text_subbars(self.window())

    sb.StartBar._ensure_text_toolbar = make_textbar
    sb.StartBar._set_text_toolbar_visible = set_visible
    sb.StartBar._show_text_toolbar = lambda self, key: set_visible(self, True, True)
    sb.StartBar._handle_tool_click = handle
    sb.StartBar.showEvent = show_event
    sb.StartBar.resizeEvent = resize_event


def _install_canvas_text_tool(edw) -> None:
    if getattr(edw.EngineeringCanvas, "_text_tool_final_patch", "") == PATCH_VERSION:
        return
    old_press = edw.EngineeringCanvas.mousePressEvent
    old_move = edw.EngineeringCanvas.mouseMoveEvent
    old_release = edw.EngineeringCanvas.mouseReleaseEvent
    old_paint = edw.EngineeringCanvas.paintEvent

    def create_text_box(self, rect: QRectF, origin: QPointF) -> None:
        box = QRectF(rect).normalized()
        if box.width() < 10 or box.height() < 10:
            box = QRectF(origin.x(), origin.y(), 190.0, 265.0)
        if box.width() < 35:
            box.setWidth(35.0)
        if box.height() < 35:
            box.setHeight(35.0)
        self._push_undo()
        obj = edw.CanvasObject(path=Path("Text Box"), pixmap=QPixmap(), rect=box, name="Text Box")
        self.objects.append(obj)
        self._select_only(len(self.objects) - 1)
        self._last_action = "text"
        self._text_tool_active = False
        self._text_box_origin = None
        self._text_box_preview = None
        self._emit_object_changes()
        self.update()
        window = self.window()
        status = getattr(window, "_set_status", None)
        if callable(status):
            status("Text box created")

    def mouse_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, "_text_tool_active", False):
            point = self._to_canvas_point(event.position())
            self._text_box_origin = point
            self._text_box_preview = QRectF(point, point)
            self._drag_action = None
            self.update()
            event.accept()
            return
        old_press(self, event)

    def mouse_move(self, event) -> None:
        point = self._to_canvas_point(event.position())
        if getattr(self, "_text_tool_active", False) and getattr(self, "_text_box_origin", None) is not None:
            self.mouse_position_changed.emit(point.x(), point.y())
            self._text_box_preview = QRectF(self._text_box_origin, point).normalized()
            self.update()
            event.accept()
            return
        old_move(self, event)

    def mouse_release(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, "_text_tool_active", False) and getattr(self, "_text_box_origin", None) is not None:
            point = self._to_canvas_point(event.position())
            origin = self._text_box_origin
            create_text_box(self, QRectF(origin, point), origin)
            event.accept()
            return
        old_release(self, event)

    def paint_event(self, event) -> None:
        old_paint(self, event)
        preview = getattr(self, "_text_box_preview", None)
        if preview is None or preview.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._zoom, self._zoom)
        painter.translate(-self.width() / 2, -self.height() / 2)
        painter.setBrush(QColor(255, 196, 90, 34))
        painter.setPen(QPen(QColor("#ff8a35"), 1.4, Qt.PenStyle.DashLine))
        painter.drawRoundedRect(QRectF(preview).normalized(), 4, 4)
        painter.end()

    edw.EngineeringCanvas.mousePressEvent = mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    edw.EngineeringCanvas.paintEvent = paint_event
    edw.EngineeringCanvas._text_tool_final_patch = PATCH_VERSION


def apply_ui_text_tool_final_patch() -> None:
    from . import final_cursor_properties_textbar_patch as fcp
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_ui_text_tool_final_patch", "") == PATCH_VERSION:
        return

    svg._CURSOR_ASSET_MAP.update(CURSOR_OVERRIDES)
    svg._CURSOR_CACHE.clear()
    fcp._CURSOR_ASSET_OVERRIDES.update(CURSOR_OVERRIDES)
    _install_textbar(sb, svg)
    _install_canvas_text_tool(edw)

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _remove_legacy_text_subbars(self)
        start_bar = getattr(self, "_start_bar_widget", None)
        if start_bar is not None:
            QTimer.singleShot(0, lambda sb=start_bar: sb._set_text_toolbar_visible(True, emit=False))
            QTimer.singleShot(0, lambda root=self: _remove_legacy_text_subbars(root))
            QTimer.singleShot(150, lambda root=self: _remove_legacy_text_subbars(root))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_ui_text_tool_final_patch = PATCH_VERSION
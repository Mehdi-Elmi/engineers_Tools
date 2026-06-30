"""Final effective UI layer for SVG cursors, Start Bar icons, control arrows, and top Text Bar."""

from __future__ import annotations

from PySide6.QtCore import QObject, QEvent, QTimer, QRectF, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-final-cursor-properties-textbar-2026-06-30-c"

_TOOL_ICON_ASSETS = {
    "select": "select_edit_object.svg",
    "line": "line.svg",
    "vector": "vector.svg",
    "angle": "angle_moment.svg",
    "text": "text.svg",
    "grid": "grid.svg",
    "snap": "snap.svg",
    "unit": "unit.svg",
    "ruler": "ruler.svg",
    "zoom": "zoom.svg",
    "zoom_in": "zoom_in.svg",
    "zoom_out": "zoom_out.svg",
    "zoom_fit": "zoom_fit.svg",
}

_SPECIAL_CURSOR_WIDGET_NAMES = {
    "EngineeringCanvas",
    "GridCanvas",
    "_RulerOverlay",
    "_RulerCorner",
    "_GuideLine",
}


def _is_special_cursor_widget(widget: QWidget) -> bool:
    name = widget.__class__.__name__
    if name in _SPECIAL_CURSOR_WIDGET_NAMES:
        return True
    return widget.objectName() in {"EngineeringCanvas", "GridCanvas"}


def _cursor_kind(hover: str | None, action: str | None = None) -> str:
    mapping = {
        "move": "move",
        "rotate": "rotate",
        "resize_n": "resize_n",
        "resize_s": "resize_s",
        "resize_e": "resize_e",
        "resize_w": "resize_w",
        "resize_ne": "resize_ne",
        "resize_sw": "resize_sw",
        "resize_nw": "resize_nw",
        "resize_se": "resize_se",
    }
    return mapping.get(action or str(hover), "default")


def _force_svg_cursor_map(svg) -> None:
    svg._CURSOR_ASSET_MAP.update(
        {
            "default": ("mouse_cursor.svg", 3, 3, 24),
            "select": ("mouse_cursor.svg", 3, 3, 24),
            "pointer": ("mouse_cursor.svg", 3, 3, 24),
            "hand_pointer": ("mouse_cursor.svg", 3, 3, 24),
            "move": ("move_cursor.svg", 12, 12, 24),
            "rotate": ("rotate.svg", 12, 12, 24),
            "rotate_drag": ("rotate.svg", 12, 12, 24),
            "resize_h": ("resize_horizontal.svg", 12, 12, 24),
            "resize_v": ("resize_vertical.svg", 12, 12, 24),
            "resize_horizontal": ("resize_horizontal.svg", 12, 12, 24),
            "resize_vertical": ("resize_vertical.svg", 12, 12, 24),
            "resize_n": ("resize_vertical.svg", 12, 12, 24),
            "resize_s": ("resize_vertical.svg", 12, 12, 24),
            "resize_e": ("resize_horizontal.svg", 12, 12, 24),
            "resize_w": ("resize_horizontal.svg", 12, 12, 24),
            "resize_ne": ("corner_resize_b.svg", 12, 12, 24),
            "resize_sw": ("corner_resize_b.svg", 12, 12, 24),
            "resize_nw": ("corner_resize_a.svg", 12, 12, 24),
            "resize_se": ("corner_resize_a.svg", 12, 12, 24),
            "resize_diag_f": ("corner_resize_a.svg", 12, 12, 24),
            "resize_diag_b": ("corner_resize_b.svg", 12, 12, 24),
            "resize_fdiag": ("corner_resize_a.svg", 12, 12, 24),
            "resize_bdiag": ("corner_resize_b.svg", 12, 12, 24),
        }
    )
    svg._CURSOR_CACHE.clear()


class _EngineerCursorFilter(QObject):
    def __init__(self, workspace, svg) -> None:
        super().__init__(workspace)
        self._workspace = workspace
        self._svg = svg

    def _belongs_to_workspace(self, widget: QWidget) -> bool:
        current = widget
        while current is not None:
            if current is self._workspace:
                return True
            current = current.parentWidget() if hasattr(current, "parentWidget") else None
        return False

    def _style_control(self, widget: QWidget) -> None:
        try:
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                styler = getattr(self._svg, "_style_spin", None)
                if callable(styler):
                    styler(widget)
                return
            if isinstance(widget, QComboBox):
                arrow = self._svg._asset_url("combo_down.svg") if hasattr(self._svg, "_asset_url") else ""
                widget.setStyleSheet(
                    widget.styleSheet()
                    + " QComboBox::drop-down {width:24px; border:0; subcontrol-origin:padding; subcontrol-position:center right;}"
                    + f" QComboBox::down-arrow {{image:url({arrow}); width:20px; height:14px;}}"
                )
        except Exception:
            return

    def _restore_default(self, widget: QWidget) -> None:
        if _is_special_cursor_widget(widget):
            return
        try:
            widget.setCursor(self._svg.project_cursor("default"))
            widget._svg_cursor_kind = "default"
            self._style_control(widget)
        except Exception:
            return

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if isinstance(obj, QWidget) and self._belongs_to_workspace(obj):
            if event.type() in {QEvent.Type.Enter, QEvent.Type.FocusIn, QEvent.Type.Show}:
                self._restore_default(obj)
                QTimer.singleShot(0, lambda widget=obj: self._restore_default(widget))
        return False


def _make_text_button(svg, text: str, width: int = 30) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("InlineTextButton")
    button.setFixedSize(width, 24)
    button.setCursor(svg.project_cursor("default"))
    font = button.font()
    font.setFamily("Times New Roman")
    font.setPointSize(9)
    font.setBold(True)
    font.setItalic(False)
    button.setFont(font)
    button.setStyleSheet(
        "QPushButton#InlineTextButton {background:#ffffff; border:1px solid #9fb0c5; border-radius:7px; color:#132238; padding:1px;}"
        "QPushButton#InlineTextButton:hover {background:#fff4cf; border-color:#ff8a35;}"
        "QPushButton#InlineTextButton:pressed {background:#d9e9f7; padding-top:2px;}"
    )
    return button


def _style_inline_spin(svg, spin: QSpinBox) -> None:
    styler = getattr(svg, "_style_spin", None)
    if callable(styler):
        styler(spin)
    spin.setFixedSize(72, 24)


def _install_startbar_svg_icons(sb, svg) -> None:
    def tool_icon(key: str) -> QIcon:
        icon = svg.asset_icon(_TOOL_ICON_ASSETS.get(key, "mouse_cursor.svg"))
        return icon if not icon.isNull() else QIcon()

    def mini_zoom_icon(action: str) -> QIcon:
        icon = svg.asset_icon(_TOOL_ICON_ASSETS.get(action, "zoom.svg"))
        return icon if not icon.isNull() else QIcon()

    sb._tool_icon = tool_icon
    sb._mini_zoom_icon = mini_zoom_icon


def _install_cursor_filter(workspace, svg) -> None:
    app = QApplication.instance()
    if app is None:
        return
    old_filter = getattr(workspace, "_engineer_cursor_filter", None)
    if old_filter is not None:
        try:
            app.removeEventFilter(old_filter)
        except Exception:
            pass
    cursor_filter = _EngineerCursorFilter(workspace, svg)
    app.installEventFilter(cursor_filter)
    workspace._engineer_cursor_filter = cursor_filter
    for child in workspace.findChildren(QWidget):
        if not _is_special_cursor_widget(child):
            child.setCursor(svg.project_cursor("default"))
            child._svg_cursor_kind = "default"
            cursor_filter._style_control(child)


def _wrap_properties_general_page(epp) -> None:
    old_general_page = epp.PropertiesDialog._general_page

    def general_page(self) -> QWidget:
        content = old_general_page(self)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        scroll = QScrollArea()
        scroll.setObjectName("FilePropertiesGeneralScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        scroll.setStyleSheet(
            "QScrollArea#FilePropertiesGeneralScroll {background:transparent; border:0;}"
            "QScrollArea#FilePropertiesGeneralScroll > QWidget > QWidget {background:transparent;}"
            "QScrollBar:vertical {background:#eef6ff; width:10px; border-radius:5px;}"
            "QScrollBar::handle:vertical {background:#8fb5dc; border-radius:5px; min-height:24px;}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height:0px;}"
        )
        page = QWidget()
        page.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(scroll, 1)
        return page

    epp.PropertiesDialog._general_page = general_page


def _install_inline_textbar(sb, svg) -> None:
    def ensure_bar(self):
        bar = getattr(self, "_text_toolbar_widget", None)
        command_bar = self.window().findChild(QWidget, "CommandBar") if self.window() is not None else None
        if bar is not None and bar.parentWidget() is command_bar:
            bar.show()
            return bar
        if command_bar is None or command_bar.layout() is None:
            return None
        layout = command_bar.layout()
        bar = QFrame(command_bar)
        bar.setObjectName("InlineTextBar")
        bar.setFixedHeight(30)
        bar.setMaximumWidth(680)
        bar.setMinimumWidth(520)
        bar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        arrow = svg._asset_url("combo_down.svg") if hasattr(svg, "_asset_url") else ""
        bar.setStyleSheet(
            "QFrame#InlineTextBar {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:.52 #eef8ff, stop:1 #fff1c8); border:1px solid #8fa2bb; border-radius:11px;}"
            "QComboBox {background:#ffffff; border:1px solid #9fb0c5; border-radius:7px; color:#132238; font-style:italic; font-weight:800; padding-left:6px;}"
            "QComboBox::drop-down {width:24px; border:0; subcontrol-origin:padding; subcontrol-position:center right;}"
            f"QComboBox::down-arrow {{image:url({arrow}); width:20px; height:14px;}}"
        )
        row = QHBoxLayout(bar)
        row.setContentsMargins(7, 3, 7, 3)
        row.setSpacing(4)
        combo = QComboBox()
        combo.addItems(list(getattr(svg, "FONT_CHOICES", ("Times New Roman",))))
        combo.setCurrentText("Times New Roman")
        combo.setFixedSize(132, 24)
        combo.setCursor(svg.project_cursor("default"))
        row.addWidget(combo)
        size = QSpinBox()
        size.setRange(1, 300)
        size.setValue(12)
        size.setSuffix(" pt")
        size.setCursor(svg.project_cursor("default"))
        _style_inline_spin(svg, size)
        row.addWidget(size)
        for text, width in (("B", 28), ("I", 28), ("•", 28), ("1.", 32), ("L", 28), ("C", 28), ("R", 28), ("J", 28), ("LS", 36), ("LTR", 42), ("RTL", 42), ("Σ", 30)):
            row.addWidget(_make_text_button(svg, text, width))
        insert_index = max(0, layout.count() - 1)
        layout.insertWidget(insert_index, bar, 0, Qt.AlignmentFlag.AlignVCenter)
        bar.show()
        self._text_toolbar_widget = bar
        self._text_toolbar_enabled = True
        return bar

    def set_bar(self, visible: bool = True, emit: bool = True) -> None:
        bar = ensure_bar(self)
        self._text_toolbar_enabled = True
        if bar is not None:
            bar.show()
        button = getattr(self, "_buttons", {}).get("text")
        if button is not None:
            button.setCheckable(True)
            button.setChecked(True)
            button.setCursor(svg.project_cursor("default"))
        if emit:
            self.tool_requested.emit("text_on")
            self._set_host_status("Text environment ready")

    def show_text_toolbar(self, key: str) -> None:
        set_bar(self, True, emit=True)
        popup = getattr(self, "_popup", None)
        if popup is not None:
            popup.close()

    old_handle = sb.StartBar._handle_tool_click

    def handle_tool_click(self, key: str) -> None:
        if key == "text":
            set_bar(self, True, emit=True)
            return
        old_handle(self, key)

    sb.StartBar._ensure_text_toolbar = ensure_bar
    sb.StartBar._set_text_toolbar_visible = set_bar
    sb.StartBar._show_text_toolbar = show_text_toolbar
    sb.StartBar._handle_tool_click = handle_tool_click


def _install_canvas_cursor_events(edw, svg) -> None:
    old_press = edw.EngineeringCanvas.mousePressEvent
    old_release = edw.EngineeringCanvas.mouseReleaseEvent
    old_delete = edw.EngineeringCanvas._delete_selected_objects
    old_restore = edw.EngineeringCanvas._restore_snapshot

    def set_kind(canvas, kind: str) -> None:
        if getattr(canvas, "_svg_cursor_kind", None) == kind:
            return
        canvas._svg_cursor_kind = kind
        canvas.setCursor(svg.project_cursor(kind))

    def reset(canvas) -> None:
        canvas._drag_action = None
        canvas._selection_origin = None
        canvas._selection_rect = None
        set_kind(canvas, "default")
        canvas.update()

    def press(self, event) -> None:
        old_press(self, event)
        if not getattr(self, "objects", None):
            reset(self)
            return
        set_kind(self, _cursor_kind(None, getattr(self, "_drag_action", None)))

    def move(self, event) -> None:
        point = self._to_canvas_point(event.position())
        self.mouse_position_changed.emit(point.x(), point.y())
        if not getattr(self, "objects", None):
            set_kind(self, "default")
            event.accept()
            return
        action = getattr(self, "_drag_action", None)
        if action is not None:
            set_kind(self, _cursor_kind(None, action))
            self._apply_drag(point)
            event.accept()
            return
        if getattr(self, "_selection_origin", None) is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._selection_rect = QRectF(self._selection_origin, point).normalized()
            self.update()
            event.accept()
            return
        _index, hover = self._hit_test_object(point)
        set_kind(self, _cursor_kind(hover))
        event.accept()

    def release(self, event) -> None:
        old_release(self, event)
        if not getattr(self, "objects", None):
            reset(self)
            return
        try:
            point = self._to_canvas_point(event.position())
            _index, hover = self._hit_test_object(point)
            set_kind(self, _cursor_kind(hover))
        except Exception:
            set_kind(self, "default")

    def delete_selected(self) -> None:
        old_delete(self)
        reset(self)

    def restore_snapshot(self, snapshot) -> None:
        old_restore(self, snapshot)
        reset(self)

    edw.EngineeringCanvas.mousePressEvent = press
    edw.EngineeringCanvas.mouseMoveEvent = move
    edw.EngineeringCanvas.mouseReleaseEvent = release
    edw.EngineeringCanvas._delete_selected_objects = delete_selected
    edw.EngineeringCanvas._restore_snapshot = restore_snapshot


def apply_final_cursor_properties_textbar_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw
    from src.engineers_tools.app import engineering_properties_patch as epp
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_final_cursor_properties_textbar_patch", "") == PATCH_VERSION:
        return

    _force_svg_cursor_map(svg)
    _install_startbar_svg_icons(sb, svg)
    _install_canvas_cursor_events(edw, svg)

    old_set_cursor_kind = getattr(svg, "_set_cursor_kind", None)

    def set_cursor_kind(widget, kind: str) -> None:
        if getattr(widget, "_svg_cursor_kind", None) == kind:
            return
        if callable(old_set_cursor_kind):
            old_set_cursor_kind(widget, kind)
        else:
            widget.setCursor(svg.project_cursor(kind))
            widget._svg_cursor_kind = kind

    svg._set_cursor_kind = set_cursor_kind

    old_workspace_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_workspace_init(self, module)
        _install_cursor_filter(self, svg)
        start_bar = getattr(self, "_start_bar_widget", None)
        if start_bar is not None:
            _install_inline_textbar(sb, svg)
            start_bar._set_text_toolbar_visible(True, emit=False)

    _wrap_properties_general_page(epp)
    _install_inline_textbar(sb, svg)
    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_final_cursor_properties_textbar_patch = PATCH_VERSION

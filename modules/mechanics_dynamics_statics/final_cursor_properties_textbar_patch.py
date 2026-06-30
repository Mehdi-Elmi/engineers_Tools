"""Authoritative final UI layer for cursors, SVG tool icons, control arrows, and fixed top Text Bar."""

from __future__ import annotations

from PySide6.QtCore import QObject, QEvent, QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QCursor
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

PATCH_VERSION = "engineering-final-cursor-properties-textbar-2026-07-01-a"

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

_CURSOR_ASSET_OVERRIDES = {
    "default": ("mouse_cursor.svg", 3, 3, 24),
    "select": ("mouse_cursor.svg", 3, 3, 24),
    "pointer": ("mouse_cursor.svg", 3, 3, 24),
    "hand_pointer": ("mouse_cursor.svg", 3, 3, 24),
    "hand_open": ("mouse_cursor.svg", 3, 3, 24),
    "hand_closed": ("mouse_cursor.svg", 3, 3, 24),
    "pan_open": ("mouse_cursor.svg", 3, 3, 24),
    "pan_closed": ("mouse_cursor.svg", 3, 3, 24),
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
    "guide_h": ("resize_vertical.svg", 12, 12, 24),
    "guide_v": ("resize_horizontal.svg", 12, 12, 24),
    "origin": ("mouse_cursor.svg", 3, 3, 24),
}

_HAND_FILE_REDIRECTS = {
    "hand_open.svg": "mouse_cursor.svg",
    "hand_closed.svg": "mouse_cursor.svg",
    "hand_pointer.svg": "mouse_cursor.svg",
    "rotate_cursor.svg": "rotate.svg",
}

_SPECIAL_CURSOR_WIDGET_NAMES = {"EngineeringCanvas", "GridCanvas", "_RulerOverlay", "_RulerCorner", "_GuideLine"}


def _is_special_cursor_widget(widget: QWidget) -> bool:
    return widget.__class__.__name__ in _SPECIAL_CURSOR_WIDGET_NAMES or widget.objectName() in {"EngineeringCanvas", "GridCanvas"}


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


def _force_svg_cursor_system(svg) -> None:
    svg._CURSOR_ASSET_MAP.update(_CURSOR_ASSET_OVERRIDES)
    svg._CURSOR_CACHE.clear()

    if not getattr(svg, "_final_asset_cursor_wrapped", False):
        original_asset_cursor = svg.asset_cursor

        def asset_cursor(file_name: str, fallback, hot_x: int = 8, hot_y: int = 8, max_side: int = 24):
            mapped = _HAND_FILE_REDIRECTS.get(file_name, file_name)
            return original_asset_cursor(mapped, fallback, hot_x, hot_y, max_side)

        svg.asset_cursor = asset_cursor
        svg._final_asset_cursor_wrapped = True

    def project_cursor(kind: str):
        _force_svg_cursor_system(svg)
        file_name, hot_x, hot_y, max_side = svg._CURSOR_ASSET_MAP.get(kind, svg._CURSOR_ASSET_MAP["default"])
        fallback = getattr(svg, "_FALLBACKS", {}).get(kind, Qt.CursorShape.ArrowCursor)
        return svg.asset_cursor(file_name, fallback, hot_x, hot_y, max_side)

    svg.project_cursor = project_cursor


def _patch_app_asset_cursor(svg) -> None:
    try:
        from src.engineers_tools.app import engineering_ui_small_fixes_patch as small
    except Exception:
        return
    if getattr(small, "_final_asset_cursor_wrapped", False):
        return
    original = small._asset_cursor

    def asset_cursor(file_name: str, fallback, hot_x: int = 8, hot_y: int = 8, max_side: int = 24):
        mapped = _HAND_FILE_REDIRECTS.get(file_name, file_name)
        return svg.asset_cursor(mapped, fallback, hot_x, hot_y, max_side)

    small._asset_cursor = asset_cursor
    small._compact_cursor_from_asset = asset_cursor
    small._final_asset_cursor_wrapped = True


def _set_cursor_kind(widget, svg, kind: str) -> None:
    _force_svg_cursor_system(svg)
    if getattr(widget, "_svg_cursor_kind", None) == kind:
        return
    widget._svg_cursor_kind = kind
    widget.setCursor(svg.project_cursor(kind))


def _style_spin(svg, spin) -> None:
    up = svg._asset_url("spin_up.svg") if hasattr(svg, "_asset_url") else ""
    down = svg._asset_url("spin_down.svg") if hasattr(svg, "_asset_url") else ""
    spin.setStyleSheet(
        "QSpinBox, QDoubleSpinBox {background:#fff8d9; border:1px solid #b38621; border-radius:7px; color:#132238; font-size:10px; font-style:normal; font-weight:800; padding:1px 27px 1px 6px;}"
        "QSpinBox::up-button, QDoubleSpinBox::up-button {width:24px; border:0; subcontrol-origin:border; subcontrol-position:top right; background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fffbe8, stop:1 #ffd36e); border-top-right-radius:6px;}"
        "QSpinBox::down-button, QDoubleSpinBox::down-button {width:24px; border:0; subcontrol-origin:border; subcontrol-position:bottom right; background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fffbe8, stop:1 #ffd36e); border-bottom-right-radius:6px;}"
        f"QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{image:url({up}); width:18px; height:12px;}}"
        f"QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{image:url({down}); width:18px; height:12px;}}"
    )


def _style_combo(svg, combo: QComboBox) -> None:
    arrow = svg._asset_url("combo_down.svg") if hasattr(svg, "_asset_url") else ""
    combo.setStyleSheet(
        "QComboBox {background:#ffffff; border:1px solid #9fb0c5; border-radius:7px; color:#132238; font-family:'Times New Roman'; font-size:10px; font-style:italic; font-weight:800; padding:1px 28px 1px 7px;}"
        "QComboBox::drop-down {width:25px; border:0; subcontrol-origin:border; subcontrol-position:center right; background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fffbe8, stop:1 #ffd36e); border-top-right-radius:6px; border-bottom-right-radius:6px;}"
        f"QComboBox::down-arrow {{image:url({arrow}); width:18px; height:12px;}}"
    )


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
                _style_spin(self._svg, widget)
            elif isinstance(widget, QComboBox):
                _style_combo(self._svg, widget)
        except Exception:
            return

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if isinstance(obj, QWidget) and self._belongs_to_workspace(obj):
            if event.type() in {QEvent.Type.Enter, QEvent.Type.FocusIn, QEvent.Type.Show}:
                self._style_control(obj)
                if not _is_special_cursor_widget(obj):
                    _set_cursor_kind(obj, self._svg, "default")
        return False


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
        cursor_filter._style_control(child)
        if not _is_special_cursor_widget(child):
            _set_cursor_kind(child, svg, "default")


def _install_startbar_svg_icons(sb, svg) -> None:
    def tool_icon(key: str) -> QIcon:
        icon = svg.asset_icon(_TOOL_ICON_ASSETS.get(key, "mouse_cursor.svg"))
        return icon if not icon.isNull() else QIcon()

    def mini_zoom_icon(action: str) -> QIcon:
        icon = svg.asset_icon(_TOOL_ICON_ASSETS.get(action, "zoom.svg"))
        return icon if not icon.isNull() else QIcon()

    sb._tool_icon = tool_icon
    sb._mini_zoom_icon = mini_zoom_icon


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


def _find_command_bar(workspace) -> QWidget | None:
    bar = workspace.findChild(QWidget, "CommandBar")
    if bar is not None and bar.layout() is not None:
        return bar
    for child in workspace.findChildren(QWidget):
        if child.objectName() == "CommandBar" and child.layout() is not None:
            return child
    return None


def _install_inline_textbar(sb, svg) -> None:
    def ensure_bar(self):
        window = self.window()
        if window is None:
            return None
        command_bar = _find_command_bar(window)
        if command_bar is None or command_bar.layout() is None:
            return None
        existing = command_bar.findChild(QFrame, "InlineTextBar")
        if existing is not None:
            existing.show()
            self._text_toolbar_widget = existing
            self._text_toolbar_enabled = True
            return existing
        layout = command_bar.layout()
        bar = QFrame(command_bar)
        bar.setObjectName("InlineTextBar")
        bar.setFixedHeight(30)
        bar.setMaximumWidth(720)
        bar.setMinimumWidth(540)
        bar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bar.setStyleSheet(
            "QFrame#InlineTextBar {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:.52 #eef8ff, stop:1 #fff1c8); border:1px solid #8fa2bb; border-radius:11px;}"
        )
        row = QHBoxLayout(bar)
        row.setContentsMargins(7, 3, 7, 3)
        row.setSpacing(4)
        combo = QComboBox()
        combo.addItems(["Times New Roman"])
        combo.setCurrentText("Times New Roman")
        combo.setFixedSize(150, 24)
        combo.setCursor(svg.project_cursor("default"))
        _style_combo(svg, combo)
        row.addWidget(combo)
        size = QSpinBox()
        size.setRange(1, 300)
        size.setValue(12)
        size.setSuffix(" pt")
        size.setCursor(svg.project_cursor("default"))
        _style_spin(svg, size)
        size.setFixedSize(76, 24)
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
        popup = getattr(self, "_popup", None)
        if popup is not None:
            popup.close()
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
    def set_kind(canvas, kind: str) -> None:
        _set_cursor_kind(canvas, svg, kind)

    def reset(canvas) -> None:
        canvas._drag_action = None
        canvas._selection_origin = None
        canvas._selection_rect = None
        set_kind(canvas, "default")
        canvas.update()

    def mouse_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            point = self._to_canvas_point(event.position())
            index, action = self._hit_test_object(point)
            ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if index is None:
                if not ctrl:
                    self.selected_indices = set()
                    self._active_group_edit = None
                    self._emit_selection_changes()
                self._selection_origin = point
                self._selection_rect = QRectF(point, point)
                self._drag_action = None
                set_kind(self, "default")
                self.update()
                event.accept()
                return
            hit_group = self.objects[index].group_id
            if ctrl:
                if hit_group is not None and self._active_group_edit != hit_group:
                    members = {i for i, obj in enumerate(self.objects) if obj.group_id == hit_group and obj.visible}
                    self.selected_indices.symmetric_difference_update(members)
                elif index in self.selected_indices:
                    self.selected_indices.remove(index)
                else:
                    self.selected_indices.add(index)
                self._emit_selection_changes()
                self.update()
                set_kind(self, _cursor_kind(action))
                event.accept()
                return
            if index not in self.selected_indices:
                self._select_only(index)
            if action is not None and not any(self.objects[selected].locked for selected in self.selected_indices):
                self._push_undo()
                self._drag_action = action
                self._drag_start = point
                self._drag_start_rects = {selected: QRectF(self.objects[selected].rect) for selected in self.selected_indices}
                self._drag_start_rotations = {selected: self.objects[selected].rotation for selected in self.selected_indices}
                self._drag_start_group_bounds = self._group_bounds()
                self._drag_group_center = self._drag_start_group_bounds.center() if len(self.selected_indices) > 1 else self.objects[index].rect.center()
                set_kind(self, _cursor_kind(None, action))
            else:
                set_kind(self, _cursor_kind(action))
            self.update()
            event.accept()
            return
        QWidget.mousePressEvent(self, event)

    def mouse_move(self, event) -> None:
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
            set_kind(self, "default")
            event.accept()
            return
        _index, hover = self._hit_test_object(point)
        set_kind(self, _cursor_kind(hover))
        event.accept()

    def mouse_release(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._selection_origin is not None:
            if self._selection_rect is not None and self._selection_rect.width() > 6 and self._selection_rect.height() > 6:
                selected = {index for index, obj in enumerate(self.objects) if obj.visible and self._selection_rect.intersects(self._object_scene_bounds(obj))}
                expanded: set[int] = set()
                for index in selected:
                    group_id = self.objects[index].group_id
                    if group_id is not None and self._active_group_edit != group_id:
                        expanded.update(i for i, obj in enumerate(self.objects) if obj.group_id == group_id and obj.visible)
                    else:
                        expanded.add(index)
                self.selected_indices = expanded
                self._emit_selection_changes()
            self._selection_origin = None
            self._selection_rect = None
            self.update()
        self._drag_action = None
        if getattr(self, "objects", None):
            try:
                point = self._to_canvas_point(event.position())
                _index, hover = self._hit_test_object(point)
                set_kind(self, _cursor_kind(hover))
            except Exception:
                set_kind(self, "default")
        else:
            reset(self)
        event.accept()

    old_delete = edw.EngineeringCanvas._delete_selected_objects
    old_restore = edw.EngineeringCanvas._restore_snapshot

    def delete_selected(self) -> None:
        old_delete(self)
        reset(self)

    def restore_snapshot(self, snapshot) -> None:
        old_restore(self, snapshot)
        reset(self)

    edw.EngineeringCanvas.mousePressEvent = mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    edw.EngineeringCanvas._delete_selected_objects = delete_selected
    edw.EngineeringCanvas._restore_snapshot = restore_snapshot


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
        page = QWidget()
        page.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(scroll, 1)
        return page

    epp.PropertiesDialog._general_page = general_page


def apply_final_cursor_properties_textbar_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from . import workspace as edw
    from src.engineers_tools.app import engineering_properties_patch as epp
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_final_cursor_properties_textbar_patch", "") == PATCH_VERSION:
        return

    _force_svg_cursor_system(svg)
    _patch_app_asset_cursor(svg)
    _install_startbar_svg_icons(sb, svg)
    _install_canvas_cursor_events(edw, svg)

    old_workspace_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_workspace_init(self, module)
        _force_svg_cursor_system(svg)
        _install_cursor_filter(self, svg)
        start_bar = getattr(self, "_start_bar_widget", None)
        if start_bar is not None:
            _install_inline_textbar(sb, svg)
            start_bar._set_text_toolbar_visible(True, emit=False)

    _wrap_properties_general_page(epp)
    _install_inline_textbar(sb, svg)
    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_final_cursor_properties_textbar_patch = PATCH_VERSION

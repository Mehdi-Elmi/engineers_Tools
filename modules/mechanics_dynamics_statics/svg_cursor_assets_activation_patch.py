"""Activate SVG cursor assets and shared Start Bar/File Properties controls.

Visual cursor/icon design must be edited in:
    src/engineers_tools/assets/ui_icons/*.svg

This patch is intentionally the last UI layer for cursor and common controls.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QCursor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QSpinBox, QVBoxLayout, QWidget

PATCH_VERSION = "engineering-svg-cursor-assets-2026-06-30-c"
FONT_CHOICES = ("Times New Roman",)

_CURSOR_ASSET_MAP = {
    "default": ("mouse_cursor.svg", 3, 3, 24),
    "select": ("mouse_cursor.svg", 3, 3, 24),
    "pointer": ("mouse_cursor.svg", 3, 3, 24),
    "hand_pointer": ("mouse_cursor.svg", 3, 3, 24),
    "pan_open": ("hand_open.svg", 12, 8, 24),
    "pan_closed": ("hand_closed.svg", 12, 8, 24),
    "hand_open": ("hand_open.svg", 12, 8, 24),
    "hand_closed": ("hand_closed.svg", 12, 8, 24),
    "rotate": ("rotate_cursor.svg", 12, 12, 24),
    "rotate_drag": ("rotate_cursor.svg", 12, 12, 24),
    "move": ("move_cursor.svg", 12, 12, 24),
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
    "zoom": ("zoom.svg", 12, 12, 24),
    "zoom_in": ("zoom_in.svg", 12, 12, 24),
    "zoom_out": ("zoom_out.svg", 12, 12, 24),
    "zoom_fit": ("zoom_fit.svg", 12, 12, 24),
}

_FALLBACKS = {
    "default": Qt.CursorShape.ArrowCursor,
    "select": Qt.CursorShape.ArrowCursor,
    "pointer": Qt.CursorShape.ArrowCursor,
    "hand_pointer": Qt.CursorShape.ArrowCursor,
    "pan_open": Qt.CursorShape.OpenHandCursor,
    "pan_closed": Qt.CursorShape.ClosedHandCursor,
    "hand_open": Qt.CursorShape.OpenHandCursor,
    "hand_closed": Qt.CursorShape.ClosedHandCursor,
    "rotate": Qt.CursorShape.CrossCursor,
    "rotate_drag": Qt.CursorShape.CrossCursor,
    "move": Qt.CursorShape.SizeAllCursor,
    "resize_h": Qt.CursorShape.SizeHorCursor,
    "resize_v": Qt.CursorShape.SizeVerCursor,
    "resize_horizontal": Qt.CursorShape.SizeHorCursor,
    "resize_vertical": Qt.CursorShape.SizeVerCursor,
    "resize_n": Qt.CursorShape.SizeVerCursor,
    "resize_s": Qt.CursorShape.SizeVerCursor,
    "resize_e": Qt.CursorShape.SizeHorCursor,
    "resize_w": Qt.CursorShape.SizeHorCursor,
    "resize_ne": Qt.CursorShape.SizeBDiagCursor,
    "resize_sw": Qt.CursorShape.SizeBDiagCursor,
    "resize_nw": Qt.CursorShape.SizeFDiagCursor,
    "resize_se": Qt.CursorShape.SizeFDiagCursor,
    "resize_diag_f": Qt.CursorShape.SizeFDiagCursor,
    "resize_diag_b": Qt.CursorShape.SizeBDiagCursor,
    "resize_fdiag": Qt.CursorShape.SizeFDiagCursor,
    "resize_bdiag": Qt.CursorShape.SizeBDiagCursor,
    "guide_h": Qt.CursorShape.SizeVerCursor,
    "guide_v": Qt.CursorShape.SizeHorCursor,
    "origin": Qt.CursorShape.CrossCursor,
    "zoom": Qt.CursorShape.CrossCursor,
    "zoom_in": Qt.CursorShape.CrossCursor,
    "zoom_out": Qt.CursorShape.CrossCursor,
    "zoom_fit": Qt.CursorShape.CrossCursor,
}

_HOVER_TO_KIND = {
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

_CURSOR_CACHE: dict[tuple[str, int, int, int], QCursor] = {}
_ICON_CACHE: dict[str, QIcon] = {}


def _asset_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "engineers_tools" / "assets" / "ui_icons"


def _asset_path(file_name: str) -> Path | None:
    path = _asset_dir() / file_name
    return path if path.exists() else None


def _asset_url(file_name: str) -> str:
    path = _asset_path(file_name)
    return path.as_posix() if path is not None else ""


def _render_svg_to_pixmap(path: Path, max_side: int) -> QPixmap:
    try:
        from PySide6.QtSvg import QSvgRenderer
    except Exception:
        return QPixmap(str(path))
    renderer = QSvgRenderer(str(path))
    if not renderer.isValid():
        return QPixmap(str(path))
    size = renderer.defaultSize()
    width = max(1, size.width())
    height = max(1, size.height())
    scale = min(float(max_side) / float(width), float(max_side) / float(height), 1.0)
    pixmap = QPixmap(max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter, QRectF(0, 0, pixmap.width(), pixmap.height()))
    painter.end()
    return pixmap


def _pixmap_from_asset(file_name: str, max_side: int) -> QPixmap:
    path = _asset_path(file_name)
    if path is None:
        return QPixmap()
    pixmap = _render_svg_to_pixmap(path, max_side) if path.suffix.lower() == ".svg" else QPixmap(str(path))
    if pixmap.isNull():
        return pixmap
    if pixmap.width() > max_side or pixmap.height() > max_side:
        pixmap = pixmap.scaled(max_side, max_side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return pixmap


def asset_cursor(file_name: str, fallback: QCursor | Qt.CursorShape, hot_x: int = 8, hot_y: int = 8, max_side: int = 24) -> QCursor:
    fallback_cursor = fallback if isinstance(fallback, QCursor) else QCursor(fallback)
    key = (file_name, int(hot_x), int(hot_y), int(max_side))
    cached = _CURSOR_CACHE.get(key)
    if cached is not None:
        return cached
    pixmap = _pixmap_from_asset(file_name, max_side)
    if pixmap.isNull():
        return fallback_cursor
    safe_hot_x = max(0, min(int(hot_x), max(0, pixmap.width() - 1)))
    safe_hot_y = max(0, min(int(hot_y), max(0, pixmap.height() - 1)))
    cursor = QCursor(pixmap, safe_hot_x, safe_hot_y)
    _CURSOR_CACHE[key] = cursor
    return cursor


def project_cursor(kind: str) -> QCursor:
    file_name, hot_x, hot_y, max_side = _CURSOR_ASSET_MAP.get(kind, _CURSOR_ASSET_MAP["default"])
    return asset_cursor(file_name, _FALLBACKS.get(kind, Qt.CursorShape.ArrowCursor), hot_x, hot_y, max_side)


def asset_icon(file_name: str) -> QIcon:
    cached = _ICON_CACHE.get(file_name)
    if cached is not None:
        return cached
    path = _asset_path(file_name)
    icon = QIcon(str(path)) if path is not None else QIcon()
    _ICON_CACHE[file_name] = icon
    return icon


def _canvas_kind_from_hover(hover: str | None, drag_action: str | None = None) -> str:
    if drag_action:
        return _HOVER_TO_KIND.get(drag_action, "default")
    return _HOVER_TO_KIND.get(str(hover), "default")


def _set_cursor_kind(widget, kind: str) -> None:
    if getattr(widget, "_svg_cursor_kind", None) == kind:
        return
    widget._svg_cursor_kind = kind
    widget.setCursor(project_cursor(kind))


def _set_canvas_hover_cursor(canvas, hover: str | None) -> None:
    _set_cursor_kind(canvas, _canvas_kind_from_hover(hover))


def _reset_canvas_interaction(canvas) -> None:
    canvas._drag_action = None
    canvas._selection_origin = None
    canvas._selection_rect = None
    canvas._drag_start_rects = {}
    canvas._drag_start_rotations = {}
    _set_cursor_kind(canvas, "default")
    canvas.update()


def _install_default_cursor_tree(widget) -> None:
    cursor = project_cursor("default")
    try:
        widget.setCursor(cursor)
        widget._svg_cursor_kind = "default"
        for child in widget.findChildren(QWidget):
            child.setCursor(cursor)
            child._svg_cursor_kind = "default"
    except Exception:
        return


def _style_spin(spin) -> None:
    up = _asset_url("spin_up.svg")
    down = _asset_url("spin_down.svg")
    spin.setStyleSheet(
        "QDoubleSpinBox, QSpinBox {background:#fff8d9; border:1px solid #b38621; border-radius:7px; color:#132238; font-size:10px; font-style:normal; font-weight:800; padding:1px 25px 1px 5px;}"
        "QDoubleSpinBox::up-button, QSpinBox::up-button {width:22px; border:0; subcontrol-origin:border; subcontrol-position:top right; background:#ffe083; border-top-right-radius:6px;}"
        "QDoubleSpinBox::down-button, QSpinBox::down-button {width:22px; border:0; subcontrol-origin:border; subcontrol-position:bottom right; background:#ffe083; border-bottom-right-radius:6px;}"
        f"QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {{image:url({up}); width:16px; height:10px;}}"
        f"QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {{image:url({down}); width:16px; height:10px;}}"
    )


def _icon_button(text: str, tooltip: str, width: int = 34) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("TextToolButton")
    button.setToolTip(tooltip)
    button.setFixedSize(width, 28)
    button.setCursor(project_cursor("default"))
    font = button.font()
    font.setFamily("Times New Roman")
    font.setBold(True)
    font.setItalic(False)
    font.setPointSize(10)
    button.setFont(font)
    button.setStyleSheet(
        "QPushButton#TextToolButton {background:#ffffff; border:1px solid #9fb0c5; border-radius:8px; color:#132238; padding:1px;}"
        "QPushButton#TextToolButton:hover {background:#fff4cf; border-color:#ff8a35;}"
        "QPushButton#TextToolButton:pressed {background:#d9e9f7; padding-top:2px;}"
    )
    return button


def _show_symbol_menu(parent: QWidget, button: QPushButton) -> None:
    menu = QMenu(parent)
    menu.setCursor(project_cursor("default"))
    menu.setStyleSheet("QMenu {background:#ffffff; border:1px solid #8fa2bb; border-radius:9px; padding:5px;} QMenu::item {padding:5px 18px; color:#132238;} QMenu::item:selected {background:#fff4cf;}")
    for title, symbols in {
        "Greek Symbols": ("α", "β", "γ", "δ", "Δ", "θ", "λ", "μ", "π", "ρ", "σ", "Σ", "φ", "Ω"),
        "Math Operators": ("±", "×", "÷", "≈", "≠", "≤", "≥", "∞", "∂", "∇", "∫", "√"),
    }.items():
        sub = menu.addMenu(title)
        for symbol in symbols:
            sub.addAction(symbol)
    menu.exec(button.mapToGlobal(button.rect().bottomLeft()))


def _show_snap_popup(self, key: str) -> None:
    if not hasattr(self, "_snap_enabled"):
        self._snap_enabled = False
    popup, layout = self._popup_base(190)
    row = QHBoxLayout()
    row.setSpacing(6)

    def set_snap(value: bool) -> None:
        self._snap_enabled = value
        self.tool_requested.emit("snap_on" if value else "snap_off")
        self._set_host_status("Snap On" if value else "Snap Off")
        if self._popup is not None:
            self._popup.close()

    row.addWidget(self._radio_button("Snap On", bool(self._snap_enabled), lambda checked=False: set_snap(True)))
    row.addWidget(self._radio_button("Snap Off", not bool(self._snap_enabled), lambda checked=False: set_snap(False)))
    layout.addLayout(row)
    _install_default_cursor_tree(popup)
    self._show_popup_near(key, popup)


def _show_text_toolbar(self, key: str) -> None:
    popup, layout = self._popup_base(520)
    row = QHBoxLayout()
    row.setContentsMargins(2, 2, 2, 2)
    row.setSpacing(6)

    font_combo = QComboBox()
    font_combo.addItems(list(FONT_CHOICES))
    font_combo.setCurrentText("Times New Roman")
    font_combo.setToolTip("Font")
    font_combo.setFixedSize(142, 28)
    font_combo.setStyleSheet("QComboBox {background:#ffffff; border:1px solid #9fb0c5; border-radius:8px; color:#132238; font-size:10px; font-style:italic; font-weight:800; padding:2px 7px;} QComboBox::drop-down {width:22px; border:0;} QComboBox::down-arrow {image:url(%s); width:14px; height:9px;}" % _asset_url("combo_down.svg"))
    row.addWidget(font_combo)

    size_spin = QSpinBox()
    size_spin.setRange(1, 300)
    size_spin.setValue(12)
    size_spin.setSuffix(" pt")
    size_spin.setToolTip("Font size")
    size_spin.setFixedSize(78, 28)
    _style_spin(size_spin)
    row.addWidget(size_spin)

    for text, tooltip in (("B", "Bold"), ("I", "Italic"), ("•", "Bullet Library"), ("1.", "Numeric Library"), ("L", "Align Left"), ("C", "Align Center"), ("R", "Align Right"), ("RTL", "Right To Left")):
        row.addWidget(_icon_button(text, tooltip, 42 if len(text) > 1 else 34))

    eq_button = _icon_button("Σ", "Math Equation and Symbols", 36)
    eq_button.clicked.connect(lambda checked=False, b=eq_button: _show_symbol_menu(self, b))
    row.addWidget(eq_button)
    layout.addLayout(row)
    _install_default_cursor_tree(popup)
    self._show_popup_near(key, popup)
    self.tool_requested.emit("text")
    self._set_host_status("Text tool")


def _patch_file_properties_general(epp, fpg) -> None:
    def no_toggle(self, event) -> None:
        QFrame.mousePressEvent(self, event)

    fpg._WaveSection.mousePressEvent = no_toggle

    def text_block(dialog, general: dict):
        section = fpg._WaveSection("Text", dialog, collapsed=False, open_height=92)
        dialog.text_font = QComboBox()
        dialog.text_font.addItems(list(FONT_CHOICES))
        dialog.text_font.setCurrentText("Times New Roman")
        dialog.text_font.setObjectName("PropertiesCombo")
        dialog.text_font.setFixedHeight(25)
        dialog.text_font.setStyleSheet("QComboBox {background:#ffffff; border:1px solid #9fb0c5; border-radius:7px; color:#132238; font-size:10px; font-style:italic; font-weight:800; padding:1px 7px;} QComboBox::drop-down {width:22px; border:0;} QComboBox::down-arrow {image:url(%s); width:14px; height:9px;}" % _asset_url("combo_down.svg"))
        dialog.text_size = QSpinBox()
        dialog.text_size.setRange(1, 300)
        dialog.text_size.setValue(int(general.get("text_size", 12) or 12))
        dialog.text_size.setSuffix(" pt")
        dialog.text_size.setFixedHeight(25)
        _style_spin(dialog.text_size)
        section.add_body_widget(fpg._row("Font", dialog.text_font))
        section.add_body_widget(fpg._row("Size", dialog.text_size))
        return section

    def snap_block(dialog, general: dict):
        section = fpg._WaveSection("Snap", dialog, collapsed=False, open_height=66)
        current = bool(general.get("snap_enabled", False))
        dialog.snap_check.setChecked(current)
        button = fpg._choice_button("Snap On" if current else "Snap Off", current, lambda checked=False: None, width=104)

        def toggle() -> None:
            value = not dialog.snap_check.isChecked()
            dialog.snap_check.setChecked(value)
            button.setChecked(value)
            button.setIcon(fpg._radio_icon(value))
            button.setText("Snap On" if value else "Snap Off")

        button.clicked.connect(toggle)
        section.add_body_widget(button)
        return section

    def page_setup_block(dialog, _general: dict):
        section = fpg._WaveSection("Page Setup", dialog, collapsed=False, open_height=56)
        label = QLabel("Defaults are edited from Page Setup.")
        label.setStyleSheet("QLabel {background:transparent; color:#5d6f85; font-size:10px; font-style:italic; font-weight:800; padding:1px 4px;}")
        section.add_body_widget(label)
        return section

    def general_page(self) -> QWidget:
        page = QWidget()
        page.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        general = self._settings.get("general", {})

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(list(fpg.UNITS))
        self.unit_combo.setCurrentText(str(general.get("unit", "mm")) if str(general.get("unit", "mm")) in fpg.UNITS else "mm")
        self.unit_combo.hide()
        self.grid_check = QCheckBox(); self.grid_check.setChecked(bool(general.get("grid_enabled", True))); self.grid_check.hide()
        self.snap_check = QCheckBox(); self.snap_check.setChecked(bool(general.get("snap_enabled", False))); self.snap_check.hide()
        self.grid_spacing = QDoubleSpinBox()
        self.grid_spacing.setRange(0.000001, 1000000.0)
        self.grid_spacing.setDecimals(6)
        self.grid_spacing.setSingleStep(0.5)
        self.grid_spacing.setValue(float(general.get("grid_spacing", 1.0) or 1.0))
        _style_spin(self.grid_spacing)

        hidden = QWidget()
        hidden_layout = QVBoxLayout(hidden)
        hidden_layout.setContentsMargins(0, 0, 0, 0)
        for widget in (self.unit_combo, self.grid_check, self.snap_check):
            hidden_layout.addWidget(widget)
        hidden.hide()
        layout.addWidget(hidden)
        layout.addWidget(fpg._unit_block(self, general))
        layout.addWidget(fpg._grid_block(self, general))
        layout.addWidget(text_block(self, general))
        layout.addWidget(snap_block(self, general))
        layout.addWidget(page_setup_block(self, general))
        layout.addStretch(1)
        return page

    epp.PropertiesDialog._general_page = general_page


def apply_svg_cursor_assets_activation_patch() -> None:
    from . import cursor_unification_fixes as cuf
    from . import file_properties_general_patch as fpg
    from . import interaction_fixes as interaction
    from . import ui_refinement_fixes
    from . import window_resize_fixes
    from . import workspace as edw
    from src.engineers_tools.app import engineering_properties_patch as epp
    from src.engineers_tools.app import engineering_ui_small_fixes_patch as small_fixes
    from src.engineers_tools.app import interaction_ui_patch as interaction_ui
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_svg_cursor_assets_patch", "") == PATCH_VERSION:
        return

    cuf.project_cursor = project_cursor
    interaction.project_cursor = project_cursor
    ui_refinement_fixes._refined_project_cursor = project_cursor
    window_resize_fixes._window_cursor = project_cursor
    small_fixes._asset_cursor = asset_cursor
    small_fixes._compact_cursor_from_asset = asset_cursor
    small_fixes._set_canvas_hover_cursor = _set_canvas_hover_cursor
    interaction_ui._cursor_from_asset = lambda file_name, fallback, hot_x=8, hot_y=8: asset_cursor(file_name, fallback, hot_x, hot_y, 24)
    sb._zoom_cursor = lambda mode: project_cursor(mode if mode in {"zoom_in", "zoom_out", "zoom_fit"} else "zoom")

    original_canvas_press = edw.EngineeringCanvas.mousePressEvent
    original_canvas_move = edw.EngineeringCanvas.mouseMoveEvent
    original_canvas_release = edw.EngineeringCanvas.mouseReleaseEvent
    original_delete_selected = edw.EngineeringCanvas._delete_selected_objects
    original_restore_snapshot = edw.EngineeringCanvas._restore_snapshot
    original_key_press = edw.EngineeringCanvas.keyPressEvent
    original_workspace_init = edw.EngineeringDesignWorkspace.__init__
    original_startbar_init = sb.StartBar.__init__
    original_startbar_show = sb.StartBar.showEvent
    original_handle_tool_click = sb.StartBar._handle_tool_click
    original_show_grid_popup = sb.StartBar._show_grid_popup
    original_guide_init = sb._GuideLine.__init__
    original_overlay_init = sb._RulerOverlay.__init__
    original_corner_init = sb._RulerCorner.__init__

    def set_from_event(canvas, event, drag_action: str | None = None) -> None:
        if not getattr(canvas, "objects", None):
            _set_cursor_kind(canvas, "default")
            return
        try:
            point = canvas._to_canvas_point(event.position())
            _index, hover = canvas._hit_test_object(point)
            _set_cursor_kind(canvas, _canvas_kind_from_hover(hover, drag_action))
        except Exception:
            _set_cursor_kind(canvas, _canvas_kind_from_hover(None, drag_action))

    def canvas_press(self, event) -> None:
        set_from_event(self, event)
        original_canvas_press(self, event)
        set_from_event(self, event, getattr(self, "_drag_action", None))

    def canvas_move(self, event) -> None:
        original_canvas_move(self, event)
        set_from_event(self, event, getattr(self, "_drag_action", None))

    def canvas_release(self, event) -> None:
        original_canvas_release(self, event)
        set_from_event(self, event)

    def delete_selected(self) -> None:
        original_delete_selected(self)
        _reset_canvas_interaction(self)

    def restore_snapshot(self, snapshot) -> None:
        original_restore_snapshot(self, snapshot)
        _reset_canvas_interaction(self)

    def key_press(self, event) -> None:
        if event.key() in {Qt.Key.Key_Delete, Qt.Key.Key_Backspace} and getattr(self, "selected_indices", None):
            self._push_undo()
            self._delete_selected_objects()
            event.accept()
            return
        original_key_press(self, event)

    def workspace_init(self, module) -> None:
        original_workspace_init(self, module)
        _install_default_cursor_tree(self)
        canvas = getattr(self, "_canvas", None)
        if canvas is not None:
            _set_cursor_kind(canvas, "default")

    def startbar_init(self, *args, **kwargs) -> None:
        original_startbar_init(self, *args, **kwargs)
        _install_default_cursor_tree(self)
        if not hasattr(self, "_snap_enabled"):
            self._snap_enabled = False

    def startbar_show(self, event) -> None:
        original_startbar_show(self, event)
        _install_default_cursor_tree(self)

    def handle_tool_click(self, key: str) -> None:
        if key == "snap":
            _show_snap_popup(self, key)
            return
        if key == "text":
            _show_text_toolbar(self, key)
            return
        original_handle_tool_click(self, key)

    def show_grid_popup(self, key: str) -> None:
        original_show_grid_popup(self, key)
        popup = getattr(self, "_popup", None)
        if popup is not None:
            for spin in popup.findChildren(QDoubleSpinBox):
                _style_spin(spin)
            _install_default_cursor_tree(popup)

    def guide_init(self, orientation: str, position: float, parent, start_bar=None, persistent: bool = True) -> None:
        original_guide_init(self, orientation, position, parent, start_bar, persistent)
        _set_cursor_kind(self, "guide_h" if orientation == "horizontal" else "guide_v")

    def overlay_init(self, start_bar, orientation: str, parent) -> None:
        original_overlay_init(self, start_bar, orientation, parent)
        _set_cursor_kind(self, "guide_h" if orientation == "top" else "guide_v")

    def corner_init(self, start_bar, parent) -> None:
        original_corner_init(self, start_bar, parent)
        _set_cursor_kind(self, "origin")

    def layer_button(self, kind: str, active: bool, tooltip: str, callback) -> QPushButton:
        button = QPushButton()
        button.setObjectName("LayerIconButton")
        button.setToolTip(tooltip)
        button.setFixedSize(26, 24)
        button.setIcon(edw._layer_icon(kind, active))
        button.setIconSize(QSize(23, 23))
        button.setCursor(project_cursor("default"))
        button.setAutoDefault(False)
        button.setDefault(False)
        button.clicked.connect(lambda checked=False: callback())
        return button

    edw.EngineeringCanvas.mousePressEvent = canvas_press
    edw.EngineeringCanvas.mouseMoveEvent = canvas_move
    edw.EngineeringCanvas.mouseReleaseEvent = canvas_release
    edw.EngineeringCanvas._delete_selected_objects = delete_selected
    edw.EngineeringCanvas._restore_snapshot = restore_snapshot
    edw.EngineeringCanvas.keyPressEvent = key_press
    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    sb.StartBar.__init__ = startbar_init
    sb.StartBar.showEvent = startbar_show
    sb.StartBar._handle_tool_click = handle_tool_click
    sb.StartBar._show_grid_popup = show_grid_popup
    sb._GuideLine.__init__ = guide_init
    sb._RulerOverlay.__init__ = overlay_init
    sb._RulerCorner.__init__ = corner_init
    edw.EngineeringDesignWorkspace._layer_button = layer_button
    _patch_file_properties_general(epp, fpg)
    edw.EngineeringDesignWorkspace._engineering_svg_cursor_assets_patch = PATCH_VERSION

"""Final visible runtime corrections for Engineering Design Tools.

This patch must run after every other engineering patch. It makes the final UI
state observable in runtime.log and reapplies the visible Text bar, color
palette, and project cursors after the real window has been built.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QWidget,
)

PATCH_VERSION = "engineering-runtime-audit-final-2026-07-01-d"

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
_PALETTE = (
    "#132238",
    "#2f7df6",
    "#0f2a44",
    "#f18a2a",
    "#c9342b",
    "#168a50",
    "#6e4ad6",
    "#536271",
)
_KNOWN_LOWER_TEXT_BARS = {
    "textsubbar",
    "texttoolbar",
    "texttoolbox",
    "floatingtextbar",
    "lowertextbar",
}
_COLOR_CONTROL_NAMES = {
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
_SWATCH_SIZE = 15
_SWATCH_GAP = 1
_ADD_BUTTON_WIDTH = 14
_ADD_BUTTON_GAP = 6


def _is_inside(widget: QWidget, parent: QWidget | None) -> bool:
    current = widget.parentWidget()
    while current is not None:
        if current is parent:
            return True
        current = current.parentWidget()
    return False


def _remove_widget(widget: QWidget | None) -> None:
    if widget is None:
        return
    widget.hide()
    widget.setParent(None)
    widget.deleteLater()


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


def _active_editor(root: QWidget | None) -> QTextEdit | None:
    canvas = getattr(root, "_canvas", None) if root is not None else None
    editor = getattr(canvas, "_active_text_editor", None) if canvas is not None else None
    return editor if isinstance(editor, QTextEdit) else None


def _apply_color(root: QWidget | None, color: str) -> None:
    editor = _active_editor(root)
    if editor is not None:
        editor.setTextColor(QColor(color))


def _icon_for_color(color: str) -> QIcon:
    pixmap = QPixmap(13, 13)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QColor("#7f95b2"))
    painter.setBrush(QColor(color))
    painter.drawRoundedRect(1, 1, 11, 11, 2, 2)
    painter.end()
    return QIcon(pixmap)


def _choose_color(button: QPushButton, root: QWidget | None) -> None:
    current = QColor(str(button.property("colorValue") or "#132238"))
    color = QColorDialog.getColor(current, button, "Custom Color")
    if not color.isValid():
        return
    value = color.name()
    button.setProperty("colorValue", value)
    button.setIcon(_icon_for_color(value))
    button.setStyleSheet(_swatch_style(value))
    _apply_color(root, value)


def _custom_colors(root: QWidget | None) -> list[str]:
    if root is None:
        return []
    values = getattr(root, "_runtime_text_custom_colors", None)
    if not isinstance(values, list):
        values = []
        setattr(root, "_runtime_text_custom_colors", values)
    return values


def _rebuild_palette(root: QWidget | None) -> None:
    if root is None:
        return
    bar = root.findChild(QWidget, "InlineTextBar")
    if bar is None:
        return
    for holder_name in ("RuntimeAuditColorPaletteHolder", "InlineColorPaletteHolder"):
        _remove_widget(bar.findChild(QWidget, holder_name))
    _install_inline_palette(root)


def _add_custom_color(root: QWidget | None) -> None:
    if root is None:
        return
    color = QColorDialog.getColor(QColor("#2f7df6"), root, "Add Custom Color")
    if not color.isValid():
        return
    value = color.name()
    colors = _custom_colors(root)
    if value not in colors:
        colors.append(value)
    _apply_color(root, value)
    _rebuild_palette(root)


def _swatch_style(color: str) -> str:
    return (
        "QPushButton{background:" + color + ";border:1px solid #7f95b2;border-radius:2px;"
        "padding:0;margin:0;}"
        "QPushButton:hover{border:2px solid #ff8a35;}"
        "QPushButton:pressed{border:2px solid #132238;}"
    )


def _make_swatch(parent: QWidget, root: QWidget | None, color: str) -> QPushButton:
    button = QPushButton(parent)
    button.setObjectName("InlineColorSwatch")
    button.setFixedSize(_SWATCH_SIZE, _SWATCH_SIZE)
    button.setIconSize(QSize(11, 11))
    button.setIcon(_icon_for_color(color))
    button.setProperty("colorValue", color)
    button.setToolTip("Color")
    button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    button.clicked.connect(lambda checked=False, b=button, w=root: _apply_color(w, str(b.property("colorValue") or color)))
    button.customContextMenuRequested.connect(lambda _pos, b=button, w=root: _choose_color(b, w))
    button.setStyleSheet(_swatch_style(color))
    return button


def _clear_color_controls(bar: QWidget) -> None:
    for child in list(bar.findChildren(QWidget)):
        name = (child.objectName() or "").lower()
        if name in _COLOR_CONTROL_NAMES or child.property("runtimeTextColorControl"):
            _remove_widget(child)


def _install_inline_palette(root: QWidget | None) -> None:
    if root is None:
        return
    bar = root.findChild(QWidget, "InlineTextBar")
    if bar is None:
        return
    existing_final = bar.findChild(QWidget, "RuntimeAuditColorPaletteHolder")
    if existing_final is not None:
        for old in list(bar.findChildren(QWidget)):
            name = (old.objectName() or "").lower()
            if old is existing_final or _is_inside(old, existing_final):
                continue
            if name in _COLOR_CONTROL_NAMES or old.property("runtimeTextColorControl"):
                _remove_widget(old)
        return

    _clear_color_controls(bar)

    colors = list(_PALETTE) + _custom_colors(root)
    columns = max(4, (len(colors) + 1) // 2)
    palette_width = columns * _SWATCH_SIZE + max(0, columns - 1) * _SWATCH_GAP
    palette_height = 2 * _SWATCH_SIZE + _SWATCH_GAP

    palette = QWidget(bar)
    palette.setObjectName("RuntimeAuditColorPalette")
    palette.setProperty("runtimeTextColorControl", True)
    palette.setFixedSize(palette_width, palette_height)
    palette.setToolTip("Text color")
    grid = QGridLayout(palette)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(_SWATCH_GAP)
    grid.setVerticalSpacing(_SWATCH_GAP)
    for index, color in enumerate(colors):
        grid.addWidget(_make_swatch(palette, root, color), index % 2, index // 2)

    add = QPushButton("+", bar)
    add.setObjectName("RuntimeAuditAddColorButton")
    add.setProperty("runtimeTextColorControl", True)
    add.setFixedSize(_ADD_BUTTON_WIDTH, palette_height)
    add.setToolTip("Add custom color")
    add.setStyleSheet(
        "QPushButton#RuntimeAuditAddColorButton{background:#fff2be;border:1px solid #b98920;"
        "border-radius:4px;color:#132238;font-family:'Times New Roman';font-size:10px;font-weight:800;"
        "padding:0;margin:0;}"
        "QPushButton#RuntimeAuditAddColorButton:hover{background:#ffd36d;border-color:#ff8a35;}"
        "QPushButton#RuntimeAuditAddColorButton:pressed{background:#f18a2a;color:#ffffff;}"
    )
    add.clicked.connect(lambda checked=False, w=root: _add_custom_color(w))

    holder = QWidget(bar)
    holder.setObjectName("RuntimeAuditColorPaletteHolder")
    holder.setProperty("runtimeTextColorControl", True)
    holder.setFixedSize(palette_width + _ADD_BUTTON_GAP + _ADD_BUTTON_WIDTH, palette_height)
    layout = QHBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(_ADD_BUTTON_GAP)
    layout.addWidget(palette)
    layout.addWidget(add)
    bar_layout = bar.layout()
    if isinstance(bar_layout, QHBoxLayout):
        bar_layout.addWidget(holder)


def _style_text_bar(root: QWidget | None) -> None:
    if root is None:
        return
    bar = root.findChild(QWidget, "InlineTextBar")
    if bar is None:
        return
    bar.setMinimumWidth(max(bar.minimumWidth(), 960))
    bar.setFixedHeight(max(bar.height(), 52))
    layout = bar.layout()
    if isinstance(layout, QHBoxLayout):
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(5)
    for button in bar.findChildren(QPushButton):
        if button.objectName() in {"InlineColorSwatch", "RuntimeAuditAddColorButton"}:
            continue
        button.setToolTip(button.toolTip() or button.text())
        if button.toolTip() in {"Bold", "Italic", "Align left", "Align center", "Align right", "Justify", "Left to right", "Right to left", "Line spacing"}:
            button.setFixedSize(34, 32)


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


def _reapply_visible_runtime(root: QWidget | None) -> None:
    _cleanup_lower_text_bars(root)
    _style_text_bar(root)
    _install_inline_palette(root)


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

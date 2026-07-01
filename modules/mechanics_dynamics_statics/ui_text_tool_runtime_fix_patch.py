"""Runtime fix for the final Text tool UI.

This patch runs last in the engineering module chain. It owns the final runtime
behavior for cursors, the top Text bar, Text Box painting/editing, and the basic
View state bridge so older patches cannot bring back hand cursors or lower text
bars.
"""

from __future__ import annotations

import html

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QTextDocument
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QWidget,
)

PATCH_VERSION = "engineering-ui-text-runtime-fix-2026-07-01-b"

FONT_CHOICES = (
    "Times New Roman",
    "Arial",
    "Calibri",
    "Cambria",
    "Cambria Math",
    "Segoe UI",
    "Tahoma",
    "Verdana",
    "Georgia",
    "Courier New",
    "Consolas",
    "Symbol",
)

_SMALL_CURSOR_OVERRIDES = {
    "default": ("mouse_cursor.svg", 3, 3, 24),
    "select": ("mouse_cursor.svg", 3, 3, 24),
    "hand_open": ("mouse_cursor.svg", 3, 3, 24),
    "hand_closed": ("move_cursor.svg", 14, 14, 28),
    "pan_open": ("mouse_cursor.svg", 3, 3, 24),
    "pan_closed": ("move_cursor.svg", 14, 14, 28),
    "move": ("move_cursor.svg", 14, 14, 28),
    "move_drag": ("move_cursor.svg", 14, 14, 28),
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

_TOOLBAR_STYLE = (
    "QFrame#InlineTextBar{"
    "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.48 #eef8ff,stop:1 #fff0c8);"
    "border:1px solid #7f95b2;border-radius:13px;}"
    "QComboBox{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#132238;"
    "font-family:'Times New Roman';font-size:12px;font-weight:800;font-style:normal;padding:1px 35px 1px 9px;}"
    "QComboBox::drop-down{width:32px;border:0;subcontrol-origin:border;subcontrol-position:center right;"
    "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #fff0a8,stop:1 #ffc95c);"
    "border-top-right-radius:8px;border-bottom-right-radius:8px;}"
    "QSpinBox{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#132238;"
    "font-family:'Times New Roman';font-size:12px;font-weight:800;font-style:normal;padding:1px 34px 1px 8px;}"
    "QPushButton{background:#ffffff;border:1px solid #9fb0c5;border-radius:9px;color:#132238;"
    "font-family:'Times New Roman';font-size:11px;font-weight:800;font-style:normal;}"
    "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"
    "QPushButton:checked{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffc35a,stop:1 #f18a2a);"
    "border-color:#7e5b10;color:#102238;padding-top:2px;}"
    "QPushButton:pressed{background:#d9e9f7;padding-top:2px;}"
)


def _font(widget: QWidget, size: int = 11, *, italic: bool = False) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setBold(True)
    font.setItalic(italic)
    widget.setFont(font)


def _inside(widget: QWidget, parent: QWidget | None) -> bool:
    current = widget
    while current is not None:
        if current is parent:
            return True
        current = current.parentWidget()
    return False


def _delete(widget: QWidget) -> None:
    widget.hide()
    widget.setParent(None)
    widget.deleteLater()


def _remove_lower_text_bars(root: QWidget | None) -> None:
    if root is None:
        return
    command_bar = root.findChild(QWidget, "CommandBar")
    for child in root.findChildren(QWidget):
        name = (child.objectName() or "").lower()
        if name == "canvastexteditor":
            continue
        if name == "inlinetextbar" and command_bar is not None and not _inside(child, command_bar):
            _delete(child)
            continue
        if name in {"textsubbar", "texttoolbar", "texttoolbox", "floatingtextbar"}:
            _delete(child)
            continue
        if isinstance(child, QFrame) and name.startswith("text") and command_bar is not None and not _inside(child, command_bar):
            _delete(child)
    start_bar = getattr(root, "_start_bar_widget", None)
    if start_bar is not None:
        legacy = getattr(start_bar, "_text_toolbar_widget", None)
        if legacy is not None and command_bar is not None and not _inside(legacy, command_bar):
            _delete(legacy)
            start_bar._text_toolbar_widget = None


def _text_controls(root: QWidget | None) -> dict:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    return controls if isinstance(controls, dict) else {}


def _active_editor(root: QWidget | None) -> QTextEdit | None:
    canvas = getattr(root, "_canvas", None) if root is not None else None
    editor = getattr(canvas, "_active_text_editor", None) if canvas is not None else None
    return editor if isinstance(editor, QTextEdit) else None


def _apply_text_action(root: QWidget | None, command: str, value=None) -> None:
    editor = _active_editor(root)
    controls = _text_controls(root)
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}

    if command == "bold":
        active = bool(value)
        button = buttons.get("Bold") if isinstance(buttons, dict) else None
        if button is not None:
            active = button.isChecked()
        if editor is not None:
            font = editor.currentFont()
            font.setBold(active)
            editor.setCurrentFont(font)
        return
    if command == "italic":
        active = bool(value)
        button = buttons.get("Italic") if isinstance(buttons, dict) else None
        if button is not None:
            active = button.isChecked()
        if editor is not None:
            font = editor.currentFont()
            font.setItalic(active)
            editor.setCurrentFont(font)
        return
    if editor is None:
        return
    if command == "bullet":
        prefix = {
            "filled": "• ",
            "hollow": "○ ",
            "square": "■ ",
            "diamond": "◆ ",
            "arrow": "➤ ",
            "check": "✓ ",
        }.get(str(value), "")
        if prefix:
            editor.textCursor().insertText(prefix)
    elif command == "numbering":
        prefix = {
            "decimal_dot": "1. ",
            "decimal_paren": "1) ",
            "roman": "I. ",
            "alpha_upper": "A. ",
            "alpha_lower": "a. ",
            "roman_lower": "i. ",
        }.get(str(value), "")
        if prefix:
            editor.textCursor().insertText(prefix)
    elif command == "align":
        mapping = {
            "left": Qt.AlignmentFlag.AlignLeft,
            "center": Qt.AlignmentFlag.AlignCenter,
            "right": Qt.AlignmentFlag.AlignRight,
            "justify": Qt.AlignmentFlag.AlignJustify,
        }
        editor.setAlignment(mapping.get(str(value), Qt.AlignmentFlag.AlignLeft))
    elif command == "direction":
        editor.setLayoutDirection(Qt.LayoutDirection.RightToLeft if value == "rtl" else Qt.LayoutDirection.LeftToRight)
        editor.setAlignment(Qt.AlignmentFlag.AlignRight if value == "rtl" else Qt.AlignmentFlag.AlignLeft)
    elif command == "line_spacing":
        editor.textCursor().insertText("\n")
    elif command == "text_color":
        editor.setTextColor(QColor(str(value)))


def _menu_action(menu: QMenu, text: str, callback) -> None:
    action = menu.addAction(text)
    action.triggered.connect(callback)


def _attach_button_menus(bar: QWidget) -> None:
    window = bar.window()
    for button in bar.findChildren(QPushButton):
        tooltip = button.toolTip()
        if tooltip == "Italic":
            font = button.font()
            font.setItalic(True)
            button.setFont(font)
            button.clicked.connect(lambda checked=False, w=window: _apply_text_action(w, "italic", checked))
        elif tooltip == "Bold":
            button.clicked.connect(lambda checked=False, w=window: _apply_text_action(w, "bold", checked))
        elif tooltip == "Bullet" and button.menu() is None:
            menu = QMenu(button)
            _menu_action(menu, "None", lambda w=window: _apply_text_action(w, "bullet", "none"))
            _menu_action(menu, "● Filled circle", lambda w=window: _apply_text_action(w, "bullet", "filled"))
            _menu_action(menu, "○ Hollow circle", lambda w=window: _apply_text_action(w, "bullet", "hollow"))
            _menu_action(menu, "■ Square", lambda w=window: _apply_text_action(w, "bullet", "square"))
            _menu_action(menu, "◆ Diamond", lambda w=window: _apply_text_action(w, "bullet", "diamond"))
            _menu_action(menu, "➤ Arrow", lambda w=window: _apply_text_action(w, "bullet", "arrow"))
            _menu_action(menu, "✓ Check", lambda w=window: _apply_text_action(w, "bullet", "check"))
            menu.addSeparator()
            _menu_action(menu, "Custom bullet settings...", lambda: None)
            button.setMenu(menu)
        elif tooltip == "Numbering" and button.menu() is None:
            menu = QMenu(button)
            _menu_action(menu, "None", lambda w=window: _apply_text_action(w, "numbering", "none"))
            _menu_action(menu, "1. 2. 3.", lambda w=window: _apply_text_action(w, "numbering", "decimal_dot"))
            _menu_action(menu, "1) 2) 3)", lambda w=window: _apply_text_action(w, "numbering", "decimal_paren"))
            _menu_action(menu, "I. II. III.", lambda w=window: _apply_text_action(w, "numbering", "roman"))
            _menu_action(menu, "A. B. C.", lambda w=window: _apply_text_action(w, "numbering", "alpha_upper"))
            _menu_action(menu, "a. b. c.", lambda w=window: _apply_text_action(w, "numbering", "alpha_lower"))
            _menu_action(menu, "i. ii. iii.", lambda w=window: _apply_text_action(w, "numbering", "roman_lower"))
            menu.addSeparator()
            _menu_action(menu, "Custom numbering settings...", lambda: None)
            button.setMenu(menu)
        elif tooltip == "Align left":
            button.setText("☰")
            button.clicked.connect(lambda checked=False, w=window: _apply_text_action(w, "align", "left"))
        elif tooltip == "Align center":
            button.setText("≡")
            button.clicked.connect(lambda checked=False, w=window: _apply_text_action(w, "align", "center"))
        elif tooltip == "Align right":
            button.setText("☷")
            button.clicked.connect(lambda checked=False, w=window: _apply_text_action(w, "align", "right"))
        elif tooltip == "Justify":
            button.setText("▤")
            button.clicked.connect(lambda checked=False, w=window: _apply_text_action(w, "align", "justify"))
        elif tooltip == "Left to right":
            button.setText("¶→")
            button.clicked.connect(lambda checked=False, w=window: _apply_text_action(w, "direction", "ltr"))
        elif tooltip == "Right to left":
            button.setText("←¶")
            button.clicked.connect(lambda checked=False, w=window: _apply_text_action(w, "direction", "rtl"))
        elif tooltip == "Line spacing" and button.menu() is None:
            button.setText("↕")
            menu = QMenu(button)
            for label in ("1.0", "1.15", "1.5", "2.0"):
                _menu_action(menu, label, lambda checked=False, w=window, v=label: _apply_text_action(w, "line_spacing", v))
            menu.addSeparator()
            _menu_action(menu, "Line and paragraph settings...", lambda: None)
            button.setMenu(menu)

    if bar.findChild(QPushButton, "TextColorButton") is None:
        color = QPushButton("A")
        color.setObjectName("TextColorButton")
        color.setToolTip("Text and bullet color")
        color.setFixedSize(38, 32)
        _font(color, 11)
        color.setStyleSheet("QPushButton#TextColorButton{background:#ffffff;border:1px solid #9fb0c5;border-radius:9px;color:#132238;font-family:'Times New Roman';font-size:12px;font-weight:800;} QPushButton#TextColorButton:hover{background:#fff4cf;border-color:#ff8a35;}")
        menu = QMenu(color)
        palette = (
            ("Black", "#132238"), ("Blue", "#2f7df6"), ("Navy", "#0f2a44"), ("Orange", "#f18a2a"),
            ("Red", "#c9342b"), ("Green", "#168a50"), ("Purple", "#6e4ad6"), ("Gray", "#536271"),
        )
        for label, value in palette:
            _menu_action(menu, f"■ {label}", lambda checked=False, w=window, v=value: _apply_text_action(w, "text_color", v))
        menu.addSeparator()
        _menu_action(menu, "Bullet color follows text ✓", lambda: None)
        _menu_action(menu, "Bullet custom color...", lambda: None)
        _menu_action(menu, "Number custom color...", lambda: None)
        color.setMenu(menu)
        layout = bar.layout()
        if isinstance(layout, QHBoxLayout):
            layout.addWidget(color)


def _style_inline_text_bar(bar: QWidget | None) -> None:
    if bar is None:
        return
    bar.setObjectName("InlineTextBar")
    bar.setProperty("runtimeFix", PATCH_VERSION)
    bar.setFixedHeight(46)
    bar.setMinimumWidth(860)
    bar.setMaximumWidth(1120)
    bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    bar.setStyleSheet(_TOOLBAR_STYLE)
    layout = bar.layout()
    if isinstance(layout, QHBoxLayout):
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)
    combos = bar.findChildren(QComboBox)
    for index, combo in enumerate(combos):
        combo.blockSignals(True)
        if index == 0:
            existing = combo.currentText() or "Times New Roman"
            combo.clear()
            combo.addItems(list(FONT_CHOICES))
            combo.setCurrentText(existing if combo.findText(existing) >= 0 else "Times New Roman")
            combo.setFixedSize(220, 34)
            combo.setToolTip("Font family")
        else:
            combo.setFixedSize(104, 34)
        combo.blockSignals(False)
        _font(combo, 12)
    for spin in bar.findChildren(QSpinBox):
        spin.setFixedSize(126, 34)
        spin.setToolTip("Font size")
        _font(spin, 12)
    for button in bar.findChildren(QPushButton):
        if button.toolTip():
            button.setStatusTip(button.toolTip())
            button.setToolTipDuration(5000)
        _font(button, 11, italic=button.toolTip() == "Italic")
        width = max(button.width(), 38 if len(button.text()) <= 2 else 54)
        button.setFixedSize(width, 32)
    _attach_button_menus(bar)


def _patch_start_bar(sb, text_final) -> None:
    if getattr(sb.StartBar, "_engineering_text_runtime_fix", "") == PATCH_VERSION:
        return
    old_ensure = sb.StartBar._ensure_text_toolbar
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


def _scene_rect_to_widget(canvas, rect: QRectF) -> QRect:
    zoom = max(float(getattr(canvas, "_zoom", 1.0)), 0.01)
    cx = canvas.width() / 2.0
    cy = canvas.height() / 2.0
    left = (rect.left() - cx) * zoom + cx
    top = (rect.top() - cy) * zoom + cy
    return QRect(round(left), round(top), max(42, round(rect.width() * zoom)), max(34, round(rect.height() * zoom)))


def _show_rich_text_editor(canvas, index: int) -> None:
    if not (0 <= index < len(canvas.objects)):
        return
    obj = canvas.objects[index]
    if not getattr(obj, "is_text_box", False):
        return
    _hide_rich_text_editor(canvas)
    editor = QTextEdit(canvas)
    editor.setObjectName("CanvasTextEditor")
    editor.setAcceptRichText(True)
    html_text = str(getattr(obj, "text_html", ""))
    if html_text:
        editor.setHtml(html_text)
    else:
        editor.setPlainText(str(getattr(obj, "text", "")))
    editor.setPlaceholderText("Type text...")
    editor.setGeometry(_scene_rect_to_widget(canvas, obj.rect).adjusted(3, 3, -3, -3))
    font = QFont(str(getattr(obj, "text_font", "Times New Roman")), int(getattr(obj, "text_size", 12)))
    font.setBold(bool(getattr(obj, "text_bold", False)))
    font.setItalic(bool(getattr(obj, "text_italic", False)))
    editor.setFont(font)
    editor.setStyleSheet("QTextEdit#CanvasTextEditor{background:rgba(255,255,255,232);border:1px solid #ff8a35;border-radius:6px;color:#132238;padding:4px;font-family:'Times New Roman';}")

    def save() -> None:
        obj.text = editor.toPlainText()
        obj.text_html = editor.toHtml()
        canvas.update()

    editor.textChanged.connect(save)
    editor.show()
    editor.raise_()
    editor.setFocus()
    canvas._active_text_editor = editor
    canvas._active_text_editor_index = index


def _hide_rich_text_editor(canvas) -> None:
    editor = getattr(canvas, "_active_text_editor", None)
    if isinstance(editor, QTextEdit):
        index = getattr(canvas, "_active_text_editor_index", None)
        if isinstance(index, int) and 0 <= index < len(canvas.objects):
            obj = canvas.objects[index]
            obj.text = editor.toPlainText()
            obj.text_html = editor.toHtml()
        editor.hide()
        editor.deleteLater()
    canvas._active_text_editor = None
    canvas._active_text_editor_index = None


def _paint_text_object(canvas, painter: QPainter, obj) -> None:
    rect = obj.rect
    painter.save()
    painter.translate(rect.center())
    painter.rotate(obj.rotation)
    local = QRectF(-rect.width() / 2, -rect.height() / 2, rect.width(), rect.height())
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    plain = str(getattr(obj, "text", ""))
    html_text = str(getattr(obj, "text_html", ""))
    selected = False
    try:
        selected = canvas.objects.index(obj) in getattr(canvas, "selected_indices", set())
    except ValueError:
        selected = False
    if not plain and selected:
        painter.setPen(QPen(QColor("#2f7df6"), 1.0, Qt.PenStyle.DashLine))
        painter.setBrush(QColor(255, 255, 255, 34))
        painter.drawRoundedRect(local, 4, 4)
    if plain or html_text:
        doc = QTextDocument()
        font = QFont(str(getattr(obj, "text_font", "Times New Roman")), int(getattr(obj, "text_size", 12)))
        font.setBold(bool(getattr(obj, "text_bold", False)))
        font.setItalic(bool(getattr(obj, "text_italic", False)))
        doc.setDefaultFont(font)
        doc.setDefaultStyleSheet("body{color:#132238;font-family:'Times New Roman';} sup{font-size:70%;} sub{font-size:70%;}")
        if html_text:
            doc.setHtml(html_text)
        else:
            doc.setHtml("<div>" + html.escape(plain).replace("\n", "<br>") + "</div>")
        doc.setTextWidth(max(1.0, local.width() - 12.0))
        painter.translate(local.left() + 6.0, local.top() + 6.0)
        doc.drawContents(painter, QRectF(0, 0, max(1.0, local.width() - 12.0), max(1.0, local.height() - 12.0)))
    painter.restore()


def _set_project_cursor(canvas, svg, kind: str) -> None:
    try:
        setter = getattr(svg, "_set_cursor_kind", None)
        if callable(setter):
            setter(canvas, kind)
            return
        canvas.setCursor(svg.project_cursor(kind))
    except Exception:
        fallback = Qt.CursorShape.ArrowCursor
        if kind.startswith("resize"):
            fallback = Qt.CursorShape.SizeAllCursor
        elif kind.startswith("rotate"):
            fallback = Qt.CursorShape.CrossCursor
        elif kind.startswith("move"):
            fallback = Qt.CursorShape.SizeAllCursor
        canvas.setCursor(fallback)


def _hover_kind(canvas, point: QPointF) -> str | None:
    try:
        _index, action = canvas._hit_test_object(point)
    except Exception:
        return None
    if action in _ACTION_TO_CURSOR:
        return _ACTION_TO_CURSOR[action]
    return None


def _patch_canvas_runtime(edw, svg, text_final) -> None:
    if getattr(edw.EngineeringCanvas, "_text_runtime_hardened", "") == PATCH_VERSION:
        return

    old_paint_object = edw.EngineeringCanvas._paint_object
    old_press = edw.EngineeringCanvas.mousePressEvent
    old_move = edw.EngineeringCanvas.mouseMoveEvent
    old_release = edw.EngineeringCanvas.mouseReleaseEvent
    old_leave = edw.EngineeringCanvas.leaveEvent

    def paint_object(self, painter: QPainter, obj) -> None:
        if getattr(obj, "is_text_box", False):
            _paint_text_object(self, painter, obj)
            return
        old_paint_object(self, painter, obj)

    def mouse_press(self, event) -> None:
        old_press(self, event)
        action = getattr(self, "_drag_action", None)
        kind = _ACTION_TO_CURSOR.get(str(action))
        if kind:
            _set_project_cursor(self, svg, kind)

    def mouse_move(self, event) -> None:
        old_move(self, event)
        action = getattr(self, "_drag_action", None)
        kind = _ACTION_TO_CURSOR.get(str(action))
        if kind is None:
            try:
                kind = _hover_kind(self, self._to_canvas_point(event.position()))
            except Exception:
                kind = None
        if kind:
            _set_project_cursor(self, svg, kind)

    def mouse_release(self, event) -> None:
        old_release(self, event)
        try:
            kind = _hover_kind(self, self._to_canvas_point(event.position()))
        except Exception:
            kind = None
        if kind:
            _set_project_cursor(self, svg, kind)

    def leave_event(self, event) -> None:
        old_leave(self, event)
        _set_project_cursor(self, svg, "default")

    text_final._show_text_editor = _show_rich_text_editor
    text_final._hide_text_editor = _hide_rich_text_editor
    edw.EngineeringCanvas._paint_object = paint_object
    edw.EngineeringCanvas.mousePressEvent = mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    edw.EngineeringCanvas.leaveEvent = leave_event
    edw.EngineeringCanvas._text_runtime_hardened = PATCH_VERSION


def _style_file_properties_dialog(epp) -> None:
    dialog_cls = getattr(epp, "PropertiesDialog", None)
    if dialog_cls is None or getattr(dialog_cls, "_runtime_standard_style", "") == PATCH_VERSION:
        return
    old_init = dialog_cls.__init__

    def init(self, *args, **kwargs) -> None:
        old_init(self, *args, **kwargs)
        self.setMinimumWidth(max(self.minimumWidth(), 520))
        self.setStyleSheet(self.styleSheet() + "\n" +
            "QDialog{background:#eaf4ff;} QLabel{font-family:'Times New Roman';font-weight:800;font-style:normal;color:#173454;}"
            "QFrame#FilePropertiesWaveSection{background:transparent;}"
            "QComboBox,QSpinBox,QDoubleSpinBox{min-height:25px;font-family:'Times New Roman';font-weight:800;font-style:normal;}"
            "QPushButton{font-family:'Times New Roman';font-weight:800;font-style:normal;}"
            "QCheckBox{font-family:'Times New Roman';font-weight:800;font-style:normal;color:#173454;}"
        )
        for label in self.findChildren(QLabel):
            _font(label, 9)
        for combo in self.findChildren(QComboBox):
            _font(combo, 9)
        for spin in self.findChildren(QSpinBox) + self.findChildren(QDoubleSpinBox):
            _font(spin, 9)
        for button in self.findChildren(QPushButton):
            _font(button, 9)

    dialog_cls.__init__ = init
    dialog_cls._runtime_standard_style = PATCH_VERSION


def _patch_view_sync(epp) -> None:
    if getattr(epp, "_runtime_view_sync_patch", "") == PATCH_VERSION:
        return
    old_apply = epp._apply_settings

    def apply_settings(workspace, settings: dict, reinstall_shortcuts: bool = True) -> None:
        old_apply(workspace, settings, reinstall_shortcuts=reinstall_shortcuts)
        start_bar = getattr(workspace, "_start_bar_widget", None)
        if start_bar is None:
            return
        view = settings.get("view", {}) if isinstance(settings, dict) else {}
        state = view.get("startbar", {}) if isinstance(view, dict) else {}
        setattr(start_bar, "_view_state", dict(state))
        for key, visible in state.items():
            if key == "text_toolbar":
                setter = getattr(start_bar, "_set_text_toolbar_visible", None)
                if callable(setter):
                    setter(bool(visible), False)
                continue
            button = getattr(start_bar, "_buttons", {}).get(key)
            if button is not None:
                button.setVisible(bool(visible))
        for check in workspace.findChildren(QCheckBox):
            key = check.property("toolKey") or check.property("viewKey")
            if key in state:
                check.setChecked(bool(state[key]))

    epp._apply_settings = apply_settings
    epp._runtime_view_sync_patch = PATCH_VERSION


def _apply_cursor_maps(svg, fcp) -> None:
    svg._CURSOR_ASSET_MAP.update(_SMALL_CURSOR_OVERRIDES)
    if hasattr(svg, "_HAND_FILE_REDIRECTS"):
        svg._HAND_FILE_REDIRECTS.update({
            "hand_open.svg": "mouse_cursor.svg",
            "hand_closed.svg": "move_cursor.svg",
            "hand_pointer.svg": "mouse_cursor.svg",
            "rotate_cursor.svg": "rotate.svg",
        })
    svg._CURSOR_CACHE.clear()
    fcp._CURSOR_ASSET_OVERRIDES.update(_SMALL_CURSOR_OVERRIDES)


def apply_ui_text_tool_runtime_fix_patch() -> None:
    from . import final_cursor_properties_textbar_patch as fcp
    from . import svg_cursor_assets_activation_patch as svg
    from . import ui_text_tool_final_patch as text_final
    from . import workspace as edw
    from src.engineers_tools.app import engineering_properties_patch as epp
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_ui_text_runtime_fix_patch", "") == PATCH_VERSION:
        return

    _apply_cursor_maps(svg, fcp)
    _patch_start_bar(sb, text_final)
    _patch_canvas_runtime(edw, svg, text_final)
    _patch_view_sync(epp)
    _style_file_properties_dialog(epp)

    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _apply_cursor_maps(svg, fcp)
        _remove_lower_text_bars(self)
        start_bar = getattr(self, "_start_bar_widget", None)
        if start_bar is not None:
            QTimer.singleShot(0, lambda sb=start_bar: sb._set_text_toolbar_visible(True, emit=False))
            QTimer.singleShot(50, lambda root=self: _remove_lower_text_bars(root))
            QTimer.singleShot(250, lambda root=self: _remove_lower_text_bars(root))
            QTimer.singleShot(800, lambda root=self: _remove_lower_text_bars(root))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_ui_text_runtime_fix_patch = PATCH_VERSION

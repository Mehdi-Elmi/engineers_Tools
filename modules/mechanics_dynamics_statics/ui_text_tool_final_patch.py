"""Final text tool and cursor sizing patch.

This patch owns the text UI. It keeps the accepted Move cursor unchanged,
shrinks Rotate/Resize cursors to a moderate size, prevents the legacy lower
TextSubBar from existing, and creates editable Text Box objects on the canvas.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QPointF, QRect, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QFrame, QHBoxLayout, QPushButton, QSizePolicy, QSpinBox, QTextEdit, QWidget

PATCH_VERSION = "engineering-ui-text-tool-final-2026-07-02-f"
FONT_CHOICES = (
    "Times New Roman",
    "B Zar",
    "B Nazanin",
    "B Mitra",
    "B Lotus",
    "B Titr",
    "B Yekan",
    "B Koodak",
    "B Traffic",
)
CURSOR_OVERRIDES = {
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
TEXT_BUTTONS = (
    ("B", "Bold", 34, True),
    ("I", "Italic", 34, True),
    ("•", "Bullet", 34, True),
    ("1.", "Numbering", 38, True),
    ("L", "Align left", 34, True),
    ("C", "Align center", 34, True),
    ("R", "Align right", 34, True),
    ("J", "Justify", 34, True),
    ("LS", "Line spacing", 44, False),
    ("LTR", "Left to right", 50, True),
    ("RTL", "Right to left", 50, True),
    ("Σ", "Math symbols", 36, False),
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
    spin.setFixedHeight(30)
    spin.setStyleSheet(
        "QSpinBox,QDoubleSpinBox{background:#fffdf6;border:1px solid #c29122;border-radius:9px;color:#132238;font-family:'Times New Roman';font-size:11px;font-weight:800;font-style:normal;padding:1px 28px 1px 8px;}"
        "QSpinBox::up-button,QDoubleSpinBox::up-button{width:26px;border:0;subcontrol-origin:border;subcontrol-position:top right;background:transparent;border-top-right-radius:8px;}"
        "QSpinBox::down-button,QDoubleSpinBox::down-button{width:26px;border:0;subcontrol-origin:border;subcontrol-position:bottom right;background:transparent;border-bottom-right-radius:8px;}"
        "QSpinBox::up-arrow,QDoubleSpinBox::up-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:7px solid #102238;}"
        "QSpinBox::down-arrow,QDoubleSpinBox::down-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:7px solid #102238;}"
        "QSpinBox:focus,QDoubleSpinBox:focus{border:1px solid #ff8a35;}"
    )


def _style_text_combo(svg, combo: QComboBox) -> None:
    combo.setFixedHeight(30)
    combo.setStyleSheet(
        "QComboBox{background:#ffffff;border:1px solid #9fb0c5;border-radius:9px;color:#132238;font-family:'Times New Roman';font-size:11px;font-weight:800;font-style:normal;padding:1px 28px 1px 9px;}"
        "QComboBox::drop-down{width:26px;border:0;subcontrol-origin:border;subcontrol-position:center right;background:transparent;border-top-right-radius:8px;border-bottom-right-radius:8px;}"
        "QComboBox::down-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:7px solid #102238;}"
        "QComboBox:focus{border:1px solid #ff8a35;}"
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


def _scene_rect_to_widget(canvas, rect: QRectF) -> QRect:
    zoom = max(float(getattr(canvas, "_zoom", 1.0)), 0.01)
    cx = canvas.width() / 2.0
    cy = canvas.height() / 2.0
    left = (rect.left() - cx) * zoom + cx
    top = (rect.top() - cy) * zoom + cy
    return QRect(round(left), round(top), max(42, round(rect.width() * zoom)), max(34, round(rect.height() * zoom)))


def _save_editor_text(canvas, editor: QTextEdit | None = None) -> None:
    if canvas is None:
        return
    editor = editor or getattr(canvas, "_active_text_editor", None)
    index = getattr(canvas, "_active_text_editor_index", None)
    if editor is None or index is None or not (0 <= index < len(canvas.objects)):
        return
    obj = canvas.objects[index]
    obj.text = editor.toPlainText()
    obj.text_html = editor.toHtml()
    font = editor.currentFont()
    obj.text_font = font.family() or getattr(obj, "text_font", "Times New Roman")
    obj.text_size = max(1, font.pointSize() if font.pointSize() > 0 else int(getattr(obj, "text_size", 12)))
    obj.text_bold = font.bold()
    obj.text_italic = font.italic()
    obj.text_rtl = editor.layoutDirection() == Qt.LayoutDirection.RightToLeft
    alignment = editor.alignment()
    if alignment & Qt.AlignmentFlag.AlignJustify:
        obj.text_align = "justify"
    elif alignment & Qt.AlignmentFlag.AlignHCenter:
        obj.text_align = "center"
    elif alignment & Qt.AlignmentFlag.AlignRight:
        obj.text_align = "right"
    else:
        obj.text_align = "left"
    canvas.update()


def _text_key_is(event, key: Qt.Key, *, ctrl: bool = False) -> bool:
    has_ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
    return event.key() == key and has_ctrl == ctrl


def _handle_editor_key(editor: QTextEdit, event) -> bool:
    canvas = getattr(editor, "_canvas_owner", None)
    if _text_key_is(event, Qt.Key.Key_C, ctrl=True):
        editor.copy()
        event.accept()
        return True
    if _text_key_is(event, Qt.Key.Key_X, ctrl=True):
        editor.cut()
        _save_editor_text(canvas, editor)
        event.accept()
        return True
    if _text_key_is(event, Qt.Key.Key_V, ctrl=True):
        editor.paste()
        _save_editor_text(canvas, editor)
        event.accept()
        return True
    if _text_key_is(event, Qt.Key.Key_A, ctrl=True):
        editor.selectAll()
        event.accept()
        return True
    if event.key() == Qt.Key.Key_Backspace:
        cursor = editor.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        else:
            cursor.deletePreviousChar()
        editor.setTextCursor(cursor)
        _save_editor_text(canvas, editor)
        event.accept()
        return True
    if event.key() == Qt.Key.Key_Delete:
        cursor = editor.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        else:
            cursor.deleteChar()
        editor.setTextCursor(cursor)
        _save_editor_text(canvas, editor)
        event.accept()
        return True
    return False


class _CanvasTextEdit(QTextEdit):
    def __init__(self, canvas) -> None:
        super().__init__(canvas)
        self._canvas_owner = canvas
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def event(self, event) -> bool:
        if event.type() == QEvent.Type.ShortcutOverride:
            if event.key() in (Qt.Key.Key_C, Qt.Key.Key_X, Qt.Key.Key_V, Qt.Key.Key_A, Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                event.accept()
                return True
        return super().event(event)

    def keyPressEvent(self, event) -> None:
        if _handle_editor_key(self, event):
            return
        super().keyPressEvent(event)
        _save_editor_text(self._canvas_owner, self)

    def contextMenuEvent(self, event) -> None:
        menu = self.createStandardContextMenu(event.pos())
        if self.textCursor().hasSelection():
            menu.addSeparator()
            delete_action = menu.addAction("Delete Selection")
            delete_action.triggered.connect(lambda: (_handle_editor_context_delete(self)))
        menu.exec(event.globalPos())
        menu.deleteLater()


def _handle_editor_context_delete(editor: QTextEdit) -> None:
    cursor = editor.textCursor()
    if cursor.hasSelection():
        cursor.removeSelectedText()
        editor.setTextCursor(cursor)
        _save_editor_text(getattr(editor, "_canvas_owner", None), editor)


def _current_text_settings(window: QWidget | None) -> dict[str, object]:
    start_bar = getattr(window, "_start_bar_widget", None) if window is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    font_combo = controls.get("font") if isinstance(controls, dict) else None
    size_spin = controls.get("size") if isinstance(controls, dict) else None
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    font_name = font_combo.currentText() if isinstance(font_combo, QComboBox) else "Times New Roman"
    font_size = size_spin.value() if isinstance(size_spin, QSpinBox) else 12
    return {
        "font": font_name or "Times New Roman",
        "size": int(font_size),
        "bold": bool(buttons.get("Bold").isChecked()) if buttons.get("Bold") is not None else False,
        "italic": bool(buttons.get("Italic").isChecked()) if buttons.get("Italic") is not None else False,
        "align": "right" if bool(buttons.get("Right to left").isChecked()) if buttons.get("Right to left") is not None else False else "left",
        "rtl": bool(buttons.get("Right to left").isChecked()) if buttons.get("Right to left") is not None else False,
    }


def _show_text_editor(canvas, index: int) -> None:
    if not (0 <= index < len(canvas.objects)):
        return
    obj = canvas.objects[index]
    if not getattr(obj, "is_text_box", False):
        return
    old_editor = getattr(canvas, "_active_text_editor", None)
    if old_editor is not None:
        old_editor.hide()
        old_editor.deleteLater()
    editor = _CanvasTextEdit(canvas)
    editor.setObjectName("CanvasTextEditor")
    editor.setAcceptRichText(True)
    if getattr(obj, "text_html", ""):
        editor.setHtml(str(getattr(obj, "text_html", "")))
    else:
        editor.setPlainText(str(getattr(obj, "text", "")))
    editor.setPlaceholderText("Type text...")
    editor.setGeometry(_scene_rect_to_widget(canvas, obj.rect).adjusted(3, 3, -3, -3))
    font = QFont(str(getattr(obj, "text_font", "Times New Roman")), int(getattr(obj, "text_size", 12)))
    font.setBold(bool(getattr(obj, "text_bold", False)))
    font.setItalic(bool(getattr(obj, "text_italic", False)))
    editor.setFont(font)
    editor.setStyleSheet("QTextEdit#CanvasTextEditor{background:rgba(255,255,255,230);border:1px solid #ff8a35;border-radius:6px;color:#132238;padding:4px;font-family:'Times New Roman';font-style:normal;font-weight:400;}")
    rtl = bool(getattr(obj, "text_rtl", False))
    editor.setLayoutDirection(Qt.LayoutDirection.RightToLeft if rtl else Qt.LayoutDirection.LeftToRight)
    align_name = str(getattr(obj, "text_align", "right" if rtl else "left"))
    alignment = {
        "right": Qt.AlignmentFlag.AlignRight,
        "center": Qt.AlignmentFlag.AlignHCenter,
        "justify": Qt.AlignmentFlag.AlignJustify,
    }.get(align_name, Qt.AlignmentFlag.AlignLeft)
    editor.setAlignment(alignment)
    editor.textChanged.connect(lambda e=editor, c=canvas: _save_editor_text(c, e))
    editor.show()
    editor.raise_()
    editor.setFocus(Qt.FocusReason.MouseFocusReason)
    canvas._active_text_editor = editor
    canvas._active_text_editor_index = index


def _hide_text_editor(canvas) -> None:
    editor = getattr(canvas, "_active_text_editor", None)
    if editor is not None:
        _save_editor_text(canvas, editor)
        editor.hide()
        editor.deleteLater()
    canvas._active_text_editor = None
    canvas._active_text_editor_index = None


def _activate_text_tool(window: QWidget | None) -> None:
    if window is None:
        return
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return
    _hide_text_editor(canvas)
    canvas._text_tool_active = True
    canvas._text_box_origin = None
    canvas._text_box_preview = None
    canvas.setCursor(Qt.CursorShape.IBeamCursor)
    status = getattr(window, "_set_status", None)
    if callable(status):
        status("Text: click for 5x7 cm box, or drag to define box")


def _text_button(label: str, tooltip: str, width: int, checkable: bool) -> QPushButton:
    button = QPushButton(label)
    button.setToolTip(tooltip)
    button.setStatusTip(tooltip)
    button.setCheckable(checkable)
    button.setFixedSize(width, 30)
    _font(button, 11)
    button.setStyleSheet(
        "QPushButton{background:#fff;border:1px solid #9fb0c5;border-radius:9px;color:#132238;padding:0;outline:0;}"
        "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;}"
        "QPushButton:checked{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffc35a,stop:1 #f18a2a);border-color:#7e5b10;color:#102238;padding-top:2px;}"
        "QPushButton:pressed{background:#d9e9f7;padding-top:2px;}"
        "QPushButton:focus{outline:0;border:1px solid #9fb0c5;}"
    )
    return button


def _prepare_command_bar(command_bar: QWidget) -> None:
    command_bar.setFixedHeight(48)
    layout = command_bar.layout()
    if layout is not None:
        layout.setContentsMargins(12, 5, 12, 5)
        layout.setSpacing(8)


def _install_textbar(sb, svg) -> None:
    def make_textbar(self):
        window = self.window()
        if window is None:
            return None
        _remove_legacy_text_subbars(window)
        command_bar = window.findChild(QWidget, "CommandBar")
        if command_bar is None or command_bar.layout() is None:
            return None
        _prepare_command_bar(command_bar)
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
        bar.setMinimumWidth(700)
        bar.setMaximumWidth(860)
        bar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bar.setStyleSheet("QFrame#InlineTextBar{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fff,stop:.52 #eef8ff,stop:1 #fff1c8);border:1px solid #8fa2bb;border-radius:13px;}")
        row = QHBoxLayout(bar)
        row.setContentsMargins(9, 4, 9, 4)
        row.setSpacing(5)
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
        size.setFixedSize(110, 30)
        _style_text_spin(svg, size)
        row.addWidget(size)
        buttons: dict[str, QPushButton] = {}
        for label, tooltip, width, checkable in TEXT_BUTTONS:
            button = _text_button(label, tooltip, width, checkable)
            buttons[tooltip] = button
            row.addWidget(button)
        if "Bold" in buttons:
            buttons["Bold"].setChecked(False)
        if "Italic" in buttons:
            italic_button = buttons["Italic"]
            italic_button.setChecked(False)
            italic_font = italic_button.font()
            italic_font.setFamily("Times New Roman")
            italic_font.setPointSize(15)
            italic_font.setBold(True)
            italic_font.setItalic(True)
            italic_button.setFont(italic_font)
            italic_button.setText("I")
        self._text_controls = {"font": combo, "size": size, "buttons": buttons}
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
    old_double = edw.EngineeringCanvas.mouseDoubleClickEvent
    old_paint = edw.EngineeringCanvas.paintEvent
    old_paint_object = edw.EngineeringCanvas._paint_object

    def create_text_box(self, rect: QRectF, origin: QPointF) -> None:
        box = QRectF(rect).normalized()
        if box.width() < 10 or box.height() < 10:
            box = QRectF(origin.x(), origin.y(), 190.0, 265.0)
        if box.width() < 35:
            box.setWidth(35.0)
        if box.height() < 35:
            box.setHeight(35.0)
        settings = _current_text_settings(self.window())
        self._push_undo()
        obj = edw.CanvasObject(path=Path("Text Box"), pixmap=QPixmap(), rect=box, name="Text Box")
        obj.is_text_box = True
        obj.text = ""
        obj.text_html = ""
        obj.text_font = settings["font"]
        obj.text_size = settings["size"]
        obj.text_bold = bool(settings["bold"])
        obj.text_italic = bool(settings["italic"])
        obj.text_rtl = settings["rtl"]
        obj.text_align = settings["align"]
        self.objects.append(obj)
        index = len(self.objects) - 1
        self._select_only(index)
        self._last_action = "text"
        self._text_tool_active = False
        self._text_box_origin = None
        self._text_box_preview = None
        self._emit_object_changes()
        self.update()
        _show_text_editor(self, index)
        window = self.window()
        status = getattr(window, "_set_status", None)
        if callable(status):
            status("Text box created")

    def paint_object(self, painter: QPainter, obj) -> None:
        if not getattr(obj, "is_text_box", False):
            old_paint_object(self, painter, obj)
            return
        rect = obj.rect
        painter.save()
        painter.translate(rect.center())
        painter.rotate(obj.rotation)
        local = QRectF(-rect.width() / 2, -rect.height() / 2, rect.width(), rect.height())
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setPen(QPen(QColor("#2f7df6"), 1.1, Qt.PenStyle.DashLine))
        painter.setBrush(QColor(255, 255, 255, 210))
        painter.drawRoundedRect(local, 4, 4)
        font = QFont(str(getattr(obj, "text_font", "Times New Roman")), int(getattr(obj, "text_size", 12)))
        font.setBold(bool(getattr(obj, "text_bold", False)))
        font.setItalic(bool(getattr(obj, "text_italic", False)))
        painter.setFont(font)
        painter.setPen(QPen(QColor("#132238"), 1.0))
        align_name = str(getattr(obj, "text_align", "right" if bool(getattr(obj, "text_rtl", False)) else "left"))
        flags = {
            "right": Qt.AlignmentFlag.AlignRight,
            "center": Qt.AlignmentFlag.AlignHCenter,
            "justify": Qt.AlignmentFlag.AlignJustify,
        }.get(align_name, Qt.AlignmentFlag.AlignLeft)
        text = str(getattr(obj, "text", "")) or "Text Box"
        painter.drawText(local.adjusted(8, 7, -8, -7), flags | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, text)
        painter.restore()

    def mouse_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, "_text_tool_active", False):
            point = self._to_canvas_point(event.position())
            self._text_box_origin = point
            self._text_box_preview = QRectF(point, point)
            self._drag_action = None
            self.update()
            event.accept()
            return
        _hide_text_editor(self)
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

    def mouse_double(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            point = self._to_canvas_point(event.position())
            index, _action = self._hit_test_object(point)
            if index is not None and getattr(self.objects[index], "is_text_box", False):
                self._select_only(index)
                _show_text_editor(self, index)
                event.accept()
                return
        old_double(self, event)

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

    edw.EngineeringCanvas._paint_object = paint_object
    edw.EngineeringCanvas.mousePressEvent = mouse_press
    edw.EngineeringCanvas.mouseMoveEvent = mouse_move
    edw.EngineeringCanvas.mouseReleaseEvent = mouse_release
    edw.EngineeringCanvas.mouseDoubleClickEvent = mouse_double
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
            QTimer.singleShot(400, lambda root=self: _remove_legacy_text_subbars(root))

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_ui_text_tool_final_patch = PATCH_VERSION

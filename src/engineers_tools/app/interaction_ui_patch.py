"""Focused interaction refinements layered after the main runtime UI patch."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QShortcut
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QDoubleSpinBox, QLabel, QLineEdit, QWidget


def _triangle_arrow_head(painter: QPainter, tip: QPointF, tail: QPointF, color: QColor, size: float = 7.0) -> None:
    direction = tip - tail
    length = max(0.01, (direction.x() ** 2 + direction.y() ** 2) ** 0.5)
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    base = QPointF(tip.x() - unit.x() * size * 1.28, tip.y() - unit.y() * size * 1.28)
    neck = QPointF(tip.x() - unit.x() * size * 0.62, tip.y() - unit.y() * size * 0.62)
    left = QPointF(base.x() + normal.x() * size * 0.42, base.y() + normal.y() * size * 0.42)
    left_wing = QPointF(neck.x() + normal.x() * size * 0.74, neck.y() + normal.y() * size * 0.74)
    right_wing = QPointF(neck.x() - normal.x() * size * 0.74, neck.y() - normal.y() * size * 0.74)
    right = QPointF(base.x() - normal.x() * size * 0.42, base.y() - normal.y() * size * 0.42)
    painter.setBrush(color)
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(QPolygonF([tip, left_wing, left, right, right_wing]))


def _solid_arrow_head(painter: QPainter, tip: QPointF, back: QPointF, size: float = 6.0) -> None:
    _triangle_arrow_head(painter, tip, back, painter.pen().color(), size)


def _paint_rotation_glyph(painter: QPainter, center: QPointF, radius: float, color: QColor) -> None:
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(color, 2.15, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawArc(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), 46 * 16, 280 * 16)
    tip = QPointF(center.x() + radius * 0.77, center.y() - radius * 0.63)
    tail = QPointF(center.x() + radius * 0.06, center.y() - radius * 0.96)
    _triangle_arrow_head(painter, tip, tail, color, max(7.4, radius * 0.88))
    painter.restore()


def _hand_cursor(closed: bool = False) -> QCursor:
    cache = getattr(_hand_cursor, "_cache", {})
    if closed in cache:
        return cache[closed]
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    skin = QColor("#fff4dc")
    outline = QColor("#132238")
    painter.setPen(QPen(outline, 1.45, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(skin)
    if closed:
        palm = QPainterPath()
        palm.addRoundedRect(QRectF(8, 11, 17, 14), 6, 6)
        painter.fillPath(palm, skin)
        painter.drawPath(palm)
        for x in (9.5, 13.5, 17.5, 21.0):
            painter.drawRoundedRect(QRectF(x, 7.0, 4.3, 10.0), 2.0, 2.0)
        painter.drawLine(QPointF(12, 22), QPointF(22, 22))
    else:
        painter.drawRoundedRect(QRectF(12, 8, 5, 16), 2.4, 2.4)
        painter.drawRoundedRect(QRectF(7, 13, 5, 12), 2.4, 2.4)
        painter.drawRoundedRect(QRectF(17, 10, 5, 14), 2.4, 2.4)
        painter.drawRoundedRect(QRectF(22, 13, 5, 11), 2.4, 2.4)
        painter.drawRoundedRect(QRectF(9, 20, 16, 7), 4.0, 4.0)
    painter.end()
    cursor = QCursor(pixmap, 15, 15)
    cache[closed] = cursor
    _hand_cursor._cache = cache
    return cursor


def _move_cursor() -> QCursor:
    cache = getattr(_move_cursor, "_cache", None)
    if cache is not None:
        return cache
    pixmap = QPixmap(34, 34)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    ink = QColor("#132238")
    accent = QColor("#2f7df6")
    painter.setPen(QPen(ink, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    center = QPointF(17, 17)
    for tip in (QPointF(17, 3), QPointF(31, 17), QPointF(17, 31), QPointF(3, 17)):
        painter.drawLine(center, tip)
        _triangle_arrow_head(painter, tip, center, accent, 6.2)
        painter.setPen(QPen(ink, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(QColor("#fff9de"))
    painter.setPen(QPen(QColor("#7e5b10"), 1.3))
    painter.drawEllipse(center, 4.0, 4.0)
    painter.end()
    cursor = QCursor(pixmap, 17, 17)
    _move_cursor._cache = cursor
    return cursor


def _layer_icon(kind: str, active: bool = True) -> QIcon:
    pixmap = QPixmap(34, 34)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    shell = QPainterPath()
    shell.addRoundedRect(QRectF(2.5, 2.5, 29, 29), 10, 10)
    gradient = QLinearGradient(2, 2, 32, 32)
    gradient.setColorAt(0.0, QColor("#ffffff"))
    gradient.setColorAt(0.52, QColor("#e8f8ff" if active else "#eef1f5"))
    gradient.setColorAt(1.0, QColor("#5fd0ea" if active else "#9aa9ba"))
    painter.fillPath(shell, gradient)
    painter.setPen(QPen(QColor("#55708f"), 1.1))
    painter.drawPath(shell)
    ink = QColor("#132238")
    painter.setPen(QPen(ink, 2.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    if kind == "eye":
        eye = QPainterPath()
        eye.moveTo(6.5, 17)
        eye.cubicTo(10.4, 9.8, 23.6, 9.8, 27.5, 17)
        eye.cubicTo(23.6, 24.2, 10.4, 24.2, 6.5, 17)
        painter.drawPath(eye)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2f7df6" if active else "#8b98a8"))
        painter.drawEllipse(QPointF(17, 17), 4.5, 4.5)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QPointF(18.6, 15.4), 1.25, 1.25)
    elif kind == "lock":
        if active:
            painter.drawArc(QRectF(10, 7, 14, 14), 0, 180 * 16)
        else:
            painter.drawArc(QRectF(11, 7, 14, 14), 35 * 16, 145 * 16)
            painter.drawLine(QPointF(22, 11), QPointF(26, 8.4))
        body = QPainterPath()
        body.addRoundedRect(QRectF(8.5, 15, 17, 11), 3.5, 3.5)
        painter.drawPath(body)
        painter.setPen(Qt.NoPen)
        painter.setBrush(ink)
        painter.drawEllipse(QPointF(17, 20), 1.8, 1.8)
        painter.drawRoundedRect(QRectF(16.25, 20, 1.5, 4.2), 0.7, 0.7)
    else:
        _paint_rotation_glyph(painter, QPointF(17, 17), 8.7, ink)
    if not active:
        painter.setPen(QPen(QColor("#d44777"), 2.2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(8, 26), QPointF(26, 8))
    painter.end()
    return QIcon(pixmap)


def _style_numeric_spin(spin: QDoubleSpinBox) -> None:
    spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
    spin.setMinimumHeight(31)
    spin.setStyleSheet(
        """
        QDoubleSpinBox#FileNameInput {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:9px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:4px 32px 4px 8px;
        }
        QDoubleSpinBox#FileNameInput::up-button, QDoubleSpinBox#FileNameInput::down-button {
            width:28px; border:0px; margin:1px 1px 1px 0px;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.45 #fff1bf, stop:1 #43d3bd);
            subcontrol-origin:border;
        }
        QDoubleSpinBox#FileNameInput::up-button { subcontrol-position:top right; border-top-right-radius:8px; }
        QDoubleSpinBox#FileNameInput::down-button { subcontrol-position:bottom right; border-bottom-right-radius:8px; }
        QDoubleSpinBox#FileNameInput::up-arrow {
            width:0; height:0; border-left:7px solid transparent; border-right:7px solid transparent; border-bottom:9px solid #132238;
        }
        QDoubleSpinBox#FileNameInput::down-arrow {
            width:0; height:0; border-left:7px solid transparent; border-right:7px solid transparent; border-top:9px solid #132238;
        }
        """
    )


def _style_combo_arrow(combo: QComboBox) -> None:
    combo.setMinimumHeight(31)
    combo.setStyleSheet(
        """
        QComboBox#FileTypeCombo {
            background:#ffffff; border:1px solid #9fb0c5; border-radius:9px;
            color:#132238; font-size:12px; font-style:normal; font-weight:800; padding:5px 33px 5px 8px;
        }
        QComboBox#FileTypeCombo::drop-down {
            width:29px; border:0; margin:1px 1px 1px 0px;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.48 #fff2b8, stop:1 #5ed7c4);
            border-top-right-radius:8px; border-bottom-right-radius:8px;
        }
        QComboBox#FileTypeCombo::down-arrow {
            width:0; height:0; border-left:7px solid transparent; border-right:7px solid transparent; border-top:9px solid #132238;
        }
        QComboBox#FileTypeCombo QAbstractItemView {
            background:#ffffff; border:1px solid #8fa2bb; border-radius:8px; selection-background-color:#cfe7ff;
        }
        """
    )


def apply_interaction_ui_patch() -> None:
    from . import module_window as mw
    from . import project_file_dialog as pfd
    from . import runtime_ui_patch as rtp
    from ..ui import start_bar as sb

    rtp._paint_rotation_glyph = _paint_rotation_glyph
    rtp._style_numeric_spin = _style_numeric_spin
    rtp._style_combo_arrow = _style_combo_arrow
    rtp._layer_icon = _layer_icon
    mw._paint_rotation_glyph = _paint_rotation_glyph
    mw._layer_icon = _layer_icon
    sb._arrow_head = _solid_arrow_head

    original_page_setup_init = rtp.PageSetupDialog.__init__

    def page_setup_init(self, *args, **kwargs):
        original_page_setup_init(self, *args, **kwargs)
        for label in self.findChildren(QLabel):
            text = label.text()
            replacements = {"W": "Width", "H": "Height", "Top": "Top", "Bottom": "Bottom", "Right": "Right", "Left": "Left"}
            if text in replacements:
                label.setText(replacements[text])
                label.setFixedWidth(48 if text in {"W", "H"} else 46)
                label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        for spin in self.findChildren(QDoubleSpinBox):
            spin.setMinimumWidth(132)
            _style_numeric_spin(spin)
        for combo in self.findChildren(QComboBox):
            _style_combo_arrow(combo)

    rtp.PageSetupDialog.__init__ = page_setup_init

    original_file_dialog_init = pfd.ProjectFileDialog.__init__

    def file_dialog_init(self, *args, **kwargs):
        original_file_dialog_init(self, *args, **kwargs)
        for combo in self.findChildren(QComboBox):
            if combo.objectName() == "FileTypeCombo":
                _style_combo_arrow(combo)

    pfd.ProjectFileDialog.__init__ = file_dialog_init

    def canvas_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            point = self._to_canvas_coordinates(event.position())
            action = self._hit_test(point)
            if action is not None and self._object_rect is not None:
                self._drag_action = action
                self._drag_start = point
                self._drag_start_rect = QRectF(self._object_rect)
                self._drag_start_rotation = self._rotation_degrees
                if action in {"move", "rotate"}:
                    self.setCursor(_hand_cursor(True))
                    app = QApplication.instance()
                    if app is not None and not getattr(self, "_engineer_drag_cursor_active", False):
                        QApplication.setOverrideCursor(_hand_cursor(True))
                        self._engineer_drag_cursor_active = True
                event.accept()
                return
        QWidget.mousePressEvent(self, event)

    def canvas_mouse_move(self, event):
        point = self._to_canvas_coordinates(event.position())
        self.mouse_position_changed.emit(point.x(), point.y())
        if self._drag_action is not None:
            self._apply_drag(point)
            if self._drag_action in {"move", "rotate"}:
                self.setCursor(_hand_cursor(True))
            event.accept()
            return
        hover = self._hit_test(point)
        if hover == "move":
            self.setCursor(_move_cursor())
        elif hover == "rotate":
            self.setCursor(_hand_cursor(False))
        elif hover in {"resize_n", "resize_s"}:
            self.setCursor(Qt.SizeVerCursor)
        elif hover in {"resize_e", "resize_w"}:
            self.setCursor(Qt.SizeHorCursor)
        elif hover in {"resize_ne", "resize_sw"}:
            self.setCursor(Qt.SizeBDiagCursor)
        elif hover in {"resize_nw", "resize_se"}:
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.unsetCursor()
        QWidget.mouseMoveEvent(self, event)

    def canvas_mouse_release(self, event):
        self._drag_action = None
        if getattr(self, "_engineer_drag_cursor_active", False):
            QApplication.restoreOverrideCursor()
            self._engineer_drag_cursor_active = False
        point = self._to_canvas_coordinates(event.position())
        hover = self._hit_test(point)
        if hover in {"move", "rotate"}:
            self.setCursor(_hand_cursor(False))
        else:
            self.unsetCursor()
        QWidget.mouseReleaseEvent(self, event)

    mw.GridCanvas.mousePressEvent = canvas_mouse_press
    mw.GridCanvas.mouseMoveEvent = canvas_mouse_move
    mw.GridCanvas.mouseReleaseEvent = canvas_mouse_release

    def force_delete(self):
        canvas = getattr(self, "_canvas", None)
        has_object = (
            canvas is not None
            and (
                getattr(canvas, "_object_rect", None) is not None
                or getattr(canvas, "_file_path", None) is not None
                or not getattr(canvas, "_file_pixmap", QPixmap()).isNull()
            )
        )
        if has_object:
            if hasattr(self, "_runtime_undo_stack"):
                snapshot = {
                    "file_path": getattr(canvas, "_file_path", None),
                    "file_pixmap": QPixmap(getattr(canvas, "_file_pixmap", QPixmap())),
                    "object_rect": QRectF(canvas._object_rect) if getattr(canvas, "_object_rect", None) is not None else None,
                    "rotation": getattr(canvas, "_rotation_degrees", 0.0),
                    "layers": list(getattr(self, "_layers", [])),
                }
                self._runtime_undo_stack.append(snapshot)
                self._runtime_undo_stack = self._runtime_undo_stack[-40:]
                self._runtime_redo_stack = []
            canvas._object_rect = None
            canvas._file_path = None
            canvas._file_pixmap = QPixmap()
            layers = getattr(self, "_layers", [])
            if layers:
                self._layers = [layer for layer in layers if str(layer).startswith("Page")]
                if not self._layers:
                    self._layers = ["Page 1"]
                self._refresh_layers()
            canvas.update()
            self._set_status("Deleted object")
            return
        self._set_status("Delete")

    mw.ModuleWindow._delete = force_delete

    def show_edit_menu(self, anchor):
        self._show_menu("Edit", (
            mw.MenuItemSpec("Copy", self._copy, "Ctrl+C"),
            mw.MenuItemSpec("Cut", self._cut, "Ctrl+X"),
            mw.MenuItemSpec("Paste", self._paste, "Ctrl+V"),
            mw.MenuItemSpec("Move", self._move),
            mw.MenuItemSpec("Undo", self._undo, "Ctrl+Z"),
            mw.MenuItemSpec("Redo", self._redo, "Ctrl+Y"),
            mw.MenuItemSpec("Delete", self._delete, "Delete"),
            mw.MenuItemSpec("Repeat Last Tools", self._repeat_last_tools, "Ctrl+R"),
            mw.MenuItemSpec("Select All", self._select_all, "Ctrl+A"),
            mw.MenuItemSpec("Group", self._group, "Ctrl+G"),
            mw.MenuItemSpec("Ungroup", self._ungroup, "Ctrl+Shift+G"),
        ), anchor)

    def show_canvas_context_menu(self, global_pos):
        self._show_menu_at("Object", (
            mw.MenuItemSpec("Repeat", self._repeat_last_tools),
            mw.MenuItemSpec("Copy", self._copy),
            mw.MenuItemSpec("Cut", self._cut),
            mw.MenuItemSpec("Paste", self._paste),
            mw.MenuItemSpec("Delete", self._delete),
            mw.MenuItemSpec("Rotate", self._rotation),
            mw.MenuItemSpec("Bring to Front", self._bring_to_front),
            mw.MenuItemSpec("Send to Back", self._send_to_back),
            mw.MenuItemSpec("Group", self._group),
            mw.MenuItemSpec("Ungroup", self._ungroup),
        ), global_pos)

    def install_shortcuts(self):
        if getattr(self, "_engineer_interaction_shortcuts_installed", False):
            return
        self._engineer_interaction_shortcuts_installed = True
        self._engineer_interaction_shortcuts = []
        for sequence, handler_name in (
            ("Ctrl+N", "_new_file"), ("Ctrl+O", "_open_file"), ("Ctrl+S", "_save_file"),
            ("Ctrl+Shift+S", "_save_as_file"), ("Ctrl+Z", "_undo"), ("Ctrl+Y", "_redo"),
            ("Ctrl+X", "_cut"), ("Ctrl+C", "_copy"), ("Ctrl+V", "_paste"),
            ("Delete", "_delete"), ("Backspace", "_delete"), ("Ctrl+R", "_repeat_last_tools"),
            ("Ctrl+A", "_select_all"), ("Ctrl+G", "_group"), ("Ctrl+Shift+G", "_ungroup"),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(lambda name=handler_name: getattr(self, name)())
            shortcut.activatedAmbiguously.connect(lambda name=handler_name: getattr(self, name)())
            self._engineer_interaction_shortcuts.append(shortcut)

    mw.ModuleWindow._show_edit_menu = show_edit_menu
    mw.ModuleWindow._show_canvas_context_menu = show_canvas_context_menu
    mw.ModuleWindow._install_shortcuts = install_shortcuts

    class _WorkspaceShortcutFilter(QObject):
        def eventFilter(self, watched, event):  # noqa: N802
            if event.type() != QEvent.Type.KeyPress:
                return False
            app = QApplication.instance()
            active = app.activeWindow() if app is not None else None
            if isinstance(active, QDialog):
                return False
            focus = QApplication.focusWidget()
            window = active or focus
            while window is not None and not isinstance(window, mw.ModuleWindow):
                window = window.parentWidget()
            if window is None:
                window = focus
                while window is not None and not isinstance(window, mw.ModuleWindow):
                    window = window.parentWidget()
            if window is None:
                return False
            if isinstance(focus, (QLineEdit, QDoubleSpinBox, QComboBox)):
                return False
            modifiers = event.modifiers()
            key = event.key()
            ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
            shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
            mapping = {
                (Qt.Key.Key_Delete, False, False): window._delete,
                (Qt.Key.Key_Backspace, False, False): window._delete,
                (Qt.Key.Key_C, True, False): window._copy,
                (Qt.Key.Key_X, True, False): window._cut,
                (Qt.Key.Key_V, True, False): window._paste,
                (Qt.Key.Key_Z, True, False): window._undo,
                (Qt.Key.Key_Y, True, False): window._redo,
                (Qt.Key.Key_A, True, False): window._select_all,
                (Qt.Key.Key_R, True, False): window._repeat_last_tools,
                (Qt.Key.Key_G, True, False): window._group,
                (Qt.Key.Key_G, True, True): window._ungroup,
            }
            handler = mapping.get((key, ctrl, shift))
            if handler is None:
                return False
            handler()
            event.accept()
            return True

    app = QApplication.instance()
    if app is not None and not hasattr(app, "_engineer_tools_shortcut_filter"):
        shortcut_filter = _WorkspaceShortcutFilter(app)
        app.installEventFilter(shortcut_filter)
        app._engineer_tools_shortcut_filter = shortcut_filter

"""Move common default settings into File > Properties > General.

The right-side runtime Properties panel is kept for canvas/object properties only.
Shared startup/default settings live in the File Properties dialog.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFontComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PATCH_VERSION = "engineering-file-properties-general-2026-06-30-b"
UNITS = ("mm", "cm", "m", "px", "pt", "in")
DEFAULT_VIEW_KEYS = ("undo", "redo", "select", "line", "vector", "angle", "text", "grid", "snap", "unit", "ruler", "zoom")


def _font(widget, size: int = 10, *, italic: bool = True, bold: bool = True) -> None:
    font = widget.font()
    font.setFamily("Times New Roman")
    font.setPointSize(size)
    font.setItalic(italic)
    font.setBold(bold)
    widget.setFont(font)


def _radio_icon(checked: bool) -> QIcon:
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor("#18314f"), 1.65))
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(QPointF(9, 9), 6.2, 6.2)
    if checked:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2f7df6"))
        painter.drawEllipse(QPointF(9, 9), 3.55, 3.55)
    painter.end()
    return QIcon(pixmap)


class _WaveSection(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None, *, collapsed: bool = False, open_height: int = 96) -> None:
        super().__init__(parent)
        self._title = title
        self._collapsed = False
        self._open_height = open_height
        self.setObjectName("FilePropertiesWaveSection")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(10, 34, 10, 8)
        self._root.setSpacing(4)
        self._body = QWidget(self)
        self._body.setObjectName("FilePropertiesWaveBody")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(4)
        self._root.addWidget(self._body)
        self.setStyleSheet("QFrame#FilePropertiesWaveSection {background:transparent; border:0;} QWidget#FilePropertiesWaveBody {background:transparent; border:0;}")
        self._set_collapsed(collapsed)

    def add_body_widget(self, widget: QWidget) -> None:
        self._body_layout.addWidget(widget)
        self._set_collapsed(self._collapsed)

    def _set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self._body.setVisible(not collapsed)
        if collapsed:
            self.setMinimumHeight(38)
            self.setMaximumHeight(38)
        else:
            self.setMinimumHeight(self._open_height)
            self.setMaximumHeight(16777215)
        self.updateGeometry()
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 38:
            self._set_collapsed(not self._collapsed)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer = QRectF(2.0, 14.0, max(1.0, self.width() - 4.0), max(1.0, self.height() - 16.0))
        tab_left = outer.left() + 12.0
        tab_right = min(outer.left() + 112.0, outer.right() - 34.0)
        tab_top = outer.top() - 11.0

        body = QPainterPath()
        body.moveTo(outer.left() + 13.0, outer.top())
        body.lineTo(tab_left - 8.0, outer.top())
        body.cubicTo(tab_left + 1.0, outer.top(), tab_left - 1.0, tab_top + 6.5, tab_left + 14.0, tab_top + 5.8)
        body.lineTo(tab_right - 15.0, tab_top + 5.8)
        body.cubicTo(tab_right - 1.0, tab_top + 5.8, tab_right - 6.0, outer.top(), tab_right + 15.0, outer.top())
        body.lineTo(outer.right() - 13.0, outer.top())
        body.quadTo(outer.right(), outer.top(), outer.right(), outer.top() + 13.0)
        body.lineTo(outer.right(), outer.bottom() - 13.0)
        body.quadTo(outer.right(), outer.bottom(), outer.right() - 13.0, outer.bottom())
        body.lineTo(outer.left() + 13.0, outer.bottom())
        body.quadTo(outer.left(), outer.bottom(), outer.left(), outer.bottom() - 13.0)
        body.lineTo(outer.left(), outer.top() + 13.0)
        body.quadTo(outer.left(), outer.top(), outer.left() + 13.0, outer.top())

        fill = QLinearGradient(outer.topLeft(), outer.bottomRight())
        fill.setColorAt(0.0, QColor("#ffffff"))
        fill.setColorAt(0.52, QColor("#eef8ff"))
        fill.setColorAt(1.0, QColor("#fff0c8"))
        painter.fillPath(body, fill)
        painter.setPen(QPen(QColor("#2d7eea"), 1.1))
        painter.drawPath(body)

        tab = QPainterPath()
        tab.moveTo(tab_left - 8.0, outer.top())
        tab.cubicTo(tab_left + 1.0, outer.top(), tab_left - 1.0, tab_top + 6.5, tab_left + 14.0, tab_top + 5.8)
        tab.lineTo(tab_right - 15.0, tab_top + 5.8)
        tab.cubicTo(tab_right - 1.0, tab_top + 5.8, tab_right - 6.0, outer.top(), tab_right + 15.0, outer.top())
        tab.cubicTo(tab_right - 2.0, outer.top() + 20.0, tab_left + 17.0, outer.top() + 21.0, tab_left - 8.0, outer.top())
        tab_fill = QLinearGradient(tab_left, tab_top, tab_right, outer.top() + 21.0)
        tab_fill.setColorAt(0.0, QColor("#0b63d8"))
        tab_fill.setColorAt(0.50, QColor("#168bff"))
        tab_fill.setColorAt(1.0, QColor("#0b4ab0"))
        painter.fillPath(tab, tab_fill)
        painter.setPen(QPen(QColor("#ffffff"), 0.5))
        painter.drawPath(tab)

        painter.setPen(QColor("#ffffff"))
        font = painter.font()
        font.setFamily("Times New Roman")
        font.setBold(True)
        font.setItalic(True)
        font.setPointSize(10)
        painter.setFont(font)
        arrow = "▾" if not self._collapsed else "▸"
        painter.drawText(QRectF(tab_left + 6.0, tab_top + 5.0, max(1.0, tab_right - tab_left - 8.0), 21.0), Qt.AlignmentFlag.AlignCenter, f"{self._title} {arrow}")
        painter.end()


def _choice_button(text: str, checked: bool, callback, *, width: int = 60) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("FilePropertiesChoice")
    button.setCheckable(True)
    button.setChecked(checked)
    button.setIcon(_radio_icon(checked))
    button.setIconSize(QSize(18, 18))
    button.setFixedHeight(24)
    button.setMinimumWidth(width)
    _font(button, 9, italic=True, bold=True)
    button.setStyleSheet(
        "QPushButton#FilePropertiesChoice {background:transparent; border:0; color:#223a58; text-align:left; padding:1px 3px;}"
        "QPushButton#FilePropertiesChoice:hover {color:#0b63d8;}"
    )
    button.clicked.connect(callback)
    return button


def _row(label_text: str, editor: QWidget) -> QWidget:
    row = QWidget()
    row.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    layout = QHBoxLayout(row)
    layout.setContentsMargins(2, 0, 2, 0)
    layout.setSpacing(7)
    label = QLabel(label_text)
    label.setFixedWidth(84)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    _font(label, 9, italic=True, bold=True)
    label.setStyleSheet("QLabel {background:transparent; color:#223a58;}")
    layout.addWidget(label)
    layout.addWidget(editor, 1)
    return row


def _unit_block(dialog, general: dict) -> _WaveSection:
    section = _WaveSection("Unit", dialog, collapsed=False, open_height=86)
    content = QWidget()
    content.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    grid = QGridLayout(content)
    grid.setContentsMargins(2, 0, 2, 0)
    grid.setHorizontalSpacing(4)
    grid.setVerticalSpacing(1)

    current = str(general.get("unit", "mm")) if str(general.get("unit", "mm")) in UNITS else "mm"
    buttons: dict[str, QPushButton] = {}

    def select_unit(selected: str) -> None:
        dialog.unit_combo.setCurrentText(selected)
        for key, button in buttons.items():
            active = key == selected
            button.setChecked(active)
            button.setIcon(_radio_icon(active))

    for index, unit in enumerate(UNITS):
        button = _choice_button(unit, unit == current, lambda checked=False, selected=unit: select_unit(selected), width=54)
        buttons[unit] = button
        grid.addWidget(button, index // 3, index % 3)

    section.add_body_widget(content)
    return section


def _grid_block(dialog, general: dict) -> _WaveSection:
    section = _WaveSection("Grid", dialog, collapsed=False, open_height=104)
    current = bool(general.get("grid_enabled", True))

    def toggle_grid(checked: bool = False) -> None:
        active = not dialog.grid_check.isChecked()
        dialog.grid_check.setChecked(active)
        grid_button.setChecked(active)
        grid_button.setIcon(_radio_icon(active))
        grid_button.setText("Grid On" if active else "Grid Off")

    grid_button = _choice_button("Grid On" if current else "Grid Off", current, toggle_grid, width=100)
    section.add_body_widget(grid_button)

    dialog.grid_spacing.setObjectName("PropertiesSpin")
    dialog.grid_spacing.setFixedHeight(26)
    dialog.grid_spacing.setSuffix(f" {dialog.unit_combo.currentText()}")
    _font(dialog.grid_spacing, 9, italic=False, bold=True)
    section.add_body_widget(_row("Grid spacing", dialog.grid_spacing))

    def sync_suffix() -> None:
        dialog.grid_spacing.setSuffix(f" {dialog.unit_combo.currentText()}")

    dialog.unit_combo.currentTextChanged.connect(lambda _text: sync_suffix())
    return section


def _font_block(dialog, general: dict) -> _WaveSection:
    section = _WaveSection("Font", dialog, collapsed=False, open_height=104)
    dialog.text_font.setObjectName("PropertiesCombo")
    dialog.text_size.setObjectName("PropertiesSpin")
    dialog.text_size.setFixedHeight(26)
    dialog.text_size.setSuffix(" pt")
    _font(dialog.text_font, 9, italic=True, bold=True)
    _font(dialog.text_size, 9, italic=False, bold=True)
    section.add_body_widget(_row("Font", dialog.text_font))
    section.add_body_widget(_row("Size", dialog.text_size))
    return section


def _view_items(workspace) -> list[tuple[str, str]]:
    start_bar = getattr(workspace, "_start_bar_widget", None)
    found: dict[str, str] = {}
    if start_bar is not None:
        for key, button in getattr(start_bar, "_buttons", {}).items():
            label = str(button.property("toolLabel") or key.title())
            found[str(key)] = label
        for button in start_bar.findChildren(QPushButton):
            key = button.property("toolKey")
            if key:
                found[str(key)] = str(button.property("toolLabel") or button.toolTip() or str(key).title())
    ordered = []
    for key in DEFAULT_VIEW_KEYS:
        if key in found:
            ordered.append((key, found[key]))
    for key, label in found.items():
        if key not in {item[0] for item in ordered}:
            ordered.append((key, label))
    return ordered


def _view_block(dialog, settings: dict) -> _WaveSection:
    section = _WaveSection("View", dialog, collapsed=False, open_height=150)
    content = QWidget()
    content.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    grid = QGridLayout(content)
    grid.setContentsMargins(2, 0, 2, 0)
    grid.setHorizontalSpacing(8)
    grid.setVerticalSpacing(2)

    startbar_state = settings.get("view", {}).get("startbar", {}) if isinstance(settings.get("view", {}), dict) else {}
    dialog._view_buttons = {}
    for index, (key, label) in enumerate(_view_items(dialog.workspace)):
        checked = bool(startbar_state.get(key, True))

        def toggle(checked_arg: bool = False, selected: str = key) -> None:
            button = dialog._view_buttons[selected]
            active = button.isChecked()
            button.setIcon(_radio_icon(active))

        button = _choice_button(label, checked, toggle, width=94)
        dialog._view_buttons[key] = button
        grid.addWidget(button, index // 3, index % 3)
    section.add_body_widget(content)
    return section


def _clean_runtime_properties_panel(workspace) -> QWidget:
    panel = QWidget()
    panel.setObjectName("SidePanel")
    panel.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)

    title = QLabel("Properties")
    title.setObjectName("PanelTitle")
    layout.addWidget(title)

    empty = QLabel("No active selection.")
    empty.setObjectName("PanelItem")
    empty.setMinimumHeight(28)
    layout.addWidget(empty)

    hint = QLabel("Select a drawing tool, object, group, or layer to view and edit its properties here.")
    hint.setObjectName("PanelItem")
    hint.setWordWrap(True)
    hint.setMinimumHeight(76)
    layout.addWidget(hint)

    layout.addStretch(1)
    return panel


def _iter_startbar_buttons(workspace):
    start_bar = getattr(workspace, "_start_bar_widget", None)
    if start_bar is None:
        return []
    buttons: list[tuple[str, QPushButton]] = []
    seen: set[str] = set()
    for key, button in getattr(start_bar, "_buttons", {}).items():
        buttons.append((str(key), button))
        seen.add(str(key))
    for button in start_bar.findChildren(QPushButton):
        key = button.property("toolKey")
        if key and str(key) not in seen:
            buttons.append((str(key), button))
            seen.add(str(key))
    return buttons


def _apply_view_settings(workspace, settings: dict) -> None:
    view = settings.get("view", {}) if isinstance(settings, dict) else {}
    startbar_state = view.get("startbar", {}) if isinstance(view, dict) else {}
    for key, button in _iter_startbar_buttons(workspace):
        button.setVisible(bool(startbar_state.get(key, True)))
        button.setCursor(Qt.CursorShape.ArrowCursor)


def _normalize_startbar_cursors(workspace) -> None:
    for _key, button in _iter_startbar_buttons(workspace):
        button.setCursor(Qt.CursorShape.ArrowCursor)


def apply_file_properties_general_patch() -> None:
    from . import workspace as edw
    from src.engineers_tools.app import engineering_properties_patch as epp

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_file_properties_general_patch", "") == PATCH_VERSION:
        return

    original_apply_settings = epp._apply_settings
    original_read_controls = epp.PropertiesDialog._read_controls
    original_start_bar_action_button = edw.EngineeringDesignWorkspace._start_bar_action_button
    original_build_start_bar = edw.EngineeringDesignWorkspace._build_start_bar

    def apply_settings(workspace, settings: dict, reinstall_shortcuts: bool = True) -> None:
        original_apply_settings(workspace, settings, reinstall_shortcuts=reinstall_shortcuts)
        _apply_view_settings(workspace, settings)

    def read_controls(self) -> dict:
        settings = original_read_controls(self)
        settings.setdefault("view", {})
        settings["view"]["startbar"] = {key: button.isChecked() for key, button in getattr(self, "_view_buttons", {}).items()}
        return settings

    def start_bar_action_button(self, tooltip: str, icon, callback):
        button = original_start_bar_action_button(self, tooltip, icon, callback)
        key = tooltip.strip().lower().replace(" ", "_")
        button.setProperty("toolKey", key)
        button.setProperty("toolLabel", tooltip)
        button.setCursor(Qt.CursorShape.ArrowCursor)
        return button

    def build_start_bar(self) -> QWidget:
        bar = original_build_start_bar(self)
        _normalize_startbar_cursors(self)
        settings = getattr(self, "_properties_settings", None)
        if isinstance(settings, dict):
            _apply_view_settings(self, settings)
        return bar

    def general_page(self) -> QWidget:
        page = QWidget()
        page.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        general = self._settings.get("general", {})

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(list(UNITS))
        self.unit_combo.setCurrentText(str(general.get("unit", "mm")) if str(general.get("unit", "mm")) in UNITS else "mm")
        self.unit_combo.hide()

        self.grid_check = QCheckBox()
        self.grid_check.setChecked(bool(general.get("grid_enabled", True)))
        self.grid_check.hide()

        self.snap_check = QCheckBox()
        self.snap_check.setChecked(bool(general.get("snap_enabled", False)))
        self.snap_check.hide()

        self.grid_spacing = QDoubleSpinBox()
        self.grid_spacing.setRange(0.000001, 1000000.0)
        self.grid_spacing.setDecimals(6)
        self.grid_spacing.setSingleStep(0.5)
        self.grid_spacing.setValue(float(general.get("grid_spacing", 1.0) or 1.0))

        self.text_font = QFontComboBox()
        self.text_font.setCurrentText(str(general.get("text_font", "Times New Roman")))

        self.text_size = QSpinBox()
        self.text_size.setRange(1, 300)
        self.text_size.setValue(int(general.get("text_size", 12) or 12))

        hidden = QWidget()
        hidden_layout = QVBoxLayout(hidden)
        hidden_layout.setContentsMargins(0, 0, 0, 0)
        for widget in (self.unit_combo, self.grid_check, self.snap_check):
            hidden_layout.addWidget(widget)
        hidden.hide()
        layout.addWidget(hidden)

        layout.addWidget(_unit_block(self, general))
        layout.addWidget(_grid_block(self, general))
        layout.addWidget(_font_block(self, general))
        layout.addWidget(_view_block(self, self._settings))
        layout.addStretch(1)
        return page

    def build_side_panel(self, title: str, rows: tuple[str, ...]) -> QWidget:
        if title == "Properties":
            return _clean_runtime_properties_panel(self)
        panel = QWidget()
        panel.setObjectName("SidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("PanelTitle")
        layout.addWidget(heading)
        for row in rows:
            item = QLabel(row)
            item.setObjectName("PanelItem")
            item.setMinimumHeight(28)
            layout.addWidget(item)
        layout.addStretch(1)
        return panel

    epp._apply_settings = apply_settings
    epp.PropertiesDialog._read_controls = read_controls
    epp.PropertiesDialog._general_page = general_page
    edw.EngineeringDesignWorkspace._start_bar_action_button = start_bar_action_button
    edw.EngineeringDesignWorkspace._build_start_bar = build_start_bar
    edw.EngineeringDesignWorkspace._build_side_panel = build_side_panel
    edw.EngineeringDesignWorkspace._engineering_file_properties_general_patch = PATCH_VERSION

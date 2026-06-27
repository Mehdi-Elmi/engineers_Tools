"""Engineering Design Tools workspace.

This file is the active workspace for mechanics, dynamics, statics, robotics,
and vector design. Future changes for this module must continue this class.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.engineers_tools.app.module_window import MenuItemSpec, ModuleWindow
from src.engineers_tools.app.modules import LauncherModule

ENGINEERING_WORKSPACE_UI_MARKER = "ENGINEERING_WORKSPACE_VIEW_STARTBAR_2026_06_27_D"


class EngineeringDesignWorkspace(ModuleWindow):
    def __init__(self, module: LauncherModule) -> None:
        self._start_bar_tool_state: dict[str, bool] = {}
        super().__init__(module)
        self._layers = []
        self._refresh_layers()

    def _build_start_bar(self) -> QWidget:
        bar = super()._build_start_bar()
        self._start_bar_tool_state = {tool.key: True for tool in self.get_start_bar_tools()}
        return bar

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(34)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)
        self._status_items = []

        tool_item = QLabel("Tool Select: Ready")
        tool_item.setObjectName("StatusItem")
        layout.addWidget(tool_item)
        self._status_items.append(tool_item)

        coordinate_item = QLabel("X: 0  Y: 0")
        coordinate_item.setObjectName("StatusItem")
        layout.addWidget(coordinate_item)
        self._status_items.append(coordinate_item)

        unit_item = QLabel("Unit: mm")
        unit_item.setObjectName("StatusItem")
        layout.addWidget(unit_item)
        self._status_items.append(unit_item)

        layout.addStretch(1)

        zoom_label = QLabel("Zoom:")
        zoom_label.setObjectName("StatusItem")
        layout.addWidget(zoom_label)
        layout.addWidget(self._build_zoom_control())
        return bar

    def _build_zoom_control(self) -> QWidget:
        control = QWidget()
        control.setObjectName("ZoomControl")
        control.setFixedSize(126, 28)
        control_layout = QHBoxLayout(control)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(2)

        self._zoom_input = QDoubleSpinBox()
        self._zoom_input.setObjectName("ZoomInput")
        self._zoom_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._zoom_input.setRange(5.0, 3200.0)
        self._zoom_input.setDecimals(2)
        self._zoom_input.setSingleStep(5.0)
        self._zoom_input.setValue(100.0)
        self._zoom_input.setSuffix(" %")
        self._zoom_input.setFixedSize(92, 26)
        self._zoom_input.setStyleSheet(
            "QDoubleSpinBox#ZoomInput {"
            "background:#fff9de; border:1px solid #b38621; border-radius:8px;"
            "color:#132238; font-size:11px; font-style:normal; font-weight:700; padding:2px 6px;"
            "selection-background-color:#43d3bd; }"
        )
        self._zoom_input.valueChanged.connect(self._set_zoom)
        control_layout.addWidget(self._zoom_input)

        arrows = QWidget()
        arrows.setObjectName("ZoomArrowStack")
        arrows_layout = QVBoxLayout(arrows)
        arrows_layout.setContentsMargins(0, 0, 0, 0)
        arrows_layout.setSpacing(2)
        up_button = self._build_zoom_arrow_button("up")
        down_button = self._build_zoom_arrow_button("down")
        up_button.clicked.connect(lambda: self._zoom_input.stepUp())
        down_button.clicked.connect(lambda: self._zoom_input.stepDown())
        arrows_layout.addWidget(up_button)
        arrows_layout.addWidget(down_button)
        control_layout.addWidget(arrows)
        return control

    def _build_zoom_arrow_button(self, direction: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName("ZoomArrowButton")
        button.setFixedSize(28, 12)
        button.setIcon(self._build_zoom_arrow_icon(direction))
        button.setIconSize(QSize(22, 10))
        button.setToolTip("Zoom in" if direction == "up" else "Zoom out")
        button.setStyleSheet(
            "QPushButton#ZoomArrowButton {"
            "background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fff9de, stop:1 #ffc35a);"
            "border:1px solid #7e5b10; border-radius:4px; padding:0px; }"
            "QPushButton#ZoomArrowButton:hover { background:#ff8a35; border-color:#ffffff; }"
            "QPushButton#ZoomArrowButton:pressed { background:#d46a16; padding-top:1px; }"
        )
        return button

    def _build_zoom_arrow_icon(self, direction: str) -> QIcon:
        pixmap = QPixmap(22, 10)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#ffffff"), 0.9))
        painter.setBrush(QColor("#132238"))
        if direction == "up":
            points = QPolygonF([QPointF(11, 1), QPointF(20, 9), QPointF(2, 9)])
        else:
            points = QPolygonF([QPointF(2, 1), QPointF(20, 1), QPointF(11, 9)])
        painter.drawPolygon(points)
        painter.end()
        return QIcon(pixmap)

    def _show_view_menu(self, anchor: QWidget) -> None:
        items: list[MenuItemSpec] = [
            MenuItemSpec("Start Bar", self._toggle_start_bar, checkable=True, checked=self._view_state["start_bar"]),
        ]
        for tool in self.get_start_bar_tools():
            items.append(
                MenuItemSpec(
                    tool.label,
                    lambda key=tool.key: self._toggle_start_bar_tool(key),
                    checkable=True,
                    checked=self._start_bar_tool_state.get(tool.key, True),
                )
            )
        self._show_menu("View", tuple(items), anchor)

    def _toggle_start_bar_tool(self, key: str) -> None:
        visible = not self._start_bar_tool_state.get(key, True)
        self._start_bar_tool_state[key] = visible
        if self._start_bar_widget is not None and hasattr(self._start_bar_widget, "set_tool_visible"):
            self._start_bar_widget.set_tool_visible(key, visible)
        label = next((tool.label for tool in self.get_start_bar_tools() if tool.key == key), key)
        self._set_status(f"{label} {'shown on' if visible else 'removed from'} Start Bar")

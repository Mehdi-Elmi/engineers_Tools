"""Engineering Design Tools workspace.

This file is the active workspace for mechanics, dynamics, statics, robotics,
and vector design. Future changes for this module must continue this class.
"""

from __future__ import annotations

from PySide6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QHBoxLayout, QLabel, QWidget

from src.engineers_tools.app.module_window import MenuItemSpec, ModuleWindow
from src.engineers_tools.app.modules import LauncherModule

ENGINEERING_WORKSPACE_UI_MARKER = "ENGINEERING_WORKSPACE_VIEW_STARTBAR_2026_06_27_A"


class EngineeringDesignWorkspace(ModuleWindow):
    def __init__(self, module: LauncherModule) -> None:
        self._start_bar_tool_state: dict[str, bool] = {}
        super().__init__(module)

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

        self._zoom_input = QDoubleSpinBox()
        self._zoom_input.setObjectName("ZoomInput")
        self._zoom_input.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self._zoom_input.setRange(5.0, 3200.0)
        self._zoom_input.setDecimals(2)
        self._zoom_input.setSingleStep(5.0)
        self._zoom_input.setValue(100.0)
        self._zoom_input.setSuffix(" %")
        self._zoom_input.setFixedWidth(104)
        self._zoom_input.setStyleSheet(
            "QDoubleSpinBox#ZoomInput {"
            "background:#ffffff; border:1px solid #8fb3dc; border-radius:8px;"
            "color:#132238; font-size:11px; padding:2px 18px 2px 6px;"
            "selection-background-color:#43d3bd; }"
            "QDoubleSpinBox#ZoomInput::up-button {"
            "subcontrol-origin:border; subcontrol-position:top right; width:17px;"
            "border-left:1px solid #8fb3dc; border-top-right-radius:7px;"
            "background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ffffff, stop:1 #bfe1ff); }"
            "QDoubleSpinBox#ZoomInput::down-button {"
            "subcontrol-origin:border; subcontrol-position:bottom right; width:17px;"
            "border-left:1px solid #8fb3dc; border-bottom-right-radius:7px;"
            "background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #d8efff, stop:1 #7aaee8); }"
            "QDoubleSpinBox#ZoomInput::up-button:hover, QDoubleSpinBox#ZoomInput::down-button:hover {"
            "background:#fff0c7; border-left:1px solid #ff8a35; }"
        )
        self._zoom_input.valueChanged.connect(self._set_zoom)
        layout.addWidget(self._zoom_input)
        return bar

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

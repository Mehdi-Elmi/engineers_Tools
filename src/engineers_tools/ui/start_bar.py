"""Reusable Start Bar component.

The Start Bar is intentionally separated from the mother window. Each module can
provide a different tool list while keeping the same visual and behavioral shell.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


@dataclass(frozen=True)
class StartBarTool:
    key: str
    label: str
    tooltip: str
    properties_schema: tuple[str, ...] = ()


DEFAULT_START_BAR_TOOLS: tuple[StartBarTool, ...] = (
    StartBarTool("select", "Select", "Select objects", ("Selection", "Coordinates", "Size", "Style")),
    StartBarTool("line", "Line", "Draw a line", ("Start", "End", "Stroke", "Behavior")),
    StartBarTool("vector", "Vector", "Draw a vector", ("Magnitude", "Angle", "Components", "Style")),
    StartBarTool("angle", "Angle", "Draw or measure an angle", ("Center", "Start", "End", "Unit")),
    StartBarTool("text", "Text", "Add text", ("Content", "Font", "Size", "Direction")),
    StartBarTool("grid", "Grid", "Grid settings", ("Spacing", "Snap", "Visibility", "Unit")),
    StartBarTool("snap", "Snap", "Snap settings", ("Mode", "Tolerance", "Targets")),
    StartBarTool("zoom", "Zoom", "Zoom controls", ("Percent", "Fit", "Center")),
)


class StartBar(QWidget):
    def __init__(self, tools: tuple[StartBarTool, ...] = DEFAULT_START_BAR_TOOLS) -> None:
        super().__init__()
        self.setObjectName("StartBar")
        self.setFixedHeight(58)
        self.tools = tools

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(9)

        for tool in tools:
            button = QPushButton(tool.label)
            button.setObjectName("ToolButton")
            button.setToolTip(tool.tooltip)
            button.setProperty("toolKey", tool.key)
            button.setProperty("propertiesSchema", tool.properties_schema)
            layout.addWidget(button)

        layout.addStretch(1)

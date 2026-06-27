"""Entry point for Engineering Flowcharts."""

from __future__ import annotations

from src.engineers_tools.app.module_window import ModuleWindow
from src.engineers_tools.app.modules import LauncherModule

from .workspace import EngineeringFlowchartsWorkspace


def create_window(module: LauncherModule) -> ModuleWindow:
    return EngineeringFlowchartsWorkspace(module)

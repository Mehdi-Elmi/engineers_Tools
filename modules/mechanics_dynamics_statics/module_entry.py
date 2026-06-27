"""Entry point for Engineering Design Tools."""

from __future__ import annotations

from src.engineers_tools.app.module_window import ModuleWindow
from src.engineers_tools.app.modules import LauncherModule

from .workspace import EngineeringDesignWorkspace


def create_window(module: LauncherModule) -> ModuleWindow:
    return EngineeringDesignWorkspace(module)

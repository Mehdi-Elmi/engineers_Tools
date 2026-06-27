"""Entry point for White Background Remover."""

from __future__ import annotations

from src.engineers_tools.app.module_window import ModuleWindow
from src.engineers_tools.app.modules import LauncherModule

from .workspace import WhiteBackgroundRemoverWorkspace


def create_window(module: LauncherModule) -> ModuleWindow:
    return WhiteBackgroundRemoverWorkspace(module)

"""Entry point for Barcode Designer."""

from __future__ import annotations

from src.engineers_tools.app.module_window import ModuleWindow
from src.engineers_tools.app.modules import LauncherModule

from .workspace import BarcodeDesignerWorkspace


def create_window(module: LauncherModule) -> ModuleWindow:
    return BarcodeDesignerWorkspace(module)

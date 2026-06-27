"""White Background Remover workspace placeholder."""

from __future__ import annotations

from src.engineers_tools.app.module_window import ModuleWindow
from src.engineers_tools.app.modules import LauncherModule


class WhiteBackgroundRemoverWorkspace(ModuleWindow):
    def __init__(self, module: LauncherModule) -> None:
        super().__init__(module)

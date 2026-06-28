"""Engineering Design Tools workspace.

This file is the active workspace for mechanics, dynamics, statics, robotics,
and vector design. Future changes for this module must continue this class.
"""

from __future__ import annotations

from src.engineers_tools.app.module_window import ModuleWindow
from src.engineers_tools.app.modules import LauncherModule


class EngineeringDesignWorkspace(ModuleWindow):
    def __init__(self, module: LauncherModule) -> None:
        super().__init__(module)

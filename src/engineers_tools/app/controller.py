"""Window controller."""

from __future__ import annotations

from importlib import import_module
from typing import Callable, cast

from PySide6.QtCore import QObject

from .launcher_window import LauncherWindow
from .module_window import ModuleWindow
from .modules import LauncherModule


class AppController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._launcher: LauncherWindow | None = None
        self._module_windows: dict[str, ModuleWindow] = {}

    def show_launcher(self) -> None:
        if self._launcher is None:
            self._launcher = LauncherWindow()
            self._launcher.module_selected.connect(self.show_module)

        for window in self._module_windows.values():
            window.hide()

        self._launcher.show()
        self._launcher.raise_()
        self._launcher.activateWindow()

    def show_module(self, module: LauncherModule) -> None:
        window = self._module_windows.get(module.key)
        if window is None:
            window = self._create_module_window(module)
            window.back_requested.connect(self.show_launcher)
            self._module_windows[module.key] = window

        window.show()
        window.raise_()
        window.activateWindow()
        if self._launcher is not None:
            self._launcher.hide()

    def _create_module_window(self, module: LauncherModule) -> ModuleWindow:
        create_window = self._load_module_entry_point(module.entry_point)
        return create_window(module)

    def _load_module_entry_point(self, entry_point: str) -> Callable[[LauncherModule], ModuleWindow]:
        module_path, function_name = entry_point.split(":", 1)
        module_object = import_module(module_path)
        return cast(Callable[[LauncherModule], ModuleWindow], getattr(module_object, function_name))

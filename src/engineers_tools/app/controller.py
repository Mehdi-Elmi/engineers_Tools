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
        self._new_workspace_counter = 0

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
            self._register_module_window(module.key, window)

        window.show()
        window.raise_()
        window.activateWindow()
        if self._launcher is not None:
            self._launcher.hide()

    def create_new_workspace(self, module: LauncherModule) -> None:
        self._new_workspace_counter += 1
        window_key = f"{module.key}:new:{self._new_workspace_counter}"
        window = self._create_module_window(module)
        window.setWindowTitle(f"{module.title} - New {self._new_workspace_counter}")
        self._register_module_window(window_key, window)
        window.show()
        window.raise_()
        window.activateWindow()

    def _register_module_window(self, key: str, window: ModuleWindow) -> None:
        window.back_requested.connect(self.show_launcher)
        window.new_workspace_requested.connect(self.create_new_workspace)
        self._module_windows[key] = window

    def _create_module_window(self, module: LauncherModule) -> ModuleWindow:
        create_window = self._load_module_entry_point(module.entry_point)
        return create_window(module)

    def _load_module_entry_point(self, entry_point: str) -> Callable[[LauncherModule], ModuleWindow]:
        module_path, function_name = entry_point.split(":", 1)
        module_object = import_module(module_path)
        return cast(Callable[[LauncherModule], ModuleWindow], getattr(module_object, function_name))

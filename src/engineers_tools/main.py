"""Application entry point."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

from .app.logging_setup import setup_runtime_logging


def _install_start_bar_compatibility() -> None:
    """Keep the shared ModuleWindow compatible with the newer icon StartBar."""
    from PySide6.QtWidgets import QWidget

    from .ui import start_bar

    @dataclass(frozen=True)
    class StartBarTool:
        key: str
        label: str

    default_tools = (
        StartBarTool("select", "Select"),
        StartBarTool("line", "Line"),
        StartBarTool("vector", "Vector"),
        StartBarTool("angle", "Angle"),
        StartBarTool("text", "Text"),
        StartBarTool("grid", "Grid"),
        StartBarTool("snap", "Snap"),
        StartBarTool("zoom", "Zoom"),
        StartBarTool("ruler", "Ruler"),
        StartBarTool("unit", "Unit"),
    )

    original_start_bar = start_bar.StartBar

    class CompatibleStartBar(original_start_bar):  # type: ignore[misc, valid-type]
        def __init__(self, tools_or_host: object | None = None, parent: QWidget | None = None) -> None:
            host = tools_or_host if isinstance(tools_or_host, QWidget) else parent
            super().__init__(host, parent)

        def showEvent(self, event):  # type: ignore[override]
            if getattr(self, "_host_window", None) is None or not hasattr(self._host_window, "findChildren"):
                self._host_window = self.window()
            super().showEvent(event)

        def _find_canvas(self):  # type: ignore[override]
            host = getattr(self, "_host_window", None)
            if host is None or not hasattr(host, "findChildren"):
                return None
            for candidate in host.findChildren(QWidget):
                if candidate.objectName() in {"DesignCanvas", "WorkspaceCanvas", "Canvas", "GridCanvas"}:
                    return candidate
            return None

    start_bar.StartBarTool = StartBarTool
    start_bar.DEFAULT_START_BAR_TOOLS = default_tools
    start_bar.StartBar = CompatibleStartBar


def main() -> int:
    log_path = setup_runtime_logging()
    logging.info("Engineer Tools startup requested.")
    logging.info("Python executable: %s", sys.executable)
    logging.info("Python argv: %s", sys.argv)

    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        logging.exception("PySide6 is not installed or cannot be imported.")
        print(f"PySide6 is not installed. Runtime log: {log_path}")
        return 1
    except Exception:
        logging.exception("Failed while importing PySide6 for startup.")
        print(f"Startup failed before UI initialization. Runtime log: {log_path}")
        return 1

    try:
        _install_start_bar_compatibility()

        from .app.controller import AppController
        from .app.theme import apply_app_theme

        app = QApplication(sys.argv)
        app.setApplicationName("Engineer Tools")
        app.setLayoutDirection(Qt.LeftToRight)
        apply_app_theme(app)

        controller = AppController()
        controller.show_launcher()
        logging.info("Launcher shown.")
        return app.exec()
    except Exception:
        logging.exception("Launcher startup failed.")
        print(f"Launcher startup failed. Runtime log: {log_path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

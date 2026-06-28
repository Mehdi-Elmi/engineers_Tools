"""Application entry point."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        print("PySide6 is not installed. Run run_engineers_tools.cmd first.")
        return 1

    from .app.controller import AppController
    from .app.logging_setup import setup_runtime_logging
    from .app.theme import apply_app_theme

    setup_runtime_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("Engineer Tools")
    app.setLayoutDirection(Qt.LeftToRight)
    apply_app_theme(app)

    controller = AppController()
    controller.show_launcher()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

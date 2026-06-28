"""Application entry point."""

from __future__ import annotations

import logging
import sys

from .app.logging_setup import setup_runtime_logging


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

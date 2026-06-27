from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .app.controller import AppController
from .app.theme import apply_app_theme


def main() -> int:
    app = QApplication(sys.argv)
    apply_app_theme(app)

    controller = AppController()
    controller.show_launcher()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

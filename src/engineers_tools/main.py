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
        from .app.engineering_export_patch import apply_engineering_export_patch
        from .app.engineering_fixed_page_rotation_patch import apply_engineering_fixed_page_rotation_patch
        from .app.engineering_fixed_viewport_patch import apply_engineering_fixed_viewport_patch
        from .app.engineering_print_setup_final_patch import apply_engineering_print_setup_final_patch
        from .app.engineering_print_setup_hotfix import apply_engineering_print_setup_hotfix
        from .app.engineering_properties_patch import apply_engineering_properties_patch
        from .app.engineering_ui_small_fixes_patch import apply_engineering_ui_small_fixes_patch
        from .app.engineering_window_geometry_patch import apply_engineering_window_geometry_patch
        from .app.engineering_workspace_finalize_patch import apply_engineering_workspace_finalize_patch
        from .app.engineering_zoom_print_patch import apply_engineering_zoom_print_patch
        from .app.interaction_ui_patch import apply_interaction_ui_patch
        from .app.runtime_ui_patch import apply_runtime_ui_patch
        from .app.theme import apply_app_theme

        app = QApplication(sys.argv)
        app.setApplicationName("Engineer Tools")
        app.setLayoutDirection(Qt.LeftToRight)
        apply_app_theme(app)
        apply_runtime_ui_patch()
        apply_interaction_ui_patch()
        apply_engineering_export_patch()
        apply_engineering_workspace_finalize_patch()
        apply_engineering_zoom_print_patch()
        apply_engineering_print_setup_hotfix()
        apply_engineering_print_setup_final_patch()
        apply_engineering_properties_patch()
        apply_engineering_ui_small_fixes_patch()
        apply_engineering_window_geometry_patch()
        apply_engineering_fixed_page_rotation_patch()
        apply_engineering_fixed_viewport_patch()

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
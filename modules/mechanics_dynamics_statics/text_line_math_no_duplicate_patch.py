"""Prevent duplicate Line/Math/List custom menu actions."""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QMenu, QPushButton, QWidget

PATCH_VERSION = "engineering-text-line-math-no-duplicate-2026-07-02-a"


def _buttons(root: QWidget | None) -> dict:
    start_bar = getattr(root, "_start_bar_widget", None) if root is not None else None
    controls = getattr(start_bar, "_text_controls", {}) if start_bar is not None else {}
    buttons = controls.get("buttons", {}) if isinstance(controls, dict) else {}
    return buttons if isinstance(buttons, dict) else {}


def _patch_apply_text_menus(tls) -> None:
    def apply_text_menus(root: QWidget | None) -> None:
        buttons = _buttons(root)
        line = buttons.get("Line spacing")
        if isinstance(line, QPushButton) and line.property("lineMenuVersion") != PATCH_VERSION:
            menu = QMenu(line)
            for label, value in (("1.0", 1.0), ("1.15", 1.15), ("1.5", 1.5), ("2.0", 2.0)):
                action = menu.addAction(label)
                action.triggered.connect(lambda checked=False, v=value, w=root: tls._apply_line_spacing(w, v))
            menu.addSeparator()
            action = menu.addAction("Line and paragraph settings...")
            action.triggered.connect(lambda checked=False, w=root: tls._apply_line_spacing(w, 1.15))
            line.setMenu(menu)
            line.setToolTip("Line spacing")
            line.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            line.setProperty("lineMenuVersion", PATCH_VERSION)

        math = buttons.get("Math symbols")
        if isinstance(math, QPushButton) and math.property("mathMenuVersion") != PATCH_VERSION:
            menu = QMenu(math)
            tls._add_symbol_section(menu, "Greek letters", tls.GREEK, root)
            tls._add_symbol_section(menu, "Math operators", tls.OPERATORS, root)
            tls._add_symbol_section(menu, "Arrows", tls.ARROWS, root)
            math.setMenu(menu)
            math.setToolTip("Math symbols")
            math.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            math.setProperty("mathMenuVersion", PATCH_VERSION)

        bullet = buttons.get("Bullet")
        if isinstance(bullet, QPushButton) and bullet.menu() is not None:
            menu = bullet.menu()
            if menu.property("lineMathCustomBulletVersion") != PATCH_VERSION:
                menu.addSeparator()
                action = menu.addAction("Custom bullet settings...")
                action.triggered.connect(lambda checked=False, w=root: tls._open_list_settings(w, "bullet"))
                menu.setProperty("lineMathCustomBulletVersion", PATCH_VERSION)

        numbering = buttons.get("Numbering")
        if isinstance(numbering, QPushButton) and numbering.menu() is not None:
            menu = numbering.menu()
            if menu.property("lineMathCustomNumberingVersion") != PATCH_VERSION:
                menu.addSeparator()
                action = menu.addAction("Custom numbering settings...")
                action.triggered.connect(lambda checked=False, w=root: tls._open_list_settings(w, "numbering"))
                menu.setProperty("lineMathCustomNumberingVersion", PATCH_VERSION)

    tls._apply_text_menus = apply_text_menus


def apply_text_line_math_no_duplicate_patch() -> None:
    from . import text_line_math_symbols_patch as tls
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_line_math_no_duplicate_patch", "") == PATCH_VERSION:
        return

    _patch_apply_text_menus(tls)
    old_init = edw.EngineeringDesignWorkspace.__init__

    def workspace_init(self, module) -> None:
        old_init(self, module)
        _patch_apply_text_menus(tls)
        tls._apply_text_menus(self)
        QTimer.singleShot(0, lambda root=self: tls._apply_text_menus(root))
        logging.info("text_line_math_no_duplicate_patch: installed version=%s", PATCH_VERSION)

    edw.EngineeringDesignWorkspace.__init__ = workspace_init
    edw.EngineeringDesignWorkspace._engineering_text_line_math_no_duplicate_patch = PATCH_VERSION

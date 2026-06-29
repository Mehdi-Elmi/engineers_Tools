"""Startup compatibility hooks for Engineer Tools.

This file is intentionally small: Python imports sitecustomize automatically when
this package directory is on sys.path. It patches older runtime patch modules
without changing their public API.
"""

from __future__ import annotations

import builtins
import logging
import sys

_ORIGINAL_IMPORT = builtins.__import__
_INSTALLED = False


def _render_engineering_export_bridge(window, painter, target, transparent=False) -> None:
    try:
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QColor
    except Exception:  # pragma: no cover - defensive startup hook
        logging.exception("sitecustomize: Qt imports failed for print export bridge")
        return

    target = QRectF(target)
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        painter.fillRect(target, Qt.GlobalColor.transparent if transparent else QColor("#ffffff"))
        return

    if not transparent:
        painter.fillRect(target, QColor("#ffffff"))

    source_w = max(1, int(canvas.width()))
    source_h = max(1, int(canvas.height()))
    scale = min(target.width() / source_w, target.height() / source_h)
    target_w = source_w * scale
    target_h = source_h * scale

    painter.save()
    painter.translate(target.left() + (target.width() - target_w) / 2.0, target.top() + (target.height() - target_h) / 2.0)
    painter.scale(scale, scale)
    canvas.render(painter)
    painter.restore()


def _patch_interaction_module(module) -> None:
    if module is None:
        return
    name = getattr(module, "__name__", "")
    if not name.endswith("interaction_ui_patch"):
        return
    if not hasattr(module, "_render_engineering_export"):
        module._render_engineering_export = _render_engineering_export_bridge
        logging.info("sitecustomize: installed _render_engineering_export bridge on %s", name)


def _patch_loaded_modules() -> None:
    for name, module in list(sys.modules.items()):
        if name.endswith("interaction_ui_patch"):
            _patch_interaction_module(module)


def _engineer_tools_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
    module = _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)
    if "interaction_ui_patch" in str(name):
        _patch_loaded_modules()
    return module


def _install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    builtins.__import__ = _engineer_tools_import
    _INSTALLED = True
    _patch_loaded_modules()
    logging.info("sitecustomize: Engineer Tools startup hooks installed")


_install()

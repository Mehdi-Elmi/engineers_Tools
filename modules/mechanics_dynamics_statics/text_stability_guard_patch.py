"""Compatibility entry point for final Text Box stability fixes.

The active implementation lives in ``text_box_copy_key_fix_patch``. Keeping this
module name stable avoids touching the Engineering Design module entry point and
keeps the patch chain order unchanged.
"""

from __future__ import annotations

import logging

PATCH_VERSION = "engineering-text-stability-guard-wrapper-2026-07-02-a"


def apply_text_stability_guard_patch() -> None:
    try:
        from .text_box_copy_key_fix_patch import apply_text_box_copy_key_fix_patch
    except Exception:
        logging.exception("text_stability_guard: focused text box fix import failed")
        return
    apply_text_box_copy_key_fix_patch()
    logging.info("text_stability_guard: delegated version=%s", PATCH_VERSION)

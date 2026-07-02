"""Deprecated compatibility file.

The Text Box stability implementation was consolidated into
``text_stability_guard_patch.py``. This file is intentionally inactive and must
not be imported by the Engineering Design module chain.
"""

from __future__ import annotations

PATCH_VERSION = "deprecated-text-box-copy-key-fix-2026-07-02"


def apply_text_box_copy_key_fix_patch() -> None:
    """No-op kept only until the deprecated file can be physically removed."""
    return None

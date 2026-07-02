"""Safe compatibility shim for the final Text toolbar patch.

This file used to be the last runtime owner for Text keyboard events, math
conversion, color dialogs, line-spacing controls, and text-box painting. That
made the Text system fragile because several earlier patches already own parts
of QTextEdit, EngineeringCanvas, menu popups, and object painting.

The safe version intentionally does not override QTextEdit.event,
QTextEdit.keyPressEvent, EngineeringCanvas._paint_object, or any global
clipboard/delete shortcuts. It leaves the earlier Text tool chain in control so
basic editing behavior can recover while the Text/Math architecture is cleaned
up in one place.
"""

from __future__ import annotations

import logging

PATCH_VERSION = "engineering-text-toolbar-final-event-safety-safe-shim-2026-07-02-a"


def apply_text_toolbar_final_event_safety_patch() -> None:
    """Keep the import/apply chain stable without patching text events.

    module_entry.py still calls this function near the end of the Engineering
    Design Tools startup sequence. Making this function a no-op compatibility
    shim is safer than deleting the module or leaving the previous final owner in
    place, because the previous implementation swallowed or rerouted QTextEdit
    keyboard events and broke Backspace, Delete, Copy, Paste, and inline math
    editing.
    """
    try:
        from . import workspace as edw
    except Exception:
        logging.exception("text_toolbar_final_event_safety_patch: workspace import failed")
        return

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_text_toolbar_final_event_safety_patch", "") == PATCH_VERSION:
        return

    edw.EngineeringDesignWorkspace._engineering_text_toolbar_final_event_safety_patch = PATCH_VERSION
    logging.info("text_toolbar_final_event_safety_patch: safe shim installed version=%s", PATCH_VERSION)

# Engineer Tools UI Icons

This folder is the canonical place for reusable UI icon assets used by Engineer Tools.

Use fixed filenames so the Python UI can load icons by name without code changes. Prefer SVG for sharp scalable icons. PNG is acceptable for cursor fallbacks when needed.

Planned canonical names:

- `rotate_arrow.svg` - rotation handle arrow and rotate glyphs.
- `undo_arrow.svg` - Start Bar Undo icon.
- `redo_arrow.svg` - Start Bar Redo icon.
- `move_cursor.svg` - canvas move cursor/icon.
- `hand_open.svg` - rotate/move hover hand cursor.
- `hand_closed.svg` - rotate/move drag cursor.
- `layer_eye.svg` - layer show/hide icon.
- `layer_lock_open.svg` - unlocked layer icon.
- `layer_lock_closed.svg` - locked layer icon.
- `layer_rotate.svg` - layer rotate-handle visibility icon.
- `combo_down.svg` - combo/dropdown arrow.
- `spin_up.svg` - numeric increment arrow.
- `spin_down.svg` - numeric decrement arrow.

Replacement rule: keep the exact filename and replace the file content. The UI should continue to load the same logical asset without changing Python code.

Design rule: these icons are product-level assets. Avoid one-off drawing code when an approved asset exists here.

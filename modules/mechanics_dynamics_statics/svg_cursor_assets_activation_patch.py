"""Activate restored SVG cursor assets as the final cursor layer.

Visual cursor/icon design must be edited in:
    src/engineers_tools/assets/ui_icons/*.svg

This patch only loads those SVG files and maps interaction states to assets.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QCursor, QIcon, QPainter, QPixmap

PATCH_VERSION = "engineering-svg-cursor-assets-2026-06-30-a"

_CURSOR_ASSET_MAP = {
    "default": ("mouse_cursor.svg", 4, 4, 24),
    "select": ("mouse_cursor.svg", 4, 4, 24),
    "pointer": ("hand_pointer.svg", 10, 3, 22),
    "hand_pointer": ("hand_pointer.svg", 10, 3, 22),
    "hand_open": ("hand_open.svg", 12, 8, 24),
    "hand_closed": ("hand_closed.svg", 12, 8, 24),
    "rotate": ("hand_open.svg", 12, 8, 24),
    "rotate_drag": ("hand_closed.svg", 12, 8, 24),
    "move": ("move_cursor.svg", 12, 12, 24),
    "resize_h": ("resize_horizontal.svg", 12, 12, 24),
    "resize_v": ("resize_vertical.svg", 12, 12, 24),
    "resize_horizontal": ("resize_horizontal.svg", 12, 12, 24),
    "resize_vertical": ("resize_vertical.svg", 12, 12, 24),
    "resize_n": ("resize_vertical.svg", 12, 12, 24),
    "resize_s": ("resize_vertical.svg", 12, 12, 24),
    "resize_e": ("resize_horizontal.svg", 12, 12, 24),
    "resize_w": ("resize_horizontal.svg", 12, 12, 24),
    "resize_ne": ("resize_horizontal.svg", 12, 12, 24),
    "resize_sw": ("resize_horizontal.svg", 12, 12, 24),
    "resize_nw": ("resize_vertical.svg", 12, 12, 24),
    "resize_se": ("resize_vertical.svg", 12, 12, 24),
    "resize_diag_f": ("resize_vertical.svg", 12, 12, 24),
    "resize_diag_b": ("resize_horizontal.svg", 12, 12, 24),
    "resize_fdiag": ("resize_vertical.svg", 12, 12, 24),
    "resize_bdiag": ("resize_horizontal.svg", 12, 12, 24),
    "guide_h": ("resize_vertical.svg", 12, 12, 24),
    "guide_v": ("resize_horizontal.svg", 12, 12, 24),
    "origin": ("mouse_cursor.svg", 4, 4, 24),
    "zoom": ("zoom.svg", 12, 12, 24),
    "zoom_in": ("zoom_in.svg", 12, 12, 24),
    "zoom_out": ("zoom_out.svg", 12, 12, 24),
    "zoom_fit": ("zoom_fit.svg", 12, 12, 24),
}

_FALLBACKS = {
    "default": Qt.CursorShape.ArrowCursor,
    "select": Qt.CursorShape.ArrowCursor,
    "pointer": Qt.CursorShape.PointingHandCursor,
    "hand_pointer": Qt.CursorShape.PointingHandCursor,
    "hand_open": Qt.CursorShape.OpenHandCursor,
    "hand_closed": Qt.CursorShape.ClosedHandCursor,
    "rotate": Qt.CursorShape.OpenHandCursor,
    "rotate_drag": Qt.CursorShape.ClosedHandCursor,
    "move": Qt.CursorShape.SizeAllCursor,
    "resize_h": Qt.CursorShape.SizeHorCursor,
    "resize_v": Qt.CursorShape.SizeVerCursor,
    "resize_horizontal": Qt.CursorShape.SizeHorCursor,
    "resize_vertical": Qt.CursorShape.SizeVerCursor,
    "resize_n": Qt.CursorShape.SizeVerCursor,
    "resize_s": Qt.CursorShape.SizeVerCursor,
    "resize_e": Qt.CursorShape.SizeHorCursor,
    "resize_w": Qt.CursorShape.SizeHorCursor,
    "resize_ne": Qt.CursorShape.SizeBDiagCursor,
    "resize_sw": Qt.CursorShape.SizeBDiagCursor,
    "resize_nw": Qt.CursorShape.SizeFDiagCursor,
    "resize_se": Qt.CursorShape.SizeFDiagCursor,
    "resize_diag_f": Qt.CursorShape.SizeFDiagCursor,
    "resize_diag_b": Qt.CursorShape.SizeBDiagCursor,
    "resize_fdiag": Qt.CursorShape.SizeFDiagCursor,
    "resize_bdiag": Qt.CursorShape.SizeBDiagCursor,
    "guide_h": Qt.CursorShape.SizeVerCursor,
    "guide_v": Qt.CursorShape.SizeHorCursor,
    "origin": Qt.CursorShape.CrossCursor,
    "zoom": Qt.CursorShape.CrossCursor,
    "zoom_in": Qt.CursorShape.CrossCursor,
    "zoom_out": Qt.CursorShape.CrossCursor,
    "zoom_fit": Qt.CursorShape.CrossCursor,
}

_HOVER_TO_KIND = {
    "move": "move",
    "rotate": "rotate",
    "resize_n": "resize_n",
    "resize_s": "resize_s",
    "resize_e": "resize_e",
    "resize_w": "resize_w",
    "resize_ne": "resize_ne",
    "resize_sw": "resize_sw",
    "resize_nw": "resize_nw",
    "resize_se": "resize_se",
}

_CURSOR_CACHE: dict[tuple[str, int, int, int], QCursor] = {}
_ICON_CACHE: dict[str, QIcon] = {}


def _asset_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "engineers_tools" / "assets" / "ui_icons"


def _asset_path(file_name: str) -> Path | None:
    path = _asset_dir() / file_name
    return path if path.exists() else None


def _render_svg_to_pixmap(path: Path, max_side: int) -> QPixmap:
    try:
        from PySide6.QtSvg import QSvgRenderer
    except Exception:
        return QPixmap(str(path))
    renderer = QSvgRenderer(str(path))
    if not renderer.isValid():
        return QPixmap(str(path))
    size = renderer.defaultSize()
    width = max(1, size.width())
    height = max(1, size.height())
    scale = min(float(max_side) / float(width), float(max_side) / float(height), 1.0)
    pixmap = QPixmap(max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter, QRectF(0, 0, pixmap.width(), pixmap.height()))
    painter.end()
    return pixmap


def _pixmap_from_asset(file_name: str, max_side: int) -> QPixmap:
    path = _asset_path(file_name)
    if path is None:
        return QPixmap()
    if path.suffix.lower() == ".svg":
        pixmap = _render_svg_to_pixmap(path, max_side)
    else:
        pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return pixmap
    if pixmap.width() > max_side or pixmap.height() > max_side:
        pixmap = pixmap.scaled(max_side, max_side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return pixmap


def asset_cursor(file_name: str, fallback: QCursor | Qt.CursorShape, hot_x: int = 8, hot_y: int = 8, max_side: int = 24) -> QCursor:
    fallback_cursor = fallback if isinstance(fallback, QCursor) else QCursor(fallback)
    key = (file_name, int(hot_x), int(hot_y), int(max_side))
    cached = _CURSOR_CACHE.get(key)
    if cached is not None:
        return cached
    pixmap = _pixmap_from_asset(file_name, max_side)
    if pixmap.isNull():
        return fallback_cursor
    safe_hot_x = max(0, min(int(hot_x), max(0, pixmap.width() - 1)))
    safe_hot_y = max(0, min(int(hot_y), max(0, pixmap.height() - 1)))
    cursor = QCursor(pixmap, safe_hot_x, safe_hot_y)
    _CURSOR_CACHE[key] = cursor
    return cursor


def project_cursor(kind: str) -> QCursor:
    asset = _CURSOR_ASSET_MAP.get(kind) or _CURSOR_ASSET_MAP["default"]
    file_name, hot_x, hot_y, max_side = asset
    fallback = _FALLBACKS.get(kind, Qt.CursorShape.ArrowCursor)
    return asset_cursor(file_name, fallback, hot_x, hot_y, max_side)


def asset_icon(file_name: str) -> QIcon:
    cached = _ICON_CACHE.get(file_name)
    if cached is not None:
        return cached
    path = _asset_path(file_name)
    icon = QIcon(str(path)) if path is not None else QIcon()
    _ICON_CACHE[file_name] = icon
    return icon


def _canvas_kind_from_hover(hover: str | None, drag_action: str | None = None) -> str:
    if drag_action == "rotate":
        return "rotate_drag"
    if drag_action:
        return _HOVER_TO_KIND.get(drag_action, "default")
    return _HOVER_TO_KIND.get(str(hover), "default")


def _set_canvas_hover_cursor(canvas, hover: str | None) -> None:
    canvas.setCursor(project_cursor(_canvas_kind_from_hover(hover)))


def _install_startbar_pointer(start_bar) -> None:
    pointer = project_cursor("hand_pointer")
    try:
        for button in getattr(start_bar, "_buttons", {}).values():
            button.setCursor(pointer)
    except Exception:
        return


def apply_svg_cursor_assets_activation_patch() -> None:
    from . import cursor_unification_fixes as cuf
    from . import interaction_fixes as interaction
    from . import ui_refinement_fixes
    from . import window_resize_fixes
    from . import workspace as edw
    from src.engineers_tools.app import engineering_ui_small_fixes_patch as small_fixes
    from src.engineers_tools.app import interaction_ui_patch as interaction_ui
    from src.engineers_tools.ui import start_bar as sb

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_svg_cursor_assets_patch", "") == PATCH_VERSION:
        return

    cuf.project_cursor = project_cursor
    interaction.project_cursor = project_cursor
    ui_refinement_fixes._refined_project_cursor = project_cursor
    window_resize_fixes._window_cursor = project_cursor
    small_fixes._asset_cursor = asset_cursor
    small_fixes._compact_cursor_from_asset = asset_cursor
    small_fixes._set_canvas_hover_cursor = _set_canvas_hover_cursor
    interaction_ui._cursor_from_asset = lambda file_name, fallback, hot_x=8, hot_y=8: asset_cursor(file_name, fallback, hot_x, hot_y, 24)
    sb._zoom_cursor = lambda mode: project_cursor(mode if mode in {"zoom_in", "zoom_out", "zoom_fit"} else "zoom")

    original_canvas_press = edw.EngineeringCanvas.mousePressEvent
    original_canvas_move = edw.EngineeringCanvas.mouseMoveEvent
    original_canvas_release = edw.EngineeringCanvas.mouseReleaseEvent
    original_startbar_init = sb.StartBar.__init__
    original_startbar_show = sb.StartBar.showEvent
    original_guide_init = sb._GuideLine.__init__
    original_overlay_init = sb._RulerOverlay.__init__
    original_corner_init = sb._RulerCorner.__init__

    def canvas_press(self, event) -> None:
        original_canvas_press(self, event)
        self.setCursor(project_cursor(_canvas_kind_from_hover(None, getattr(self, "_drag_action", None))))

    def canvas_move(self, event) -> None:
        original_canvas_move(self, event)
        drag_action = getattr(self, "_drag_action", None)
        if drag_action:
            self.setCursor(project_cursor(_canvas_kind_from_hover(None, drag_action)))
            return
        try:
            point = self._to_canvas_point(event.position())
            _index, hover = self._hit_test_object(point)
            self.setCursor(project_cursor(_canvas_kind_from_hover(hover)))
        except Exception:
            self.setCursor(project_cursor("default"))

    def canvas_release(self, event) -> None:
        original_canvas_release(self, event)
        try:
            point = self._to_canvas_point(event.position())
            _index, hover = self._hit_test_object(point)
            self.setCursor(project_cursor(_canvas_kind_from_hover(hover)))
        except Exception:
            self.setCursor(project_cursor("default"))

    def startbar_init(self, *args, **kwargs) -> None:
        original_startbar_init(self, *args, **kwargs)
        _install_startbar_pointer(self)

    def startbar_show(self, event) -> None:
        original_startbar_show(self, event)
        _install_startbar_pointer(self)

    def guide_init(self, orientation: str, position: float, parent, start_bar=None, persistent: bool = True) -> None:
        original_guide_init(self, orientation, position, parent, start_bar, persistent)
        self.setCursor(project_cursor("guide_h" if orientation == "horizontal" else "guide_v"))

    def overlay_init(self, start_bar, orientation: str, parent) -> None:
        original_overlay_init(self, start_bar, orientation, parent)
        self.setCursor(project_cursor("guide_h" if orientation == "top" else "guide_v"))

    def corner_init(self, start_bar, parent) -> None:
        original_corner_init(self, start_bar, parent)
        self.setCursor(project_cursor("origin"))

    edw.EngineeringCanvas.mousePressEvent = canvas_press
    edw.EngineeringCanvas.mouseMoveEvent = canvas_move
    edw.EngineeringCanvas.mouseReleaseEvent = canvas_release
    sb.StartBar.__init__ = startbar_init
    sb.StartBar.showEvent = startbar_show
    sb._GuideLine.__init__ = guide_init
    sb._RulerOverlay.__init__ = overlay_init
    sb._RulerCorner.__init__ = corner_init
    edw.EngineeringDesignWorkspace._engineering_svg_cursor_assets_patch = PATCH_VERSION

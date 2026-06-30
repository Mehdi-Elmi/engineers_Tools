"""Window resize behavior for the Engineering Design Tools shell.

The main window is frameless, so Qt does not provide native resize borders.
This module adds project-styled edge/corner resize behavior without changing the
engineering page size. Window resize changes the viewport only.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QApplication, QAbstractButton, QAbstractSpinBox, QLineEdit, QWidget

PATCH_VERSION = "engineering-window-resize-2026-06-30-b"
RESIZE_MARGIN = 11
MOVE_BAND_HEIGHT = 46
WORKSPACE_SIZE_MM = (400.0, 220.0)
_FILTER: QObject | None = None

_INTERACTIVE_NAMES = {
    "WindowButton",
    "CloseButton",
    "HomeButton",
    "MenuButton",
    "ToolButton",
    "ToolIconButton",
    "LayerIconButton",
    "LayerExpandButton",
    "PageButton",
    "PageButtonActive",
    "AddPageButton",
    "IconChoice",
    "RadioChoice",
}


def _cursor_arrow(painter: QPainter, tip: QPointF, tail: QPointF, size: float = 5.0) -> None:
    direction = tip - tail
    length = max(0.01, math.hypot(direction.x(), direction.y()))
    unit = QPointF(direction.x() / length, direction.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    base = QPointF(tip.x() - unit.x() * size, tip.y() - unit.y() * size)
    left = QPointF(base.x() + normal.x() * size * 0.48, base.y() + normal.y() * size * 0.48)
    right = QPointF(base.x() - normal.x() * size * 0.48, base.y() - normal.y() * size * 0.48)
    painter.drawPolygon(QPolygonF([tip, left, right]))


def _window_cursor(kind: str) -> QCursor:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    glow = QColor("#ffffff")
    ink = QColor("#dff6ff")
    edge = QColor("#163452")

    def stroke_line(a: QPointF, b: QPointF) -> None:
        painter.setPen(QPen(glow, 4.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(a, b)
        painter.setPen(QPen(edge, 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(a, b)
        painter.setPen(QPen(ink, 1.15, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(a, b)
        painter.setBrush(edge)
        painter.setPen(Qt.PenStyle.NoPen)
        _cursor_arrow(painter, a, b, 5.4)
        _cursor_arrow(painter, b, a, 5.4)

    if kind == "resize_h":
        stroke_line(QPointF(6, 16), QPointF(26, 16))
    elif kind == "resize_v":
        stroke_line(QPointF(16, 6), QPointF(16, 26))
    elif kind == "resize_fdiag":
        stroke_line(QPointF(8, 8), QPointF(24, 24))
    elif kind == "resize_bdiag":
        stroke_line(QPointF(24, 8), QPointF(8, 24))
    else:
        stroke_line(QPointF(16, 6), QPointF(16, 26))
    painter.end()
    return QCursor(pixmap, 16, 16)


def _set_window_cursor(window: QWidget, kind: str | None) -> None:
    app = QApplication.instance()
    if app is None:
        return
    active = bool(getattr(window, "_engineering_window_cursor_active", False))
    current = getattr(window, "_engineering_window_cursor_kind", None)
    if kind is None:
        if active:
            app.restoreOverrideCursor()
        window._engineering_window_cursor_active = False
        window._engineering_window_cursor_kind = None
        return
    if active and current == kind:
        return
    if active:
        app.restoreOverrideCursor()
    app.setOverrideCursor(_window_cursor(kind))
    window._engineering_window_cursor_active = True
    window._engineering_window_cursor_kind = kind


def _window_edges(window: QWidget, pos: QPoint) -> frozenset[str]:
    if getattr(window, "_is_manually_maximized", False) or window.isMaximized():
        return frozenset()
    rect = window.rect()
    if pos.x() < 0 or pos.y() < 0 or pos.x() > rect.width() or pos.y() > rect.height():
        return frozenset()
    edges: set[str] = set()
    if pos.x() <= RESIZE_MARGIN:
        edges.add("left")
    if pos.x() >= rect.width() - RESIZE_MARGIN:
        edges.add("right")
    if pos.y() <= RESIZE_MARGIN:
        edges.add("top")
    if pos.y() >= rect.height() - RESIZE_MARGIN:
        edges.add("bottom")
    return frozenset(edges)


def _cursor_kind(edges: frozenset[str]) -> str | None:
    if not edges:
        return None
    if {"left", "top"}.issubset(edges) or {"right", "bottom"}.issubset(edges):
        return "resize_fdiag"
    if {"right", "top"}.issubset(edges) or {"left", "bottom"}.issubset(edges):
        return "resize_bdiag"
    if "left" in edges or "right" in edges:
        return "resize_h"
    if "top" in edges or "bottom" in edges:
        return "resize_v"
    return None


def _interactive_child(widget: QWidget, window: QWidget) -> bool:
    current: QWidget | None = widget
    while current is not None and current is not window:
        if isinstance(current, (QAbstractButton, QAbstractSpinBox, QLineEdit)):
            return True
        if current.objectName() in _INTERACTIVE_NAMES:
            return True
        current = current.parentWidget()
    return False


def _is_move_surface(widget: QWidget, window: QWidget, window_pos: QPoint) -> bool:
    if getattr(window, "_is_manually_maximized", False) or window.isMaximized():
        return False
    if window_pos.y() > MOVE_BAND_HEIGHT:
        return False
    if _window_edges(window, window_pos):
        return False
    return not _interactive_child(widget, window)


def _apply_window_resize(window: QWidget, global_pos: QPoint) -> None:
    edges: frozenset[str] = getattr(window, "_engineering_resize_edges", frozenset())
    start_global: QPoint = getattr(window, "_engineering_resize_start_global", global_pos)
    start_geometry: QRect = getattr(window, "_engineering_resize_start_geometry", window.geometry())
    delta = global_pos - start_global
    rect = QRect(start_geometry)
    min_w = max(720, int(window.minimumWidth()))
    min_h = max(460, int(window.minimumHeight()))

    if "left" in edges:
        rect.setLeft(min(start_geometry.left() + delta.x(), start_geometry.right() - min_w))
    if "right" in edges:
        rect.setRight(max(start_geometry.right() + delta.x(), start_geometry.left() + min_w))
    if "top" in edges:
        rect.setTop(min(start_geometry.top() + delta.y(), start_geometry.bottom() - min_h))
    if "bottom" in edges:
        rect.setBottom(max(start_geometry.bottom() + delta.y(), start_geometry.top() + min_h))

    window.setGeometry(rect)
    _sync_fixed_workspace_metadata(window)


def _apply_window_move(window: QWidget, global_pos: QPoint) -> None:
    start_global: QPoint = getattr(window, "_engineering_move_start_global", global_pos)
    start_geometry: QRect = getattr(window, "_engineering_move_start_geometry", window.geometry())
    window.move(start_geometry.topLeft() + (global_pos - start_global))


def _sync_fixed_workspace_metadata(window: QWidget) -> None:
    canvas = getattr(window, "_canvas", None)
    if canvas is None:
        return
    canvas._engineering_workspace_size_mm = WORKSPACE_SIZE_MM
    canvas._page_setup_size_mm = WORKSPACE_SIZE_MM
    canvas.update()
    start_bar = getattr(window, "_start_bar_widget", None)
    if start_bar is not None and getattr(start_bar, "_ruler_enabled", False):
        position = getattr(start_bar, "_position_rulers", None)
        if callable(position):
            position()


class _WindowResizeFilter(QObject):
    def __init__(self, module_window_cls: type[QWidget]) -> None:
        super().__init__()
        self._module_window_cls = module_window_cls

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if not isinstance(watched, QWidget):
            return False
        window = watched.window()
        if not isinstance(window, self._module_window_cls):
            return False
        event_type = event.type()
        if event_type not in {QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.Leave}:
            return False

        try:
            if event_type == QEvent.Type.Leave:
                if not getattr(window, "_engineering_resize_active", False):
                    _set_window_cursor(window, None)
                return False
            local_pos = event.position().toPoint()
            window_pos = watched.mapTo(window, local_pos)
            global_pos = event.globalPosition().toPoint()
        except AttributeError:
            return False

        if event_type == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            edges = _window_edges(window, window_pos)
            if edges:
                window._engineering_resize_active = True
                window._engineering_resize_edges = edges
                window._engineering_resize_start_global = global_pos
                window._engineering_resize_start_geometry = QRect(window.geometry())
                _set_window_cursor(window, _cursor_kind(edges))
                event.accept()
                return True
            if _is_move_surface(watched, window, window_pos):
                window._engineering_move_active = True
                window._engineering_move_start_global = global_pos
                window._engineering_move_start_geometry = QRect(window.geometry())
                window._drag_position = None
                event.accept()
                return True
            return False

        if event_type == QEvent.Type.MouseMove:
            if getattr(window, "_engineering_resize_active", False):
                _apply_window_resize(window, global_pos)
                _set_window_cursor(window, _cursor_kind(getattr(window, "_engineering_resize_edges", frozenset())))
                event.accept()
                return True
            if getattr(window, "_engineering_move_active", False):
                _apply_window_move(window, global_pos)
                event.accept()
                return True
            if event.buttons() & Qt.MouseButton.LeftButton:
                return False
            edges = _window_edges(window, window_pos)
            _set_window_cursor(window, _cursor_kind(edges))
            return False

        if event_type == QEvent.Type.MouseButtonRelease:
            if getattr(window, "_engineering_resize_active", False):
                window._engineering_resize_active = False
                window._engineering_resize_edges = frozenset()
                _set_window_cursor(window, None)
                _sync_fixed_workspace_metadata(window)
                event.accept()
                return True
            if getattr(window, "_engineering_move_active", False):
                window._engineering_move_active = False
                event.accept()
                return True

        return False


def apply_window_resize_fixes() -> None:
    global _FILTER
    from src.engineers_tools.app.module_window import ModuleWindow

    if getattr(ModuleWindow, "_engineering_window_resize_patch", "") == PATCH_VERSION:
        return

    original_resize_event = ModuleWindow.resizeEvent

    def resize_event(self, event) -> None:
        original_resize_event(self, event)
        _sync_fixed_workspace_metadata(self)

    ModuleWindow.resizeEvent = resize_event
    ModuleWindow._engineering_window_resize_patch = PATCH_VERSION

    app = QApplication.instance()
    if app is not None and _FILTER is None:
        _FILTER = _WindowResizeFilter(ModuleWindow)
        app.installEventFilter(_FILTER)

"""Shared engineering workspace window."""

from __future__ import annotations

import base64
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QRegion, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..ui.start_bar import DEFAULT_START_BAR_TOOLS, StartBar, StartBarTool
from .modules import LauncherModule
from .project_file_dialog import ProjectFileDialog


def _apply_rounded_mask(widget: QWidget, radius: float) -> None:
    if widget.width() <= 0 or widget.height() <= 0:
        return
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, widget.width(), widget.height()), radius, radius)
    widget.setMask(QRegion(path.toFillPolygon().toPolygon()))


@dataclass(frozen=True)
class MenuItemSpec:
    label: str
    handler: Callable[[], None] | None = None
    shortcut: str = ""
    checkable: bool = False
    checked: bool = False


class GridCanvas(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._grid_visible = True
        self._zoom = 1.0

    def set_grid_visible(self, visible: bool) -> None:
        self._grid_visible = visible
        self.update()

    def set_zoom(self, zoom_percent: float) -> None:
        self._zoom = max(0.05, zoom_percent / 100.0)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#f9fbff"))
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._zoom, self._zoom)
        painter.translate(-self.width() / 2, -self.height() / 2)

        if not self._grid_visible:
            return

        painter.setPen(QPen(QColor(70, 96, 130, 45), 1))
        columns = 16
        rows = 12
        for column in range(1, columns):
            x = round(self.width() * column / columns)
            painter.drawLine(x, 0, x, self.height())
        for row in range(1, rows):
            y = round(self.height() * row / rows)
            painter.drawLine(0, y, self.width(), y)


class ProjectHelpDialog(QDialog):
    """Project-styled help page opened by the Help command."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectHelpDialog")
        self.setWindowTitle("Help")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumSize(480, 300)

        shell = QWidget()
        shell.setObjectName("ProjectHelpShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(12)

        header = QWidget()
        header.setObjectName("HelpHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 8, 0)
        header_layout.setSpacing(8)

        title = QLabel("Engineer Tools Help")
        title.setObjectName("HelpTitle")
        header_layout.addWidget(title, 1)

        close = QPushButton("×")
        close.setObjectName("MenuDialogClose")
        close.setFixedSize(28, 26)
        close.clicked.connect(self.accept)
        header_layout.addWidget(close)
        layout.addWidget(header)

        body = QLabel(
            "Common workspace commands are available from the top command bar.\n\n"
            "File manages project documents. Edit handles object and clipboard operations. "
            "View controls shared workspace visibility such as Grid, Ruler and Snap. "
            "Insert is reserved for adding design content."
        )
        body.setObjectName("HelpBody")
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(body, 1)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        _apply_rounded_mask(self, 16)


class ProjectMenuDialog(QDialog):
    """Rounded dropdown menu used by the Command Bar."""

    def __init__(self, title: str, items: tuple[MenuItemSpec, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectMenuDialog")
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        shell = QWidget()
        shell.setObjectName("ProjectMenuShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)

        if not items:
            empty = QLabel("No tools defined yet.")
            empty.setObjectName("MenuDialogEmpty")
            empty.setWordWrap(True)
            layout.addWidget(empty)
        for item in items:
            button_text = self._build_button_text(item)
            button = QPushButton(button_text)
            button.setObjectName("MenuItemButton")
            button.setMinimumHeight(28)
            if item.handler is not None:
                button.clicked.connect(self._wrap_handler(item.handler))
            layout.addWidget(button)

        self.setFixedWidth(self._preferred_width(items))

    def _preferred_width(self, items: tuple[MenuItemSpec, ...]) -> int:
        if not items:
            return 190
        longest = max(self.fontMetrics().horizontalAdvance(self._build_button_text(item)) for item in items)
        return max(188, min(242, longest + 54))

    def _build_button_text(self, item: MenuItemSpec) -> str:
        prefix = "◉  " if item.checkable and item.checked else "○  " if item.checkable else ""
        shortcut = f"    {item.shortcut}" if item.shortcut else ""
        return f"{prefix}{item.label}{shortcut}"

    def _wrap_handler(self, handler: Callable[[], None]) -> Callable[[], None]:
        def run() -> None:
            handler()
            self.accept()

        return run

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        _apply_rounded_mask(self, 12)


class ModuleWindow(QMainWindow):
    back_requested = Signal()
    new_workspace_requested = Signal(object)

    def __init__(self, module: LauncherModule) -> None:
        super().__init__()
        self.module = module
        self.setWindowTitle(module.title)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(960, 620)
        self.resize(1180, 760)
        self._drag_position: QPoint | None = None
        self._normal_geometry: QRect | None = None
        self._is_manually_maximized = False
        self._maximize_button: QPushButton | None = None
        self._start_bar_widget: StartBar | None = None
        self._canvas: GridCanvas | None = None
        self._status_items: list[QLabel] = []
        self._zoom_input: QDoubleSpinBox | None = None
        self._current_file_path: Path | None = None
        self._last_file_dir: Path | None = None
        self._view_state = {"start_bar": True, "grid": True, "ruler": False, "snap": False}

        root = QWidget()
        root.setObjectName("WindowRoot")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_top_bar())
        layout.addWidget(self._build_command_bar())
        layout.addWidget(self._build_start_bar())
        layout.addWidget(self._build_workspace(), 1)
        layout.addWidget(self._build_page_bar())
        layout.addWidget(self._build_status_bar())
        self._install_shortcuts()

    def get_start_bar_tools(self) -> tuple[StartBarTool, ...]:
        return DEFAULT_START_BAR_TOOLS

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(46)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 10, 0)
        layout.setSpacing(10)
        layout.addWidget(self._build_window_mark())

        title = QLabel(self.module.title)
        title.setObjectName("WindowTitle")
        layout.addWidget(title, 1)

        minimize = QPushButton("-")
        minimize.setObjectName("WindowButton")
        minimize.setFixedSize(34, 30)
        minimize.clicked.connect(self._minimize_window)
        layout.addWidget(minimize)

        maximize = QPushButton("[]")
        maximize.setObjectName("WindowButton")
        maximize.setFixedSize(34, 30)
        maximize.clicked.connect(self._toggle_maximize)
        self._maximize_button = maximize
        layout.addWidget(maximize)

        close = QPushButton("×")
        close.setObjectName("CloseButton")
        close.setFixedSize(34, 30)
        close.clicked.connect(self.close)
        layout.addWidget(close)
        return bar

    def _build_window_mark(self) -> QLabel:
        mark = QLabel("AT")
        mark.setObjectName("WindowMark")
        mark.setFixedSize(42, 36)
        mark.setAlignment(Qt.AlignCenter)
        logo_path = self._find_logo_path()
        if logo_path is None:
            return mark
        pixmap = QPixmap(str(logo_path))
        if pixmap.isNull():
            return mark
        mark.setText("")
        mark.setObjectName("WindowLogoMark")
        mark.setPixmap(pixmap.scaled(36, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return mark

    def _find_logo_path(self) -> Path | None:
        logo_dir = Path(__file__).resolve().parents[3] / "logo"
        if not logo_dir.exists():
            return None
        allowed_suffixes = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
        candidates = sorted(path for path in logo_dir.iterdir() if path.is_file() and path.suffix.lower() in allowed_suffixes)
        return candidates[0] if candidates else None

    def _build_command_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("CommandBar")
        bar.setFixedHeight(40)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 4, 14, 4)
        layout.setSpacing(10)

        home = QPushButton()
        home.setObjectName("HomeButton")
        home.setToolTip("Back to launcher")
        home.setFixedSize(48, 30)
        home.setIcon(self._build_home_icon())
        home.setIconSize(QSize(31, 25))
        home.clicked.connect(self.back_requested.emit)
        layout.addWidget(home)

        menu_map: tuple[tuple[str, Callable[[QWidget], None]], ...] = (
            ("File", self._show_file_menu),
            ("Edit", self._show_edit_menu),
            ("View", self._show_view_menu),
            ("Insert", self._show_insert_menu),
            ("Draw", self._show_draw_menu),
            ("Help", lambda source: self._open_help_page()),
        )
        for label, handler in menu_map:
            button = QPushButton(label)
            button.setObjectName("MenuButton")
            button.setFixedHeight(26)
            button.clicked.connect(lambda checked=False, source=button, action=handler: action(source))
            layout.addWidget(button)
        layout.addStretch(1)
        return bar

    def _build_start_bar(self) -> QWidget:
        self._start_bar_widget = StartBar(self.get_start_bar_tools())
        return self._start_bar_widget

    def _build_workspace(self) -> QWidget:
        area = QWidget()
        area.setObjectName("WorkspaceArea")
        layout = QHBoxLayout(area)
        layout.setContentsMargins(14, 14, 14, 10)
        layout.setSpacing(12)
        properties = self._build_side_panel("Properties", ("Selection", "Coordinates", "Size", "Style", "Behavior"))
        properties.setFixedWidth(220)
        layout.addWidget(properties)

        canvas_shell = QWidget()
        canvas_shell.setObjectName("CanvasShell")
        canvas_layout = QVBoxLayout(canvas_shell)
        canvas_layout.setContentsMargins(12, 12, 12, 12)
        canvas_layout.setSpacing(0)
        self._canvas = GridCanvas()
        self._canvas.setObjectName("GridCanvas")
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas_layout.addWidget(self._canvas, 1)
        layout.addWidget(canvas_shell, 1)

        layers = self._build_side_panel("Layers", ("Page 1", "Grid", "Objects", "Annotations"))
        layers.setFixedWidth(220)
        layout.addWidget(layers)
        return area

    def _build_side_panel(self, title: str, rows: tuple[str, ...]) -> QWidget:
        panel = QWidget()
        panel.setObjectName("SidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("PanelTitle")
        layout.addWidget(heading)
        for row in rows:
            item = QLabel(row)
            item.setObjectName("PanelItem")
            item.setFixedHeight(30)
            layout.addWidget(item)
        layout.addStretch(1)
        return panel

    def _build_page_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("PageBar")
        bar.setFixedHeight(44)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 5, 14, 5)
        layout.setSpacing(8)
        page = QPushButton("Page 1")
        page.setObjectName("ToolButton")
        layout.addWidget(page)
        layout.addStretch(1)
        add_page = QPushButton("Add Page")
        add_page.setObjectName("ConfirmButton")
        add_page.clicked.connect(lambda: self._set_status("Page added"))
        layout.addWidget(add_page)
        return bar

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(34)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)
        self._status_items = []

        zoom_label = QLabel("Zoom:")
        zoom_label.setObjectName("StatusItem")
        layout.addWidget(zoom_label)
        self._zoom_input = QDoubleSpinBox()
        self._zoom_input.setObjectName("ZoomInput")
        self._zoom_input.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self._zoom_input.setRange(5.0, 3200.0)
        self._zoom_input.setDecimals(2)
        self._zoom_input.setSingleStep(5.0)
        self._zoom_input.setValue(100.0)
        self._zoom_input.setSuffix(" %")
        self._zoom_input.setFixedWidth(92)
        self._zoom_input.valueChanged.connect(self._set_zoom)
        layout.addWidget(self._zoom_input)

        tool_item = QLabel("Tool Select: Ready")
        tool_item.setObjectName("StatusItem")
        layout.addWidget(tool_item)
        self._status_items.append(tool_item)

        coordinate_item = QLabel("X: 0  Y: 0")
        coordinate_item.setObjectName("StatusItem")
        layout.addWidget(coordinate_item)
        self._status_items.append(coordinate_item)

        layout.addStretch(1)
        unit_item = QLabel("Unit: mm")
        unit_item.setObjectName("StatusItem")
        layout.addWidget(unit_item)
        self._status_items.append(unit_item)
        return bar

    def _install_shortcuts(self) -> None:
        shortcuts: tuple[tuple[str, Callable[[], None]], ...] = (
            ("Ctrl+N", self._new_file), ("Ctrl+O", self._open_file), ("Ctrl+S", self._save_file),
            ("Ctrl+Shift+S", self._save_as_file), ("Ctrl+Z", self._undo), ("Ctrl+Y", self._redo),
            ("Ctrl+X", self._cut), ("Ctrl+C", self._copy), ("Ctrl+V", self._paste),
            ("Delete", self._delete), ("Ctrl+R", self._repeat_last_tools), ("Ctrl+A", self._select_all),
            ("Ctrl+G", self._group), ("Ctrl+Shift+G", self._ungroup),
        )
        for sequence, handler in shortcuts:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(handler)

    def _show_menu(self, title: str, items: tuple[MenuItemSpec, ...], anchor: QWidget) -> None:
        dialog = ProjectMenuDialog(title, items, self)
        dialog.adjustSize()
        position = anchor.mapToGlobal(QPoint(0, anchor.height() + 3))
        screen = anchor.screen()
        if screen is not None:
            available = screen.availableGeometry()
            if position.x() + dialog.width() > available.right():
                position.setX(max(available.left(), available.right() - dialog.width()))
            if position.y() + dialog.height() > available.bottom():
                position.setY(anchor.mapToGlobal(QPoint(0, -dialog.height() - 3)).y())
        dialog.move(position)
        dialog.exec()

    def _show_file_menu(self, anchor: QWidget) -> None:
        self._show_menu("File", (
            MenuItemSpec("New", self._new_file, "Ctrl+N"),
            MenuItemSpec("Open", self._open_file, "Ctrl+O"),
            MenuItemSpec("Save", self._save_file, "Ctrl+S"),
            MenuItemSpec("Save As", self._save_as_file, "Ctrl+Shift+S"),
            MenuItemSpec("Page Setup", self._page_setup),
            MenuItemSpec("Print Setup", self._print_setup),
            MenuItemSpec("Import", self._import_file),
            MenuItemSpec("Export", self._export_file),
            MenuItemSpec("Properties", self._file_properties),
        ), anchor)

    def _show_edit_menu(self, anchor: QWidget) -> None:
        self._show_menu("Edit", (
            MenuItemSpec("Copy", self._copy, "Ctrl+C"),
            MenuItemSpec("Cut", self._cut, "Ctrl+X"),
            MenuItemSpec("Paste", self._paste, "Ctrl+V"),
            MenuItemSpec("Move", self._move),
            MenuItemSpec("Undo", self._undo, "Ctrl+Z"),
            MenuItemSpec("Redo", self._redo, "Ctrl+Y"),
            MenuItemSpec("Repeat Last Tools", self._repeat_last_tools, "Ctrl+R"),
            MenuItemSpec("Select All", self._select_all, "Ctrl+A"),
            MenuItemSpec("Group", self._group, "Ctrl+G"),
            MenuItemSpec("Ungroup", self._ungroup, "Ctrl+Shift+G"),
        ), anchor)

    def _show_view_menu(self, anchor: QWidget) -> None:
        self._show_menu("View", (
            MenuItemSpec("Start Bar", self._toggle_start_bar, checkable=True, checked=self._view_state["start_bar"]),
            MenuItemSpec("Grid", self._toggle_grid, checkable=True, checked=self._view_state["grid"]),
            MenuItemSpec("Ruler", self._toggle_ruler, checkable=True, checked=self._view_state["ruler"]),
            MenuItemSpec("Snap", self._toggle_snap, checkable=True, checked=self._view_state["snap"]),
        ), anchor)

    def _show_insert_menu(self, anchor: QWidget) -> None:
        self._show_menu("Insert", (MenuItemSpec("Text", self._insert_text),), anchor)

    def _show_draw_menu(self, anchor: QWidget) -> None:
        self._show_menu("Draw", (), anchor)

    def _open_help_page(self) -> None:
        ProjectHelpDialog(self).exec()
        self._set_status("Help opened")

    def _new_file(self) -> None:
        self.new_workspace_requested.emit(self.module)
        self._set_status("New workspace opened")

    def _open_file(self) -> None:
        result = ProjectFileDialog.get_open_file(self, self._last_file_dir)
        if result is None:
            self._set_status("Open canceled")
            return
        self._current_file_path = result.path
        self._last_file_dir = result.path.parent
        self._set_status(f"Opened {result.path.name}")

    def _save_file(self) -> None:
        if self._current_file_path is None:
            self._save_as_file()
            return
        self._write_document(self._current_file_path)
        self._set_status(f"Saved {self._current_file_path.name}")

    def _save_as_file(self) -> None:
        result = ProjectFileDialog.get_save_file(self, self._last_file_dir)
        if result is None:
            self._set_status("Save As canceled")
            return
        self._write_document(result.path)
        self._current_file_path = result.path
        self._last_file_dir = result.path.parent
        self._set_status(f"Saved As {result.path.name}")

    def _write_document(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            path.write_bytes(self._blank_pdf_bytes())
        elif suffix == ".svg":
            path.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"800\" height=\"600\"></svg>\n", encoding="utf-8")
        elif suffix == ".png":
            path.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="))
        else:
            path.write_text("Engineer Tools document placeholder\n", encoding="utf-8")

    def _blank_pdf_bytes(self) -> bytes:
        return (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000053 00000 n \n0000000102 00000 n \n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n169\n%%EOF\n"
        )

    def _page_setup(self) -> None:
        self._set_status("Page Setup opened")

    def _print_setup(self) -> None:
        self._set_status("Print Setup opened")

    def _import_file(self) -> None:
        result = ProjectFileDialog.get_open_file(self, self._last_file_dir)
        self._set_status(f"Imported {result.path.name}" if result else "Import canceled")

    def _export_file(self) -> None:
        result = ProjectFileDialog.get_save_file(self, self._last_file_dir)
        if result:
            self._write_document(result.path)
            self._set_status(f"Exported {result.path.name}")
        else:
            self._set_status("Export canceled")

    def _file_properties(self) -> None:
        self._set_status("File Properties opened")

    def _run_focus_command(self, command: str) -> bool:
        focused = QApplication.focusWidget()
        if focused is None or focused is self:
            return False
        action = getattr(focused, command, None)
        if not callable(action):
            return False
        action()
        return True

    def _undo(self) -> None:
        self._run_focus_command("undo")
        self._set_status("Undo")

    def _redo(self) -> None:
        self._run_focus_command("redo")
        self._set_status("Redo")

    def _cut(self) -> None:
        self._run_focus_command("cut")
        self._set_status("Cut")

    def _copy(self) -> None:
        self._run_focus_command("copy")
        self._set_status("Copy")

    def _paste(self) -> None:
        self._run_focus_command("paste")
        self._set_status("Paste")

    def _delete(self) -> None:
        self._set_status("Delete")

    def _repeat_last_tools(self) -> None:
        self._set_status("Repeat Last Tools")

    def _select_all(self) -> None:
        self._run_focus_command("selectAll")
        self._set_status("Select All")

    def _group(self) -> None:
        self._set_status("Group")

    def _ungroup(self) -> None:
        self._set_status("Ungroup")

    def _move(self) -> None:
        self._set_status("Move")

    def _toggle_start_bar(self) -> None:
        self._view_state["start_bar"] = not self._view_state["start_bar"]
        if self._start_bar_widget is not None:
            self._start_bar_widget.setVisible(self._view_state["start_bar"])
        self._set_status(f"Start Bar {'On' if self._view_state['start_bar'] else 'Off'}")

    def _toggle_grid(self) -> None:
        self._view_state["grid"] = not self._view_state["grid"]
        if self._canvas is not None:
            self._canvas.set_grid_visible(self._view_state["grid"])
        self._set_status(f"Grid {'On' if self._view_state['grid'] else 'Off'}")

    def _toggle_ruler(self) -> None:
        self._view_state["ruler"] = not self._view_state["ruler"]
        self._set_status(f"Ruler {'On' if self._view_state['ruler'] else 'Off'}")

    def _toggle_snap(self) -> None:
        self._view_state["snap"] = not self._view_state["snap"]
        self._set_status(f"Snap {'On' if self._view_state['snap'] else 'Off'}")

    def _insert_text(self) -> None:
        self._set_status("Text tool ready")

    def _set_zoom(self, value: float) -> None:
        if self._canvas is not None:
            self._canvas.set_zoom(value)
        self._set_status(f"Zoom {value:.2f}%")

    def _set_status(self, text: str) -> None:
        if self._status_items:
            self._status_items[0].setText(f"Tool Select: {text}")

    def _minimize_window(self) -> None:
        self.setWindowState(self.windowState() | Qt.WindowMinimized)
        self.showMinimized()

    def _toggle_maximize(self) -> None:
        if self._is_manually_maximized:
            self._restore_from_maximize()
            return
        self._normal_geometry = self.geometry()
        screen = self.windowHandle().screen() if self.windowHandle() is not None else self.screen()
        if screen is not None:
            self.setGeometry(screen.availableGeometry())
        else:
            self.showMaximized()
        self._is_manually_maximized = True
        if self._maximize_button is not None:
            self._maximize_button.setText("[ ]")
            self._maximize_button.setToolTip("Restore")

    def _restore_from_maximize(self) -> None:
        self.showNormal()
        if self._normal_geometry is not None:
            self.setGeometry(self._normal_geometry)
        self._is_manually_maximized = False
        if self._maximize_button is not None:
            self._maximize_button.setText("[]")
            self._maximize_button.setToolTip("Maximize")

    def _build_home_icon(self) -> QIcon:
        pixmap = QPixmap(42, 30)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        base = QPainterPath()
        base.addRoundedRect(QRectF(5.0, 4.5, 32.0, 22.0), 8.0, 8.0)
        base_gradient = QLinearGradient(5, 4, 37, 27)
        base_gradient.setColorAt(0.0, QColor("#fff9e8"))
        base_gradient.setColorAt(0.52, QColor("#b8ecff"))
        base_gradient.setColorAt(1.0, QColor("#5e72c9"))
        painter.fillPath(base, base_gradient)
        painter.setPen(QPen(QColor("#ffffff"), 1.1))
        painter.drawPath(base)
        roof = QPolygonF([QPointF(10.5, 15.2), QPointF(21.0, 6.8), QPointF(31.5, 15.2), QPointF(28.8, 17.8), QPointF(21.0, 11.5), QPointF(13.2, 17.8)])
        roof_gradient = QLinearGradient(11, 7, 31, 18)
        roof_gradient.setColorAt(0.0, QColor("#ff9b42"))
        roof_gradient.setColorAt(1.0, QColor("#d44777"))
        painter.setBrush(roof_gradient)
        painter.drawPolygon(roof)
        body = QPainterPath()
        body.addRoundedRect(QRectF(14.0, 15.0, 14.0, 9.0), 2.4, 2.4)
        body_gradient = QLinearGradient(14, 15, 28, 24)
        body_gradient.setColorAt(0.0, QColor("#ffffff"))
        body_gradient.setColorAt(0.48, QColor("#4ed8c3"))
        body_gradient.setColorAt(1.0, QColor("#24548f"))
        painter.fillPath(body, body_gradient)
        painter.drawPath(body)
        painter.drawRoundedRect(QRectF(19.4, 17.9, 3.2, 6.0), 0.9, 0.9)
        painter.end()
        return QIcon(pixmap)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        _apply_rounded_mask(self, 18)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and event.position().y() <= 46:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_position is not None and event.buttons() & Qt.LeftButton and not self._is_manually_maximized:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_position = None
        event.accept()

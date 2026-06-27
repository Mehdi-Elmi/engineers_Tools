"""Shared engineering workspace window.

This window is the mother pattern for project workspaces. Menu dropdowns must use
project-styled rounded surfaces. Native file dialogs may only be used behind
those project surfaces for reliable filesystem operations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
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

    def set_grid_visible(self, visible: bool) -> None:
        self._grid_visible = visible
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#f9fbff"))
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


class ProjectDialog(QDialog):
    """Project-styled dialog shell for File/Open/Save and future dialogs."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(420, 240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel(title)
        heading.setObjectName("PanelTitle")
        layout.addWidget(heading)

        note = QLabel("Project styled dialog. Native file selection is used only behind this layer.")
        note.setObjectName("DialogNote")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        open_button = QPushButton("Open File")
        open_button.setObjectName("ConfirmButton")
        open_button.clicked.connect(self._open_file_backend)
        buttons.addWidget(open_button)

        close_button = QPushButton("Close")
        close_button.setObjectName("ConfirmButton")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    def _open_file_backend(self) -> None:
        # Backend operation: keep the visual shell project-styled, but rely on
        # QFileDialog for real filesystem selection and Windows integration.
        QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.*)")


class ProjectMenuDialog(QDialog):
    """Rounded dropdown menu used by the Command Bar."""

    def __init__(self, title: str, items: tuple[MenuItemSpec, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectMenuDialog")
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(280)

        shell = QWidget()
        shell.setObjectName("ProjectMenuShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(10, 9, 10, 10)
        layout.setSpacing(6)

        heading = QLabel(title)
        heading.setObjectName("MenuDropdownTitle")
        layout.addWidget(heading)

        if not items:
            empty = QLabel("No tools defined yet.")
            empty.setObjectName("MenuDialogEmpty")
            empty.setWordWrap(True)
            layout.addWidget(empty)
        for item in items:
            button_text = self._build_button_text(item)
            button = QPushButton(button_text)
            button.setObjectName("MenuItemButton")
            button.setMinimumHeight(32)
            if item.handler is not None:
                button.clicked.connect(self._wrap_handler(item.handler))
            layout.addWidget(button)

    def _build_button_text(self, item: MenuItemSpec) -> str:
        prefix = "✓  " if item.checkable and item.checked else "□  " if item.checkable else ""
        shortcut = f"    {item.shortcut}" if item.shortcut else ""
        return f"{prefix}{item.label}{shortcut}"

    def _wrap_handler(self, handler: Callable[[], None]) -> Callable[[], None]:
        def run() -> None:
            handler()
            self.accept()

        return run


class ModuleWindow(QMainWindow):
    back_requested = Signal()

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
        """Return tools for the current module's Start Bar.

        Module workspaces can override this method to provide their own tools
        without editing the shared mother window.
        """

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
        home.setFixedSize(54, 32)
        home.setIcon(self._build_home_icon())
        home.setIconSize(QSize(36, 28))
        home.clicked.connect(self.back_requested.emit)
        layout.addWidget(home)

        menu_map: tuple[tuple[str, Callable[[QWidget], None]], ...] = (
            ("File", self._show_file_menu),
            ("Edit", self._show_edit_menu),
            ("View", self._show_view_menu),
            ("Insert", self._show_insert_menu),
            ("Draw", self._show_draw_menu),
            ("Help", self._show_help_menu),
        )
        for label, handler in menu_map:
            button = QPushButton(label)
            button.setObjectName("MenuButton")
            button.setFixedHeight(28)
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
        bar.setFixedHeight(32)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(18)
        self._status_items = []
        for text in ("Tool Select: Ready", "X: 0  Y: 0", "Zoom: 100%", "Unit: mm"):
            item = QLabel(text)
            item.setObjectName("StatusItem")
            layout.addWidget(item)
            self._status_items.append(item)
        layout.addStretch(1)
        return bar

    def _install_shortcuts(self) -> None:
        shortcuts: tuple[tuple[str, Callable[[], None]], ...] = (
            ("Ctrl+N", self._new_file),
            ("Ctrl+O", self._open_file),
            ("Ctrl+S", self._save_file),
            ("Ctrl+Shift+S", self._save_as_file),
            ("Ctrl+Z", self._undo),
            ("Ctrl+Y", self._redo),
            ("Ctrl+X", self._cut),
            ("Ctrl+C", self._copy),
            ("Ctrl+V", self._paste),
            ("Delete", self._delete),
            ("Ctrl+R", self._repeat_last_tools),
            ("Ctrl+A", self._select_all),
            ("Ctrl+G", self._group),
            ("Ctrl+Shift+G", self._ungroup),
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
        self._show_menu(
            "File",
            (
                MenuItemSpec("New", self._new_file, "Ctrl+N"),
                MenuItemSpec("Open", self._open_file, "Ctrl+O"),
                MenuItemSpec("Save", self._save_file, "Ctrl+S"),
                MenuItemSpec("Save As", self._save_as_file, "Ctrl+Shift+S"),
                MenuItemSpec("Page Setup", self._page_setup),
                MenuItemSpec("Print Setup", self._print_setup),
                MenuItemSpec("Import", self._import_file),
                MenuItemSpec("Export", self._export_file),
                MenuItemSpec("Properties", self._file_properties),
            ),
            anchor,
        )

    def _show_edit_menu(self, anchor: QWidget) -> None:
        self._show_menu(
            "Edit",
            (
                MenuItemSpec("Undo", self._undo, "Ctrl+Z"),
                MenuItemSpec("Redo", self._redo, "Ctrl+Y"),
                MenuItemSpec("Cut", self._cut, "Ctrl+X"),
                MenuItemSpec("Copy", self._copy, "Ctrl+C"),
                MenuItemSpec("Paste", self._paste, "Ctrl+V"),
                MenuItemSpec("Delete", self._delete, "Del"),
                MenuItemSpec("Repeat Last Tools", self._repeat_last_tools, "Ctrl+R"),
                MenuItemSpec("Select All", self._select_all, "Ctrl+A"),
                MenuItemSpec("Group", self._group, "Ctrl+G"),
                MenuItemSpec("Ungroup", self._ungroup, "Ctrl+Shift+G"),
                MenuItemSpec("Move", self._move),
            ),
            anchor,
        )

    def _show_view_menu(self, anchor: QWidget) -> None:
        self._show_menu(
            "View",
            (
                MenuItemSpec("Start Bar", self._toggle_start_bar, checkable=True, checked=self._view_state["start_bar"]),
                MenuItemSpec("Grid", self._toggle_grid, checkable=True, checked=self._view_state["grid"]),
                MenuItemSpec("Ruler", self._toggle_ruler, checkable=True, checked=self._view_state["ruler"]),
                MenuItemSpec("Snap", self._toggle_snap, checkable=True, checked=self._view_state["snap"]),
            ),
            anchor,
        )

    def _show_insert_menu(self, anchor: QWidget) -> None:
        self._show_menu("Insert", (MenuItemSpec("Image", self._insert_image), MenuItemSpec("Text", self._insert_text)), anchor)

    def _show_draw_menu(self, anchor: QWidget) -> None:
        self._show_menu("Draw", (), anchor)

    def _show_help_menu(self, anchor: QWidget) -> None:
        self._show_menu("Help", (MenuItemSpec("Shortcuts", self._show_shortcuts), MenuItemSpec("About", self._show_about)), anchor)

    def _new_file(self) -> None:
        self._set_status("New file created")

    def _open_file(self) -> None:
        QFileDialog.getOpenFileName(self, "Open", "", "All Files (*.*)")
        self._set_status("Open completed")

    def _save_file(self) -> None:
        self._set_status("Save completed")

    def _save_as_file(self) -> None:
        QFileDialog.getSaveFileName(self, "Save As", "", "All Files (*.*)")
        self._set_status("Save As completed")

    def _page_setup(self) -> None:
        self._set_status("Page Setup opened")

    def _print_setup(self) -> None:
        self._set_status("Print Setup opened")

    def _import_file(self) -> None:
        QFileDialog.getOpenFileName(self, "Import", "", "All Files (*.*)")
        self._set_status("Import completed")

    def _export_file(self) -> None:
        QFileDialog.getSaveFileName(self, "Export", "", "All Files (*.*)")
        self._set_status("Export completed")

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

    def _insert_image(self) -> None:
        QFileDialog.getOpenFileName(self, "Insert Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.svg);;All Files (*.*)")
        self._set_status("Image inserted")

    def _insert_text(self) -> None:
        self._set_status("Text tool ready")

    def _show_shortcuts(self) -> None:
        self._set_status("Shortcuts opened")

    def _show_about(self) -> None:
        self._set_status("About Engineer Tools")

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
        pixmap = QPixmap(46, 34)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)

        base = QPainterPath()
        base.addRoundedRect(QRectF(5.0, 4.5, 36.0, 25.0), 9.0, 9.0)
        base_gradient = QLinearGradient(5, 4, 41, 30)
        base_gradient.setColorAt(0.0, QColor("#ffffff"))
        base_gradient.setColorAt(0.46, QColor("#dbeaff"))
        base_gradient.setColorAt(1.0, QColor("#4e76aa"))
        painter.fillPath(base, base_gradient)
        painter.setPen(QPen(QColor("#ffffff"), 1.2))
        painter.drawPath(base)

        roof = QPolygonF([QPointF(11.0, 16.7), QPointF(23.0, 7.0), QPointF(35.0, 16.7), QPointF(31.8, 19.6), QPointF(23.0, 12.5), QPointF(14.2, 19.6)])
        painter.setPen(QPen(QColor("#ffffff"), 1.35))
        painter.setBrush(QColor("#1f416f"))
        painter.drawPolygon(roof)

        body = QPainterPath()
        body.addRoundedRect(QRectF(15.0, 16.0, 16.0, 10.8), 2.8, 2.8)
        body_gradient = QLinearGradient(15, 16, 31, 27)
        body_gradient.setColorAt(0.0, QColor("#ffffff"))
        body_gradient.setColorAt(0.42, QColor("#86b7f2"))
        body_gradient.setColorAt(1.0, QColor("#18355d"))
        painter.fillPath(body, body_gradient)
        painter.setPen(QPen(QColor("#ffffff"), 1.2))
        painter.drawPath(body)
        painter.drawRoundedRect(QRectF(21.0, 19.5, 4.0, 7.0), 1.0, 1.0)
        painter.drawLine(QPointF(17.6, 18.7), QPointF(28.4, 18.7))
        painter.end()
        return QIcon(pixmap)

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

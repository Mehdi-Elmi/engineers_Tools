"""Shared engineering workspace window.

This window is the mother pattern for project workspaces. Menu dialogs must use
project-styled windows. Native file dialogs may only be used behind those windows
for reliable filesystem operations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

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
    """Rounded project-styled menu dialog used by the Command Bar."""

    def __init__(self, title: str, items: tuple[MenuItemSpec, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectMenuDialog")
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(340)

        shell = QWidget()
        shell.setObjectName("ProjectMenuShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(8)

        header = QWidget()
        header.setObjectName("MenuDialogHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 8, 0)
        header_layout.setSpacing(8)

        heading = QLabel(title)
        heading.setObjectName("MenuDialogTitle")
        header_layout.addWidget(heading, 1)

        close = QPushButton("×")
        close.setObjectName("MenuDialogClose")
        close.setFixedSize(28, 26)
        close.clicked.connect(self.reject)
        header_layout.addWidget(close)
        layout.addWidget(header)

        if not items:
            empty = QLabel("No tools defined yet.")
            empty.setObjectName("MenuDialogEmpty")
            empty.setWordWrap(True)
            layout.addWidget(empty)
        for item in items:
            button_text = self._build_button_text(item)
            button = QPushButton(button_text)
            button.setObjectName("MenuItemButton")
            button.setMinimumHeight(34)
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
        layout.setContentsMargins(16, 0, 10, 0)
        layout.setSpacing(10)

        mark = QLabel("AT")
        mark.setObjectName("WindowMark")
        mark.setFixedSize(36, 36)
        mark.setAlignment(Qt.AlignCenter)
        layout.addWidget(mark)

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
        home.setFixedSize(50, 32)
        home.setIcon(self._build_home_icon())
        home.setIconSize(QSize(31, 27))
        home.clicked.connect(self.back_requested.emit)
        layout.addWidget(home)

        menu_map: tuple[tuple[str, Callable[[], None]], ...] = (
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
            button.clicked.connect(handler)
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
            ("Ctrl+R", self._repeat_last_tool),
            ("Ctrl+A", self._select_all),
            ("Ctrl+G", self._group),
            ("Ctrl+Shift+G", self._ungroup),
        )
        for sequence, handler in shortcuts:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(handler)

    def _show_menu(self, title: str, items: tuple[MenuItemSpec, ...]) -> None:
        dialog = ProjectMenuDialog(title, items, self)
        dialog.exec()

    def _show_file_menu(self) -> None:
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
        )

    def _show_edit_menu(self) -> None:
        self._show_menu(
            "Edit",
            (
                MenuItemSpec("Undo", self._undo, "Ctrl+Z"),
                MenuItemSpec("Redo", self._redo, "Ctrl+Y"),
                MenuItemSpec("Cut", self._cut, "Ctrl+X"),
                MenuItemSpec("Copy", self._copy, "Ctrl+C"),
                MenuItemSpec("Paste", self._paste, "Ctrl+V"),
                MenuItemSpec("Delete", self._delete, "Del"),
                MenuItemSpec("Repeat Last Tool", self._repeat_last_tool, "Ctrl+R"),
                MenuItemSpec("Select All", self._select_all, "Ctrl+A"),
                MenuItemSpec("Group", self._group, "Ctrl+G"),
                MenuItemSpec("Ungroup", self._ungroup, "Ctrl+Shift+G"),
                MenuItemSpec("Move", self._move),
            ),
        )

    def _show_view_menu(self) -> None:
        self._show_menu(
            "View",
            (
                MenuItemSpec("Start Bar", self._toggle_start_bar, checkable=True, checked=self._view_state["start_bar"]),
                MenuItemSpec("Grid", self._toggle_grid, checkable=True, checked=self._view_state["grid"]),
                MenuItemSpec("Ruler", self._toggle_ruler, checkable=True, checked=self._view_state["ruler"]),
                MenuItemSpec("Snap", self._toggle_snap, checkable=True, checked=self._view_state["snap"]),
            ),
        )

    def _show_insert_menu(self) -> None:
        self._show_menu("Insert", (MenuItemSpec("Image", self._insert_image), MenuItemSpec("Text", self._insert_text)))

    def _show_draw_menu(self) -> None:
        self._show_menu("Draw", ())

    def _show_help_menu(self) -> None:
        self._show_menu("Help", (MenuItemSpec("Shortcuts", self._show_shortcuts), MenuItemSpec("About", self._show_about)))

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

    def _repeat_last_tool(self) -> None:
        self._set_status("Repeat Last Tool")

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
        pixmap = QPixmap(42, 34)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)

        shadow = QPainterPath()
        shadow.addRoundedRect(QRectF(5.5, 6.5, 31.0, 24.0), 9.0, 9.0)
        painter.fillPath(shadow, QColor(4, 13, 26, 80))

        base = QPainterPath()
        base.addRoundedRect(QRectF(4.0, 4.0, 32.0, 24.8), 8.0, 8.0)
        base_gradient = QLinearGradient(4, 4, 36, 29)
        base_gradient.setColorAt(0.0, QColor("#ffffff"))
        base_gradient.setColorAt(0.42, QColor("#e8f2ff"))
        base_gradient.setColorAt(1.0, QColor("#5b83b8"))
        painter.fillPath(base, base_gradient)
        painter.setPen(QPen(QColor("#ffffff"), 1.2))
        painter.drawPath(base)

        roof_shadow = QPolygonF([QPointF(10.0, 17.8), QPointF(21.0, 8.6), QPointF(32.0, 17.8), QPointF(28.6, 20.7), QPointF(21.0, 14.4), QPointF(13.4, 20.7)])
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(13, 30, 54, 78))
        painter.drawPolygon(roof_shadow)

        roof = QPolygonF([QPointF(9.0, 16.0), QPointF(21.0, 6.2), QPointF(33.0, 16.0), QPointF(29.8, 18.9), QPointF(21.0, 11.6), QPointF(12.2, 18.9)])
        roof_gradient = QLinearGradient(9, 6, 33, 19)
        roof_gradient.setColorAt(0.0, QColor("#ffffff"))
        roof_gradient.setColorAt(0.48, QColor("#9fc7f7"))
        roof_gradient.setColorAt(1.0, QColor("#234a7e"))
        painter.setPen(QPen(QColor("#ffffff"), 1.25))
        painter.setBrush(roof_gradient)
        painter.drawPolygon(roof)

        body_gradient = QLinearGradient(13, 15, 29, 28)
        body_gradient.setColorAt(0.0, QColor("#ffffff"))
        body_gradient.setColorAt(0.48, QColor("#98c1f2"))
        body_gradient.setColorAt(1.0, QColor("#1f416f"))
        painter.setBrush(body_gradient)
        painter.drawRoundedRect(QRectF(13.0, 15.6, 16.0, 10.8), 2.8, 2.8)

        painter.setPen(QPen(QColor("#ffffff"), 1.2))
        painter.drawRoundedRect(QRectF(19.0, 19.0, 4.0, 7.1), 1.1, 1.1)
        painter.drawLine(QPointF(15.5, 18.3), QPointF(26.5, 18.3))
        painter.setPen(QPen(QColor(255, 255, 255, 155), 1.0))
        painter.drawLine(QPointF(12.2, 8.6), QPointF(28.4, 8.6))
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

"""Shared engineering workspace window.

This window is the mother pattern for project workspaces. Menu dialogs must use
project-styled windows. Native file dialogs may only be used behind those windows
for reliable filesystem operations.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
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


class GridCanvas(QWidget):
    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#f9fbff"))
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
        note.setObjectName("StatusItem")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        open_button = QPushButton("Open File")
        open_button.setObjectName("ToolButton")
        open_button.clicked.connect(self._open_file_backend)
        buttons.addWidget(open_button)

        close_button = QPushButton("Close")
        close_button.setObjectName("ToolButton")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    def _open_file_backend(self) -> None:
        # Backend operation: keep the visual shell project-styled, but rely on
        # QFileDialog for real filesystem selection and Windows integration.
        QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.*)")


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
        self._maximize_button: QPushButton | None = None

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
        minimize.clicked.connect(self.showMinimized)
        layout.addWidget(minimize)

        maximize = QPushButton("[]")
        maximize.setObjectName("WindowButton")
        maximize.setFixedSize(34, 30)
        maximize.clicked.connect(self._toggle_maximize)
        self._maximize_button = maximize
        layout.addWidget(maximize)

        close = QPushButton("x")
        close.setObjectName("CloseButton")
        close.setFixedSize(34, 30)
        close.clicked.connect(self.close)
        layout.addWidget(close)
        return bar

    def _build_command_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("CommandBar")
        bar.setFixedHeight(38)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 4, 14, 4)
        layout.setSpacing(8)

        home = QPushButton("Home")
        home.setObjectName("HomeButton")
        home.clicked.connect(self.back_requested.emit)
        layout.addWidget(home)

        menu_map = {
            "File": self._show_file_dialog,
            "Edit": None,
            "View": None,
            "Insert": None,
            "Draw": None,
            "Modify": None,
        }
        for label, handler in menu_map.items():
            button = QPushButton(label)
            button.setObjectName("MenuButton")
            if handler is not None:
                button.clicked.connect(handler)
            layout.addWidget(button)

        layout.addStretch(1)
        return bar

    def _build_start_bar(self) -> QWidget:
        return StartBar(self.get_start_bar_tools())

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

        canvas = GridCanvas()
        canvas.setObjectName("GridCanvas")
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas_layout.addWidget(canvas, 1)
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
        add_page.setObjectName("ToolButton")
        layout.addWidget(add_page)
        return bar

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(30)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(18)
        for text in ("Tool Select: Ready", "X: 0  Y: 0", "Zoom: 100%", "Unit: mm"):
            item = QLabel(text)
            item.setObjectName("StatusItem")
            layout.addWidget(item)
        layout.addStretch(1)
        return bar

    def _show_file_dialog(self) -> None:
        dialog = ProjectDialog("File", self)
        dialog.exec()

    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
            if self._normal_geometry is not None:
                self.setGeometry(self._normal_geometry)
            if self._maximize_button is not None:
                self._maximize_button.setText("[]")
            return

        self._normal_geometry = self.geometry()
        self.showMaximized()
        if self._maximize_button is not None:
            self._maximize_button.setText("[ ]")

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and event.position().y() <= 46:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_position is not None and event.buttons() & Qt.LeftButton and not self.isMaximized():
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_position = None
        event.accept()

"""Shared engineering workspace window.

This window is the mother pattern for project workspaces. Menu dialogs must use
project-styled windows. Native file dialogs may only be used behind those windows
for reliable filesystem operations.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
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
        bar.setFixedHeight(38)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 4, 14, 4)
        layout.setSpacing(10)

        home = QPushButton()
        home.setObjectName("HomeButton")
        home.setToolTip("Back to launcher")
        home.setFixedSize(40, 30)
        home.setIcon(self._build_home_icon())
        home.setIconSize(QSize(23, 23))
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
            button.setFixedHeight(28)
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
        add_page.setObjectName("ConfirmButton")
        layout.addWidget(add_page)
        return bar

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(32)
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
        pixmap = QPixmap(30, 30)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)

        shadow = QPainterPath()
        shadow.addRoundedRect(QRectF(7, 14, 16, 11), 3, 3)
        painter.fillPath(shadow, QColor(12, 24, 40, 72))

        roof = QPolygonF(
            [
                QPointF(5.5, 14.0),
                QPointF(15.0, 5.8),
                QPointF(24.5, 14.0),
                QPointF(22.0, 16.2),
                QPointF(15.0, 10.2),
                QPointF(8.0, 16.2),
            ]
        )
        roof_gradient = QLinearGradient(6, 5, 24, 16)
        roof_gradient.setColorAt(0.0, QColor("#ffffff"))
        roof_gradient.setColorAt(0.45, QColor("#9fc4f3"))
        roof_gradient.setColorAt(1.0, QColor("#315e9a"))
        painter.setPen(QPen(QColor("#ffffff"), 1.1))
        painter.setBrush(roof_gradient)
        painter.drawPolygon(roof)

        body_gradient = QLinearGradient(8, 13, 22, 25)
        body_gradient.setColorAt(0.0, QColor("#ffffff"))
        body_gradient.setColorAt(0.52, QColor("#8fb8f0"))
        body_gradient.setColorAt(1.0, QColor("#274a78"))
        painter.setBrush(body_gradient)
        painter.drawRoundedRect(QRectF(8.2, 13.4, 13.6, 10.8), 2.4, 2.4)

        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        painter.drawRoundedRect(QRectF(13.2, 17.0, 3.6, 7.0), 1.0, 1.0)
        painter.drawLine(QPointF(10.8, 15.9), QPointF(19.2, 15.9))
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

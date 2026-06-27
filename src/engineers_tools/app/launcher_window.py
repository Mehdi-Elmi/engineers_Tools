"""Main launcher window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from .modules import MODULES, LauncherModule
from ..ui.launcher_button import LauncherButton


class LauncherWindow(QMainWindow):
    module_selected = Signal(LauncherModule)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Engineer Tools")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(960, 620)
        self._drag_position: QPoint | None = None
        self._cards: list[LauncherButton] = []

        root = QWidget()
        root.setObjectName("WindowRoot")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 26)
        layout.setSpacing(24)
        layout.addWidget(self._build_top_bar())
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_grid(), 1)

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(46)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 10, 0)
        layout.setSpacing(10)

        layout.addWidget(self._build_window_mark())

        title = QLabel("Engineer Tools")
        title.setObjectName("WindowTitle")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title, 1)

        minimize = QPushButton("-")
        minimize.setObjectName("WindowButton")
        minimize.setFixedSize(34, 30)
        minimize.clicked.connect(self.showMinimized)
        layout.addWidget(minimize)

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
        mark.setPixmap(pixmap.scaled(38, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return mark

    def _find_logo_path(self) -> Path | None:
        logo_dir = Path(__file__).resolve().parents[3] / "logo"
        if not logo_dir.exists():
            return None
        allowed_suffixes = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
        candidates = sorted(path for path in logo_dir.iterdir() if path.is_file() and path.suffix.lower() in allowed_suffixes)
        return candidates[0] if candidates else None

    def _build_header(self) -> QWidget:
        outer = QWidget()
        outer.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(outer)
        layout.setContentsMargins(44, 6, 44, 0)

        header = QWidget()
        header.setObjectName("LauncherHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(22, 13, 22, 13)
        header_layout.setSpacing(4)

        title = QLabel("Engineer Tools Launcher")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Select the design workspace")
        subtitle.setObjectName("HeaderSubtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)
        return outer

    def _build_grid(self) -> QWidget:
        area = QWidget()
        area.setStyleSheet("background: transparent;")
        grid = QGridLayout(area)
        grid.setContentsMargins(44, 4, 44, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        for index, module in enumerate(MODULES):
            card = LauncherButton(module)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            card.clicked.connect(lambda checked=False, item=module: self.module_selected.emit(item))
            self._cards.append(card)
            grid.addWidget(card, index // 3, index % 3)

        for column in range(3):
            grid.setColumnStretch(column, 1)
        return area

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and event.position().y() <= 46:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_position is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_position = None
        event.accept()

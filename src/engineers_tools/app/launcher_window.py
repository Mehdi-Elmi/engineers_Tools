"""Main launcher window."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Signal, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from .modules import MODULES, LauncherModule


class LauncherWindow(QMainWindow):
    module_selected = Signal(LauncherModule)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Engineer Tools")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(960, 620)
        self._drag_position: QPoint | None = None

        root = QWidget()
        root.setObjectName("WindowRoot")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 28)
        layout.setSpacing(24)
        layout.addWidget(self._build_top_bar())
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_cards(), 1)

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

        title = QLabel("Engineer Tools")
        title.setObjectName("WindowTitle")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title, 1)

        minimize = QPushButton("-")
        minimize.setObjectName("WindowButton")
        minimize.setFixedSize(34, 30)
        minimize.clicked.connect(self.showMinimized)
        layout.addWidget(minimize)

        close = QPushButton("x")
        close.setObjectName("CloseButton")
        close.setFixedSize(34, 30)
        close.clicked.connect(self.close)
        layout.addWidget(close)
        return bar

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
        subtitle = QLabel("Select the active engineering workspace")
        subtitle.setObjectName("HeaderSubtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)
        return outer

    def _build_cards(self) -> QWidget:
        area = QWidget()
        area.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(area)
        layout.setContentsMargins(44, 6, 44, 0)
        layout.setSpacing(18)

        for module in MODULES:
            card = QPushButton(f"{module.label}\n\n{module.description}")
            card.setObjectName("LauncherCard")
            card.setMinimumSize(300, 210)
            card.clicked.connect(lambda checked=False, item=module: self.module_selected.emit(item))
            layout.addWidget(card)

        layout.addStretch(1)
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

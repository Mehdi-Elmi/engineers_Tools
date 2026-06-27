"""Project-styled file dialogs for Engineer Tools.

The UI follows the project window language while using the local filesystem
through Python and Qt models. It intentionally avoids native QFileDialog visuals.
"""

from __future__ import annotations

import os
import string
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QFileInfo, QPoint, QRectF, QSize, QStandardPaths, Qt
from PySide6.QtGui import QPainterPath, QRegion
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileIconProvider,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


PROJECT_FILE_FILTERS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("Engineer Tools Files", (".etools", ".etool"), ".etools"),
    ("PDF Files", (".pdf",), ".pdf"),
    ("Image Files", (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".svg"), ".png"),
    ("SVG Files", (".svg",), ".svg"),
    ("All Supported Files", (".etools", ".etool", ".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp", ".svg"), ".etools"),
    ("All Files", (".*",), ".etools"),
)


@dataclass(frozen=True)
class FileDialogResult:
    path: Path
    filter_name: str


class ProjectFileDialog(QDialog):
    """Rounded file picker with project styling and Windows-like behavior."""

    def __init__(self, mode: str, parent: QWidget | None = None, start_dir: Path | None = None) -> None:
        super().__init__(parent)
        self.mode = mode
        self.selected_result: FileDialogResult | None = None
        self._history: list[Path] = []
        self._history_index = -1
        self._icon_provider = QFileIconProvider()
        self._current_dir = self._resolve_start_dir(start_dir)

        title = "Open" if mode == "open" else "Save As"
        self.setObjectName("ProjectFileDialog")
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumSize(760, 500)
        self.resize(820, 540)

        shell = QWidget()
        shell.setObjectName("ProjectFileShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header(title))
        layout.addWidget(self._build_navigation_bar())
        layout.addWidget(self._build_body(), 1)
        layout.addWidget(self._build_footer())

        self._navigate_to(self._current_dir, add_history=True)

    @classmethod
    def get_open_file(cls, parent: QWidget | None = None, start_dir: Path | None = None) -> FileDialogResult | None:
        dialog = cls("open", parent, start_dir)
        return dialog.selected_result if dialog.exec() == QDialog.Accepted else None

    @classmethod
    def get_save_file(cls, parent: QWidget | None = None, start_dir: Path | None = None) -> FileDialogResult | None:
        dialog = cls("save", parent, start_dir)
        return dialog.selected_result if dialog.exec() == QDialog.Accepted else None

    def _build_header(self, title: str) -> QWidget:
        header = QWidget()
        header.setObjectName("FileDialogHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(10)

        mark = QLabel("AT")
        mark.setObjectName("WindowMark")
        mark.setFixedSize(34, 30)
        mark.setAlignment(Qt.AlignCenter)
        layout.addWidget(mark)

        label = QLabel(title)
        label.setObjectName("FileDialogTitle")
        layout.addWidget(label, 1)

        close = QPushButton("×")
        close.setObjectName("CloseButton")
        close.setFixedSize(34, 28)
        close.clicked.connect(self.reject)
        layout.addWidget(close)
        return header

    def _build_navigation_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("FileDialogNavBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        self._back_button = QPushButton("Back")
        self._back_button.setObjectName("FileNavButton")
        self._back_button.clicked.connect(self._go_back)
        layout.addWidget(self._back_button)

        self._up_button = QPushButton("Up")
        self._up_button.setObjectName("FileNavButton")
        self._up_button.clicked.connect(self._go_up)
        layout.addWidget(self._up_button)

        self._path_label = QLabel("")
        self._path_label.setObjectName("FilePathLabel")
        layout.addWidget(self._path_label, 1)
        return bar

    def _build_body(self) -> QWidget:
        body = QWidget()
        body.setObjectName("FileDialogBody")
        layout = QHBoxLayout(body)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(10)

        self._places = QListWidget()
        self._places.setObjectName("PlacesList")
        self._places.setFixedWidth(170)
        self._populate_places()
        self._places.itemClicked.connect(self._place_clicked)
        layout.addWidget(self._places)

        self._files = QListWidget()
        self._files.setObjectName("FilesList")
        self._files.setIconSize(QSize(22, 22))
        self._files.itemDoubleClicked.connect(self._file_double_clicked)
        self._files.itemClicked.connect(self._file_clicked)
        layout.addWidget(self._files, 1)
        return body

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        footer.setObjectName("FileDialogFooter")
        layout = QGridLayout(footer)
        layout.setContentsMargins(12, 6, 12, 12)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        file_name_label = QLabel("File Name:")
        file_name_label.setObjectName("FileFieldLabel")
        layout.addWidget(file_name_label, 0, 0)

        self._file_name = QLineEdit()
        self._file_name.setObjectName("FileNameInput")
        layout.addWidget(self._file_name, 0, 1)

        type_label = QLabel("File Type:")
        type_label.setObjectName("FileFieldLabel")
        layout.addWidget(type_label, 1, 0)

        self._file_type = QComboBox()
        self._file_type.setObjectName("FileTypeCombo")
        for name, suffixes, _default_suffix in PROJECT_FILE_FILTERS:
            suffix_text = " ".join(f"*{suffix}" for suffix in suffixes)
            self._file_type.addItem(f"{name} ({suffix_text})", (name, suffixes, _default_suffix))
        self._file_type.currentIndexChanged.connect(lambda _index: self._refresh_files())
        layout.addWidget(self._file_type, 1, 1)

        action_label = "Open" if self.mode == "open" else "Save"
        action = QPushButton(action_label)
        action.setObjectName("ConfirmButton")
        action.clicked.connect(self._accept_selection)
        layout.addWidget(action, 0, 2)

        cancel = QPushButton("Cancel")
        cancel.setObjectName("ConfirmButton")
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel, 1, 2)
        return footer

    def _populate_places(self) -> None:
        for label, path in self._places_paths():
            item = QListWidgetItem(self._icon_provider.icon(QFileInfo(str(path))), label)
            item.setData(Qt.UserRole, str(path))
            self._places.addItem(item)

    def _places_paths(self) -> list[tuple[str, Path]]:
        paths: list[tuple[str, Path]] = []
        home = Path.home()
        standard_locations = (
            ("Desktop", QStandardPaths.DesktopLocation, home / "Desktop"),
            ("Downloads", QStandardPaths.DownloadLocation, home / "Downloads"),
            ("Documents", QStandardPaths.DocumentsLocation, home / "Documents"),
            ("Pictures", QStandardPaths.PicturesLocation, home / "Pictures"),
        )
        paths.append(("Home", home))
        for label, standard_location, fallback in standard_locations:
            location = QStandardPaths.writableLocation(standard_location)
            path = Path(location) if location else fallback
            if path.exists():
                paths.append((label, path))
        one_drive = os.environ.get("OneDrive") or os.environ.get("OneDriveCommercial")
        if one_drive and Path(one_drive).exists():
            paths.append(("OneDrive", Path(one_drive)))
        paths.extend(self._drive_paths())
        return paths

    def _drive_paths(self) -> list[tuple[str, Path]]:
        if os.name != "nt":
            return [("Root", Path("/"))]
        drives: list[tuple[str, Path]] = []
        for letter in string.ascii_uppercase:
            path = Path(f"{letter}:\\")
            if path.exists():
                drives.append((f"Drive {letter}:", path))
        return drives

    def _resolve_start_dir(self, start_dir: Path | None) -> Path:
        if start_dir is not None and start_dir.exists():
            return start_dir if start_dir.is_dir() else start_dir.parent
        documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        if documents:
            return Path(documents)
        return Path.home()

    def _navigate_to(self, path: Path, add_history: bool = False) -> None:
        if not path.exists() or not path.is_dir():
            return
        self._current_dir = path
        if add_history:
            self._history = self._history[: self._history_index + 1]
            self._history.append(path)
            self._history_index = len(self._history) - 1
        self._path_label.setText(str(path))
        self._refresh_files()
        self._update_nav_state()

    def _refresh_files(self) -> None:
        self._files.clear()
        suffixes = self._selected_suffixes()
        try:
            children = sorted(self._current_dir.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        except PermissionError:
            return
        for child in children:
            if child.is_file() and not self._matches_filter(child, suffixes):
                continue
            item = QListWidgetItem(self._icon_provider.icon(QFileInfo(str(child))), child.name)
            item.setData(Qt.UserRole, str(child))
            self._files.addItem(item)

    def _selected_suffixes(self) -> tuple[str, ...]:
        data = self._file_type.currentData()
        return data[1] if data else (".*",)

    def _selected_default_suffix(self) -> str:
        data = self._file_type.currentData()
        return data[2] if data else ".etools"

    def _selected_filter_name(self) -> str:
        data = self._file_type.currentData()
        return data[0] if data else "All Files"

    def _matches_filter(self, path: Path, suffixes: tuple[str, ...]) -> bool:
        return ".*" in suffixes or path.suffix.lower() in suffixes

    def _place_clicked(self, item: QListWidgetItem) -> None:
        self._navigate_to(Path(item.data(Qt.UserRole)), add_history=True)

    def _file_clicked(self, item: QListWidgetItem) -> None:
        path = Path(item.data(Qt.UserRole))
        if path.is_file():
            self._file_name.setText(path.name)

    def _file_double_clicked(self, item: QListWidgetItem) -> None:
        path = Path(item.data(Qt.UserRole))
        if path.is_dir():
            self._navigate_to(path, add_history=True)
            return
        self._file_name.setText(path.name)
        if self.mode == "open":
            self._accept_selection()

    def _go_back(self) -> None:
        if self._history_index <= 0:
            return
        self._history_index -= 1
        self._navigate_to(self._history[self._history_index], add_history=False)

    def _go_up(self) -> None:
        parent = self._current_dir.parent
        if parent != self._current_dir:
            self._navigate_to(parent, add_history=True)

    def _update_nav_state(self) -> None:
        self._back_button.setEnabled(self._history_index > 0)
        self._up_button.setEnabled(self._current_dir.parent != self._current_dir)

    def _accept_selection(self) -> None:
        raw_name = self._file_name.text().strip()
        if not raw_name:
            return
        path = Path(raw_name)
        if not path.is_absolute():
            path = self._current_dir / raw_name
        if self.mode == "save" and not path.suffix:
            path = path.with_suffix(self._selected_default_suffix())
        if self.mode == "open" and (not path.exists() or path.is_dir()):
            return
        self.selected_result = FileDialogResult(path=path, filter_name=self._selected_filter_name())
        self.accept()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 16, 16)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

"""Project-styled file dialogs for Engineer Tools."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QFileInfo, QPoint, QPointF, QRectF, QSize, QStandardPaths, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QRegion
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
    ("Engineer Tools", (".etools", ".etool"), ".etools"),
    ("PDF", (".pdf",), ".pdf"),
    ("PNG", (".png",), ".png"),
    ("JPEG", (".jpg", ".jpeg"), ".jpg"),
    ("BMP", (".bmp",), ".bmp"),
    ("WebP", (".webp",), ".webp"),
    ("SVG", (".svg",), ".svg"),
    ("All Files", (".*",), ".etools"),
)

OFFICE_FILE_FILTERS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("Engineer Tools", (".etools", ".etool"), ".etools"),
    ("Word", (".doc", ".docx", ".dot", ".dotx", ".rtf"), ".docx"),
    ("PowerPoint", (".ppt", ".pptx", ".pot", ".potx", ".pps", ".ppsx"), ".pptx"),
    ("Excel", (".xls", ".xlsx", ".xlsm", ".xlt", ".xltx", ".csv"), ".xlsx"),
    ("PDF", (".pdf",), ".pdf"),
    ("All Files", (".*",), ".etools"),
)


@dataclass(frozen=True)
class FileDialogResult:
    path: Path
    filter_name: str


class ProjectFileDialog(QDialog):
    """Rounded file picker with project styling and Windows-like behavior."""

    def __init__(self, mode: str, parent: QWidget | None = None, start_dir: Path | None = None, filter_kind: str = "project") -> None:
        super().__init__(parent)
        self.mode = mode
        self.filter_kind = filter_kind
        self.selected_result: FileDialogResult | None = None
        self._history: list[Path] = []
        self._history_index = -1
        self._icon_provider = QFileIconProvider()
        self._current_dir = self._resolve_start_dir(start_dir)
        self._drag_position: QPoint | None = None

        title = self._dialog_title()
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
        if self.mode in {"save", "export"}:
            self._set_default_file_name(force=True)

    @classmethod
    def get_open_file(cls, parent: QWidget | None = None, start_dir: Path | None = None) -> FileDialogResult | None:
        dialog = cls("open", parent, start_dir, "project")
        return dialog.selected_result if dialog.exec() == QDialog.Accepted else None

    @classmethod
    def get_save_file(cls, parent: QWidget | None = None, start_dir: Path | None = None) -> FileDialogResult | None:
        dialog = cls("save", parent, start_dir, "project")
        return dialog.selected_result if dialog.exec() == QDialog.Accepted else None

    @classmethod
    def get_import_file(cls, parent: QWidget | None = None, start_dir: Path | None = None) -> FileDialogResult | None:
        dialog = cls("import", parent, start_dir, "office")
        return dialog.selected_result if dialog.exec() == QDialog.Accepted else None

    @classmethod
    def get_export_file(cls, parent: QWidget | None = None, start_dir: Path | None = None) -> FileDialogResult | None:
        dialog = cls("export", parent, start_dir, "office")
        return dialog.selected_result if dialog.exec() == QDialog.Accepted else None

    def _dialog_title(self) -> str:
        return {"open": "Open", "save": "Save As", "import": "Import", "export": "Export"}.get(self.mode, "Open")

    def _build_header(self, title: str) -> QWidget:
        header = QWidget()
        header.setObjectName("FileDialogHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(10)
        layout.addWidget(self._build_window_mark())
        label = QLabel(title)
        label.setObjectName("FileDialogTitle")
        layout.addWidget(label, 1)
        close = QPushButton("×")
        close.setObjectName("CloseButton")
        close.setFixedSize(34, 28)
        close.clicked.connect(self.reject)
        layout.addWidget(close)
        return header

    def _build_window_mark(self) -> QLabel:
        mark = QLabel("AT")
        mark.setObjectName("WindowMark")
        mark.setFixedSize(36, 30)
        mark.setAlignment(Qt.AlignCenter)
        logo_path = self._find_logo_path()
        if logo_path is None:
            return mark
        pixmap = QPixmap(str(logo_path))
        if pixmap.isNull():
            return mark
        mark.setText("")
        mark.setObjectName("WindowLogoMark")
        mark.setPixmap(pixmap.scaled(32, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return mark

    def _find_logo_path(self) -> Path | None:
        logo_dir = Path(__file__).resolve().parents[3] / "logo"
        if not logo_dir.exists():
            return None
        suffixes = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
        candidates = sorted(path for path in logo_dir.iterdir() if path.is_file() and path.suffix.lower() in suffixes)
        return candidates[0] if candidates else None

    def _build_navigation_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("FileDialogNavBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)
        self._back_button = self._build_nav_button("back", "Back")
        self._back_button.clicked.connect(self._go_back)
        layout.addWidget(self._back_button)
        self._forward_button = self._build_nav_button("forward", "Forward")
        self._forward_button.clicked.connect(self._go_forward)
        layout.addWidget(self._forward_button)
        self._up_button = self._build_nav_button("up", "Up")
        self._up_button.clicked.connect(self._go_up)
        layout.addWidget(self._up_button)
        self._path_label = QLabel("")
        self._path_label.setObjectName("FilePathLabel")
        layout.addWidget(self._path_label, 1)
        return bar

    def _build_nav_button(self, direction: str, tooltip: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName("FileNavButton")
        button.setToolTip(tooltip)
        button.setFixedSize(38, 30)
        button.setIcon(self._build_nav_icon(direction))
        button.setIconSize(QSize(28, 24))
        return button

    def _build_nav_icon(self, direction: str) -> QIcon:
        pixmap = QPixmap(30, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        base = QPainterPath()
        base.addRoundedRect(QRectF(3, 3, 24, 18), 7, 7)
        gradient = QLinearGradient(3, 3, 27, 21)
        gradient.setColorAt(0.0, QColor("#ffffff"))
        gradient.setColorAt(0.48, QColor("#fff1bf"))
        gradient.setColorAt(1.0, QColor("#ff8a35"))
        painter.fillPath(base, gradient)
        painter.setPen(QPen(QColor("#ffffff"), 0.9))
        painter.drawPath(base)
        painter.setPen(QPen(QColor("#132238"), 1.0))
        painter.setBrush(QColor("#132238"))
        if direction == "back":
            points = QPolygonF([QPointF(8, 12), QPointF(17, 6), QPointF(17, 10), QPointF(23, 10), QPointF(23, 14), QPointF(17, 14), QPointF(17, 18)])
        elif direction == "forward":
            points = QPolygonF([QPointF(22, 12), QPointF(13, 6), QPointF(13, 10), QPointF(7, 10), QPointF(7, 14), QPointF(13, 14), QPointF(13, 18)])
        else:
            points = QPolygonF([QPointF(15, 6), QPointF(23, 14), QPointF(19, 14), QPointF(19, 19), QPointF(11, 19), QPointF(11, 14), QPointF(7, 14)])
        painter.drawPolygon(points)
        painter.end()
        return QIcon(pixmap)

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
        for name, suffixes, default_suffix in self._filters():
            suffix_text = " ".join(f"*{suffix}" for suffix in suffixes)
            self._file_type.addItem(f"{name} ({suffix_text})", (name, suffixes, default_suffix))
        self._file_type.currentIndexChanged.connect(self._file_type_changed)
        layout.addWidget(self._file_type, 1, 1)
        action_label = {"open": "Open", "save": "Save", "import": "Import", "export": "Export"}.get(self.mode, "Open")
        action = QPushButton(action_label)
        action.setObjectName("PrimaryDialogButton")
        action.clicked.connect(self._accept_selection)
        layout.addWidget(action, 0, 2)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryDialogButton")
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel, 1, 2)
        return footer

    def _filters(self) -> tuple[tuple[str, tuple[str, ...], str], ...]:
        return OFFICE_FILE_FILTERS if self.filter_kind == "office" else PROJECT_FILE_FILTERS

    def _populate_places(self) -> None:
        for label, path in self._places_paths():
            item = QListWidgetItem(self._icon_provider.icon(QFileInfo(str(path))), label)
            item.setData(Qt.UserRole, str(path))
            self._places.addItem(item)
        computer_icon = self._icon_provider.icon(QFileIconProvider.IconType.Computer)
        this_pc = QListWidgetItem(computer_icon, "This PC")
        this_pc.setData(Qt.UserRole, "__THIS_PC__")
        self._places.addItem(this_pc)

    def _places_paths(self) -> list[tuple[str, Path]]:
        paths: list[tuple[str, Path]] = []
        home = Path.home()
        paths.append(("Home", home))
        for label, standard_location, fallback in (
            ("Desktop", QStandardPaths.DesktopLocation, home / "Desktop"),
            ("Downloads", QStandardPaths.DownloadLocation, home / "Downloads"),
            ("Documents", QStandardPaths.DocumentsLocation, home / "Documents"),
            ("Pictures", QStandardPaths.PicturesLocation, home / "Pictures"),
        ):
            location = QStandardPaths.writableLocation(standard_location)
            path = Path(location) if location else fallback
            if path.exists():
                paths.append((label, path))
        one_drive = os.environ.get("OneDrive") or os.environ.get("OneDriveCommercial")
        if one_drive and Path(one_drive).exists():
            paths.append(("OneDrive", Path(one_drive)))
        return paths

    def _drive_paths(self) -> list[tuple[str, Path]]:
        if os.name != "nt":
            return [("Root", Path("/"))]
        drives: list[tuple[str, Path]] = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            path = Path(f"{letter}:\\")
            if path.exists():
                drives.append((f"Local Disk ({letter}:)", path))
        return drives

    def _resolve_start_dir(self, start_dir: Path | None) -> Path:
        if start_dir is not None and start_dir.exists():
            return start_dir if start_dir.is_dir() else start_dir.parent
        documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        return Path(documents) if documents else Path.home()

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
        if self.mode in {"save", "export"} and not self._file_name.text().strip():
            self._set_default_file_name(force=True)

    def _show_this_pc(self) -> None:
        self._path_label.setText("This PC")
        self._files.clear()
        for label, path in self._drive_paths():
            item = QListWidgetItem(self._icon_provider.icon(QFileInfo(str(path))), label)
            item.setData(Qt.UserRole, str(path))
            self._files.addItem(item)
        self._back_button.setEnabled(self._history_index > 0)
        self._forward_button.setEnabled(self._history_index < len(self._history) - 1)
        self._up_button.setEnabled(False)

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

    def _file_type_changed(self, _index: int) -> None:
        if self.mode in {"save", "export"} and (not self._file_name.text().strip() or self._file_name.text().startswith("EngineerTools")):
            self._set_default_file_name(force=True)
        self._refresh_files()

    def _set_default_file_name(self, force: bool = False) -> None:
        if not force and self._file_name.text().strip():
            return
        candidate = self._make_unique_path(self._current_dir / f"EngineerTools{self._selected_default_suffix()}")
        self._file_name.setText(candidate.name)

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
        data = str(item.data(Qt.UserRole))
        if data == "__THIS_PC__":
            self._show_this_pc()
            return
        self._navigate_to(Path(data), add_history=True)

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
        if self.mode in {"open", "import"}:
            self._accept_selection()

    def _go_back(self) -> None:
        if self._history_index <= 0:
            return
        self._history_index -= 1
        self._navigate_to(self._history[self._history_index], add_history=False)

    def _go_forward(self) -> None:
        if self._history_index >= len(self._history) - 1:
            return
        self._history_index += 1
        self._navigate_to(self._history[self._history_index], add_history=False)

    def _go_up(self) -> None:
        parent = self._current_dir.parent
        if parent != self._current_dir:
            self._navigate_to(parent, add_history=True)

    def _update_nav_state(self) -> None:
        self._back_button.setEnabled(self._history_index > 0)
        self._forward_button.setEnabled(self._history_index < len(self._history) - 1)
        self._up_button.setEnabled(self._current_dir.parent != self._current_dir)

    def _accept_selection(self) -> None:
        raw_name = self._file_name.text().strip()
        if not raw_name and self.mode in {"save", "export"}:
            self._set_default_file_name(force=True)
            raw_name = self._file_name.text().strip()
        if not raw_name:
            return
        path = Path(raw_name)
        if not path.is_absolute():
            path = self._current_dir / raw_name
        if self.mode in {"save", "export"}:
            if not path.suffix:
                path = path.with_suffix(self._selected_default_suffix())
            path = self._make_unique_path(path)
        if self.mode in {"open", "import"} and (not path.exists() or path.is_dir()):
            return
        self.selected_result = FileDialogResult(path=path, filter_name=self._selected_filter_name())
        self.accept()

    def _make_unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        counter = 1
        while True:
            candidate = path.with_name(f"{stem}_{counter}{suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 16, 16)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and event.position().y() <= 44:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_position is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_position = None
        super().mouseReleaseEvent(event)

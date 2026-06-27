"""Project-styled file dialogs for Engineer Tools."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QFileInfo, QPoint, QPointF, QRectF, QSize, QStandardPaths, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QRegion, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileIconProvider,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMenu,
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
    ("Word", (".docx", ".rtf"), ".docx"),
    ("PowerPoint", (".pptx",), ".pptx"),
    ("Excel", (".xlsx", ".csv"), ".xlsx"),
    ("PDF", (".pdf",), ".pdf"),
    ("All Files", (".*",), ".etools"),
)


def _option_icon(checked: bool) -> QIcon:
    pixmap = QPixmap(26, 26)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(QPen(QColor("#18314f"), 2.0))
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(4, 4, 18, 18)
    if checked:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2f7df6"))
        painter.drawEllipse(9, 9, 8, 8)
    painter.end()
    return QIcon(pixmap)


@dataclass(frozen=True)
class FileDialogResult:
    path: Path
    filter_name: str
    options: dict[str, bool] | None = None


class ProjectFileDialog(QDialog):
    """Rounded file picker with project styling and Windows-like behavior."""

    _pending_file_action: tuple[str, Path] | None = None

    def __init__(self, mode: str, parent: QWidget | None = None, start_dir: Path | None = None, filter_kind: str = "project") -> None:
        super().__init__(parent)
        self.mode = mode
        self.filter_kind = filter_kind
        self.selected_result: FileDialogResult | None = None
        self.save_options = {"save_grid": False, "remove_white_background": False}
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

        self._delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self._delete_shortcut.setContext(Qt.WindowShortcut)
        self._delete_shortcut.activated.connect(self._delete_current_file)

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
        self._places.setFocusPolicy(Qt.NoFocus)
        self._places.setSelectionMode(QAbstractItemView.SingleSelection)
        self._places.setStyleSheet("QListWidget#PlacesList { outline:0; } QListWidget#PlacesList::item:selected { background:transparent; color:#1f3148; border:0; } QListWidget#PlacesList::item:focus { outline:0; border:0; }")
        self._populate_places()
        self._places.itemClicked.connect(self._place_clicked)
        layout.addWidget(self._places)
        self._files = QListWidget()
        self._files.setObjectName("FilesList")
        self._files.setViewMode(QListView.ListMode)
        self._files.setSelectionMode(QAbstractItemView.SingleSelection)
        self._files.setResizeMode(QListView.Adjust)
        self._files.setMovement(QListView.Static)
        self._files.setWrapping(False)
        self._files.setSpacing(2)
        self._files.setIconSize(QSize(24, 24))
        self._files.setFocusPolicy(Qt.NoFocus)
        self._files.setStyleSheet("QListWidget#FilesList { outline:0; } QListWidget#FilesList::item:selected { background:transparent; color:#1f3148; border:0; } QListWidget#FilesList::item:focus { outline:0; border:0; }")
        self._files.setContextMenuPolicy(Qt.CustomContextMenu)
        self._files.customContextMenuRequested.connect(self._show_files_context_menu)
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
        if self.mode in {"save", "export"}:
            layout.addWidget(self._build_save_options_row(), 2, 1)
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

    def _build_save_options_row(self) -> QWidget:
        row = QWidget()
        row.setObjectName("SaveOptionsRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self._build_option_button("Save Grid", "save_grid"))
        layout.addWidget(self._build_option_button("Remove White Background", "remove_white_background"))
        layout.addStretch(1)
        return row

    def _build_option_button(self, label: str, option_key: str) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("SaveOptionButton")
        button.setCheckable(True)
        button.setChecked(self.save_options.get(option_key, False))
        button.setIcon(_option_icon(button.isChecked()))
        button.setIconSize(QSize(24, 24))
        button.clicked.connect(lambda checked, key=option_key, source=button: self._set_save_option(key, checked, source))
        return button

    def _set_save_option(self, option_key: str, checked: bool, button: QPushButton) -> None:
        self.save_options[option_key] = checked
        button.setIcon(_option_icon(checked))

    def _filters(self) -> tuple[tuple[str, tuple[str, ...], str], ...]:
        return OFFICE_FILE_FILTERS if self.filter_kind == "office" else PROJECT_FILE_FILTERS

    def _populate_places(self) -> None:
        for label, path in self._places_paths():
            self._add_place_item(label, str(path), self._icon_provider.icon(QFileInfo(str(path))))
        self._add_place_item("This PC", "__THIS_PC__", self._icon_provider.icon(QFileIconProvider.IconType.Computer))

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

    def _add_place_item(self, label: str, data: str, icon: QIcon) -> None:
        item = QListWidgetItem("")
        item.setData(Qt.UserRole, data)
        item.setSizeHint(QSize(self._place_item_width(label), 30))
        self._places.addItem(item)
        row = self._build_compact_item_widget(label, icon, "PlaceItemRow", self._place_item_width(label))
        self._places.setItemWidget(item, row)

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
            self._add_file_item(label, path)
        self._sync_file_selection(None)
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
            self._add_file_item(child.name, child)
        self._sync_file_selection(None)

    def _add_file_item(self, label: str, path: Path) -> None:
        item = QListWidgetItem("")
        item.setData(Qt.UserRole, str(path))
        item.setSizeHint(self._file_item_size(label))
        self._files.addItem(item)
        row = self._build_compact_item_widget(label, self._icon_provider.icon(QFileInfo(str(path))), "FileItemRow", self._file_item_size(label).width())
        self._files.setItemWidget(item, row)

    def _build_compact_item_widget(self, label: str, icon: QIcon, object_name: str, width: int) -> QWidget:
        row = QWidget()
        row.setObjectName(object_name)
        row.setProperty("selected", False)
        row.setFixedSize(width, 28)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(4, 2, 5, 2)
        layout.setSpacing(5)
        icon_label = QLabel()
        icon_label.setFixedSize(22, 22)
        icon_label.setPixmap(icon.pixmap(22, 22))
        icon_label.setStyleSheet("background:transparent; border:0;")
        layout.addWidget(icon_label)
        text = QLabel(label)
        text.setFixedHeight(24)
        text.setStyleSheet("background:transparent; color:#1f3148; font-style:normal; font-weight:700; border:0;")
        layout.addWidget(text)
        row.setStyleSheet(
            f"QWidget#{object_name} {{background:transparent; border:0; border-radius:6px;}}"
            f"QWidget#{object_name}[selected=\"true\"] {{background:#cfe7ff; border:0;}}"
            f"QWidget#{object_name}:hover {{background:#fff3d4; border:0;}}"
        )
        return row

    def _sync_file_selection(self, selected_item: QListWidgetItem | None) -> None:
        self._sync_list_selection(self._files, selected_item)

    def _sync_place_selection(self, selected_item: QListWidgetItem | None) -> None:
        self._sync_list_selection(self._places, selected_item)

    def _sync_list_selection(self, list_widget: QListWidget, selected_item: QListWidgetItem | None) -> None:
        for row_index in range(list_widget.count()):
            item = list_widget.item(row_index)
            widget = list_widget.itemWidget(item)
            if widget is None:
                continue
            widget.setProperty("selected", item is selected_item)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def _file_item_size(self, name: str) -> QSize:
        return QSize(max(44, min(520, self.fontMetrics().horizontalAdvance(name) + 35)), 30)

    def _place_item_width(self, name: str) -> int:
        return max(44, min(150, self.fontMetrics().horizontalAdvance(name) + 35))

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
        self._places.setCurrentItem(item)
        self._sync_place_selection(item)
        data = str(item.data(Qt.UserRole))
        if data == "__THIS_PC__":
            self._show_this_pc()
            return
        self._navigate_to(Path(data), add_history=True)

    def _file_clicked(self, item: QListWidgetItem) -> None:
        self._files.setCurrentItem(item)
        self._sync_file_selection(item)
        path = Path(item.data(Qt.UserRole))
        if path.is_file():
            self._file_name.setText(path.name)

    def _file_double_clicked(self, item: QListWidgetItem) -> None:
        self._files.setCurrentItem(item)
        self._sync_file_selection(item)
        path = Path(item.data(Qt.UserRole))
        if path.is_dir():
            self._navigate_to(path, add_history=True)
            return
        self._file_name.setText(path.name)
        if self.mode in {"open", "import"}:
            self._accept_selection()

    def _selected_file_path(self) -> Path | None:
        item = self._files.currentItem()
        if item is None:
            return None
        data = item.data(Qt.UserRole)
        return Path(data) if data else None

    def _show_files_context_menu(self, position: QPoint) -> None:
        item = self._files.itemAt(position)
        if item is not None:
            self._files.setCurrentItem(item)
            self._sync_file_selection(item)
        selected_path = Path(item.data(Qt.UserRole)) if item is not None else self._selected_file_path()
        menu = QMenu(self)
        menu.setObjectName("ProjectContextMenu")
        menu.setStyleSheet(
            "QMenu#ProjectContextMenu {background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.42 #eef8ff, stop:1 #fff3d4); border:1px solid #8fa2bb; border-radius:10px; padding:6px;}"
            "QMenu#ProjectContextMenu::item {background:rgba(255,255,255,205); border:1px solid #b8c5d4; border-left:3px solid #43d3bd; border-radius:7px; color:#1f3148; font-size:12px; font-style:italic; font-weight:800; padding:5px 28px 5px 10px; margin:2px;}"
            "QMenu#ProjectContextMenu::item:selected {background:#fff4cf; border-color:#ff8a35; border-left-color:#d91f5c;}"
            "QMenu#ProjectContextMenu::item:disabled {color:#8a98a8; background:rgba(238,244,250,130); border-left-color:#b8c5d4;}"
            "QMenu#ProjectContextMenu::separator {height:1px; background:#b8c5d4; margin:5px 8px;}"
        )
        copy_action = QAction("Copy", self)
        cut_action = QAction("Cut", self)
        paste_action = QAction("Paste", self)
        delete_action = QAction("Delete", self)
        copy_action.setEnabled(selected_path is not None and selected_path.exists())
        cut_action.setEnabled(selected_path is not None and selected_path.exists())
        delete_action.setEnabled(selected_path is not None and selected_path.exists())
        paste_action.setEnabled(ProjectFileDialog._pending_file_action is not None)
        copy_action.triggered.connect(lambda checked=False, path=selected_path: self._remember_file_action("copy", path))
        cut_action.triggered.connect(lambda checked=False, path=selected_path: self._remember_file_action("cut", path))
        paste_action.triggered.connect(self._paste_file_action)
        delete_action.triggered.connect(lambda checked=False, path=selected_path: self._delete_file_action(path))
        menu.addAction(copy_action)
        menu.addAction(cut_action)
        menu.addAction(paste_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(self._files.mapToGlobal(position))

    def _remember_file_action(self, action: str, path: Path | None) -> None:
        if path is not None and path.exists():
            ProjectFileDialog._pending_file_action = (action, path)

    def _paste_file_action(self) -> None:
        pending = ProjectFileDialog._pending_file_action
        if pending is None:
            return
        action, source = pending
        if not source.exists():
            ProjectFileDialog._pending_file_action = None
            return
        destination = self._make_unique_path(self._current_dir / source.name)
        try:
            if action == "cut":
                shutil.move(str(source), str(destination))
                ProjectFileDialog._pending_file_action = None
            elif source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
        except OSError:
            return
        self._refresh_files()

    def _delete_current_file(self) -> None:
        self._delete_file_action(self._selected_file_path())

    def _delete_file_action(self, path: Path | None) -> None:
        if path is None or not path.exists():
            return
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError:
            return
        self._file_name.clear()
        self._refresh_files()

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
        options = dict(self.save_options) if self.mode in {"save", "export"} else None
        self.selected_result = FileDialogResult(path=path, filter_name=self._selected_filter_name(), options=options)
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

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Backspace and not self._file_name.hasFocus():
            self._go_back()
            event.accept()
            return
        if event.key() == Qt.Key_Delete:
            self._delete_current_file()
            event.accept()
            return
        super().keyPressEvent(event)

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

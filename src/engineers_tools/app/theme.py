"""Shared project visual theme."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

BACKGROUND = "#dfe7f2"
SURFACE = "#f6f8fc"
TEXT = "#182638"
EDGE = "#b8c5d4"
NAVY = "#132238"


def apply_app_theme(app: QApplication) -> None:
    font = QFont("Times New Roman", 10)
    font.setBold(True)
    font.setItalic(True)
    app.setFont(font)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BACKGROUND))
    palette.setColor(QPalette.WindowText, QColor(TEXT))
    palette.setColor(QPalette.Base, QColor(SURFACE))
    palette.setColor(QPalette.Text, QColor(TEXT))
    palette.setColor(QPalette.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.Highlight, QColor("#2f7df6"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    app.setStyleSheet(
        f"""
        QWidget {{
            color: {TEXT};
            background: {BACKGROUND};
            font-family: "Times New Roman";
            font-style: italic;
            font-weight: 700;
        }}
        QWidget#WindowRoot {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #f9fcff, stop:0.45 #eaf2fb, stop:1 #d3deeb);
            border: 1px solid {EDGE};
            border-radius: 18px;
        }}
        QWidget#TopBar {{
            background: {NAVY};
            border-top-left-radius: 18px;
            border-top-right-radius: 18px;
            border-bottom: 1px solid #0b1729;
        }}
        QLabel#WindowTitle {{ background: transparent; color: #eef4fb; font-size: 16px; font-weight: 800; }}
        QLabel#WindowMark {{
            background: #2f4664; border: 1px solid #ffffff; border-radius: 8px;
            color: #ffffff; font-size: 12px; font-weight: 800;
        }}
        QLabel#WindowLogoMark {{ background: transparent; border: 0; border-radius: 0; }}
        QPushButton#WindowButton, QPushButton#CloseButton {{
            background: transparent; border: 0; border-radius: 6px; color: #eef4fb;
            font-size: 16px; font-weight: 800; font-style: italic;
        }}
        QPushButton#WindowButton:hover {{ background: #243a59; }}
        QPushButton#CloseButton:hover {{ background: #e65252; color: #ffffff; }}

        QWidget#LauncherHeader {{ background: {NAVY}; border: 1px solid #ffffff; border-radius: 12px; }}
        QLabel#HeaderTitle {{ background: transparent; color: #ffffff; font-size: 24px; font-weight: 800; }}
        QLabel#HeaderSubtitle {{ background: transparent; color: #dfeafb; font-size: 13px; }}

        QWidget#CommandBar {{ background: #d8e3f0; border-bottom: 1px solid #b9c7d6; }}
        QWidget#StartBar {{ background: #eef4fb; border-bottom: 1px solid #c1cedd; }}
        QPushButton#MenuButton {{
            background: transparent; border: 1px solid transparent; border-radius: 4px;
            color: #1f3148; font-size: 12px; font-weight: 800; padding: 2px 7px; text-align: left;
        }}
        QPushButton#MenuButton:hover {{ background: rgba(255,255,255,92); border-color: #b4c2d3; }}
        QPushButton#MenuButton:pressed {{ background: #c7d5e6; padding-top: 3px; }}
        QPushButton#HomeButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ffffff, stop:0.36 #fff1bf, stop:0.72 #9fe0ff, stop:1 #7183d8);
            border: 1px solid #54749c; border-bottom: 2px solid #354c78;
            border-radius: 9px; color: #223650; padding: 1px 7px;
        }}
        QPushButton#HomeButton:hover {{
            border-color: #ff8a35;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:0.45 #ffe5a8, stop:1 #7fd9ff);
        }}
        QPushButton#HomeButton:pressed {{ padding-top: 3px; padding-left: 8px; border-bottom: 1px solid #354c78; }}

        QWidget#WorkspaceArea {{ background: transparent; }}
        QWidget#SidePanel, QWidget#CanvasShell {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255,255,255,220), stop:1 rgba(235,244,255,210));
            border: 1px solid #bdc9d8; border-radius: 12px;
        }}
        QLabel#PanelTitle, QLabel#CanvasTitle {{ background: transparent; font-size: 15px; color: #1f3148; }}
        QLabel#PanelItem {{
            background: #edf3fa; border: 1px solid #c8d4e2; border-radius: 7px;
            padding-left: 8px; color: #2b405d;
        }}
        QWidget#LayerRow {{
            background: rgba(255,255,255,170); border: 1px solid #c6d3e2; border-radius: 9px;
        }}
        QPushButton#LayerIconButton {{
            background: transparent; border: 0; border-radius: 7px; padding: 0px;
        }}
        QPushButton#LayerIconButton:hover {{ background: #fff1bf; }}
        QLineEdit#LayerNameInput {{
            background: #f9fbff; border: 1px solid #c3d0df; border-radius: 7px;
            color: #1f3148; font-size: 12px; font-style: normal; font-weight: 700; padding: 3px 6px;
        }}
        QLineEdit#LayerNameInput:focus {{ border-color: #2f7df6; background: #ffffff; }}
        QWidget#GridCanvas {{ background: #fbfdff; border: 1px solid #c1cedd; border-radius: 9px; }}

        QWidget#PageBar {{ background: #d8e3f0; border-top: 1px solid #b9c7d6; }}
        QWidget#PageStrip {{ background: transparent; }}
        QPushButton#PageButton, QPushButton#PageButtonActive {{
            min-width: 80px; min-height: 27px; border-radius: 9px; padding: 4px 10px;
            color: #223650; font-size: 12px; font-weight: 800;
        }}
        QPushButton#PageButton {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ffffff, stop:1 #cddbeb);
            border: 1px solid #95a9c1; border-bottom: 2px solid #7188a5;
        }}
        QPushButton#PageButtonActive {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fff9de, stop:1 #ffc35a);
            border: 1px solid #7e5b10; border-bottom: 2px solid #7e5b10;
        }}
        QPushButton#PageButton:hover, QPushButton#PageButtonActive:hover {{ border-color: #2f7df6; }}
        QPushButton#AddPageButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.42 #fff1bf, stop:1 #43d3bd);
            border: 1px solid #4b778b; border-bottom: 3px solid #28556a;
            border-radius: 11px; color: #132238; font-size: 12px; font-weight: 900; padding: 5px 14px;
        }}
        QPushButton#AddPageButton:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.45 #ffe0a3, stop:1 #73e6d5); border-color: #ff8a35; }}
        QPushButton#AddPageButton:pressed {{ padding-top: 7px; border-bottom: 1px solid #28556a; }}

        QWidget#StatusBar {{
            background: {NAVY}; border-top: 1px solid #0b1729;
            border-bottom-left-radius: 18px; border-bottom-right-radius: 18px;
        }}
        QLabel#StatusItem {{ background: transparent; color: #eef4fb; font-size: 11px; }}
        QWidget#ZoomControl, QWidget#ZoomArrowStack {{ background: transparent; }}

        QPushButton#ConfirmButton, QPushButton#ToolButton, QPushButton#FileNavButton,
        QPushButton#PrimaryDialogButton, QPushButton#SecondaryDialogButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ffffff, stop:0.48 #f4f9ff, stop:1 #bfd2e8);
            border: 1px solid #95a9c1; border-bottom: 2px solid #7188a5;
            border-radius: 8px; color: #223650; font-size: 12px; font-weight: 800; padding: 4px 10px;
        }}
        QPushButton#PrimaryDialogButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:0.42 #fff1bf, stop:1 #ff8a35);
            border-color: #7e5b10; border-bottom-color: #7e5b10;
        }}
        QPushButton#SecondaryDialogButton {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ffffff, stop:1 #d8e3f0);
        }}
        QPushButton#ConfirmButton:hover, QPushButton#ToolButton:hover, QPushButton#FileNavButton:hover,
        QPushButton#PrimaryDialogButton:hover, QPushButton#SecondaryDialogButton:hover {{ border-color: #2f7df6; background: #ffffff; }}
        QPushButton#ConfirmButton:pressed, QPushButton#ToolButton:pressed, QPushButton#FileNavButton:pressed,
        QPushButton#PrimaryDialogButton:pressed, QPushButton#SecondaryDialogButton:pressed {{ padding-top: 6px; border-bottom: 1px solid #7188a5; }}

        QDialog#ProjectMenuDialog, QDialog#ProjectHelpDialog, QDialog#ProjectFileDialog {{ background: transparent; }}
        QWidget#ProjectMenuShell {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #ffffff, stop:0.40 #eef8ff, stop:1 #fff3d4);
            border: 1px solid #8fa2bb; border-radius: 12px;
        }}
        QLabel#MenuDialogEmpty {{
            background: rgba(255,255,255,135); border: 1px dashed #9fb0c5; border-radius: 9px;
            color: #39516f; font-size: 12px; padding: 10px;
        }}
        QPushButton#MenuItemButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255,255,255,205), stop:0.78 rgba(238,246,255,205), stop:1 rgba(226,240,255,205));
            border: 1px solid #b8c5d4; border-left: 3px solid #43d3bd; border-radius: 7px;
            color: #1f3148; font-size: 12px; font-weight: 800; padding: 4px 8px; text-align: left;
        }}
        QPushButton#MenuItemButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ffffff, stop:0.60 #fff4cf, stop:1 #dff6ff);
            border-color: #ff8a35; border-left-color: #d91f5c;
        }}
        QPushButton#MenuItemButton:pressed {{ background: #cddbeb; padding-top: 6px; }}

        QWidget#ProjectHelpShell, QWidget#ProjectFileShell {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #ffffff, stop:0.50 #edf6ff, stop:1 #dbe6f4);
            border: 1px solid #8fa2bb; border-radius: 16px;
        }}
        QWidget#HelpHeader, QWidget#FileDialogHeader {{
            background: {NAVY}; border-top-left-radius: 16px; border-top-right-radius: 16px;
        }}
        QWidget#FileDialogHeader {{ min-height: 42px; max-height: 42px; }}
        QLabel#HelpTitle, QLabel#FileDialogTitle {{ background: transparent; color: #ffffff; font-size: 15px; font-weight: 800; padding: 6px 2px; }}
        QWidget#FileDialogNavBar {{ background: #0f1725; border-top: 1px solid #243752; border-bottom: 1px solid #0a101a; }}
        QLabel#FilePathLabel {{
            background: #f7fbff; border: 1px solid #536a89; border-radius: 8px;
            color: #1f3148; font-size: 12px; font-style: normal; padding: 4px 9px;
        }}
        QWidget#FileDialogBody, QWidget#FileDialogFooter {{ background: transparent; }}
        QListWidget#PlacesList, QListWidget#FilesList {{
            background: rgba(255,255,255,185); border: 1px solid #b9c7d8; border-radius: 10px;
            color: #1f3148; font-size: 12px; font-style: normal; padding: 5px;
        }}
        QListWidget#PlacesList::item, QListWidget#FilesList::item {{ min-height: 28px; border-radius: 7px; padding: 3px; }}
        QListWidget#PlacesList::item:selected, QListWidget#FilesList::item:selected {{ background: #cfe7ff; color: #132238; }}
        QListWidget#PlacesList::item:hover, QListWidget#FilesList::item:hover {{ background: #fff3d4; }}
        QLabel#FileFieldLabel {{ background: transparent; color: #1f3148; font-size: 12px; }}
        QLineEdit#FileNameInput, QComboBox#FileTypeCombo {{
            background: #ffffff; border: 1px solid #9fb0c5; border-radius: 8px;
            color: #1f3148; font-size: 12px; font-style: normal; padding: 5px 8px;
        }}
        QLabel#HelpBody {{
            background: rgba(255,255,255,160); border: 1px solid #c3d0df; border-radius: 10px;
            color: #213550; font-size: 13px; padding: 14px;
        }}
        QPushButton#MenuDialogClose {{
            background: transparent; border: 0; border-radius: 6px; color: #eef4fb;
            font-size: 16px; font-weight: 800;
        }}
        QPushButton#MenuDialogClose:hover {{ background: #e65252; color: #ffffff; }}
        QScrollBar:vertical {{ background: #d8e3f0; width: 12px; margin: 2px; border-radius: 6px; }}
        QScrollBar::handle:vertical {{ background: #7f94af; min-height: 30px; border-radius: 6px; }}
        QScrollBar::handle:vertical:hover {{ background: #ff8a35; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """
    )

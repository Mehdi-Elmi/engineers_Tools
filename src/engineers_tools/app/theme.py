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
                stop:0 #f8fbff, stop:0.52 #e7eef8, stop:1 #d4dfec);
            border: 1px solid {EDGE};
            border-radius: 18px;
        }}
        QWidget#TopBar {{
            background: {NAVY};
            border-top-left-radius: 18px;
            border-top-right-radius: 18px;
            border-bottom: 1px solid #0b1729;
        }}
        QLabel#WindowTitle {{
            background: transparent;
            color: #eef4fb;
            font-size: 16px;
            font-weight: 800;
        }}
        QLabel#WindowMark {{
            background: #2f4664;
            border: 1px solid #ffffff;
            border-radius: 8px;
            color: #ffffff;
            font-size: 12px;
            font-weight: 800;
        }}
        QPushButton#WindowButton, QPushButton#CloseButton {{
            background: transparent;
            border: 0;
            border-radius: 6px;
            color: #eef4fb;
            font-size: 16px;
            font-weight: 800;
            font-style: italic;
        }}
        QPushButton#WindowButton:hover {{ background: #243a59; }}
        QPushButton#CloseButton:hover {{ background: #e65252; color: #ffffff; }}
        QWidget#LauncherHeader {{
            background: #2f4664;
            border: 1px solid #ffffff;
            border-radius: 12px;
        }}
        QLabel#HeaderTitle {{
            background: transparent;
            color: #ffffff;
            font-size: 24px;
            font-weight: 800;
        }}
        QLabel#HeaderSubtitle {{
            background: transparent;
            color: #dfeafb;
            font-size: 13px;
        }}
        QPushButton#LauncherCard {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #ffffff, stop:0.56 #eef4fb, stop:1 #d6e2f0);
            border: 1px solid #b8c5d4;
            border-bottom: 7px solid #9fb0c5;
            border-radius: 12px;
            color: #182638;
            font-size: 17px;
            padding: 14px;
            text-align: center;
        }}
        QPushButton#LauncherCard:hover {{ border-color: #2f7df6; background: #ffffff; }}
        QPushButton#LauncherCard:pressed {{ padding-top: 18px; border-bottom: 3px solid #9fb0c5; }}
        QWidget#CommandBar {{
            background: #d8e3f0;
            border-bottom: 1px solid #b9c7d6;
        }}
        QWidget#StartBar {{
            background: #eef4fb;
            border-bottom: 1px solid #c1cedd;
        }}
        QPushButton#MenuButton {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            color: #1f3148;
            font-size: 12px;
            font-weight: 800;
            padding: 2px 8px;
            text-align: left;
        }}
        QPushButton#MenuButton:hover {{
            background: rgba(255, 255, 255, 92);
            border-color: #b4c2d3;
        }}
        QPushButton#MenuButton:pressed {{
            background: #c7d5e6;
            padding-top: 3px;
        }}
        QPushButton#HomeButton, QPushButton#ConfirmButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ffffff, stop:0.48 #f4f9ff, stop:1 #bfd2e8);
            border: 1px solid #95a9c1;
            border-bottom: 2px solid #7188a5;
            border-radius: 8px;
            color: #223650;
            font-size: 12px;
            font-weight: 800;
            padding: 4px 10px;
        }}
        QPushButton#HomeButton:hover, QPushButton#ConfirmButton:hover {{
            border-color: #2f7df6;
            background: #ffffff;
        }}
        QPushButton#HomeButton:pressed, QPushButton#ConfirmButton:pressed {{
            padding-top: 6px;
            padding-left: 11px;
            border-bottom: 1px solid #7188a5;
        }}
        QPushButton#ToolButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ffffff, stop:0.48 #f4f9ff, stop:1 #bfd2e8);
            border: 1px solid #95a9c1;
            border-bottom: 2px solid #7188a5;
            border-radius: 8px;
            color: #223650;
            font-size: 12px;
            font-weight: 800;
            padding: 4px 10px;
        }}
        QPushButton#ToolButton:hover {{
            border-color: #2f7df6;
            background: #ffffff;
        }}
        QPushButton#ToolButton:pressed {{
            padding-top: 6px;
            padding-left: 11px;
        }}
        QWidget#WorkspaceArea {{ background: transparent; }}
        QWidget#SidePanel, QWidget#CanvasShell {{
            background: rgba(255, 255, 255, 190);
            border: 1px solid #bdc9d8;
            border-radius: 10px;
        }}
        QLabel#PanelTitle, QLabel#CanvasTitle {{
            background: transparent;
            font-size: 14px;
            color: #1f3148;
        }}
        QLabel#PanelItem {{
            background: #edf3fa;
            border: 1px solid #c8d4e2;
            border-radius: 7px;
            padding-left: 8px;
            color: #2b405d;
        }}
        QWidget#GridCanvas {{
            background: #f9fbff;
            border: 1px solid #c1cedd;
            border-radius: 8px;
        }}
        QWidget#PageBar {{
            background: #d8e3f0;
            border-top: 1px solid #b9c7d6;
        }}
        QWidget#StatusBar {{
            background: {NAVY};
            border-top: 1px solid #0b1729;
            border-bottom-left-radius: 18px;
            border-bottom-right-radius: 18px;
        }}
        QLabel#StatusItem {{
            background: transparent;
            color: #eef4fb;
            font-size: 11px;
        }}
        QLabel#DialogNote {{
            background: transparent;
            color: #2b405d;
            font-size: 12px;
        }}
        QDialog#ProjectDialog {{ background: #dfe7f2; }}
        """
    )

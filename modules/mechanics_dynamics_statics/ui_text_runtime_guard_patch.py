"""Final guard for Text runtime menus and font choices.

Runs after the runtime Text patch and before the workspace is created. It keeps
font choices consistent across the Text bar and File Properties, makes menu
actions ignore the QAction ``checked`` argument, and restores the project's
blue/orange visual language for Text controls.
"""

from __future__ import annotations

PATCH_VERSION = "engineering-ui-text-runtime-guard-2026-07-02-d"

FONT_CHOICES = (
    "Times New Roman",
    "B Zar",
    "B Nazanin",
    "B Mitra",
    "B Lotus",
    "B Titr",
    "B Yekan",
    "B Koodak",
    "B Traffic",
)

POLISHED_TEXTBAR_STYLE = (
    "QFrame#InlineTextBar{"
    "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.45 #eaf7ff,stop:.72 #d9f0ff,stop:1 #fff0c8);"
    "border:1px solid #5f86ad;border-radius:14px;}"
    "QComboBox{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#123d6f;"
    "font-family:'Times New Roman';font-size:12px;font-weight:800;font-style:normal;padding:1px 35px 1px 9px;}"
    "QComboBox::drop-down{width:32px;border:0;subcontrol-origin:border;subcontrol-position:center right;"
    "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fffef9,stop:.55 #ffe58a,stop:1 #ffad37);"
    "border-top-right-radius:8px;border-bottom-right-radius:8px;}"
    "QSpinBox{background:#fffefa;border:1px solid #b98920;border-radius:9px;color:#123d6f;"
    "font-family:'Times New Roman';font-size:12px;font-weight:800;font-style:normal;padding:1px 34px 1px 8px;}"
    "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #e6f4ff);"
    "border:1px solid #7fa6ca;border-radius:9px;color:#123d6f;font-family:'Times New Roman';font-size:12px;font-weight:900;font-style:normal;}"
    "QPushButton:hover{background:#fff4cf;border-color:#ff8a35;color:#0b4a87;}"
    "QPushButton:checked{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffc35a,stop:1 #f18a2a);"
    "border-color:#7e5b10;color:#102238;padding-top:2px;}"
    "QPushButton:pressed{background:#d9e9f7;padding-top:2px;}"
    "QMenu{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.55 #eef8ff,stop:1 #fff0c8);"
    "border:1px solid #6f91b2;border-radius:10px;padding:6px;}"
    "QMenu::item{color:#123d6f;background:rgba(255,255,255,210);border:1px solid #b8c5d4;border-radius:7px;"
    "font-family:'Times New Roman';font-weight:800;padding:5px 22px 5px 10px;margin:2px;}"
    "QMenu::item:selected{background:#fff4cf;border-color:#ff8a35;color:#102238;}"
)


def apply_ui_text_runtime_guard_patch() -> None:
    from . import svg_cursor_assets_activation_patch as svg
    from . import ui_text_tool_final_patch as text_final
    from . import ui_text_tool_runtime_fix_patch as runtime
    from . import workspace as edw

    if getattr(edw.EngineeringDesignWorkspace, "_engineering_ui_text_runtime_guard_patch", "") == PATCH_VERSION:
        return

    svg.FONT_CHOICES = FONT_CHOICES
    text_final.FONT_CHOICES = FONT_CHOICES
    runtime.FONT_CHOICES = FONT_CHOICES
    runtime._TOOLBAR_STYLE = POLISHED_TEXTBAR_STYLE

    def safe_menu_action(menu, text: str, callback) -> None:
        action = menu.addAction(text)
        action.triggered.connect(lambda checked=False, cb=callback: cb())

    runtime._menu_action = safe_menu_action
    edw.EngineeringDesignWorkspace._engineering_ui_text_runtime_guard_patch = PATCH_VERSION

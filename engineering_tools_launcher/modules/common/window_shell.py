"""Central window and page shell for Engineering Tools."""

from __future__ import annotations

import ctypes
import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox

try:
    from modules.common.launcher_icon_data import ICON_DATA
except ImportError:
    ICON_DATA = {}


ROOT_DIR = Path(__file__).resolve().parents[2]
TRANSPARENT = "#ff00ff"
TITLE_H = 42
EDGE = 9
MOVE_EDGE_GUARD = 18
APP_USER_MODEL_ID = "MehdiElmi.EngineeringTools"

COLORS = {
    "frame": "#1198d4",
    "title": "#163f68",
    "title_hover": "#245680",
    "close": "#c7444d",
    "bg": "#edf4fb",
    "panel": "#ffffff",
    "panel_soft": "#f8fbff",
    "line": "#c7d8e8",
    "text": "#10233f",
    "muted": "#435b75",
    "blue": "#075f9f",
    "shadow": "#d6e1ec",
    "card_top": "#425f7f",
}


def configure_process_identity() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        pass


configure_process_identity()


@dataclass(frozen=True)
class ModuleItem:
    title: str
    key: str
    subtitle: str
    target: str
    accent_a: str
    accent_b: str


MODULES: tuple[ModuleItem, ...] = (
    ModuleItem("Engineering Design Tools", "engineer_design", "Draw vectors, axes, angles, and mechanics diagrams.", "modules/engineer_design/main.py", "#3778ff", "#16bdd6"),
    ModuleItem("Circuit Design", "circuit_design", "Build clean electrical schematics and circuit layouts.", "modules/circuit_design/main.py", "#8057f4", "#dd66cf"),
    ModuleItem("Background Remover", "background_remover", "Remove image backgrounds for clean visual outputs.", "modules/background_remover/main.py", "#128f88", "#2675be"),
    ModuleItem("Flowchart", "flowchart_designer", "Create process maps and logic diagrams.", "modules/flowchart_designer/main.py", "#0fb59f", "#2a97df"),
    ModuleItem("Barcode", "barcode_generator", "Generate barcodes and QR code layouts.", "modules/barcode_generator/main.py", "#252c78", "#5964d8"),
)


CARD_RECTS = (
    (52, 274, 250, 468),
    (296, 274, 494, 468),
    (540, 274, 738, 468),
    (52, 502, 250, 696),
    (296, 502, 494, 696),
)


def rounded_rect(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, radius: float, **kwargs) -> int:
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)


class BaseShell(tk.Tk):
    def __init__(self, title: str, design_w: int, design_h: int, min_w: int, min_h: int) -> None:
        super().__init__()
        self.shell_title = title
        self.design_w = design_w
        self.design_h = design_h
        self.min_w = min_w
        self.min_h = min_h
        self.title(title)
        self.overrideredirect(True)
        self.minsize(min_w, min_h)
        self.configure(bg=TRANSPARENT)
        try:
            self.wm_attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            self.configure(bg=COLORS["frame"])

        self.canvas = tk.Canvas(self, bg=TRANSPARENT, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.window_w = float(design_w)
        self.window_h = float(design_h)
        self.scale = 1.0
        self.ox = 0.0
        self.oy = 0.0
        self.normal_geometry = ""
        self.is_maximized = False
        self.drag_offset = (0, 0)
        self.drag_active = False
        self.resize_start: tuple[int, int, int, int, int, int, str] | None = None
        self.hover_control = ""
        self.controls: dict[str, tuple[float, float, float, float]] = {}

        self._center(design_w, design_h)
        self._bind_events()
        self._prepare_assets()
        self._draw()
        self.after(120, self._enable_taskbar_button)

    def _center(self, width: int, height: int) -> None:
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.normal_geometry = f"{width}x{height}+{x}+{y}"

    def _bind_events(self) -> None:
        self.bind("<Map>", self._restore_titleless)
        self.bind("<Configure>", lambda event: self._draw() if event.widget is self else None)
        self.canvas.bind("<ButtonPress-1>", self._down)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._up)
        self.canvas.bind("<Motion>", self._move)
        self.canvas.bind("<Leave>", self._leave)

    def _layout(self) -> None:
        width = max(self.winfo_width(), self.min_w)
        height = max(self.winfo_height(), self.min_h)
        self.window_w = float(width)
        self.window_h = float(height)
        content_h = max(1, self.design_h - TITLE_H)
        available_h = max(1, height - TITLE_H)
        self.scale = min(width / self.design_w, available_h / content_h)
        self.scale = max(0.82, min(self.scale, 1.18))
        self.ox = (width - self.design_w * self.scale) / 2
        self.oy = TITLE_H * (1.0 - self.scale)

    def _x(self, value: float) -> float:
        return self.ox + value * self.scale

    def _y(self, value: float) -> float:
        return self.oy + value * self.scale

    def _r(self, value: float) -> float:
        return value * self.scale

    def _rect(self, x1: float, y1: float, x2: float, y2: float) -> tuple[float, float, float, float]:
        return self._x(x1), self._y(y1), self._x(x2), self._y(y2)

    def _font(self, size: int, weight: str = "normal") -> tuple[str, int, str] | tuple[str, int]:
        scaled = max(7, int(round(size * self.scale)))
        return ("Segoe UI", scaled, weight) if weight != "normal" else ("Segoe UI", scaled)

    def _draw(self) -> None:
        self._layout()
        self.canvas.delete("all")
        self.controls.clear()
        rounded_rect(self.canvas, 0, 0, self.window_w, self.window_h, 16, fill=COLORS["frame"], outline="")
        rounded_rect(self.canvas, 2, 2, self.window_w - 2, self.window_h - 2, 14, fill=COLORS["bg"], outline="")
        rounded_rect(self.canvas, 2, 2, self.window_w - 2, TITLE_H + 2, 12, fill=COLORS["title"], outline="")
        self.canvas.create_rectangle(2, TITLE_H - 10, self.window_w - 2, TITLE_H + 2, fill=COLORS["title"], outline="")
        self._draw_titlebar()
        self._draw_content()

    def _draw_titlebar(self) -> None:
        rounded_rect(self.canvas, 13, 7, 43, 35, 8, fill="#ffffff", outline="")
        self.canvas.create_text(28, 21, text="ET", fill=COLORS["title"], font=("Segoe UI", 9, "bold"))
        self.canvas.create_text(54, 21, text=self.shell_title, fill="#ffffff", font=("Segoe UI", 10, "bold"), anchor="w", justify="left")

        for index, name in enumerate(("min", "max", "close")):
            x1 = self.window_w - 132 + index * 44
            x2 = x1 + 44
            self.controls[name] = (x1, 2, x2, TITLE_H + 2)
            if self.hover_control == name:
                self.canvas.create_rectangle(*self.controls[name], fill=COLORS["close"] if name == "close" else COLORS["title_hover"], outline="")
            cx, cy = (x1 + x2) / 2, 22
            if name == "min":
                self.canvas.create_line(cx - 7, cy + 6, cx + 7, cy + 6, fill="#ffffff", width=2)
            elif name == "max":
                self.canvas.create_rectangle(cx - 6, cy - 5, cx + 6, cy + 7, outline="#ffffff", width=2)
            else:
                self.canvas.create_line(cx - 6, cy - 6, cx + 6, cy + 6, fill="#ffffff", width=2)
                self.canvas.create_line(cx + 6, cy - 6, cx - 6, cy + 6, fill="#ffffff", width=2)

    def _draw_content(self) -> None:
        raise NotImplementedError

    def _prepare_assets(self) -> None:
        pass

    def _control_at(self, x: float, y: float) -> str:
        for name, (x1, y1, x2, y2) in self.controls.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return name
        return ""

    def _edge_at(self, x: float, y: float) -> str:
        return ""

    def _is_move_zone(self, x: float, y: float) -> bool:
        if self.is_maximized:
            return False
        if y < MOVE_EDGE_GUARD or y > TITLE_H - 4:
            return False
        if x < 54 or x > self.winfo_width() - 132:
            return False
        return not self._control_at(x, y)

    def _down(self, event: tk.Event) -> None:
        self.resize_start = None
        self.drag_active = False
        control = self._control_at(event.x, event.y)
        if control:
            self._handle_control(control)
            return
        if self._content_click(event.x, event.y):
            return
        if self._is_move_zone(event.x, event.y):
            self.drag_offset = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())
            self.drag_active = True
            self.canvas.configure(cursor="fleur")

    def _content_click(self, _x: float, _y: float) -> bool:
        return False

    def _content_hover(self, _x: float, _y: float) -> bool:
        return False

    def _drag(self, event: tk.Event) -> None:
        if self.drag_active and not self.is_maximized:
            self.geometry(f"+{event.x_root - self.drag_offset[0]}+{event.y_root - self.drag_offset[1]}")

    def _up(self, _event: tk.Event) -> None:
        self.resize_start = None
        self.drag_active = False

    def _move(self, event: tk.Event) -> None:
        control = self._control_at(event.x, event.y)
        if control != self.hover_control:
            self.hover_control = control
            self._draw()
        hovered = self._content_hover(event.x, event.y)
        if control or hovered:
            self.canvas.configure(cursor="hand2")
        elif self._is_move_zone(event.x, event.y):
            self.canvas.configure(cursor="fleur")
        else:
            self.canvas.configure(cursor="")

    def _leave(self, _event: tk.Event) -> None:
        if self.hover_control:
            self.hover_control = ""
            self._draw()
        self.canvas.configure(cursor="")

    def _resize(self, event: tk.Event) -> None:
        self.resize_start = None

    def _handle_control(self, name: str) -> None:
        if name == "min":
            self.overrideredirect(False)
            self.update_idletasks()
            self.state("iconic")
        elif name == "max":
            if self.is_maximized:
                self.geometry(self.normal_geometry)
                self.is_maximized = False
            else:
                self.normal_geometry = self.geometry()
                x, y, width, height = self._usable_screen_geometry()
                self.geometry(f"{width}x{height}+{x}+{y}")
                self.is_maximized = True
        elif name == "close":
            self.destroy()

    def _restore_titleless(self, _event: tk.Event) -> None:
        self.after(10, lambda: self.overrideredirect(True))

    def _usable_screen_geometry(self) -> tuple[int, int, int, int]:
        if sys.platform == "win32":
            try:
                from ctypes import wintypes

                rect = wintypes.RECT()
                ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
                return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
            except (AttributeError, OSError, ValueError):
                pass
        return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    def _enable_taskbar_button(self) -> None:
        if sys.platform != "win32":
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            style = (style & ~0x00000080) | 0x00040000
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
            self.withdraw()
            self.after(10, self.deiconify)
        except (AttributeError, OSError, tk.TclError):
            pass


class LauncherWindow(BaseShell):
    def __init__(self) -> None:
        self.hover_card = -1
        self.cards: list[tuple[float, float, float, float, ModuleItem]] = []
        self.icon_images: dict[str, tk.PhotoImage] = {}
        super().__init__("Engineering Tools", 900, 720, 760, 620)

    def _prepare_assets(self) -> None:
        self.icon_images = {}
        for key, data in ICON_DATA.items():
            try:
                self.icon_images[key] = tk.PhotoImage(data=data, format="png")
            except tk.TclError:
                continue

    def _draw_content(self) -> None:
        self.cards.clear()
        rounded_rect(self.canvas, *self._rect(25, 67, 881, 209), self._r(16), fill=COLORS["shadow"], outline="")
        rounded_rect(self.canvas, *self._rect(22, 62, 878, 204), self._r(16), fill=COLORS["panel"], outline=COLORS["line"], width=max(1, int(self._r(1))))
        self.canvas.create_text(self._x(50), self._y(104), text="Engineering Tools", fill=COLORS["text"], font=self._font(28, "bold"), anchor="w", justify="left")
        self.canvas.create_text(self._x(52), self._y(148), text="A focused engineering workspace for design, circuits, diagrams, image cleanup, and codes.", fill=COLORS["muted"], font=self._font(11), anchor="w", justify="left", width=self._r(720))
        self.canvas.create_text(self._x(52), self._y(177), text="Choose a module to open its dedicated environment.", fill=COLORS["blue"], font=self._font(9, "bold"), anchor="w", justify="left")

        rounded_rect(self.canvas, *self._rect(22, 224, 878, 704), self._r(16), fill=COLORS["panel_soft"], outline=COLORS["line"], width=max(1, int(self._r(1))))
        for index, item in enumerate(MODULES):
            x1, y1, x2, y2 = CARD_RECTS[index]
            self.cards.append((*self._rect(x1, y1, x2, y2), item))
            self._draw_card(index, x1, y1, x2 - x1, y2 - y1, item)
        self.canvas.create_text(self._x(14), self._y(704), text="Drag the title bar to move the window", fill="#45637d", font=self._font(7), anchor="w")

    def _draw_card(self, index: int, x: float, y: float, w: float, h: float, item: ModuleItem) -> None:
        lift = -3 if index == self.hover_card else 0
        rounded_rect(self.canvas, *self._rect(x + 3, y + 7, x + w + 3, y + h + 7), self._r(18), fill=COLORS["shadow"], outline="")
        rounded_rect(self.canvas, *self._rect(x, y + lift, x + w, y + h + lift), self._r(18), fill="#ffffff", outline=item.accent_a if index == self.hover_card else COLORS["line"], width=max(1, int(self._r(1.4))))
        self.canvas.create_line(self._x(x + 18), self._y(y + 5 + lift), self._x(x + w - 18), self._y(y + 5 + lift), fill=COLORS["card_top"], width=self._r(7), capstyle=tk.ROUND)

        icon = 72
        cx, cy = x + w / 2, y + 73 + lift
        image = self.icon_images.get(item.key)
        if image:
            rounded_rect(self.canvas, *self._rect(cx - icon / 2 + 8, cy - icon / 2 + 9, cx + icon / 2 + 8, cy + icon / 2 + 9), self._r(18), fill="#d3dce8", outline="")
            self.canvas.create_image(self._x(cx), self._y(cy), image=image, anchor="center")
        else:
            rounded_rect(self.canvas, *self._rect(cx - icon / 2 + 7, cy - icon / 2 + 8, cx + icon / 2 + 7, cy + icon / 2 + 8), self._r(18), fill="#d3dce8", outline="")
            rounded_rect(self.canvas, *self._rect(cx - icon / 2, cy - icon / 2, cx + icon / 2, cy + icon / 2), self._r(18), fill=item.accent_a, outline="")
            rounded_rect(self.canvas, *self._rect(cx - icon / 2 + 8, cy - icon / 2 + 8, cx + icon / 2 - 8, cy + icon / 2 - 8), self._r(14), fill=item.accent_b, outline="")
            self.canvas.create_line(self._x(cx - 18), self._y(cy - 25), self._x(cx + 18), self._y(cy - 25), fill="#ffffff", width=self._r(1.4), capstyle=tk.ROUND)
            self._draw_icon(item.key, cx, cy)

        self.canvas.create_text(self._x(x + 22), self._y(y + h - 64 + lift), text=item.title, fill=COLORS["text"], font=self._font(11, "bold"), anchor="w", justify="left", width=self._r(w - 44))
        self.canvas.create_text(self._x(x + 22), self._y(y + h - 34 + lift), text=item.subtitle, fill=COLORS["muted"], font=self._font(8), anchor="w", justify="left", width=self._r(w - 44))

    def _draw_icon(self, key: str, cx: float, cy: float) -> None:
        white = "#ffffff"
        soft = "#dff7ff"
        if key == "engineer_design":
            ox, oy = cx - 24, cy + 23
            vx, vy = cx + 20, cy - 19
            self.canvas.create_line(self._x(ox), self._y(oy), self._x(cx + 27), self._y(oy), fill=white, width=self._r(3.2), arrow=tk.LAST, arrowshape=(9, 11, 4))
            self.canvas.create_line(self._x(ox), self._y(oy), self._x(ox), self._y(cy - 27), fill=white, width=self._r(3.2), arrow=tk.LAST, arrowshape=(9, 11, 4))
            self.canvas.create_line(self._x(ox + 8), self._y(oy), self._x(ox + 8), self._y(oy - 5), fill=soft, width=self._r(1.6))
            self.canvas.create_line(self._x(ox + 18), self._y(oy), self._x(ox + 18), self._y(oy - 5), fill=soft, width=self._r(1.6))
            self.canvas.create_line(self._x(ox), self._y(oy - 9), self._x(ox + 5), self._y(oy - 9), fill=soft, width=self._r(1.6))
            self.canvas.create_line(self._x(ox), self._y(oy - 19), self._x(ox + 5), self._y(oy - 19), fill=soft, width=self._r(1.6))
            self.canvas.create_line(self._x(ox), self._y(oy), self._x(vx), self._y(vy), fill=white, width=self._r(3.8), arrow=tk.LAST, arrowshape=(10, 12, 4))
            self.canvas.create_arc(*self._rect(ox - 23, oy - 23, ox + 23, oy + 23), start=0, extent=43, style=tk.ARC, outline=soft, width=max(1, int(self._r(2.8))))
            self.canvas.create_line(self._x(ox + 19), self._y(oy - 4), self._x(ox + 23), self._y(oy - 2), fill=soft, width=self._r(1.6))
            self.canvas.create_oval(*self._rect(ox - 4, oy - 4, ox + 4, oy + 4), fill=white, outline="")
            self.canvas.create_oval(*self._rect(vx - 4, vy - 4, vx + 4, vy + 4), fill=white, outline="")
        elif key == "circuit_design":
            self.canvas.create_line(self._x(cx - 28), self._y(cy - 15), self._x(cx - 14), self._y(cy - 15), fill=white, width=self._r(3.0))
            zigzag = [(-14, -15), (-9, -22), (-4, -8), (1, -22), (6, -8), (11, -15)]
            for (x1, y1), (x2, y2) in zip(zigzag, zigzag[1:]):
                self.canvas.create_line(self._x(cx + x1), self._y(cy + y1), self._x(cx + x2), self._y(cy + y2), fill=white, width=self._r(2.8))
            self.canvas.create_line(self._x(cx + 11), self._y(cy - 15), self._x(cx + 28), self._y(cy - 15), fill=white, width=self._r(3.0))
            self.canvas.create_line(self._x(cx - 22), self._y(cy - 15), self._x(cx - 22), self._y(cy + 19), self._x(cx + 1), self._y(cy + 19), fill=white, width=self._r(3.0))
            self.canvas.create_line(self._x(cx + 8), self._y(cy + 19), self._x(cx + 28), self._y(cy + 19), fill=white, width=self._r(3.0))
            self.canvas.create_line(self._x(cx + 1), self._y(cy + 8), self._x(cx + 1), self._y(cy + 30), fill=white, width=self._r(2.8))
            self.canvas.create_line(self._x(cx + 8), self._y(cy + 8), self._x(cx + 8), self._y(cy + 30), fill=white, width=self._r(2.8))
            self.canvas.create_line(self._x(cx + 1), self._y(cy + 7), self._x(cx + 1), self._y(cy + 31), fill=soft, width=self._r(1.1))
            self.canvas.create_line(self._x(cx + 8), self._y(cy + 7), self._x(cx + 8), self._y(cy + 31), fill=soft, width=self._r(1.1))
            for px, py in [(-28, -15), (28, -15), (-22, 19), (28, 19)]:
                self.canvas.create_oval(*self._rect(cx + px - 4, cy + py - 4, cx + px + 4, cy + py + 4), fill=white, outline="")
        elif key == "background_remover":
            rounded_rect(self.canvas, *self._rect(cx - 24, cy - 18, cx + 24, cy + 18), self._r(5), outline=white, width=max(1, int(self._r(2.4))), fill="")
            self.canvas.create_oval(*self._rect(cx - 9, cy - 10, cx + 9, cy + 8), outline=white, width=max(1, int(self._r(2.8))))
            self.canvas.create_line(self._x(cx - 20), self._y(cy + 13), self._x(cx - 8), self._y(cy + 3), self._x(cx + 5), self._y(cy + 14), self._x(cx + 20), self._y(cy - 10), fill=white, width=self._r(2.6), smooth=True)
            self.canvas.create_line(self._x(cx - 27), self._y(cy + 24), self._x(cx + 27), self._y(cy - 24), fill=white, width=self._r(3.2))
        elif key == "flowchart_designer":
            rounded_rect(self.canvas, *self._rect(cx - 15, cy - 27, cx + 15, cy - 13), self._r(7), outline=white, width=max(1, int(self._r(3))), fill="")
            rounded_rect(self.canvas, *self._rect(cx - 18, cy - 6, cx + 18, cy + 8), self._r(3), outline=white, width=max(1, int(self._r(3))), fill="")
            rounded_rect(self.canvas, *self._rect(cx - 15, cy + 16, cx + 15, cy + 30), self._r(7), outline=white, width=max(1, int(self._r(3))), fill="")
            self.canvas.create_line(self._x(cx), self._y(cy - 13), self._x(cx), self._y(cy - 6), fill=white, width=self._r(3), arrow=tk.LAST, arrowshape=(7, 9, 3))
            self.canvas.create_line(self._x(cx), self._y(cy + 8), self._x(cx), self._y(cy + 16), fill=white, width=self._r(3), arrow=tk.LAST, arrowshape=(7, 9, 3))
        else:
            rounded_rect(self.canvas, *self._rect(cx - 30, cy - 23, cx + 30, cy + 23), self._r(5), outline=white, width=max(1, int(self._r(2.2))), fill="")
            x = cx - 24
            for line_w in [2, 5, 2, 7, 2, 3, 6, 2]:
                self.canvas.create_line(self._x(x), self._y(cy - 16), self._x(x), self._y(cy + 16), fill=white, width=max(1, int(self._r(line_w))))
                x += line_w + 2.8
            for qx, qy in [(17, -15), (25, -15), (17, -7), (25, -7), (17, 11), (25, 11), (17, 19), (25, 19)]:
                self.canvas.create_rectangle(*self._rect(cx + qx - 2.4, cy + qy - 2.4, cx + qx + 2.4, cy + qy + 2.4), fill=white, outline="")

    def _card_at(self, x: float, y: float) -> int | None:
        for index, (x1, y1, x2, y2, _item) in enumerate(self.cards):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return index
        return None

    def _content_click(self, x: float, y: float) -> bool:
        card_index = self._card_at(x, y)
        if card_index is None:
            return False
        self._open_module(self.cards[card_index][4])
        return True

    def _content_hover(self, x: float, y: float) -> bool:
        card_index = self._card_at(x, y)
        next_card = card_index if card_index is not None else -1
        if next_card != self.hover_card:
            self.hover_card = next_card
            self._draw()
        return card_index is not None

    def _open_module(self, item: ModuleItem) -> None:
        target = ROOT_DIR / item.target
        if not target.exists():
            messagebox.showerror("Module file missing", f"Missing module entry file:\n{target}")
            return
        if item.key == "engineer_design":
            self.destroy()
            from modules.engineer_design.design_window import run_engineer_design

            run_engineer_design()
            return

        subprocess.Popen([sys.executable, str(target)], cwd=str(target.parent), close_fds=True)
        self.destroy()


class ModuleWindow(BaseShell):
    def __init__(self, title: str, description: str, accent: str) -> None:
        self.description = description
        self.accent = accent
        self.hover_button = ""
        self.buttons: dict[str, tuple[float, float, float, float]] = {}
        super().__init__(title, 940, 640, 820, 560)

    def _draw_content(self) -> None:
        self.buttons.clear()
        rounded_rect(self.canvas, *self._rect(25, 67, 915, 169), self._r(16), fill=COLORS["shadow"], outline="")
        rounded_rect(self.canvas, *self._rect(22, 62, 912, 164), self._r(16), fill=COLORS["panel"], outline=COLORS["line"], width=max(1, int(self._r(1))))
        self.canvas.create_text(self._x(50), self._y(100), text=self.shell_title, fill=COLORS["text"], font=self._font(24, "bold"), anchor="w", justify="left")
        self.canvas.create_text(self._x(52), self._y(135), text=self.description, fill=COLORS["muted"], font=self._font(10), anchor="w", justify="left", width=self._r(760))

        self.buttons["home"] = self._rect(806, 88, 882, 132)
        rounded_rect(self.canvas, *self.buttons["home"], self._r(10), fill=self.accent if self.hover_button == "home" else "#ffffff", outline=self.accent, width=max(1, int(self._r(1.2))))
        self.canvas.create_text(self._x(844), self._y(110), text="Home", fill="#ffffff" if self.hover_button == "home" else self.accent, font=self._font(9, "bold"), anchor="center")

        rounded_rect(self.canvas, *self._rect(22, 184, 912, 244), self._r(14), fill=COLORS["panel"], outline=COLORS["line"], width=max(1, int(self._r(1))))
        tools = ("File Open", "Save", "Print", "Line Properties", "Shape Properties", "Settings")
        x = 44
        for label in tools:
            width = 86 if label in {"File Open", "Line Properties", "Shape Properties"} else 66
            rounded_rect(self.canvas, *self._rect(x, 200, x + width, 228), self._r(8), fill="#f8fbff", outline=COLORS["line"], width=max(1, int(self._r(1))))
            self.canvas.create_text(self._x(x + 12), self._y(214), text=label, fill=COLORS["text"], font=self._font(8), anchor="w", justify="left")
            x += width + 12

        rounded_rect(self.canvas, *self._rect(25, 266, 915, 613), self._r(16), fill=COLORS["shadow"], outline="")
        rounded_rect(self.canvas, *self._rect(22, 260, 912, 607), self._r(16), fill=COLORS["panel_soft"], outline=COLORS["line"], width=max(1, int(self._r(1))))
        self.canvas.create_text(self._x(467), self._y(416), text="Workspace container is ready.", fill=self.accent, font=self._font(18, "bold"), anchor="center")
        self.canvas.create_text(self._x(467), self._y(452), text="Real tools for this module must be built inside this module folder.", fill=COLORS["muted"], font=self._font(10), anchor="center")

    def _button_at(self, x: float, y: float) -> str:
        for name, (x1, y1, x2, y2) in self.buttons.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return name
        return ""

    def _content_click(self, x: float, y: float) -> bool:
        if self._button_at(x, y) == "home":
            self._back_to_launcher()
            return True
        return False

    def _content_hover(self, x: float, y: float) -> bool:
        button = self._button_at(x, y)
        if button != self.hover_button:
            self.hover_button = button
            self._draw()
        return bool(button)

    def _back_to_launcher(self) -> None:
        launcher = ROOT_DIR / "main.py"
        subprocess.Popen([sys.executable, str(launcher)], cwd=str(ROOT_DIR), close_fds=True)
        self.destroy()


def run_launcher() -> None:
    LauncherWindow().mainloop()


def run_module(title: str, description: str, accent: str) -> None:
    ModuleWindow(title, description, accent).mainloop()

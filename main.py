"""
QR Nova — a clean, dark-themed QR Code generator.

Features:
    - Generate QR codes from any text / URL
    - Custom foreground & background colors
    - Adjustable error correction level and QR size
    - Optional logo embedding in the center of the QR
    - Save as PNG or copy directly to clipboard (Windows)
    - Auto-saved generation history you can revisit anytime
    - Self-drawn app icon/logo (no external image files needed)

Author: Built for Sadia
"""

import io
import os
import json
import sys
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox

import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image, ImageTk, ImageDraw, ImageOps

# Clipboard support is Windows-only (via pywin32). We degrade gracefully
# on other platforms instead of crashing.
try:
    import win32clipboard
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False


# --------------------------------------------------------------------------- #
#  App constants & paths
# --------------------------------------------------------------------------- #

APP_NAME = "QR Nova"
APP_TAGLINE = "Generate. Customize. Done."

# Writable data folder in the user's home dir — works whether we're running
# as a .py script or a frozen .exe (Program Files is often read-only).
DATA_DIR = os.path.join(os.path.expanduser("~"), ".qrnova")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
ICON_PATH = os.path.join(DATA_DIR, "qrnova_icon.ico")
ICON_PNG_PATH = os.path.join(DATA_DIR, "qrnova_icon.png")

os.makedirs(HISTORY_DIR, exist_ok=True)

# --------------------------------------------------------------------------- #
#  Color palette — light, clean, teal/pink accent
# --------------------------------------------------------------------------- #

BG_MAIN = "#f4f6fa"
BG_PANEL = "#ffffff"
BG_CARD = "#ffffff"
BG_INPUT = "#eef1f7"
BORDER = "#dde1ea"

ACCENT = "#0eb8a0"        # teal
ACCENT_DARK = "#0a8f7d"
ACCENT2 = "#e0245e"        # pink

TEXT_MAIN = "#1a1d24"
TEXT_MUTED = "#6b7280"
TEXT_ON_ACCENT = "#ffffff"

FONT_FAMILY = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"


# --------------------------------------------------------------------------- #
#  Icon / logo generation (drawn with Pillow — no external assets needed)
# --------------------------------------------------------------------------- #

def generate_app_icon():
    """Draws a small QR-inspired neon logo and saves it as .ico + .png.
    Only regenerates if the files don't already exist."""
    if os.path.exists(ICON_PATH) and os.path.exists(ICON_PNG_PATH):
        return

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Rounded dark background card
    d.rounded_rectangle([6, 6, size - 6, size - 6], radius=44,
                         fill=(13, 15, 20, 255), outline=(0, 245, 212, 255), width=6)

    def finder_pattern(x, y, color):
        """Draws a QR-style finder square (the corner squares of a QR code)."""
        d.rectangle([x, y, x + 58, y + 58], outline=color, width=9)
        d.rectangle([x + 18, y + 18, x + 40, y + 40], fill=color)

    finder_pattern(26, 26, (0, 245, 212, 255))     # top-left, teal
    finder_pattern(size - 84, 26, (255, 46, 136, 255))   # top-right, pink
    finder_pattern(26, size - 84, (255, 46, 136, 255))   # bottom-left, pink

    # Small scattered data dots bottom-right, suggesting QR data cells
    dot = 14
    gap = 4
    start_x, start_y = size - 96, size - 96
    pattern = [
        (0, 0), (1, 0), (0, 1), (2, 2), (3, 1), (1, 3), (3, 3), (2, 0)
    ]
    for i, (cx, cy) in enumerate(pattern):
        color = (0, 245, 212, 255) if i % 2 == 0 else (255, 46, 136, 255)
        px = start_x + cx * (dot + gap)
        py = start_y + cy * (dot + gap)
        d.rectangle([px, py, px + dot, py + dot], fill=color)

    img.save(ICON_PNG_PATH)
    img.save(ICON_PATH, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


# --------------------------------------------------------------------------- #
#  Main Application
# --------------------------------------------------------------------------- #

class QRNovaApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.configure(bg=BG_MAIN)
        self.root.geometry("1000x660")
        self.root.minsize(940, 620)

        generate_app_icon()
        self._set_window_icon()

        # --- state ---
        self.fg_color = "#1a1d24"
        self.bg_color = "#ffffff"
        self.logo_path = None
        self.embed_logo = tk.BooleanVar(value=False)
        self.error_level = tk.StringVar(value="H (High ~30%)")
        self.box_size = tk.IntVar(value=10)
        self.current_image = None       # full-res PIL image currently shown
        self.current_image_path = None  # path of last saved/history copy

        self._build_style()
        self._build_ui()
        self._load_history()

    # ------------------------------------------------------------------- #
    #  Window icon
    # ------------------------------------------------------------------- #
    def _set_window_icon(self):
        try:
            if sys.platform.startswith("win"):
                self.root.iconbitmap(ICON_PATH)
            else:
                icon_img = tk.PhotoImage(file=ICON_PNG_PATH)
                self.root.iconphoto(True, icon_img)
                self._icon_photo_ref = icon_img  # prevent garbage collection
        except Exception:
            pass  # non-fatal — app still runs fine without a taskbar icon

    # ------------------------------------------------------------------- #
    #  Styling
    # ------------------------------------------------------------------- #
    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TCombobox",
                         fieldbackground=BG_INPUT,
                         background=BG_INPUT,
                         foreground=TEXT_MAIN,
                         arrowcolor=ACCENT,
                         bordercolor=BORDER,
                         lightcolor=BG_INPUT,
                         darkcolor=BG_INPUT)
        style.map("TCombobox", fieldbackground=[("readonly", BG_INPUT)])

        style.configure("Neon.Horizontal.TScale",
                         background=BG_PANEL, troughcolor=BG_INPUT)

        style.configure("Vertical.TScrollbar",
                         background=BG_CARD, troughcolor=BG_PANEL,
                         bordercolor=BG_PANEL, arrowcolor=ACCENT)

    def _font(self, size=10, weight="normal"):
        return (FONT_FAMILY, size, weight)

    def _make_button(self, parent, text, command, bg=ACCENT, fg=TEXT_ON_ACCENT,
                      hover_bg=None, width=None, font=None, state="normal"):
        hover_bg = hover_bg or self._lighten(bg)
        btn = tk.Button(parent, text=text, command=command,
                         bg=bg, fg=fg, activebackground=hover_bg, activeforeground=fg,
                         relief="flat", bd=0, cursor="hand2",
                         font=font or self._font(10, "bold"),
                         padx=14, pady=8, width=width, state=state)

        def on_enter(e):
            if btn["state"] != "disabled":
                btn.configure(bg=hover_bg)

        def on_leave(e):
            if btn["state"] != "disabled":
                btn.configure(bg=bg)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    @staticmethod
    def _lighten(hex_color, factor=1.15):
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        r, g, b = (min(255, int(c * factor)) for c in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ------------------------------------------------------------------- #
    #  UI Construction
    # ------------------------------------------------------------------- #
    def _build_ui(self):
        self._build_header()

        body = tk.Frame(self.root, bg=BG_MAIN)
        body.pack(fill="both", expand=True, padx=24, pady=(4, 20))
        body.columnconfigure(0, weight=5)
        body.columnconfigure(1, weight=4)
        body.rowconfigure(0, weight=1)

        self._build_left_panel(body)
        self._build_right_panel(body)

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG_MAIN)
        header.pack(fill="x", padx=24, pady=(20, 10))

        try:
            raw = Image.open(ICON_PNG_PATH).resize((46, 46), Image.LANCZOS)
            self._header_icon = ImageTk.PhotoImage(raw)
            tk.Label(header, image=self._header_icon, bg=BG_MAIN).pack(side="left", padx=(0, 12))
        except Exception:
            pass

        title_box = tk.Frame(header, bg=BG_MAIN)
        title_box.pack(side="left")
        tk.Label(title_box, text=APP_NAME, bg=BG_MAIN, fg=TEXT_MAIN,
                 font=self._font(20, "bold")).pack(anchor="w")
        tk.Label(title_box, text=APP_TAGLINE, bg=BG_MAIN, fg=TEXT_MUTED,
                 font=self._font(9)).pack(anchor="w")

        # thin neon underline for the whole header
        underline = tk.Frame(self.root, bg=ACCENT, height=2)
        underline.pack(fill="x", padx=24)

    def _card(self, parent, **pack_opts):
        card = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER,
                         highlightthickness=1)
        card.pack(**pack_opts)
        return card

    # -------------------------- LEFT: input + settings ------------------ #
    def _build_left_panel(self, parent):
        left = tk.Frame(parent, bg=BG_MAIN)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        # --- Text input card ---
        input_card = self._card(left, fill="x", pady=(0, 14))
        tk.Label(input_card, text="TEXT OR URL", bg=BG_CARD, fg=ACCENT,
                 font=self._font(9, "bold")).pack(anchor="w", padx=16, pady=(14, 4))

        text_frame = tk.Frame(input_card, bg=BG_CARD)
        text_frame.pack(fill="x", padx=16, pady=(0, 16))
        self.text_input = tk.Text(text_frame, height=5, bg=BG_INPUT, fg=TEXT_MAIN,
                                   insertbackground=ACCENT, relief="flat", bd=0,
                                   font=self._font(10), wrap="word",
                                   highlightbackground=BORDER, highlightthickness=1,
                                   padx=10, pady=10)
        self.text_input.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(text_frame, command=self.text_input.yview)
        scroll.pack(side="right", fill="y")
        self.text_input.configure(yscrollcommand=scroll.set)

        # --- Settings card ---
        settings_card = self._card(left, fill="x", pady=(0, 14))
        tk.Label(settings_card, text="CUSTOMIZE", bg=BG_CARD, fg=ACCENT,
                 font=self._font(9, "bold")).pack(anchor="w", padx=16, pady=(14, 8))

        row1 = tk.Frame(settings_card, bg=BG_CARD)
        row1.pack(fill="x", padx=16, pady=4)
        self._color_swatch_control(row1, "QR Color", "fg")
        self._color_swatch_control(row1, "Background", "bg")

        row2 = tk.Frame(settings_card, bg=BG_CARD)
        row2.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(row2, text="Error Correction", bg=BG_CARD, fg=TEXT_MUTED,
                 font=self._font(9)).pack(side="left")
        ec_combo = ttk.Combobox(row2, textvariable=self.error_level, state="readonly",
                                 width=16, font=self._font(9),
                                 values=["L (Low ~7%)", "M (Medium ~15%)",
                                         "Q (Quartile ~25%)", "H (High ~30%)"])
        ec_combo.pack(side="right")

        row3 = tk.Frame(settings_card, bg=BG_CARD)
        row3.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(row3, text="QR Size", bg=BG_CARD, fg=TEXT_MUTED,
                 font=self._font(9)).pack(side="left")
        size_scale = ttk.Scale(row3, from_=4, to=20, orient="horizontal",
                                variable=self.box_size, style="Neon.Horizontal.TScale",
                                command=lambda e: None)
        size_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))

        row4 = tk.Frame(settings_card, bg=BG_CARD)
        row4.pack(fill="x", padx=16, pady=(10, 16))
        chk = tk.Checkbutton(row4, text="Embed logo in center", variable=self.embed_logo,
                              bg=BG_CARD, fg=TEXT_MAIN, selectcolor=BG_INPUT,
                              activebackground=BG_CARD, activeforeground=TEXT_MAIN,
                              font=self._font(9), command=self._toggle_logo_button)
        chk.pack(side="left")
        self.browse_logo_btn = self._make_button(row4, "Browse...", self._browse_logo,
                                                   bg=BG_INPUT, fg=TEXT_MAIN,
                                                   hover_bg=BORDER, font=self._font(9),
                                                   state="disabled")
        self.browse_logo_btn.pack(side="right")

        self.logo_label = tk.Label(settings_card, text="No logo selected", bg=BG_CARD,
                                    fg=TEXT_MUTED, font=self._font(8), anchor="w")
        self.logo_label.pack(fill="x", padx=16, pady=(0, 14))

        # --- Generate button ---
        gen_btn = self._make_button(left, "⚡  GENERATE QR CODE", self.generate_qr,
                                     bg=ACCENT, fg=TEXT_ON_ACCENT, font=self._font(12, "bold"))
        gen_btn.pack(fill="x", ipady=8, pady=(4, 0))

    def _color_swatch_control(self, parent, label, which):
        box = tk.Frame(parent, bg=BG_CARD)
        box.pack(side="left", expand=True, fill="x", padx=(0, 10) if which == "fg" else 0)
        tk.Label(box, text=label, bg=BG_CARD, fg=TEXT_MUTED,
                 font=self._font(9)).pack(anchor="w")
        swatch = tk.Button(box, bg=self.fg_color if which == "fg" else self.bg_color,
                            relief="flat", bd=0, width=10, height=1, cursor="hand2",
                            command=lambda: self._pick_color(which))
        swatch.pack(anchor="w", pady=(4, 0), fill="x")
        if which == "fg":
            self.fg_swatch = swatch
        else:
            self.bg_swatch = swatch

    def _pick_color(self, which):
        initial = self.fg_color if which == "fg" else self.bg_color
        color = colorchooser.askcolor(color=initial, title="Choose a color")
        if color and color[1]:
            if which == "fg":
                self.fg_color = color[1]
                self.fg_swatch.configure(bg=color[1])
            else:
                self.bg_color = color[1]
                self.bg_swatch.configure(bg=color[1])

    def _toggle_logo_button(self):
        self.browse_logo_btn.configure(state="normal" if self.embed_logo.get() else "disabled")

    def _browse_logo(self):
        path = filedialog.askopenfilename(
            title="Select a logo image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if path:
            self.logo_path = path
            self.logo_label.configure(text=os.path.basename(path), fg=ACCENT)

    # -------------------------- RIGHT: preview + history ----------------- #
    def _build_right_panel(self, parent):
        right = tk.Frame(parent, bg=BG_MAIN)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)

        # --- Preview card ---
        preview_card = self._card(right, fill="x", pady=(0, 14))
        tk.Label(preview_card, text="PREVIEW", bg=BG_CARD, fg=ACCENT,
                 font=self._font(9, "bold")).pack(anchor="w", padx=16, pady=(14, 8))

        self.preview_frame = tk.Frame(preview_card, bg=BG_INPUT, width=260, height=260,
                                       highlightbackground=BORDER, highlightthickness=1)
        self.preview_frame.pack(padx=16, pady=(0, 12))
        self.preview_frame.pack_propagate(False)

        self.preview_label = tk.Label(self.preview_frame, text="Your QR code\nwill appear here",
                                       bg=BG_INPUT, fg=TEXT_MUTED, font=self._font(10),
                                       justify="center")
        self.preview_label.pack(expand=True)

        btn_row = tk.Frame(preview_card, bg=BG_CARD)
        btn_row.pack(fill="x", padx=16, pady=(0, 16))
        self.save_btn = self._make_button(btn_row, "Save PNG", self.save_png,
                                           bg=ACCENT, fg=TEXT_ON_ACCENT, state="disabled")
        self.save_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        clip_state = "disabled"
        self.copy_btn = self._make_button(btn_row, "Copy to Clipboard", self.copy_to_clipboard,
                                           bg=ACCENT2, fg="#ffffff",
                                           hover_bg=self._lighten(ACCENT2), state=clip_state)
        self.copy_btn.pack(side="left", expand=True, fill="x", padx=(6, 0))

        if not HAS_CLIPBOARD:
            tk.Label(preview_card, text="Clipboard copy needs: pip install pywin32",
                     bg=BG_CARD, fg=TEXT_MUTED, font=self._font(8)).pack(padx=16, pady=(0, 12))

        # --- History card ---
        history_card = self._card(right, fill="both", expand=True)
        head = tk.Frame(history_card, bg=BG_CARD)
        head.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(head, text="HISTORY", bg=BG_CARD, fg=ACCENT,
                 font=self._font(9, "bold")).pack(side="left")
        tk.Button(head, text="Clear", command=self._clear_history, bg=BG_CARD, fg=TEXT_MUTED,
                  relief="flat", bd=0, cursor="hand2", font=self._font(8, "underline")
                  ).pack(side="right")

        list_frame = tk.Frame(history_card, bg=BG_CARD)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.history_list = tk.Listbox(list_frame, bg=BG_INPUT, fg=TEXT_MAIN,
                                        selectbackground=ACCENT, selectforeground=TEXT_ON_ACCENT,
                                        relief="flat", bd=0, font=self._font(9),
                                        highlightbackground=BORDER, highlightthickness=1,
                                        activestyle="none")
        self.history_list.pack(side="left", fill="both", expand=True)
        hist_scroll = ttk.Scrollbar(list_frame, command=self.history_list.yview)
        hist_scroll.pack(side="right", fill="y")
        self.history_list.configure(yscrollcommand=hist_scroll.set)
        self.history_list.bind("<Double-Button-1>", self._load_history_item)

    # ------------------------------------------------------------------- #
    #  QR Generation
    # ------------------------------------------------------------------- #
    def _error_correction_const(self):
        mapping = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M,
                   "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}
        return mapping[self.error_level.get()[0]]

    def generate_qr(self):
        text = self.text_input.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning(APP_NAME, "Please enter some text or a URL first.")
            return

        try:
            qr = qrcode.QRCode(
                version=None,
                error_correction=self._error_correction_const(),
                box_size=self.box_size.get(),
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color=self.fg_color, back_color=self.bg_color).convert("RGB")

            if self.embed_logo.get() and self.logo_path:
                img = self._embed_logo(img, self.logo_path)

            self.current_image = img
            self._update_preview(img)
            self._auto_save_history(text, img)

            self.save_btn.configure(state="normal")
            if HAS_CLIPBOARD:
                self.copy_btn.configure(state="normal")

        except Exception as e:
            messagebox.showerror(APP_NAME, f"Couldn't generate the QR code:\n{e}")

    @staticmethod
    def _embed_logo(qr_img, logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        w, h = qr_img.size
        logo_size = int(w * 0.22)
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

        # White backing so the logo doesn't break the QR's contrast/scannability
        pad = 8
        backing = Image.new("RGB", (logo_size + pad * 2, logo_size + pad * 2), "white")
        bx = (w - backing.width) // 2
        by = (h - backing.height) // 2
        qr_img.paste(backing, (bx, by))
        qr_img.paste(logo, (bx + pad, by + pad), mask=logo)
        return qr_img

    def _update_preview(self, img):
        preview = ImageOps.contain(img, (240, 240))
        self._preview_photo = ImageTk.PhotoImage(preview)
        self.preview_label.configure(image=self._preview_photo, text="")

    # ------------------------------------------------------------------- #
    #  Save / Clipboard
    # ------------------------------------------------------------------- #
    def save_png(self):
        if not self.current_image:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            initialfile=f"qrcode_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        if path:
            self.current_image.save(path)
            messagebox.showinfo(APP_NAME, "QR code saved successfully!")

    def copy_to_clipboard(self):
        if not self.current_image or not HAS_CLIPBOARD:
            return
        try:
            output = io.BytesIO()
            self.current_image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # strip the 14-byte BMP file header
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            messagebox.showinfo(APP_NAME, "Copied to clipboard!")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Couldn't copy to clipboard:\n{e}")

    # ------------------------------------------------------------------- #
    #  History
    # ------------------------------------------------------------------- #
    def _load_history_data(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _save_history_data(self, data):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _auto_save_history(self, text, img):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qr_{timestamp}.png"
        filepath = os.path.join(HISTORY_DIR, filename)
        img.save(filepath)

        data = self._load_history_data()
        snippet = text if len(text) <= 40 else text[:37] + "..."
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text": snippet,
            "filepath": filepath,
        }
        data.insert(0, entry)
        data = data[:100]  # cap history size
        self._save_history_data(data)
        self._refresh_history_listbox(data)

    def _load_history(self):
        data = self._load_history_data()
        self._refresh_history_listbox(data)

    def _refresh_history_listbox(self, data):
        self.history_list.delete(0, "end")
        self._history_data = data
        for entry in data:
            self.history_list.insert("end", f"{entry['timestamp']}  |  {entry['text']}")

    def _load_history_item(self, event):
        selection = self.history_list.curselection()
        if not selection:
            return
        entry = self._history_data[selection[0]]
        path = entry["filepath"]
        if not os.path.exists(path):
            messagebox.showwarning(APP_NAME, "That history file no longer exists on disk.")
            return
        img = Image.open(path).convert("RGB")
        self.current_image = img
        self._update_preview(img)
        self.save_btn.configure(state="normal")
        if HAS_CLIPBOARD:
            self.copy_btn.configure(state="normal")

    def _clear_history(self):
        if not self._history_data:
            return
        if not messagebox.askyesno(APP_NAME, "Clear all history? This deletes saved history images too."):
            return
        for entry in self._history_data:
            try:
                if os.path.exists(entry["filepath"]):
                    os.remove(entry["filepath"])
            except OSError:
                pass
        self._save_history_data([])
        self._refresh_history_listbox([])


# --------------------------------------------------------------------------- #
#  Entry point
# --------------------------------------------------------------------------- #

def main():
    root = tk.Tk()
    app = QRNovaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
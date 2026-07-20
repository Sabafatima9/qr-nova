<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00F5D4,100:FF2E88&height=220&section=header&text=QR%20Nova%20%E2%9A%A1&fontSize=50&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Dark%20Themed%20%7C%20QR%20Generator%20%7C%20Python&descAlignY=55&descSize=18" width="100%"/>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=2500&pause=500&color=00F5D4&center=true&vCenter=true&width=700&lines=%E2%9A%A1+Generate+QR+Codes+Instantly!;%F0%9F%8E%A8+Custom+Colors+%26+Embedded+Logos;%F0%9F%92%BE+Save+as+PNG+or+Copy+to+Clipboard;%F0%9F%95%92%EF%B8%8F+Auto-Saved+Generation+History" alt="Typing SVG" />

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-00F5D4?style=for-the-badge&logo=python&logoColor=white)
![qrcode](https://img.shields.io/badge/qrcode-Pillow-FF2E88?style=for-the-badge&logo=qr-code&logoColor=white)
![PyInstaller](https://img.shields.io/badge/Build-PyInstaller-3776AB?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</div>

---

## 🎯 Overview

**QR Nova** is a sleek, dark-themed **QR Code Generator** built entirely in **Python** using **Tkinter**. Type in any text or URL and instantly generate a fully customizable QR code — pick your own colors, error correction level, and even embed a logo right in the center. Save your codes as PNG, copy them straight to your clipboard, and revisit anything you've generated with the built-in history panel.

---

## 🎬 App Preview

<div align="center">

| 🏠 Main Window | ⚡ Generated QR | 🖼️ Logo Embed |
|:---:|:---:|:---:|
| <img src="screenshots/main_window.png" width="240"/> | <img src="screenshots/qr_preview.png" width="240"/> | <img src="screenshots/logo_embed.png" width="240"/> |

| 🎨 Color Customization | 🕘 History Panel |
|:---:|:---:|
| <img src="screenshots/color_picker.png" width="240"/> | <img src="screenshots/history_panel.png" width="240"/> |

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

### ⚡ Core Generation
- 📝 Text / URL → QR code, instantly
- 🎨 Custom foreground & background colors
- 🛡️ Adjustable error correction (L / M / Q / H)
- 📏 Adjustable QR size
- 🖼️ Optional logo embedding, center-aligned

</td>
<td width="50%" valign="top">

### 💾 Workflow & Experience
- 💾 Save as PNG anywhere on disk
- 📋 One-click copy to clipboard (Windows)
- 🕘 Auto-saved history, double-click to reload
- 🌌 Custom-drawn neon app icon — no external assets
- 🖥️ Clean, unique dark UI with neon accents

</td>
</tr>
</table>

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=rect&color=0:00F5D4,100:FF2E88&height=3&width=100%"/>
</div>

## 🛠️ Tech Stack

<div align="center">
<img src="https://skillicons.dev/icons?i=python,git,github" />
</div>

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| GUI Framework | Tkinter (custom dark theme, hand-rolled widgets) |
| QR Engine | `qrcode` |
| Image Processing | `Pillow` (logo embed, icon generation, previews) |
| Clipboard | `pywin32` (Windows) |
| Packaging | `PyInstaller` (.exe build) |

---

## 🚀 Getting Started

**1. Clone the repo**
```bash
git clone https://github.com/Sabafatima9/qr-nova.git
cd qr-nova
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the app**
```bash
python main.py
```

> **Tip:** double-click any entry in the History panel to reload that QR code back into the preview.

---

## 📦 Building a Standalone .exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "QRNova" main.py
```

Your executable will be in `dist/QRNova.exe` — no Python install required to run it.

---

## 🏗️ Project Structure

```
qr-nova/
├── main.py               # 🎮 Entry point — full app logic
├── requirements.txt       # Dependencies
├── screenshots/           # README preview images
│   ├── main_window.png
│   ├── qr_preview.png
│   ├── logo_embed.png
│   ├── color_picker.png
│   └── history_panel.png
└── README.md              # 📖 You're here
```

> The app's own logo/icon and generation history are stored automatically in `~/.qrnova/` at runtime — no assets folder needed for that part.

---

## 🧠 How It Works

| Concept | Implementation |
|---|---|
| **QR Generation** | `qrcode.QRCode()` with configurable `error_correction`, `box_size`, and `border` |
| **Custom Colors** | `make_image(fill_color=..., back_color=...)` from user-picked hex values |
| **Logo Embedding** | Pillow resizes logo to ~22% of QR width, pastes on a white backing at center for scan reliability |
| **Clipboard Copy** | Image converted to raw DIB bytes via `BMP` encoding, pushed with `win32clipboard` |
| **History** | Every generation auto-saves a PNG + JSON entry to `~/.qrnova/history/` |

---

## 📈 Roadmap

- [ ] Batch generation from a CSV list of texts/URLs
- [ ] Export as SVG / PDF in addition to PNG
- [ ] Built-in scan test to verify readability after logo embedding
- [ ] Drag-and-drop text/CSV files onto the window
- [ ] Remember last-used colors & settings between sessions

---

<div align="center">

### ⭐ Star this repo if QR Nova made your workflow easier!

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:FF2E88,100:00F5D4&height=120&section=footer"/>

</div>

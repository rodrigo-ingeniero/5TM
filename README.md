# 5TM 

### Terminal Tiling Window Manager 📟

**5TM** is a keyboard-driven tiling window manager that runs entirely in the terminal.
Inspired by Hyprland, it brings dynamic layouts, animated splits, and a minimal workflow to a pure TUI environment.

---

## ✨ Features

* 🪟 Tiling window management inside the terminal
* 🎦 Animated splits and transitions
* ⌨️ Fully keyboard-driven workflow
* 🌲 Tree-based layout system
* ⚡ Fast window switching
* 🪶 Lightweight

---

## 🤷‍♂️ What is 5TM?

**5TM** stands for:

> **5 Terminal Manager**

* **5** → up to 5 windows (design constraint for simplicity and clarity)
* **Terminal** → runs fully in a terminal
* **Manager** → manages layouts, focus, and window lifecycle

---

## 🚀 Getting Started

### Requirements

* Python 3.10+
* A Unix-like environment (Linux, macOS)
* A compatible terminal (zsh, xterm, kitty, alacritty…)
* pyte and psutil external dependences are needed (install with 'pip install pyte psutil')

### Run

```bash
python main.py
```
---

## ⌨️ Keybindings

| Key       | Action              |
| --------- | ------------------- |
| `Alt + h` | Split horizontally  |
| `Alt + v` | Split vertically    |
| `Alt + d` | Close active window |
| `Alt + s` | Focus next window   |
| `Alt + a` | Focus previous win. |

(On MacBook PCs use "option" key instead of "Alt)

---

## 🏗️ Architecture

5TM is built within this architecture:

* main.py * 

This separation allows clean logic between layout, rendering, and input handling.

---

## 🎯 Goals

* Explore terminal-based UI systems
* Recreate tiling WM concepts in a TUI
* Keep everything minimal, fast, and hackable

---

## 🛠️ Roadmap

* [ ] Directional focus (like i3 / Hyprland)
* [ ] Resizing windows
* [ ] Mouse support
* [ ] Configurable keybindings
* [ ] Plugin / extension system

---

## 📸 Preview

*(Add screenshots or GIFs here — highly recommended)*

---

## 🤝 Contributing

Contributions, ideas, and feedback are welcome.
Feel free to open issues or submit pull requests.

---

## 📄 License

MIT License (or your preferred license)

---

## 💡 Inspiration

* Hyprland
* i3 / sway
* tmux
* Neovim

---

## ⚡ Final Note

5TM is an experiment in pushing the limits of what a terminal interface can do.
A window manager — without leaving the terminal.


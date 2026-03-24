# 🎯 Focus Mode App

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](#)

A powerful desktop application for Linux (optimized for Wayland) that blocks distracting apps and web apps during study or work sessions. Built with Python and PyQt6.

## ✨ Features

- 🎯 **Native App Blocking** - Automatically terminates specific application processes.
- 🌐 **Web App Blocking** - Blocks browser-based web apps (Chrome, Firefox, etc.) via URL or ID.
- ⏱️ **Focus Lock** - Set a timer or target time to prevent premature disabling of focus mode.
- 🔄 **Session Restore** - Automatically tracks killed applications and can restart them when focus mode ends.
- 🎨 **Modern GUI** - Clean user interface built with PyQt6.
- ⌨️ **CLI Support** - Full command-line interface (`study-mode`) for quick terminal access.
- 🖱️ **System Tray** - Convenient system tray icon for quick toggling.
- 💾 **Data Persistence** - Automatically saves your blocklist and configurations.

---

## 📋 Prerequisites

- **Python 3.10+**
- **Linux Environment** (Tested heavily on Wayland, X11 fallback available)

---

## 🚀 Installation & Usage

### 1. Install from Source

```bash
git clone https://github.com/gorlix/focus-mode-app-linux.git
cd focus-mode-app-linux
pip install -e .
```

### 2. Run the Application

**To start the GUI:**

```bash
focus-mode-app
```

*(Or run `python -m focus_mode_app.main`)*

**To use the Command Line Interface (CLI):**

```bash
study-mode --help
study-mode list
study-mode add firefox app
study-mode start
```

*(Or run `python -m focus_mode_app.cli`)*

---

## 📖 User Guide

### Using the GUI

1. Launch `focus-mode-app`.
2. Add apps you want to block by selecting Native App or Webapp and typing the name/URL.
3. Click **"▶️ ACTIVATE STUDY MODE"**.
4. The app will quietly run in the background (or in the system tray) and instantly close any matching processes.

### Focus Lock

Prevent yourself from cheating! You can lock the focus mode for a specific duration (e.g., 25 minutes) or until a specific time of day. While locked, you cannot turn off the blocking.

### Session Restore

When enabled, the app tracks every process it kills. When you disable Focus Mode, it can automatically restore those applications so you can pick up exactly where you left off.

---

## 🏗️ Architecture & Development

If you are interested in contributing, modifying the code, or understanding how `focus-mode-app` works under the hood, please refer to our internal documentation:

- [ARCHITECTURE.md](ARCHITECTURE.md): Detailed overview of the core loops, process termination, and Wayland considerations.
- [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md): Step-by-step instructions for setting up a local development environment, running tests, and linting.
- [CONTRIBUTING.md](CONTRIBUTING.md): Guidelines for submitting pull requests and reporting bugs.

---

## 🤝 Credits

- **Author:** Alessandro Gorla (gorlix)
- **License:** MIT
- **Framework GUI:** ttkbootstrap / PyQt6
- **Process Management:** psutil

# Development Setup

This guide will help you set up your local environment for developing Focus Mode App.

## Prerequisites

- Python 3.10 or higher
- Linux OS (Tested primarily on Wayland / KDE Plasma / GNOME)
- Git

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/gorlix/focus-mode-app-linux.git
cd focus-mode-app-linux
```

### 2. Create a virtual environment

It is highly recommended to use a virtual environment to isolate the dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

Install the package in editable mode along with all development and GUI dependencies:

```bash
pip install -e ".[dev,gui]"
```

*(This installs `pytest`, `pytest-cov`, `black`, `flake8`, and the `PyQt6` GUI components).*

### 4. Running the application

You can now run the application locally using the installed CLI entry points:

**Run the GUI app:**

```bash
focus-mode-app
```

*(Alternative: `python -m focus_mode_app.main`)*

**Run the CLI app:**

```bash
study-mode
```

*(Alternative: `python -m focus_mode_app.cli`)*

## Running Tests and Linting

We enforce code quality using `flake8` and `black`. If you submit a PR, please make sure your code passes these checks.

**Format code (Black):**

```bash
black focus_mode_app/
```

**Lint code (Flake8):**

```bash
flake8 focus_mode_app/
```

**Run tests (Pytest):**

```bash
pytest focus_mode_app/
```

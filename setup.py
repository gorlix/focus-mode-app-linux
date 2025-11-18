#!/usr/bin/env python3
"""
Setup per Focus Mode App - PyPI Distribution
"""

from setuptools import setup, find_packages
from pathlib import Path

# Leggi README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    # Metadata
    name="focus-mode-app",
    version="1.0.2",
    description="Focus Mode App - Linux app blocker with session restore and focus lock",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Alessandro Gorla (gorlix)",
    author_email="ale.gorla2002@gmail.com",
    url="https://github.com/gorlix/focus-mode-app-linux",
    project_urls={
        "Bug Tracker": "https://github.com/gorlix/focus-mode-app-linux/issues",
        "Documentation": "https://github.com/gorlix/focus-mode-app-linux/blob/main/README.md",
        "Source Code": "https://github.com/gorlix/focus-mode-app-linux",
    },

    # License
    license="MIT",

    # Classificazione
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Topic :: Desktop Environment",
    ],

    # Packages
    packages=find_packages(exclude=["tests", "docs", "data"]),

    # Entry Points (comandi CLI)
    entry_points={
        'console_scripts': [
            'focus-mode-app=focus_mode_app.main:main',
            'study-mode=focus_mode_app.cli:main',
        ],
    },

    # Python Version
    python_requires=">=3.10",

    # Dependencies
    install_requires=[
        "psutil>=5.8.0",
        "ttkbootstrap>=1.6.0",
        "Pillow>=9.0.0",
        "PyQt6>=6.0.0",
        "rich>=13.0.0",
    ],

    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "gui": ["PyQt6>=6.0.0"],
    },

    # Include extra files
    include_package_data=True,
    package_data={
        "focus_mode_app": ["data/.gitkeep"],
    },

    # Metadata
    keywords="focus blocker productivity linux wayland",
    zip_safe=False,
)

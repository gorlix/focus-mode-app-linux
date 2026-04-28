"""
PyInstaller runtime hook — fix TCL_LIBRARY / TK_LIBRARY inside AppImage.

When frozen, PyInstaller sets sys._MEIPASS but may not export TCL_LIBRARY
before the Tcl C library initialises (especially on non-Ubuntu distros where
the compile-time Tcl path does not exist).  Without a correct TCL_LIBRARY,
Tcl cannot find 'package require msgcat' and ttkbootstrap crashes.

This hook runs before any user import so the env vars are in place when
_tkinter.so is loaded.
"""

import os
import sys

if getattr(sys, "frozen", False):
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        if "TCL_LIBRARY" not in os.environ:
            for name in ("tcl8.6", "tcl9.0", "_tcl_data"):
                path = os.path.join(meipass, name)
                if os.path.isdir(path):
                    os.environ["TCL_LIBRARY"] = path
                    break

        if "TK_LIBRARY" not in os.environ:
            for name in ("tk8.6", "tk9.0", "_tk_data"):
                path = os.path.join(meipass, name)
                if os.path.isdir(path):
                    os.environ["TK_LIBRARY"] = path
                    break

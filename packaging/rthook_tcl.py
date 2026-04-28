"""
PyInstaller runtime hook — environment fixes for AppImage on non-Ubuntu distros.

Runs before any user import, so all env vars are in place before _tkinter.so
and the requests/websocket-client SSL stack are initialised.

Fixes applied when sys.frozen is True:
1. TCL_LIBRARY / TK_LIBRARY — point to bundled Tcl/Tk scripts so that
   ttkbootstrap's msgcat localization finds ::msgcat::mcmset.
2. SSL_CERT_FILE / REQUESTS_CA_BUNDLE — use the system CA bundle so HTTPS
   and WSS connections work with any certificate, not just those in the
   (possibly outdated) certifi bundle compiled on the build host.
"""

import os
import sys

if getattr(sys, "frozen", False):
    meipass = getattr(sys, "_MEIPASS", "")

    # ── Tcl / Tk ─────────────────────────────────────────────────────────────
    if meipass:
        if "TCL_LIBRARY" not in os.environ:
            for name in ("_tcl_data", "tcl8.6", "tcl9.0"):
                path = os.path.join(meipass, name)
                if os.path.isdir(path):
                    os.environ["TCL_LIBRARY"] = path
                    break

        if "TK_LIBRARY" not in os.environ:
            for name in ("_tk_data", "tk8.6", "tk9.0"):
                path = os.path.join(meipass, name)
                if os.path.isdir(path):
                    os.environ["TK_LIBRARY"] = path
                    break

    # ── SSL CA bundle ─────────────────────────────────────────────────────────
    if "SSL_CERT_FILE" not in os.environ:
        for _bundle in (
            "/etc/ssl/certs/ca-certificates.crt",  # Debian / Ubuntu / Arch
            "/etc/pki/tls/certs/ca-bundle.crt",  # RHEL / CentOS / Fedora
            "/etc/ssl/cert.pem",  # Alpine / macOS / FreeBSD
        ):
            if os.path.isfile(_bundle):
                os.environ["SSL_CERT_FILE"] = _bundle
                os.environ["REQUESTS_CA_BUNDLE"] = _bundle
                break

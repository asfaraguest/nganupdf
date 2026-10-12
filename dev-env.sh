#!/usr/bin/env bash
# Env tkinter portable TANPA sudo (khusus dev Linux ini).
# .deb diunduh via `apt-get download` lalu diekstrak ke /tmp/opencode/tklocal/root.
# Pakai: source dev-env.sh
TKROOT=/tmp/opencode/tklocal/root
export PYTHONPATH="$TKROOT/usr/lib/python3.12:$TKROOT/usr/lib/python3.12/lib-dynload"
export LD_LIBRARY_PATH="$TKROOT/usr/lib/x86_64-linux-gnu:$TKROOT/usr/lib"
export TCL_LIBRARY="$TKROOT/usr/share/tcltk/tcl8.6"
export TK_LIBRARY="$TKROOT/usr/share/tcltk/tk8.6"

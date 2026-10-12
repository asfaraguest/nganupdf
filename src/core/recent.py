"""Recent files portable: data/recent.json sebelah exe. Headless-safe."""
from __future__ import annotations

import json
import os
import sys
import time

MAX_ITEMS = 10


def _root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.abspath(os.path.join(here, "..", ".."))


def _path() -> str:
    d = os.path.join(_root(), "data")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "recent.json")


def load() -> list[dict]:
    try:
        with open(_path(), encoding="utf-8") as f:
            items = json.load(f)
            return [x for x in items if isinstance(x, dict) and x.get("path")]
    except Exception:
        return []


def add(tool: str, path: str) -> list[dict]:
    """Catat hasil sukses. Return list terbaru (max 10, teratas paling baru)."""
    if not path:
        return load()
    items = [x for x in load() if x.get("path") != path]
    items.insert(0, {"tool": tool, "path": path, "time": int(time.time())})
    items = items[:MAX_ITEMS]
    try:
        with open(_path(), "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return items


def clear() -> None:
    try:
        os.remove(_path())
    except OSError:
        pass

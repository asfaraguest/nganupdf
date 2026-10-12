"""Settings portable: selalu di folder data/ sebelah exe, bukan %APPDATA%."""
import json
import os
import sys


def resource_path(rel: str) -> str:
    """Path aset read-only (icon, dsb): _MEIPASS saat frozen, repo saat dev."""
    base = getattr(sys, "_MEIPASS", None) or _root()
    return os.path.join(base, rel)


def _root() -> str:
    # src/core/settings.py -> pdf-tool/
    here = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.abspath(os.path.join(here, "..", ".."))


def data_dir() -> str:
    d = os.path.join(_root(), "data")
    os.makedirs(d, exist_ok=True)
    return d


def settings_path() -> str:
    return os.path.join(data_dir(), "settings.json")


DEFAULTS = {"theme": "darkly", "last_dir": "", "language": "id"}


def load() -> dict:
    try:
        with open(settings_path(), encoding="utf-8") as f:
            s = json.load(f)
            return {**DEFAULTS, **s}
    except Exception:
        return dict(DEFAULTS)


def save(s: dict) -> None:
    try:
        with open(settings_path(), "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

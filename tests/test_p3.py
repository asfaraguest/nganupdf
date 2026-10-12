"""Test P3: recent-files core (headless)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core import recent

# isolasi: arahkan _path ke tmp via monkeypatch sederhana
import core.recent as R

TMP = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(TMP, exist_ok=True)
R._path = lambda: os.path.join(TMP, "recent-test.json")  # noqa: E731
try:
    os.remove(os.path.join(TMP, "recent-test.json"))
except OSError:
    pass


def main():
    assert R.load() == [], "harus kosong awal"
    R.add("Merge", "/tmp/a.pdf")
    R.add("Split", "/tmp/b.pdf")
    items = R.load()
    assert len(items) == 2 and items[0]["path"] == "/tmp/b.pdf", "urutan LIFO gagal"
    R.add("Merge", "/tmp/a.pdf")  # duplikat naik ke atas, tidak ganda
    items = R.load()
    assert len(items) == 2 and items[0]["path"] == "/tmp/a.pdf", "dedup gagal"
    for i in range(15):
        R.add("T", f"/tmp/f{i}.pdf")
    assert len(R.load()) == 10, "batas 10 gagal"
    R.clear()
    assert R.load() == [], "clear gagal"
    print("TEST P3 LOLOS")


if __name__ == "__main__":
    main()

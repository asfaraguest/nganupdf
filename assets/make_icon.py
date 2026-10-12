"""Generate assets/icon.png + icon.ico (butuh Pillow saja, headless OK).

    python3 assets/make_icon.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # linux dev
    "C:/Windows/Fonts/segoeuib.ttf",  # windows
]


def _font(size: int):
    for p in CANDIDATES:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main():
    S = 256
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([28, 20, 228, 236], radius=28, fill=(38, 86, 160, 255))
    d.rounded_rectangle([28, 20, 228, 90], radius=28, fill=(56, 120, 210, 255))
    d.rounded_rectangle([28, 62, 228, 90], radius=0, fill=(56, 120, 210, 255))
    d.rectangle([120, 20, 160, 90], fill=(200, 220, 245, 255))
    d.text((72, 96), "N", font=_font(96), fill=(255, 255, 255, 255))
    d.rectangle([52, 196, 204, 206], fill=(255, 255, 255, 220))
    d.rectangle([52, 200, 160, 210], fill=(255, 255, 255, 160))
    im.save(os.path.join(HERE, "icon.png"))
    im.save(os.path.join(HERE, "icon.ico"),
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("icon.png + icon.ico OK")


if __name__ == "__main__":
    main()

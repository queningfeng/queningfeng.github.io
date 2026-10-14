#!/usr/bin/env python3
"""Generate the avatar placeholder and the favicon set for the homepage.

Everything here is a *placeholder* built from the initials "NQ" so the site
looks finished out of the box. Replace images/avatar.jpg (and re-run this script
with --from-avatar if you want the favicons to match your own photo) whenever you
have a real portrait.

Usage:
    python tools/generate_images.py
"""
from __future__ import annotations

import argparse
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMAGES = ROOT / "images"

BRAND = (0, 54, 159)          # #00369f, the same blue the theme uses for badges
BRAND_DARK = (0, 26, 82)
WHITE = (255, 255, 255)

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        path = pathlib.Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def centered_text(size: int, text: str, font_ratio: float = 0.46):
    """Return (x, y) that visually centres `text` in a size x size canvas."""
    font = load_font(int(size * font_ratio))
    # Use a scratch image to measure the text box.
    scratch = ImageDraw.Draw(Image.new("RGB", (size, size)))
    left, top, right, bottom = scratch.textbbox((0, 0), text, font=font)
    x = (size - (right - left)) / 2 - left
    y = (size - (bottom - top)) / 2 - top
    return font, (x, y)


def gradient_square(size: int) -> Image.Image:
    """Diagonal blue gradient used as the icon background."""
    image = Image.new("RGB", (size, size), BRAND)
    draw = ImageDraw.Draw(image)
    for y in range(size):
        for_x = y / max(size - 1, 1)
        colour = tuple(
            int(BRAND[i] + (BRAND_DARK[i] - BRAND[i]) * for_x) for i in range(3)
        )
        draw.line([(0, y), (size, y)], fill=colour)
    return image


def make_icon(size: int, rounded: bool = True) -> Image.Image:
    image = gradient_square(size)
    if rounded:
        # Rounded-square mask, like a modern app icon.
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255
        )
        background = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        background.paste(image, (0, 0), mask)
        image = background
    else:
        image = image.convert("RGBA")

    draw = ImageDraw.Draw(image)
    font, (x, y) = centered_text(size, "NQ")
    draw.text((x, y), "NQ", font=font, fill=WHITE)
    return image


def make_avatar(size: int = 512) -> Image.Image:
    """A soft circular placeholder portrait."""
    image = Image.new("RGB", (size, size), WHITE)
    draw = ImageDraw.Draw(image)
    for y in range(size):
        ratio = y / max(size - 1, 1)
        colour = tuple(
            int(BRAND[i] + (BRAND_DARK[i] - BRAND[i]) * ratio) for i in range(3)
        )
        draw.line([(0, y), (size, y)], fill=colour)

    font, (x, y) = centered_text(size, "NQ", font_ratio=0.40)
    draw.text((x, y), "NQ", font=font, fill=WHITE)
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-avatar",
        action="store_true",
        help="build the favicons from images/avatar.jpg instead of the initials mark",
    )
    args = parser.parse_args()

    IMAGES.mkdir(parents=True, exist_ok=True)

    avatar_path = IMAGES / "avatar.jpg"
    if not args.from_avatar:
        make_avatar(512).save(avatar_path, "JPEG", quality=92, optimize=True)
        print(f"wrote {avatar_path.relative_to(ROOT)} (placeholder)")

    if args.from_avatar:
        if not avatar_path.exists():
            raise SystemExit(f"{avatar_path} not found")
        source = Image.open(avatar_path).convert("RGBA")
        side = min(source.size)
        left = (source.width - side) // 2
        top = (source.height - side) // 2
        source = source.crop((left, top, left + side, top + side))
        base = source
    else:
        base = None

    raster_targets = {
        "favicon-16x16.png": 16,
        "favicon-32x32.png": 32,
        "apple-touch-icon.png": 180,
        "android-chrome-192x192.png": 192,
        "android-chrome-512x512.png": 512,
    }
    for name, size in raster_targets.items():
        if base is not None:
            icon = base.resize((size, size), Image.LANCZOS)
        else:
            icon = make_icon(size)
        path = IMAGES / name
        icon.save(path, "PNG", optimize=True)
        print(f"wrote {path.relative_to(ROOT)} ({size}x{size})")

    # Multi-resolution .ico, the file browsers actually ask for by name.
    if base is not None:
        ico_sizes = [(16, 16), (32, 32), (48, 48)]
        icon_set = [base.resize(size, Image.LANCZOS) for size in ico_sizes]
        icon_set[0].save(
            IMAGES / "favicon.ico", sizes=[s for s in ico_sizes]
        )
    else:
        make_icon(256, rounded=False).save(
            IMAGES / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)]
        )
    print(f"wrote {(IMAGES / 'favicon.ico').relative_to(ROOT)}")


if __name__ == "__main__":
    main()

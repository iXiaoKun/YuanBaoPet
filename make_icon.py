"""
Build yuanbao.ico (multi-size Windows icon) from a sprite frame.

Run:  python make_icon.py                 # transparent background (default)
      python make_icon.py --style outline # transparent + dark outline (best contrast)
      python make_icon.py --style tile    # warm rounded tile behind the dog

Then: build_exe.bat picks up yuanbao.ico automatically (--icon + bundled).

Want your own picture instead? Replace yuanbao.ico with any .ico that contains
16/24/32/48/64/128/256 px images and rebuild. The tray / window icon follows the
same file.
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
SPRITES = os.path.join(BASE, "sprites")
OUT_PATH = os.path.join(BASE, "yuanbao.ico")

# Source frame: the idle pose reads best at small sizes (no hearts to muddy 16px)
SOURCE = os.path.join(SPRITES, "yuanbao_idle_0_4x.png")

SIZES = [16, 24, 32, 48, 64, 128, 256]

STYLES = ("transparent", "outline", "tile")

# Warm tile so the white dog stays visible on light and dark taskbars
TILE_TOP = (255, 205, 120)
TILE_BOTTOM = (240, 150, 60)
OUTLINE_COLOR = (72, 52, 34)
MARGIN = 0.05  # share of the canvas kept free around the dog


def rounded_tile(size):
    """Rounded square with a soft vertical gradient."""
    gradient = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(gradient)
    for y in range(size):
        t = y / max(1, size - 1)
        color = tuple(
            int(TILE_TOP[i] + (TILE_BOTTOM[i] - TILE_TOP[i]) * t) for i in range(3)
        )
        draw.line([(0, y), (size, y)], fill=color + (255,))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255
    )

    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tile.paste(gradient, (0, 0), mask)
    return tile


def _outline_width(size):
    """Keep the outline visually one pixel wide at every size."""
    if size <= 32:
        return 1
    if size <= 96:
        return 2
    return 3


def _scaled_dog(dog, size):
    inner = max(1, int(size * (1 - 2 * MARGIN)))
    width, height = dog.size
    scale = min(inner / width, inner / height)
    return dog.resize(
        (max(1, round(width * scale)), max(1, round(height * scale))),
        Image.NEAREST,
    )


def render(size, dog, style="transparent"):
    """One icon size in the requested style."""
    canvas = rounded_tile(size) if style == "tile" else Image.new(
        "RGBA", (size, size), (0, 0, 0, 0)
    )
    scaled = _scaled_dog(dog, size)
    x = (size - scaled.size[0]) // 2
    y = size - scaled.size[1] - int(size * MARGIN * 0.6)

    if style == "outline":
        # Dilated silhouette behind the dog: keeps a white dog readable on a
        # white Explorer background while the canvas stays transparent.
        width = _outline_width(size)
        grown = scaled.getchannel("A").filter(ImageFilter.MaxFilter(2 * width + 1))
        ring = Image.new("RGBA", scaled.size, OUTLINE_COLOR + (0,))
        ring.putalpha(grown)
        canvas.alpha_composite(ring, (x, y))

    canvas.alpha_composite(scaled, (x, y))
    return canvas


def main():
    parser = argparse.ArgumentParser(description="Generate yuanbao.ico")
    parser.add_argument(
        "--style",
        choices=STYLES,
        default="transparent",
        help="icon background style (default: transparent)",
    )
    args = parser.parse_args()

    dog = Image.open(SOURCE).convert("RGBA")
    bbox = dog.getbbox()
    if bbox:
        dog = dog.crop(bbox)

    frames = [render(size, dog, args.style) for size in SIZES]

    try:
        frames[-1].save(
            OUT_PATH,
            format="ICO",
            sizes=[(s, s) for s in SIZES],
            append_images=frames[:-1],
        )
    except TypeError:
        frames[-1].save(OUT_PATH, format="ICO", sizes=[(s, s) for s in SIZES])

    saved = Image.open(OUT_PATH)
    print("wrote %s [%s] (%d sizes: %s)" % (
        OUT_PATH,
        args.style,
        len(saved.info.get("sizes", [])),
        sorted(saved.info.get("sizes", [])),
    ))


if __name__ == "__main__":
    main()

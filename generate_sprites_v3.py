"""
Yuanbao Pixel Art Sprite Generator v3
Uses AI cutouts + hand-drawn effects for rich multi-frame animations.
Each action has proper visual feedback: bowls, particles, bubbles, etc.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import os, math, random

SZ = 64
random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'YuanBaoPet', 'sprites')
CUTOUT_SIT = '微信图片_20260617161155_1263_285_cutout.png'
CUTOUT_LIE = '微信图片_20260617161142_1259_285_cutout.png'

# ==============================================
# Color palette for drawing effects
# ==============================================
BOWL_DARK = (80, 60, 40, 255)
BOWL_MID = (120, 95, 65, 255)
BOWL_LIGHT = (160, 135, 100, 255)
WATER = (120, 180, 220, 220)
WATER_SHINE = (200, 235, 255, 200)
FOOD_KIBBLE = (180, 140, 90, 255)
FOOD_KIBBLE2 = (160, 120, 70, 255)
BUBBLE = (220, 235, 250, 180)
BUBBLE_SHINE = (255, 255, 255, 220)
SOAP = (240, 245, 255, 200)
HEART = (230, 80, 100, 255)
SPARKLE = (255, 250, 200, 255)
DUST = (200, 190, 170, 150)
DROP = (150, 200, 235, 200)


def load_dog(path):
    """Load and crop dog cutout to square."""
    img = Image.open(path).convert('RGBA')
    bbox = img.getbbox()
    if not bbox:
        return None
    x1, y1, x2, y2 = bbox
    pad = 8
    x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
    x2, y2 = min(img.size[0], x2 + pad), min(img.size[1], y2 + pad)
    cropped = img.crop((x1, y1, x2, y2))
    w, h = cropped.size
    sq = max(w, h)
    square = Image.new('RGBA', (sq, sq), (0, 0, 0, 0))
    square.paste(cropped, ((sq - w) // 2, (sq - h) // 2))
    return square


def pixel_down(img, size=SZ):
    """Resize to pixel art size with LANCZOS then NEAREST for crisp result."""
    # First go slightly larger for detail preservation
    mid = img.resize((size * 2, size * 2), Image.LANCZOS)
    return mid.resize((size, size), Image.NEAREST)


def make_canvas():
    return Image.new('RGBA', (SZ, SZ), (0, 0, 0, 0))


def draw_ellipse(draw, cx, cy, rx, ry, fill):
    """Draw ellipse on PIL draw object."""
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)


def draw_bowl(canvas, x, y):
    """Draw a food/water bowl at position (x, y)."""
    draw = ImageDraw.Draw(canvas)
    w = 16
    # Bowl body
    draw.ellipse([x - w, y - 4, x + w, y + 8], fill=BOWL_DARK)
    draw.ellipse([x - w + 2, y - 2, x + w - 1, y + 7], fill=BOWL_MID)
    # Bowl rim
    draw.ellipse([x - w, y - 6, x + w, y + 1], fill=BOWL_LIGHT)
    draw.ellipse([x - w + 1, y - 5, x + w - 1, y], fill=BOWL_MID)
    return canvas


def draw_water_in_bowl(canvas, x, y, level=1.0):
    """Draw water inside the bowl."""
    draw = ImageDraw.Draw(canvas)
    h = int(4 * level)
    if h > 0:
        draw.ellipse([x - 7, y - 3, x + 7, y - 3 + h], fill=WATER)
        # Shine
        if h >= 2:
            draw.ellipse([x - 4, y - 2, x, y - 2 + min(2, h)], fill=WATER_SHINE)
    return canvas


def draw_food_in_bowl(canvas, x, y):
    """Draw kibble/food in bowl."""
    draw = ImageDraw.Draw(canvas)
    kibble_positions = [
        (x - 5, y - 1), (x - 2, y - 2), (x + 1, y - 1),
        (x + 4, y), (x - 3, y), (x, y + 1), (x + 3, y + 1),
        (x - 1, y - 3), (x + 2, y - 2),
    ]
    for px, py in kibble_positions:
        color = FOOD_KIBBLE if random.random() > 0.3 else FOOD_KIBBLE2
        draw.ellipse([px - 1, py - 1, px + 1, py + 1], fill=color)
    return canvas


def draw_water_drops(canvas, droplets):
    """Draw water droplets at given positions."""
    draw = ImageDraw.Draw(canvas)
    for dx, dy, size in droplets:
        draw.ellipse([dx - size, dy - size, dx + size, dy + size], fill=DROP)
        if size > 1:
            draw.ellipse([dx - size // 2, dy - size, dx, dy - size // 2], fill=WATER_SHINE)
    return canvas


def draw_bubbles(canvas, bubbles):
    """Draw soap bubbles."""
    draw = ImageDraw.Draw(canvas)
    for bx, by, r in bubbles:
        draw.ellipse([bx - r, by - r, bx + r, by + r], fill=BUBBLE)
        if r > 2:
            draw.ellipse([bx - r // 2, by - r + 1, bx, by - r // 2 + 2], fill=BUBBLE_SHINE)
    return canvas


def draw_hearts(canvas, hearts):
    """Draw floating hearts."""
    draw = ImageDraw.Draw(canvas)
    for hx, hy, s in hearts:
        # Simple heart: two circles + triangle
        draw.ellipse([hx - s, hy - s, hx, hy], fill=HEART)
        draw.ellipse([hx, hy - s, hx + s, hy], fill=HEART)
        # Triangle bottom
        pts = [(hx - s, hy - s // 2), (hx + s, hy - s // 2), (hx, hy + s)]
        draw.polygon(pts, fill=HEART)
    return canvas


def draw_dust_puffs(canvas, puffs):
    """Draw dust clouds (for walking)."""
    draw = ImageDraw.Draw(canvas)
    for dx, dy, r in puffs:
        for i in range(3):
            ox = dx + random.randint(-2, 2)
            oy = dy + random.randint(-1, 1)
            rr = r + random.randint(-1, 1)
            draw.ellipse([ox - rr, oy - rr // 2, ox + rr, oy + rr // 2], fill=DUST)
    return canvas


def paste_dog(canvas, dog_img, offset_y=0, offset_x=0, scale=1.0):
    """Paste the dog image onto canvas at given offset."""
    if scale != 1.0:
        w, h = dog_img.size
        new_w, new_h = int(w * scale), int(h * scale)
        dog_scaled = dog_img.resize((new_w, new_h), Image.LANCZOS)
    else:
        dog_scaled = dog_img

    dw, dh = dog_scaled.size
    px = (SZ - dw) // 2 + offset_x
    py = (SZ - dh) // 2 + offset_y
    canvas.paste(dog_scaled, (px, py), dog_scaled)
    return canvas


# ==============================================
# IDLE ANIMATION (2 frames)
# ==============================================
def make_idle(dog):
    frames = []
    # Frame 0: normal
    c0 = make_canvas()
    # Scale dog to fit nicely in 64x64
    dog_small = dog.resize((SZ - 8, SZ - 8), Image.LANCZOS)
    paste_dog(c0, dog_small)
    frames.append(pixel_down(c0))

    # Frame 1: very slight vertical bounce (breathing)
    c1 = make_canvas()
    paste_dog(c1, dog_small, offset_y=-1)
    frames.append(pixel_down(c1))

    return frames


# ==============================================
# WALK ANIMATION (4 frames) - bounce + dust
# ==============================================
def make_walk(dog):
    frames = []
    dog_small = dog.resize((SZ - 10, SZ - 10), Image.LANCZOS)

    # Walk cycle with vertical bounce
    bounce = [0, -3, 0, -2]  # Bounce pattern per frame
    dust_positions = [
        [(26, 58, 2), (38, 58, 1)],   # frame 0
        [(28, 59, 3), (36, 58, 2)],   # frame 1
        [(24, 58, 2), (40, 58, 1)],   # frame 2
        [(30, 60, 3), (34, 59, 2)],   # frame 3
    ]

    for i in range(4):
        c = make_canvas()
        paste_dog(c, dog_small, offset_y=bounce[i])
        # Dust puffs at feet
        draw_dust_puffs(c, dust_positions[i])
        frames.append(pixel_down(c))

    return frames


# ==============================================
# DRINK ANIMATION (4 frames) - bowl + dog drinking + water drops
# ==============================================
def make_drink(dog):
    frames = []
    dog_small = dog.resize((SZ - 12, SZ - 12), Image.LANCZOS)

    # Animation sequence
    head_positions = [0, 2, 4, 1]  # Head bobs down toward bowl
    water_levels = [1.0, 0.8, 0.6, 0.9]  # Water decreases as dog drinks
    droplets = [
        [(30, 30, 1), (32, 28, 1)],           # frame 0 - starting
        [(28, 32, 2), (33, 29, 1), (35, 31, 1)],  # frame 1 - drinking
        [(27, 30, 2), (30, 28, 2), (34, 27, 1), (37, 30, 1)],  # frame 2 - gulping
        [(29, 31, 1), (32, 29, 1)],           # frame 3 - finishing
    ]

    for i in range(4):
        c = make_canvas()
        # Bowl at bottom
        draw_bowl(c, 32, 55)
        draw_water_in_bowl(c, 32, 55, water_levels[i])
        # Dog bobbing down
        paste_dog(c, dog_small, offset_y=head_positions[i])
        # Splash droplets
        draw_water_drops(c, droplets[i])
        frames.append(pixel_down(c))

    return frames


# ==============================================
# EAT ANIMATION (4 frames) - bowl + dog eating + crumbs
# ==============================================
def make_eat(dog):
    frames = []
    dog_small = dog.resize((SZ - 12, SZ - 12), Image.LANCZOS)

    head_positions = [0, 2, 3, 1]
    crumbs = [
        [(27, 53, 1), (30, 54, 1)],
        [(26, 52, 2), (29, 53, 1), (33, 54, 1), (36, 52, 1)],
        [(25, 51, 2), (28, 52, 2), (32, 53, 1), (35, 51, 2), (38, 53, 1)],
        [(28, 53, 1), (31, 54, 1)],
    ]

    for i in range(4):
        c = make_canvas()
        draw_bowl(c, 32, 55)
        draw_food_in_bowl(c, 32, 55)
        paste_dog(c, dog_small, offset_y=head_positions[i])
        # Food crumbs flying
        for cx, cy, cs in crumbs[i]:
            draw = ImageDraw.Draw(c)
            draw.ellipse([cx - cs, cy - cs, cx + cs, cy + cs], fill=FOOD_KIBBLE)
        frames.append(pixel_down(c))

    return frames


# ==============================================
# BATH ANIMATION (4 frames) - shaking + bubbles + droplets
# ==============================================
def make_bath(dog):
    frames = []
    dog_small = dog.resize((SZ - 10, SZ - 10), Image.LANCZOS)

    # Shake offsets
    shakes = [(-2, 0), (2, -1), (-1, 1), (1, -1)]
    bubble_sets = [
        [(40, 15, 5), (50, 22, 3), (18, 18, 4)],
        [(42, 12, 6), (52, 20, 4), (15, 15, 5), (48, 28, 3)],
        [(38, 14, 5), (48, 18, 6), (20, 16, 4), (45, 30, 4), (14, 22, 3)],
        [(40, 16, 5), (50, 24, 4), (16, 20, 5)],
    ]
    drop_sets = [
        [(22, 35, 1), (28, 32, 1), (35, 38, 1)],
        [(20, 33, 2), (26, 30, 2), (33, 35, 1), (38, 32, 1), (30, 40, 1)],
        [(18, 35, 2), (24, 28, 2), (30, 33, 2), (36, 30, 2), (40, 36, 1), (28, 42, 1)],
        [(22, 38, 1), (28, 34, 1), (34, 40, 1)],
    ]

    for i in range(4):
        c = make_canvas()
        paste_dog(c, dog_small, offset_x=shakes[i][0], offset_y=shakes[i][1])
        draw_bubbles(c, bubble_sets[i])
        draw_water_drops(c, drop_sets[i])
        frames.append(pixel_down(c))

    return frames


# ==============================================
# HAPPY ANIMATION (3 frames) - bounce + hearts
# ==============================================
def make_happy(dog):
    frames = []
    dog_small = dog.resize((SZ - 10, SZ - 10), Image.LANCZOS)

    bounces = [0, -3, -1]
    heart_sets = [
        [(22, 8, 3), (36, 5, 2)],
        [(20, 5, 4), (34, 2, 3), (40, 8, 2)],
        [(24, 8, 3), (38, 6, 2)],
    ]

    for i in range(3):
        c = make_canvas()
        paste_dog(c, dog_small, offset_y=bounces[i])
        draw_hearts(c, heart_sets[i])
        frames.append(pixel_down(c))

    return frames


# ==============================================
# SLEEP ANIMATION (2 frames) - ZZZ + breathing
# ==============================================
def make_sleep(dog):
    frames = []
    dog_small = dog.resize((SZ - 10, SZ - 10), Image.LANCZOS)

    z_positions = [
        [(46, 16), (50, 12), (54, 8)],   # frame 0
        [(47, 17), (51, 13), (55, 9)],   # frame 1 (slight float)
    ]

    for i in range(2):
        c = make_canvas()
        paste_dog(c, dog_small, offset_y=i)
        draw = ImageDraw.Draw(c)
        # Draw ZZZ
        for zx, zy in z_positions[i]:
            # Z shape with pixels
            for dx in range(4):
                draw.point((zx + dx, zy), fill=(255, 255, 255, 200))
            for dx in range(4):
                draw.point((zx + 3 - dx, zy + 2), fill=(255, 255, 255, 200))
            for dx in range(4):
                draw.point((zx + dx, zy + 4), fill=(255, 255, 255, 200))
        frames.append(pixel_down(c))

    return frames


# ==============================================
# MAIN
# ==============================================
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    dog_sit = load_dog(CUTOUT_SIT)
    dog_lie = load_dog(CUTOUT_LIE)

    if not dog_sit:
        print("ERROR: Sitting dog cutout not found!")
        return

    print(f"Generating sprites...")
    print(f"  Sit dog: {dog_sit.size}")
    print(f"  Lie dog: {dog_lie.size if dog_lie else 'N/A'}")

    all_frames = {}

    # IDLE
    frames = make_idle(dog_sit)
    for i, f in enumerate(frames):
        all_frames[f'idle_{i}'] = f

    # WALK
    frames = make_walk(dog_sit)
    for i, f in enumerate(frames):
        all_frames[f'walk_{i}'] = f

    # DRINK
    frames = make_drink(dog_sit)
    for i, f in enumerate(frames):
        all_frames[f'drink_{i}'] = f

    # EAT
    frames = make_eat(dog_sit)
    for i, f in enumerate(frames):
        all_frames[f'eat_{i}'] = f

    # BATH
    frames = make_bath(dog_sit)
    for i, f in enumerate(frames):
        all_frames[f'bath_{i}'] = f

    # HAPPY
    frames = make_happy(dog_sit)
    for i, f in enumerate(frames):
        all_frames[f'happy_{i}'] = f

    # SLEEP
    if dog_lie:
        frames = make_sleep(dog_lie)
    else:
        frames = make_sleep(dog_sit)  # fallback
    for i, f in enumerate(frames):
        all_frames[f'sleep_{i}'] = f

    # Save all
    for name, frame in all_frames.items():
        frame.save(os.path.join(OUT_DIR, f'yuanbao_{name}.png'))
        # 4x preview
        frame.resize((256, 256), Image.NEAREST).save(
            os.path.join(OUT_DIR, f'yuanbao_{name}_4x.png'))

    print(f"\nSaved {len(all_frames)} frames:")
    for name in sorted(all_frames.keys()):
        print(f"  yuanbao_{name}.png")

    print(f"\nAll sprites saved to: {OUT_DIR}")
    print("v3: Multi-frame animations with bowls, particles, bubbles, hearts, dust!")


if __name__ == '__main__':
    main()

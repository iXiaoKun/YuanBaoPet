"""
Pet widget - pixel art sprite rendering and animation system.
Renders Yuanbao the dog with smooth multi-frame animations.
"""
import os
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QPixmap


# Sprite directories to search (handles both dev and PyInstaller bundled mode)
import sys as _sys
if getattr(_sys, 'frozen', False):
    # Running as PyInstaller bundle - sprites are in _MEIPASS/sprites
    _BASE = _sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

SPRITE_SEARCH_DIRS = [
    os.path.join(_BASE, "sprites"),
    os.path.join(_BASE, ".."),  # parent dir (dev mode)
    _BASE,
]


class PetWidget(QWidget):
    """Renders the pixel art dog sprite with multi-frame animations."""

    STATE_IDLE = "idle"
    STATE_WALK = "walk"
    STATE_DRINK = "drink"
    STATE_BATH = "bath"
    STATE_EAT = "eat"
    STATE_HAPPY = "happy"
    STATE_SLEEP = "sleep"

    # Frame counts and speeds for each state
    STATE_CONFIG = {
        "idle":  {"frames": 2, "interval": 500},   # slow breathing
        "walk":  {"frames": 4, "interval": 180},   # brisk walk
        "drink": {"frames": 4, "interval": 300},   # drinking with bowl
        "bath":  {"frames": 4, "interval": 250},   # shaking with bubbles
        "eat":   {"frames": 4, "interval": 280},   # eating with bowl
        "happy": {"frames": 3, "interval": 300},   # bouncing with hearts
        "sleep": {"frames": 2, "interval": 800},   # slow breathing + ZZZ
    }

    # Display constants
    SPRITE_SCALE = 3          # 64x64 * 3 = 192px on screen
    WIDGET_SIZE = 200         # widget size

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(self.WIDGET_SIZE, self.WIDGET_SIZE)

        # Sprite cache
        self._sprites = {}
        self._sprite_scaled = self.SPRITE_SCALE * 64  # = 192
        self._load_sprites()

        # Current animation state
        self._state = self.STATE_IDLE
        self._frame = 0
        self._sprite_key = "idle_0"

        # Animation timer (cycles through frames)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._next_frame)
        self._start_state_animation()

        # State return timer (auto-return to idle after duration)
        self._state_timer = QTimer(self)
        self._state_timer.setSingleShot(True)
        self._state_timer.timeout.connect(self._return_to_idle)

        # Walk movement
        self._walk_timer = QTimer(self)
        self._walk_timer.timeout.connect(self._walk_step)
        self._walk_steps = 0
        self._walk_dx = 0
        self._walk_dy = 0

        # Sprite offset: center the scaled sprite in the widget
        ox = (self.WIDGET_SIZE - self._sprite_scaled) // 2
        oy = (self.WIDGET_SIZE - self._sprite_scaled) // 2
        self._sprite_offset = QPoint(ox, oy)

    def _load_sprites(self):
        """Load all sprite PNG files. Auto-discovers frames by scanning files."""
        # Define which states to look for
        sprite_patterns = {}
        for state, config in self.STATE_CONFIG.items():
            for i in range(config["frames"]):
                key = f"{state}_{i}"
                filename = f"yuanbao_{state}_{i}.png"
                sprite_patterns[key] = filename

        for key, filename in sprite_patterns.items():
            found = False
            for search_dir in SPRITE_SEARCH_DIRS:
                path = os.path.join(search_dir, filename)
                if os.path.exists(path):
                    pixmap = QPixmap(path)
                    if not pixmap.isNull():
                        self._sprites[key] = pixmap.scaled(
                            self._sprite_scaled, self._sprite_scaled,
                            Qt.KeepAspectRatio,
                            Qt.FastTransformation
                        )
                        found = True
                        break
            if not found:
                print(f"[PetWidget] Warning: Sprite not found: {filename}")

    def _start_state_animation(self):
        """Start the frame timer with the current state's interval."""
        config = self.STATE_CONFIG.get(self._state, {"interval": 400})
        self._anim_timer.start(config["interval"])

    def _next_frame(self):
        """Advance to the next frame for the current state."""
        config = self.STATE_CONFIG.get(self._state, {"frames": 1})
        num_frames = config["frames"]
        if num_frames > 1:
            self._frame = (self._frame + 1) % num_frames
        else:
            self._frame = 0
        self._sprite_key = f"{self._state}_{self._frame}"
        self.update()

    def _return_to_idle(self):
        """Return to idle state."""
        self.set_state(self.STATE_IDLE)

    def set_state(self, state, duration_ms=0):
        """Set animation state. Auto-returns to idle after duration_ms."""
        self._state = state
        self._frame = 0
        self._sprite_key = f"{state}_0"
        self._start_state_animation()
        self.update()

        if duration_ms > 0 and state != self.STATE_IDLE:
            self._state_timer.start(duration_ms)
        elif state == self.STATE_IDLE:
            self._state_timer.stop()

    def start_walk(self, dx, dy, steps=10):
        """Start walk animation moving the pet incrementally."""
        self._walk_dx = dx / max(steps, 1)
        self._walk_dy = dy / max(steps, 1)
        self._walk_steps = steps
        self.set_state(self.STATE_WALK)
        self._walk_timer.start(50)

    def _walk_step(self):
        """Execute one walk step: move parent window."""
        if self._walk_steps <= 0:
            self._walk_timer.stop()
            self._return_to_idle()
            return

        if self.parent():
            pos = self.parent().pos()
            self.parent().move(
                pos.x() + int(self._walk_dx),
                pos.y() + int(self._walk_dy)
            )

        self._walk_steps -= 1

    def paintEvent(self, event):
        """Render current sprite frame with nearest-neighbor scaling."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)

        pixmap = self._sprites.get(self._sprite_key)
        if pixmap and not pixmap.isNull():
            painter.drawPixmap(self._sprite_offset, pixmap)

        painter.end()

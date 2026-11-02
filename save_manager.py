"""
Save/Load manager for Yuanbao desktop pet.
Handles persistent storage of pet stats, position, and settings.
"""
import json
import os
from datetime import datetime


class SaveManager:
    def __init__(self):
        home = os.getenv('APPDATA') or os.path.expanduser('~')
        self.save_dir = os.path.join(home, 'YuanBaoPet')
        self.save_path = os.path.join(self.save_dir, 'save.json')

        # Default save data
        self.default_data = {
            "version": 1,
            "stats": {
                "hunger": 80,
                "thirst": 80,
                "clean": 80,
                "mood": 80,
            },
            "pet_position": {"x": 800, "y": 400},
            "total_interactions": 0,
            "created_at": datetime.now().isoformat(),
        }
        self.data = None

        # True on the very first launch (no readable save file yet)
        self.is_new = False
        # How long the owner was away, measured when the app starts
        self.away_seconds = 0.0

        self.load()

    def ensure_dir(self):
        """Create save directory if it doesn't exist."""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def _fresh_data(self):
        data = dict(self.default_data)
        data["stats"] = dict(self.default_data["stats"])
        data["pet_position"] = dict(self.default_data["pet_position"])
        return data

    def load(self):
        """Load save data from file. Returns cached data after the first call."""
        if self.data is not None:
            return self.data

        self.ensure_dir()

        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                if not isinstance(loaded, dict):
                    raise ValueError("save file is not an object")

                self.data = loaded
                # Validate required fields
                for key in self.default_data:
                    self.data.setdefault(key, self.default_data[key])
                self.data.setdefault("stats", dict(self.default_data["stats"]))
                self.data.setdefault("pet_position", dict(self.default_data["pet_position"]))

                # Measured before anything writes a fresh last_save_time
                self.away_seconds = self._seconds_since(self.data.get("last_save_time"))
                return self.data
            except (json.JSONDecodeError, IOError, OSError, ValueError, TypeError):
                # Corrupted save, start over with defaults
                self.data = None

        self.is_new = True
        self.data = self._fresh_data()
        self.save()  # Create initial save
        return self.data

    @staticmethod
    def _seconds_since(iso_text):
        if not iso_text:
            return 0.0
        try:
            then = datetime.fromisoformat(str(iso_text))
        except (ValueError, TypeError):
            return 0.0
        return max(0.0, (datetime.now() - then).total_seconds())

    @staticmethod
    def _parse_datetime(iso_text):
        try:
            return datetime.fromisoformat(str(iso_text))
        except (ValueError, TypeError):
            return None

    def days_owned(self):
        """How many days Yuanbao has lived with this owner."""
        created = self._parse_datetime(self.data.get("created_at") if self.data else None)
        if created is None:
            return 0
        return max(0, (datetime.now() - created).days)

    def is_birthday(self, now=None):
        """True when today is the anniversary of the first launch."""
        if self.is_new or self.data is None:
            return False
        created = self._parse_datetime(self.data.get("created_at"))
        if created is None:
            return False
        today = now or datetime.now()
        return (created.month, created.day) == (today.month, today.day)

    def save(self):
        """Save current data to file."""
        if self.data is None:
            return

        self.ensure_dir()
        self.data["last_save_time"] = datetime.now().isoformat()

        try:
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"[SaveManager] Failed to save: {e}")

    def get_stat(self, key):
        """Get a stat value."""
        if self.data is None:
            self.load()
        return self.data["stats"].get(key, 80)

    def set_stat(self, key, value):
        """Set a stat value (clamped to 0-100)."""
        if self.data is None:
            self.load()
        self.data["stats"][key] = max(0, min(100, value))

    def modify_stat(self, key, delta):
        """Modify a stat value by delta."""
        current = self.get_stat(key)
        self.set_stat(key, current + delta)

    def get_position(self):
        """Get saved pet position."""
        if self.data is None:
            self.load()
        pos = self.data["pet_position"]
        return pos.get("x", 800), pos.get("y", 400)

    def set_position(self, x, y):
        """Save pet position."""
        if self.data is None:
            self.load()
        self.data["pet_position"] = {"x": x, "y": y}

    def increment_interactions(self):
        """Increment total interaction counter."""
        if self.data is None:
            self.load()
        self.data["total_interactions"] = self.data.get("total_interactions", 0) + 1

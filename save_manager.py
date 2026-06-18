"""
Save/Load manager for Yuanbao desktop pet.
Handles persistent storage of pet stats, position, and settings.
"""
import json
import os
from datetime import datetime


class SaveManager:
    def __init__(self):
        self.save_dir = os.path.join(os.getenv('APPDATA'), 'YuanBaoPet')
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

    def ensure_dir(self):
        """Create save directory if it doesn't exist."""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def load(self):
        """Load save data from file. Returns default if no save exists."""
        self.ensure_dir()

        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)

                # Validate required fields
                for key in self.default_data:
                    if key not in self.data:
                        self.data[key] = self.default_data[key]

                return self.data
            except (json.JSONDecodeError, IOError):
                # Corrupted save, use defaults
                pass

        # No save file or corrupted - use defaults
        self.data = dict(self.default_data)
        self.data["stats"] = dict(self.default_data["stats"])
        self.data["pet_position"] = dict(self.default_data["pet_position"])
        self.save()  # Create initial save
        return self.data

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

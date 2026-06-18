"""
Status system for Yuanbao desktop pet.
Manages hunger, thirst, cleanliness, and mood with time-based decay.
"""
from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class StatusSystem(QObject):
    """Manages pet stats with gradual decay over time."""

    # Signal emitted when stats change
    stats_changed = pyqtSignal(dict)
    # Signal when a stat drops below threshold
    alert_needed = pyqtSignal(str, int)  # stat_key, current_value

    # Decay per tick (each tick = 60 seconds)
    DECAY_RATES = {
        "hunger": -1.0,
        "thirst": -1.2,
        "clean": -0.5,
        "mood": -0.8,
    }

    # Alert when stat drops below this
    ALERT_THRESHOLD = 20

    # Critical threshold
    CRITICAL_THRESHOLD = 5

    def __init__(self, save_manager):
        super().__init__()
        self.save_mgr = save_manager

        # Load saved stats
        data = self.save_mgr.load()
        self.stats = dict(data["stats"])

        # Decay timer (fires every 60 seconds)
        self.decay_timer = QTimer(self)
        self.decay_timer.timeout.connect(self._on_decay_tick)
        self.decay_timer.start(60000)  # 60 seconds

        # Alert cooldown (prevent spam)
        self._alerted = {k: False for k in self.DECAY_RATES}

    def _on_decay_tick(self):
        """Apply decay to all stats."""
        changed = False
        for key, rate in self.DECAY_RATES.items():
            old_val = self.stats[key]
            new_val = max(0, old_val + rate)
            self.stats[key] = new_val

            if old_val != new_val:
                changed = True

            # Check for alert threshold
            if new_val <= self.ALERT_THRESHOLD and not self._alerted[key]:
                self.alert_needed.emit(key, new_val)
                self._alerted[key] = True
            elif new_val > self.ALERT_THRESHOLD:
                self._alerted[key] = False

        if changed:
            self._save()
            self.stats_changed.emit(dict(self.stats))

    def modify(self, key, delta):
        """Modify a stat by delta value. Clamped to 0-100."""
        old_val = self.stats.get(key, 50)
        new_val = max(0, min(100, old_val + delta))
        self.stats[key] = new_val

        # Clear alert flag if raised above threshold
        if new_val > self.ALERT_THRESHOLD:
            self._alerted[key] = False

        self._save()
        self.stats_changed.emit(dict(self.stats))
        return new_val

    def get_all(self):
        """Get all current stats."""
        return dict(self.stats)

    def get(self, key):
        """Get a specific stat value."""
        return self.stats.get(key, 50)

    def is_critical(self, key):
        """Check if a stat is at critical level."""
        return self.stats.get(key, 100) <= self.CRITICAL_THRESHOLD

    def get_lowest_stat(self):
        """Get the key of the lowest stat."""
        return min(self.stats, key=self.stats.get)

    def _save(self):
        """Save stats to disk."""
        for key, val in self.stats.items():
            self.save_mgr.set_stat(key, val)
        self.save_mgr.save()

    def stop(self):
        """Stop decay timer."""
        self.decay_timer.stop()

"""
Main transparent pet window - always on top, frameless, draggable.
Combines the pet sprite, speech bubble, and control menu.
"""
import random
import time
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QEvent
from PyQt5.QtGui import QPainter, QColor, QMouseEvent

import dialog_lines
import gestures
import screens
import time_context
from pet_widget import PetWidget
from bubble_widget import BubbleWidget
from control_menu import ControlMenu, StatusPanel
from status_system import StatusSystem
from save_manager import SaveManager

# Drag threshold: how many pixels the mouse must move before dragging starts
DRAG_THRESHOLD = 5


class PetWindow(QWidget):
    """Main desktop pet window - transparent, frameless, always on top."""

    def __init__(self):
        super().__init__()

        # Initialize systems
        self.save_mgr = SaveManager()
        self.status_sys = StatusSystem(self.save_mgr)

        # Set by main.py once the tray icon exists
        self.tray = None

        # Mouse state for click vs drag detection
        self._mouse_pressed = False
        self._mouse_press_pos = QPoint()
        self._press_clock = 0.0
        self._press_hug = False
        self._drag_active = False
        self._drag_offset = QPoint()
        self._click_times = []

        # Bubble state
        self._bubble_queue = []  # Queue for multiple messages
        self._bubble_showing = False

        # Window setup
        self._setup_window()

        # Create components
        self._setup_components()

        # Restore position, but never off screen
        self._restore_position()

        # Timers (auto walk, chatter, autosave, eye contact)
        self._setup_timers()

        # Connect signals
        self._connect_signals()

        # Say hello a moment after the window appears
        QTimer.singleShot(1200, self._greet_on_start)

    # ==============================================
    # Setup
    # ==============================================

    def _setup_window(self):
        """Configure the main window properties."""
        self.setWindowTitle("元宝 - 桌面宠物")
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(210, 260)
        self.setMouseTracking(True)

    def _setup_components(self):
        """Create and position all child widgets."""
        # Pet sprite (covers most of window)
        self.pet = PetWidget(self)
        self.pet.move(5, 55)
        self.pet.installEventFilter(self)  # Intercept mouse events for click/drag
        self.pet.show()

        # Speech bubble (above pet)
        self.bubble = BubbleWidget(self)
        self.bubble.move(0, 0)
        self.bubble.hide()

        # Status panel (shown on demand)
        self.status_panel = StatusPanel(self.status_sys)
        self.status_panel.hide()

        # Control menu
        self.control_menu = ControlMenu(self)

    def _restore_position(self):
        """Put the pet back where it was, on a screen that still exists."""
        x, y = self.save_mgr.get_position()
        x, y = screens.clamp_point(x, y, self.width(), self.height())
        self.move(x, y)

    def _setup_timers(self):
        # Auto-walk timer (every 5-10 minutes, pet walks around on its own)
        self._autowalk_timer = QTimer(self)
        self._autowalk_timer.timeout.connect(self._auto_walk)
        self._schedule_auto_walk()

        # Idle chatter timer
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._idle_chatter)
        self._schedule_idle_chatter()

        # Auto-save timer (every 5 minutes)
        self._save_timer = QTimer(self)
        self._save_timer.timeout.connect(self._auto_save)
        self._save_timer.start(300000)

    def _connect_signals(self):
        """Connect all signals between components."""
        self.status_sys.alert_needed.connect(self._on_alert)

        self.control_menu.feed_clicked.connect(self._on_feed)
        self.control_menu.water_clicked.connect(self._on_water)
        self.control_menu.bath_clicked.connect(self._on_bath)
        self.control_menu.walk_clicked.connect(self._on_walk)
        self.control_menu.status_clicked.connect(self._on_show_status)
        self.control_menu.quit_clicked.connect(self.quit_app)

    # ==============================================
    # Startup greeting (P0: welcome back)
    # ==============================================

    def _greet_on_start(self):
        """First thing the pet says: hello, welcome back, or happy festival."""
        now = datetime.now()
        fest = time_context.festival(now)
        border = None

        if self.save_mgr.is_new:
            line = time_context.welcome_line(0, is_new=True, now=now)
        elif self.save_mgr.is_birthday(now):
            line = time_context.birthday_line()
            border = time_context.festival_color("birthday")
        elif fest and random.random() < 0.6:
            line = time_context.festival_line(fest)
            border = time_context.festival_color(fest)
        elif self.save_mgr.away_seconds < 60 * 30:
            line = time_context.greeting_prefix(now)
        else:
            line = time_context.welcome_line(self.save_mgr.away_seconds, now=now)
            border = time_context.festival_color(fest) if fest else None

        self.bubble.set_border_color(border)
        self.pet.set_state(PetWidget.STATE_HAPPY, 2500)
        self._show_bubble(line or "汪！我回来啦～", 5000)

    # ==============================================
    # Interaction handlers
    # ==============================================

    def _on_pat(self):
        """Short click: pet the dog."""
        line = random.choice(dialog_lines.CLICK_LINES)
        self._show_bubble(line, 2500)
        self.pet.set_state(PetWidget.STATE_HAPPY, 1500)
        self.status_sys.modify("mood", 3)
        self.save_mgr.increment_interactions()

    def _on_hug(self):
        """Long press: picked up for a hug."""
        self._show_bubble(random.choice(dialog_lines.HUG_LINES), 2500)
        self.pet.set_state(PetWidget.STATE_HAPPY, 1800)
        self.status_sys.modify("mood", 6)
        self.save_mgr.increment_interactions()

    def _on_hug_release(self):
        """Put back down after a hug."""
        self._show_bubble(random.choice(dialog_lines.HUG_RELEASE_LINES), 2000)
        self.pet.set_state(PetWidget.STATE_HAPPY, 1200)
        self.status_sys.modify("mood", 6)
        self.save_mgr.increment_interactions()

    def _on_angry(self):
        """Rapid clicking: the pet gets annoyed."""
        self._show_bubble(random.choice(dialog_lines.ANGRY_LINES), 2500)
        self.pet.shake()
        self.status_sys.modify("mood", -6)
        self.save_mgr.increment_interactions()

    def _on_feed(self):
        self.pet.set_state(PetWidget.STATE_EAT, 2500)
        self.status_sys.modify("hunger", 30)
        self.status_sys.modify("mood", 5)
        self._show_bubble(random.choice(dialog_lines.FEED_LINES), 3000)
        self.save_mgr.increment_interactions()

    def _on_water(self):
        self.pet.set_state(PetWidget.STATE_DRINK, 2500)
        self.status_sys.modify("thirst", 30)
        self.status_sys.modify("mood", 3)
        self._show_bubble(random.choice(dialog_lines.WATER_LINES), 3000)
        self.save_mgr.increment_interactions()

    def _on_bath(self):
        self.pet.set_state(PetWidget.STATE_BATH, 3000)
        self.status_sys.modify("clean", 40)
        self.status_sys.modify("mood", 8)
        self._show_bubble(random.choice(dialog_lines.BATH_LINES), 3000)
        self.save_mgr.increment_interactions()

    def _on_walk(self):
        """Handle walk action - move pet with animation."""
        dx = random.randint(-300, 300)
        dy = random.randint(-200, 200)
        dx, dy = screens.allowed_delta(self, dx, dy)

        steps = max(6, abs(dx) // 15 + abs(dy) // 15)
        self.pet.start_walk(dx, dy, min(steps, 30))

        self.status_sys.modify("mood", 25)
        self._show_bubble(random.choice(dialog_lines.WALK_LINES), 3000)
        self.save_mgr.increment_interactions()

    def _on_show_status(self):
        """Show the status panel next to the pet, inside the screen."""
        anchor = self.pos() + QPoint(self.width(), 0)
        area = screens.area_at(anchor)
        x, y = screens.clamp_to(area, anchor.x(), anchor.y(), 220, 260)
        self.status_panel.show_at(QPoint(x, y))

    def _on_alert(self, stat_key, value):
        """Handle stat alert."""
        alert_map = {
            "hunger": dialog_lines.ALERT_HUNGER,
            "thirst": dialog_lines.ALERT_THIRST,
            "clean": dialog_lines.ALERT_CLEAN,
            "mood": dialog_lines.ALERT_MOOD,
        }
        lines = alert_map.get(stat_key, ["我需要关注！"])
        self._show_bubble(random.choice(lines), 4000)
        self.pet.set_state(PetWidget.STATE_HAPPY, 2000)

    # ==============================================
    # Idle behaviour
    # ==============================================

    def _auto_walk(self):
        """Pet walks around on its own randomly."""
        if self.pet._state == PetWidget.STATE_WALK:
            self._schedule_auto_walk()
            return

        dx = random.randint(-150, 150)
        dy = random.randint(-100, 100)
        dx, dy = screens.allowed_delta(self, dx, dy)
        steps = max(5, abs(dx) // 15 + abs(dy) // 15)
        self.pet.start_walk(dx, dy, min(steps, 20))
        self._schedule_auto_walk()

    def _schedule_auto_walk(self):
        """Schedule next auto-walk (5-10 minutes)."""
        delay = random.randint(300000, 600000)  # 5-10 min
        self._autowalk_timer.start(delay)

    def _idle_chatter(self):
        """Random self-talk when idle, flavoured by time of day."""
        if not self.bubble.isVisible():
            self._show_bubble(random.choice(time_context.idle_lines()), 3000)
        self._schedule_idle_chatter()

    def _schedule_idle_chatter(self):
        delay = random.randint(180000, 300000)  # 3-5 min
        self._idle_timer.start(delay)

    # ==============================================
    # Movement helpers
    # ==============================================

    def move_by(self, dx, dy):
        """Move the window while staying on the current screen."""
        if dx == 0 and dy == 0:
            return
        dx, dy = screens.allowed_delta(self, dx, dy)
        if dx or dy:
            self.move(self.x() + dx, self.y() + dy)

    def _save_position(self):
        pos = self.pos()
        self.save_mgr.set_position(pos.x(), pos.y())

    def _auto_save(self):
        self._save_position()
        self.save_mgr.save()

    # ==============================================
    # Gesture handling (pat / hug / angry / drag)
    # ==============================================

    def _begin_press(self, local_pos):
        self._mouse_pressed = True
        self._mouse_press_pos = local_pos
        self._press_clock = time.monotonic()
        self._drag_active = False
        self._press_hug = False
        self._drag_offset = QPoint()

    def _held_ms(self):
        return (time.monotonic() - self._press_clock) * 1000.0

    def _recent_click_count(self):
        now = time.monotonic()
        self._click_times = gestures.recent_clicks(self._click_times, now)
        self._click_times.append(now)
        return len(self._click_times)

    def _handle_move(self, event):
        """Shared drag / hold detection for both the pet and the window."""
        if not self._drag_active and not self._press_hug:
            delta = event.pos() - self._mouse_press_pos
            if abs(delta.x()) > DRAG_THRESHOLD or abs(delta.y()) > DRAG_THRESHOLD:
                self._drag_active = True
                self._drag_offset = event.globalPos() - self.pos()
                self.setCursor(Qt.ClosedHandCursor)

        if self._drag_active:
            self.move(event.globalPos() - self._drag_offset)
            return

        if self._held_ms() >= gestures.GRAB_MS:
            self._start_hug()

    def _start_hug(self):
        self._press_hug = True
        self.pet.set_lift(True)

    def _end_press(self):
        if not self._mouse_pressed:
            return

        duration = self._held_ms()
        was_drag = self._drag_active
        was_hug = self._press_hug

        self._mouse_pressed = False
        self._drag_active = False
        self._press_hug = False
        self.setCursor(Qt.ArrowCursor)

        if was_hug:
            self.pet.set_lift(False)
            self._on_hug_release()
            self._save_position()
            return

        if was_drag:
            self._save_position()
            return

        kind = gestures.classify_press(duration, False, self._recent_click_count())
        if kind == "hug":
            self._on_hug()
        elif kind == "angry":
            self._click_times = []
            self._on_angry()
        else:
            self._on_pat()
        self._save_position()

    # ==============================================
    # Bubble queue
    # ==============================================

    def _show_bubble(self, text, duration=3000):
        """Show speech bubble. Queues if one is already showing."""
        if self._bubble_showing:
            self._bubble_queue.append((text, duration))
            return

        self._bubble_showing = True
        self.bubble.show_text(text, duration)
        bx = (self.width() - self.bubble.width()) // 2
        self.bubble.move(bx, 0)

        # When this bubble finishes, check queue
        QTimer.singleShot(duration + 200, self._on_bubble_done)

    def _on_bubble_done(self):
        """Called when a bubble finishes showing."""
        self._bubble_showing = False
        if self._bubble_queue:
            text, duration = self._bubble_queue.pop(0)
            self._show_bubble(text, duration)

    # ==============================================
    # Event filter - intercept pet widget mouse events
    # ==============================================

    def eventFilter(self, obj, event):
        """Intercept mouse events from child widgets for click/drag handling."""
        if obj is self.pet:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._begin_press(event.pos())
                    return True
                elif event.button() == Qt.RightButton:
                    self.control_menu.exec_(event.globalPos())
                    return True

            elif event.type() == QEvent.MouseMove:
                if self._mouse_pressed:
                    self._handle_move(event)
                    return True

            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self._end_press()
                    return True

        return super().eventFilter(obj, event)

    # ==============================================
    # Mouse events - for clicks on the window itself (not pet)
    # ==============================================

    def mousePressEvent(self, event: QMouseEvent):
        """Record press position; decide click vs drag on release."""
        if event.button() == Qt.LeftButton:
            self._begin_press(event.pos())
        elif event.button() == Qt.RightButton:
            self.control_menu.exec_(event.globalPos())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._mouse_pressed:
            self._handle_move(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._end_press()

    # ==============================================
    # Show / hide / quit (used by the tray icon)
    # ==============================================

    def show_pet(self):
        screens.clamp_widget(self)
        self.show()
        self.raise_()
        self.activateWindow()

    def bring_to_front(self):
        """Show the pet and say hello (second launch / tray click)."""
        self.show_pet()
        self._show_bubble(random.choice(["我在这儿呢！", "汪！叫我吗？", "来啦来啦～"]), 2500)

    def hide_pet(self):
        """Hide the pet but keep it alive in the tray."""
        if self.tray is None:
            # Without a tray icon the pet could never be called back, so stay put
            self._show_bubble("这台电脑没有托盘，我就不躲啦～", 2500)
            return
        self._save_position()
        self.save_mgr.save()
        self.pet.set_lift(False)
        self.hide()
        self.tray.showMessage(
            "元宝",
            "我先躲起来啦，双击托盘图标叫我出来～",
            QSystemTrayIcon.Information,
            3000,
        )

    def toggle_visible(self):
        if self.isVisible():
            self.hide_pet()
        else:
            self.bring_to_front()

    # Tray menu actions
    def feed_from_tray(self):
        if not self.isVisible():
            self.show_pet()
        self._on_feed()

    def show_status_from_tray(self):
        if not self.isVisible():
            self.show_pet()
        self._on_show_status()

    def quit_app(self):
        """Real quit: save everything, drop the tray icon, exit."""
        self._save_position()
        self.save_mgr.save()
        self.status_sys.stop()
        self._autowalk_timer.stop()
        self._idle_timer.stop()
        self._save_timer.stop()
        if self.tray is not None:
            self.tray.hide()
            self.tray = None
        QApplication.quit()

    # ==============================================
    # Lifecycle
    # ==============================================

    def closeEvent(self, event):
        # Closing the window (Alt+F4) only hides the pet; quit from the tray.
        self._save_position()
        self.save_mgr.save()
        event.ignore()
        self.hide_pet()

    def paintEvent(self, event):
        """Paint transparent background."""
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.end()

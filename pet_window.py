"""
Main transparent pet window - always on top, frameless, draggable.
Combines the pet sprite, speech bubble, and control menu.
"""
import random
from PyQt5.QtWidgets import QWidget, QApplication, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QEvent
from PyQt5.QtGui import QPainter, QColor, QMouseEvent

from pet_widget import PetWidget
from bubble_widget import BubbleWidget
from control_menu import ControlMenu, StatusPanel
from status_system import StatusSystem
from save_manager import SaveManager
from dialog_lines import (
    CLICK_LINES, FEED_LINES, WATER_LINES, BATH_LINES,
    WALK_LINES, IDLE_LINES, ALERT_HUNGER, ALERT_THIRST,
    ALERT_CLEAN, ALERT_MOOD
)

# Drag threshold: how many pixels the mouse must move before dragging starts
DRAG_THRESHOLD = 5


class PetWindow(QWidget):
    """Main desktop pet window - transparent, frameless, always on top."""

    def __init__(self):
        super().__init__()

        # Initialize systems
        self.save_mgr = SaveManager()
        self.status_sys = StatusSystem(self.save_mgr)

        # Window setup
        self._setup_window()

        # Create components
        self._setup_components()

        # Load saved position
        x, y = self.save_mgr.get_position()
        # Ensure on screen
        screen = QDesktopWidget().availableGeometry()
        x = max(0, min(screen.width() - self.width(), x))
        y = max(0, min(screen.height() - self.height(), y))
        self.move(x, y)

        # Mouse state for click vs drag detection
        self._mouse_pressed = False
        self._mouse_press_pos = QPoint()
        self._drag_active = False
        self._drag_offset = QPoint()

        # Bubble state
        self._bubble_queue = []  # Queue for multiple messages
        self._bubble_showing = False

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

        # Connect signals
        self._connect_signals()

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

    def _connect_signals(self):
        """Connect all signals between components."""
        self.status_sys.alert_needed.connect(self._on_alert)

        self.control_menu.feed_clicked.connect(self._on_feed)
        self.control_menu.water_clicked.connect(self._on_water)
        self.control_menu.bath_clicked.connect(self._on_bath)
        self.control_menu.walk_clicked.connect(self._on_walk)
        self.control_menu.status_clicked.connect(self._on_show_status)
        self.control_menu.quit_clicked.connect(self._on_quit)

    # ==============================================
    # Interaction handlers
    # ==============================================

    def _on_pet_clicked(self):
        """Handle click on the pet."""
        line = random.choice(CLICK_LINES)
        self._show_bubble(line, 2500)
        self.pet.set_state(PetWidget.STATE_HAPPY, 1500)
        self.status_sys.modify("mood", 3)

    def _on_feed(self):
        self.pet.set_state(PetWidget.STATE_EAT, 2500)
        self.status_sys.modify("hunger", 30)
        self.status_sys.modify("mood", 5)
        self._show_bubble(random.choice(FEED_LINES), 3000)
        self.save_mgr.increment_interactions()

    def _on_water(self):
        self.pet.set_state(PetWidget.STATE_DRINK, 2500)
        self.status_sys.modify("thirst", 30)
        self.status_sys.modify("mood", 3)
        self._show_bubble(random.choice(WATER_LINES), 3000)
        self.save_mgr.increment_interactions()

    def _on_bath(self):
        self.pet.set_state(PetWidget.STATE_BATH, 3000)
        self.status_sys.modify("clean", 40)
        self.status_sys.modify("mood", 8)
        self._show_bubble(random.choice(BATH_LINES), 3000)
        self.save_mgr.increment_interactions()

    def _on_walk(self):
        """Handle walk action - move pet with animation."""
        dx = random.randint(-300, 300)
        dy = random.randint(-200, 200)

        screen = QDesktopWidget().availableGeometry()
        cur = self.pos()
        new_x = max(0, min(screen.width() - self.width(), cur.x() + dx))
        new_y = max(0, min(screen.height() - self.height(), cur.y() + dy))
        actual_dx = new_x - cur.x()
        actual_dy = new_y - cur.y()

        steps = max(6, abs(actual_dx) // 15 + abs(actual_dy) // 15)
        self.pet.start_walk(actual_dx, actual_dy, min(steps, 30))

        self.status_sys.modify("mood", 25)
        self._show_bubble(random.choice(WALK_LINES), 3000)
        self.save_mgr.increment_interactions()

    def _on_show_status(self):
        """Show the status panel."""
        pos = self.pos() + QPoint(210, 0)
        screen = QDesktopWidget().availableGeometry()
        if pos.x() + 220 > screen.right():
            pos.setX(screen.right() - 230)
        if pos.y() + 260 > screen.bottom():
            pos.setY(screen.bottom() - 270)
        self.status_panel.show_at(pos)

    def _on_quit(self):
        """Exit the application."""
        self._save_position()
        self.save_mgr.save()
        self.status_sys.stop()
        QApplication.quit()

    def _on_alert(self, stat_key, value):
        """Handle stat alert."""
        alert_map = {
            "hunger": ALERT_HUNGER,
            "thirst": ALERT_THIRST,
            "clean": ALERT_CLEAN,
            "mood": ALERT_MOOD,
        }
        lines = alert_map.get(stat_key, ["我需要关注！"])
        self._show_bubble(random.choice(lines), 4000)
        self.pet.set_state(PetWidget.STATE_HAPPY, 2000)

    def _auto_walk(self):
        """Pet walks around on its own randomly."""
        if self.pet._state == PetWidget.STATE_WALK:
            self._schedule_auto_walk()
            return

        dx = random.randint(-150, 150)
        dy = random.randint(-100, 100)
        screen = QDesktopWidget().availableGeometry()
        cur = self.pos()
        new_x = max(0, min(screen.width() - self.width(), cur.x() + dx))
        new_y = max(0, min(screen.height() - self.height(), cur.y() + dy))
        actual_dx = new_x - cur.x()
        actual_dy = new_y - cur.y()
        steps = max(5, abs(actual_dx) // 15 + abs(actual_dy) // 15)
        self.pet.start_walk(actual_dx, actual_dy, min(steps, 20))
        self._schedule_auto_walk()

    def _schedule_auto_walk(self):
        """Schedule next auto-walk (5-10 minutes)."""
        delay = random.randint(300000, 600000)  # 5-10 min
        self._autowalk_timer.start(delay)

    def _idle_chatter(self):
        """Random self-talk when idle."""
        if not self.bubble.isVisible():
            self._show_bubble(random.choice(IDLE_LINES), 3000)
        self._schedule_idle_chatter()

    def _schedule_idle_chatter(self):
        delay = random.randint(180000, 300000)  # 3-5 min
        self._idle_timer.start(delay)

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

    def _auto_save(self):
        self._save_position()
        self.save_mgr.save()

    def _save_position(self):
        pos = self.pos()
        self.save_mgr.set_position(pos.x(), pos.y())

    # ==============================================
    # Event filter - intercept pet widget mouse events
    # ==============================================

    def eventFilter(self, obj, event):
        """Intercept mouse events from child widgets for click/drag handling."""
        if obj is self.pet:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._mouse_pressed = True
                    self._mouse_press_pos = event.pos()
                    self._drag_active = False
                    return True  # Consume the event
                elif event.button() == Qt.RightButton:
                    self.control_menu.exec_(event.globalPos())
                    return True

            elif event.type() == QEvent.MouseMove:
                if self._mouse_pressed and not self._drag_active:
                    delta = event.pos() - self._mouse_press_pos
                    if abs(delta.x()) > DRAG_THRESHOLD or abs(delta.y()) > DRAG_THRESHOLD:
                        self._drag_active = True
                        self._drag_offset = event.pos()
                        self.setCursor(Qt.ClosedHandCursor)

                if self._drag_active:
                    new_pos = event.globalPos() - self._drag_offset
                    self.move(new_pos)
                    return True

            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    if self._mouse_pressed and not self._drag_active:
                        # It was a click, not a drag
                        self._on_pet_clicked()

                    self._mouse_pressed = False
                    self._drag_active = False
                    self.setCursor(Qt.ArrowCursor)
                    self._save_position()
                    return True

        return super().eventFilter(obj, event)

    # ==============================================
    # Mouse events - for clicks on the window itself (not pet)
    # ==============================================

    def mousePressEvent(self, event: QMouseEvent):
        """Record press position; decide click vs drag on release."""
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._mouse_press_pos = event.pos()
            self._drag_active = False
        elif event.button() == Qt.RightButton:
            self.control_menu.exec_(event.globalPos())

    def mouseMoveEvent(self, event: QMouseEvent):
        """Check if movement exceeds threshold to start dragging."""
        if self._mouse_pressed and not self._drag_active:
            delta = event.pos() - self._mouse_press_pos
            if abs(delta.x()) > DRAG_THRESHOLD or abs(delta.y()) > DRAG_THRESHOLD:
                self._drag_active = True
                self._drag_offset = self._mouse_press_pos
                self.setCursor(Qt.ClosedHandCursor)

        if self._drag_active:
            new_pos = event.globalPos() - self._drag_offset
            self.move(new_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """On release: if it was a click (not drag), trigger pet click."""
        if event.button() == Qt.LeftButton:
            if self._mouse_pressed and not self._drag_active:
                # It was a click, not a drag
                self._on_pet_clicked()

            self._mouse_pressed = False
            self._drag_active = False
            self.setCursor(Qt.ArrowCursor)
            self._save_position()

    # ==============================================
    # Lifecycle
    # ==============================================

    def closeEvent(self, event):
        self._save_position()
        self.save_mgr.save()
        self.status_sys.stop()
        super().closeEvent(event)

    def paintEvent(self, event):
        """Paint transparent background."""
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.end()

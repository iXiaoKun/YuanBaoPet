"""
Speech bubble widget for Yuanbao desktop pet.
Displays pixel-style dialog bubbles above the pet.
"""
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QFontDatabase


class BubbleWidget(QWidget):
    """A speech bubble that appears above the pet with dialog text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.text = ""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.hide_bubble)
        self._timer.setSingleShot(True)

        # Bubble dimensions
        self.bubble_w = 200
        self.bubble_h = 50
        self.tail_h = 10

        self.setFixedSize(self.bubble_w + 20, self.bubble_h + self.tail_h + 10)

        # Pixel-style font
        self._font = QFont("Microsoft YaHei", 10)
        self._font.setStyleHint(QFont.SansSerif)

    def show_text(self, text, duration=3000):
        """Show a speech bubble with the given text."""
        self.text = text

        # Calculate appropriate width based on text length
        text_width = len(text) * 14 + 30
        self.bubble_w = max(100, min(300, text_width))
        self.setFixedSize(self.bubble_w + 20, self.bubble_h + self.tail_h + 10)

        self.show()
        self.raise_()
        self.update()

        # Auto-hide after duration
        self._timer.start(duration)

    def hide_bubble(self):
        """Hide the speech bubble."""
        self.hide()

    def paintEvent(self, event):
        """Draw the pixel-style speech bubble."""
        if not self.text:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        w = self.bubble_w
        h = self.bubble_h

        # Bubble background (white with border)
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))

        # Draw rounded rectangle (pixel-style with sharp corners)
        painter.drawRoundedRect(5, 5, w, h, 8, 8)

        # Draw tail triangle (below bubble, pointing down to pet)
        tail_cx = w // 2  # Center of bubble
        tail_points = [
            QPoint(tail_cx - 8, h + 5),
            QPoint(tail_cx + 8, h + 5),
            QPoint(tail_cx, h + 5 + self.tail_h),
        ]
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.drawPolygon(*tail_points)

        # Draw text centered in bubble
        painter.setPen(QColor(40, 40, 40))
        painter.setFont(self._font)
        text_rect = painter.boundingRect(
            10, 8, w - 20, h - 16,
            Qt.AlignCenter | Qt.TextWordWrap,
            self.text
        )

        # Adjust and draw
        painter.drawText(5, 5, w, h, Qt.AlignCenter | Qt.TextWordWrap, self.text)

        painter.end()

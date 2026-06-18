"""
Control menu and status panel for Yuanbao desktop pet.
Right-click context menu with interaction options and stats display.
"""
from PyQt5.QtWidgets import (
    QMenu, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QAction, QDialog
)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette


class StatusPanel(QDialog):
    """Floating status panel showing pet stats."""

    def __init__(self, status_system, parent=None):
        super().__init__(parent)
        self.setWindowTitle("元宝的状态")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(220, 260)

        self.status_sys = status_system
        self._bars = {}
        self._setup_ui()
        self._refresh()

    def _setup_ui(self):
        """Build the status panel UI."""
        # Main frame with pixel-style border
        frame = QFrame(self)
        frame.setGeometry(5, 5, 210, 250)
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 235);
                border: 2px solid #555;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # Title
        title = QLabel("🐕 元宝的状态")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; border: none;")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border: 1px solid #ddd;")
        layout.addWidget(sep)

        # Stats bars
        stats_info = [
            ("hunger", "🍖 饱食度"),
            ("thirst", "💧 口渴度"),
            ("clean", "🧼 清洁度"),
            ("mood", "😊 心情值"),
        ]

        for key, label_text in stats_info:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Microsoft YaHei", 9))
            lbl.setFixedWidth(80)
            lbl.setStyleSheet("border: none; color: #444;")
            row.addWidget(lbl)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setFixedHeight(14)
            bar.setTextVisible(True)
            bar.setFormat("%v")
            bar.setFont(QFont("Microsoft YaHei", 7))

            # Color based on stat type
            colors = {
                "hunger": "#FF9800",
                "thirst": "#2196F3",
                "clean": "#4CAF50",
                "mood": "#E91E63",
            }
            color = colors.get(key, "#999")
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background: #eee;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 2px;
                }}
            """)
            row.addWidget(bar)
            layout.addLayout(row)
            self._bars[key] = bar

        # Close button
        close_btn = QPushButton("关闭")
        close_btn.setFont(QFont("Microsoft YaHei", 9))
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #888;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 20px;
            }
            QPushButton:hover {
                background: #666;
            }
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

    def _refresh(self):
        """Update stats display."""
        stats = self.status_sys.get_all()
        for key, bar in self._bars.items():
            val = int(stats.get(key, 0))
            bar.setValue(val)
            # Change color when low
            if val <= 20:
                bar.setStyleSheet(bar.styleSheet().replace(
                    "background-color: #FF9800",
                    "background-color: #F44336"
                ).replace(
                    "background-color: #2196F3",
                    "background-color: #F44336"
                ).replace(
                    "background-color: #4CAF50",
                    "background-color: #F44336"
                ).replace(
                    "background-color: #E91E63",
                    "background-color: #F44336"
                ))

    def show_at(self, pos):
        """Show the panel at the given position and refresh."""
        self._refresh()
        self.move(pos)
        self.show()
        self.raise_()


class ControlMenu(QMenu):
    """Right-click context menu for pet interactions."""

    feed_clicked = pyqtSignal()
    water_clicked = pyqtSignal()
    bath_clicked = pyqtSignal()
    walk_clicked = pyqtSignal()
    status_clicked = pyqtSignal()
    quit_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QMenu {
                background-color: rgba(255, 255, 255, 240);
                border: 2px solid #888;
                border-radius: 6px;
                padding: 5px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
            }
            QMenu::item {
                padding: 8px 30px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #FFE0B2;
                color: #333;
            }
            QMenu::separator {
                height: 1px;
                background: #ddd;
                margin: 4px 10px;
            }
        """)

        self._setup_actions()

    def _setup_actions(self):
        """Create menu actions."""
        # Feed
        feed_action = self.addAction("🍖  喂食")
        feed_action.triggered.connect(self.feed_clicked.emit)

        # Water
        water_action = self.addAction("💧  喂水")
        water_action.triggered.connect(self.water_clicked.emit)

        # Bath
        bath_action = self.addAction("🧼  洗澡")
        bath_action.triggered.connect(self.bath_clicked.emit)

        # Walk
        walk_action = self.addAction("🚶  遛狗")
        walk_action.triggered.connect(self.walk_clicked.emit)

        self.addSeparator()

        # Status
        status_action = self.addAction("📊  查看状态")
        status_action.triggered.connect(self.status_clicked.emit)

        self.addSeparator()

        # Quit
        quit_action = self.addAction("❌  退出")
        quit_action.triggered.connect(self.quit_clicked.emit)

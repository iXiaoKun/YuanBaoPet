"""System tray icon: show/hide the pet, feed it, toggle autostart, quit."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon

import autostart
from paths import app_icon_path


class PetTray(QSystemTrayIcon):
    def __init__(self, pet, parent=None):
        super().__init__(QIcon(app_icon_path()), parent)
        self.pet = pet
        self.setToolTip("元宝 - 桌面宠物")
        self._build_menu()
        self.activated.connect(self._on_activated)
        self.show()

    def _build_menu(self):
        menu = QMenu()

        show_action = QAction("👀  显示元宝", menu)
        show_action.triggered.connect(self.pet.bring_to_front)
        menu.addAction(show_action)

        hide_action = QAction("🙈  隐藏元宝", menu)
        hide_action.triggered.connect(self.pet.hide_pet)
        menu.addAction(hide_action)

        menu.addSeparator()

        feed_action = QAction("🍖  喂食", menu)
        feed_action.triggered.connect(self.pet.feed_from_tray)
        menu.addAction(feed_action)

        status_action = QAction("📊  查看状态", menu)
        status_action.triggered.connect(self.pet.show_status_from_tray)
        menu.addAction(status_action)

        menu.addSeparator()

        self.autostart_action = QAction("🚀  开机自动启动", menu)
        self.autostart_action.setCheckable(True)
        self.autostart_action.triggered.connect(self._toggle_autostart)
        menu.addAction(self.autostart_action)

        menu.addSeparator()

        quit_action = QAction("❌  退出", menu)
        quit_action.triggered.connect(self.pet.quit_app)
        menu.addAction(quit_action)

        menu.aboutToShow.connect(self._sync_autostart)
        self.setContextMenu(menu)
        self._menu = menu

    def _sync_autostart(self):
        self.autostart_action.setChecked(autostart.is_enabled())

    def _toggle_autostart(self):
        want = self.autostart_action.isChecked()
        ok, message = autostart.set_enabled(want)
        if not ok:
            self.autostart_action.setChecked(autostart.is_enabled())
            self.showMessage("开机自启设置失败", message, QSystemTrayIcon.Warning, 4000)
            return
        text = "以后开机元宝会自己出来～" if want else "开机自启已关闭"
        self.showMessage("元宝", text, QSystemTrayIcon.Information, 3000)

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.pet.bring_to_front()

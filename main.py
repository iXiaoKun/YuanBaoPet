"""
YuanBao Desktop Pet - Main Entry Point
A pixel-art golden retriever dog that lives on your desktop.

Double-click start_yuanbao.bat to launch, or run: python main.py
"""
import sys
import os

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8 output so the emoji/Chinese below never crash on a GBK console.
# (Windowed/bundled builds have no stdout, hence the None checks.)
for _stream in (sys.stdout, sys.stderr):
    try:
        if _stream is not None:
            _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from paths import app_icon_path
from single_instance import SingleInstance


def main():
    # Enable High DPI scaling (compatible with different PyQt5 versions)
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("YuanBaoPet")
    app.setOrganizationName("YuanBao")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(app_icon_path()))

    # Only one Yuanbao at a time; a second launch brings the first one forward
    guard = SingleInstance()
    if guard.notify_existing():
        print("元宝已经在运行啦，已经把它叫到前面来了～")
        return 0

    # Set default font
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # Create and show the pet window
    from pet_window import PetWindow

    pet = PetWindow()

    guard.listen()
    guard.activated.connect(pet.bring_to_front)

    # Tray icon: show/hide, feed, status, autostart, quit
    if QSystemTrayIcon.isSystemTrayAvailable():
        from tray import PetTray

        pet.tray = PetTray(pet)
    else:
        print("[提示] 当前系统没有托盘区，退出请用右键菜单里的『退出』。")

    pet.show()

    print("🐕 元宝来啦！狗狗已出现在你的桌面上~")
    print("   - 左键拖动：移动元宝")
    print("   - 左键点击：摸摸元宝（长按是抱抱，连点会生气）")
    print("   - 右键点击：打开菜单（喂食/喂水/洗澡/遛狗/状态）")
    print("   - 托盘图标：显示/隐藏、开机自启、退出")
    print("   - 元宝会自己说话哦！")

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())

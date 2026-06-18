"""
YuanBao Desktop Pet - Main Entry Point
A pixel-art golden retriever dog that lives on your desktop.

Double-click start_yuanbao.bat to launch, or run: python main.py
"""
import sys
import os

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


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

    # Set default font
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # Create and show the pet window
    from pet_window import PetWindow
    pet = PetWindow()
    pet.show()

    print("🐕 元宝来啦！狗狗已出现在你的桌面上~")
    print("   - 左键拖动：移动元宝")
    print("   - 左键点击：摸摸元宝")
    print("   - 右键点击：打开菜单（喂食/喂水/洗澡/遛狗/状态）")
    print("   - 元宝会自己说话哦！")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

# 🐕 元宝桌宠 (YuanBaoPet)

像素风格桌面电子宠物狗 —— 一只叫"元宝"的白色小狗，永远悬浮在你的桌面上。

## ✨ 功能

- 🪟 **窗口置顶** — 悬浮在所有窗口之上
- 👻 **背景透明** — 只看到元宝本体
- 🖱️ **自由拖拽** — 左键拖到任意位置
- 💬 **对话气泡** — 点击说话、互动反馈、自言自语
- 🎬 **多帧动画** — 待机、走路、喝水、吃饭、洗澡、开心、睡觉
- 📊 **状态系统** — 饱食度/口渴度/清洁度/心情值随时间衰减
- 💾 **自动存档** — 退出自动保存，下次启动恢复

## 🎮 操作

| 操作 | 效果 |
|------|------|
| 左键拖拽 | 移动元宝 |
| 左键点击 | 摸摸元宝 → 对话气泡 |
| 右键点击 | 菜单：喂食 / 喂水 / 洗澡 / 遛狗 / 状态 / 退出 |

## 🚀 运行

```bash
# 开发模式
pip install PyQt5 Pillow
python main.py

# 或双击
start_yuanbao.bat
```

## 📦 打包

```bash
pip install pyinstaller Pillow
build_exe.bat
# EXE 输出在 dist/YuanBaoPet.exe
```

## 📁 项目结构

```
YuanBaoPet/
├── main.py               # 入口
├── pet_window.py          # 透明置顶窗口
├── pet_widget.py          # 精灵渲染 + 动画
├── bubble_widget.py       # 对话气泡
├── control_menu.py        # 右键菜单 + 状态面板
├── status_system.py       # 状态衰减系统
├── save_manager.py        # JSON存档
├── dialog_lines.py        # 60+条对话文本
├── generate_sprites_v3.py # 精灵生成器（AI抠图+特效）
├── sprites/               # 23帧像素精灵
└── build_exe.bat          # PyInstaller打包脚本
```

## 🎨 精灵生成

基于真实狗狗照片，使用 rembg (U2Net AI) 抠图，然后像素化并添加碗、水花、食物、泡泡、爱心等特效。

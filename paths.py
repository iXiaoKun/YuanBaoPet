"""Resource path helpers for dev mode and PyInstaller bundles."""
import os
import sys


def base_dir():
    """Directory that holds sprites/ both in dev mode and inside a bundle."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def sprite_search_dirs():
    """Where to look for yuanbao_*.png files, most specific first."""
    base = base_dir()
    return [
        os.path.join(base, "sprites"),
        os.path.join(base, ".."),  # parent dir (dev mode)
        base,
    ]


def sprite_path(filename):
    return os.path.join(base_dir(), "sprites", filename)


def app_icon_path():
    """Window / tray / exe icon: yuanbao.ico, else icon.png, else a sprite frame."""
    base = base_dir()
    for name in ("yuanbao.ico", "icon.png"):
        candidate = os.path.join(base, name)
        if os.path.exists(candidate):
            return candidate
    return sprite_path("yuanbao_idle_0.png")

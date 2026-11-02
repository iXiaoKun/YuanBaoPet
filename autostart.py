"""Start-with-Windows support (HKCU Run key, no admin rights needed)."""
import os
import sys

try:
    import winreg
except ImportError:  # pragma: no cover - non Windows
    winreg = None

APP_NAME = "YuanBaoPet"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def launch_command():
    """Command Windows should run at logon."""
    if getattr(sys, "frozen", False):
        return '"%s"' % sys.executable

    python = sys.executable
    pythonw = os.path.join(os.path.dirname(python), "pythonw.exe")
    if os.path.exists(pythonw):
        python = pythonw  # no console window for the pet
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return '"%s" "%s"' % (python, script)


def is_enabled():
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except OSError:
        return False


def set_enabled(enabled):
    """Enable/disable autostart. Returns (ok, error_message)."""
    if winreg is None:
        return False, "当前系统不支持注册表自启设置"
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, launch_command())
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        return True, ""
    except OSError as exc:
        return False, str(exc)

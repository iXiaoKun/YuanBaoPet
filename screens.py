"""Multi-monitor geometry helpers.

Everything the pet does with positions goes through here so it never walks off
a second monitor or hides under the taskbar.
"""
from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtWidgets import QApplication

FALLBACK_AREA = QRect(0, 0, 1024, 768)


def available_areas():
    """Usable (taskbar-free) geometry of every screen."""
    app = QApplication.instance()
    if app is None:
        return [FALLBACK_AREA]
    return [screen.availableGeometry() for screen in app.screens()]


def area_at(point):
    """Usable geometry of the screen containing point (falls back to primary)."""
    app = QApplication.instance()
    if app is None:
        return FALLBACK_AREA
    screen = app.screenAt(QPoint(point))
    if screen is None:
        screen = app.primaryScreen()
    return screen.availableGeometry() if screen is not None else FALLBACK_AREA


def clamp_to(area, x, y, w, h):
    """Pure helper: clamp a w x h rectangle's origin into area."""
    max_x = area.x() + max(0, area.width() - w)
    max_y = area.y() + max(0, area.height() - h)
    return max(area.x(), min(int(x), max_x)), max(area.y(), min(int(y), max_y))


def clamp_point(x, y, w, h):
    """Clamp a window origin so the window stays on the screen it belongs to."""
    area = area_at(QPoint(int(x) + w // 2, int(y) + h // 2))
    return clamp_to(area, x, y, w, h)


def clamp_widget(widget):
    """Move widget back on screen if needed; returns the (possibly new) origin."""
    x, y = clamp_point(widget.x(), widget.y(), widget.width(), widget.height())
    if (x, y) != (widget.x(), widget.y()):
        widget.move(x, y)
    return x, y


def allowed_delta(widget, dx, dy):
    """Largest (dx, dy) step that keeps widget inside its current screen."""
    area = area_at(widget.geometry().center())
    target_x, target_y = clamp_to(
        area, widget.x() + dx, widget.y() + dy, widget.width(), widget.height()
    )
    return target_x - widget.x(), target_y - widget.y()

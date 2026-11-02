"""Time-of-day, holiday and absence awareness for Yuanbao."""
import random
from datetime import date, datetime

import dialog_lines

# Lunar holidays follow the Chinese calendar; extend the tables when they run out.
SPRING_FESTIVAL = {
    2026: (2, 17),
    2027: (2, 6),
    2028: (1, 26),
    2029: (2, 13),
    2030: (2, 3),
}
MID_AUTUMN = {
    2026: (9, 25),
    2027: (9, 15),
    2028: (10, 3),
    2029: (9, 22),
    2030: (9, 12),
}

FESTIVALS = {
    "spring": ("春节", "#E53935"),
    "midautumn": ("中秋", "#FB8C00"),
    "newyear": ("元旦", "#E53935"),
    "national": ("国庆", "#E53935"),
    "christmas": ("圣诞", "#43A047"),
    "children": ("儿童节", "#F06292"),
    "birthday": ("生日", "#FF4081"),
}

PERIOD_GREETINGS = dialog_lines.PERIOD_GREETINGS


def period(now=None):
    """Rough day-part used to pick greetings and chatter."""
    hour = (now or datetime.now()).hour
    if 5 <= hour < 8:
        return "dawn"
    if 8 <= hour < 12:
        return "morning"
    if 12 <= hour < 14:
        return "noon"
    if 14 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 23:
        return "evening"
    return "night"


def greeting_prefix(now=None):
    """A time-of-day hello, used when the owner was only briefly away."""
    return _pick(PERIOD_GREETINGS[period(now)])


def _within(day, month_day, before, after):
    if not month_day:
        return False
    month, dom = month_day
    try:
        anchor = date(day.year, month, dom)
    except ValueError:
        return False
    return -before <= (day - anchor).days <= after


def festival(now=None):
    """Return a festival key for today, or None."""
    today = (now or datetime.now()).date()

    if _within(today, SPRING_FESTIVAL.get(today.year), 3, 6):
        return "spring"
    if _within(today, MID_AUTUMN.get(today.year), 1, 1):
        return "midautumn"
    if (today.month == 12 and today.day >= 31) or (today.month == 1 and today.day <= 2):
        return "newyear"
    if today.month == 12 and 24 <= today.day <= 26:
        return "christmas"
    if today.month == 10 and 1 <= today.day <= 7:
        return "national"
    if today.month == 6 and today.day == 1:
        return "children"
    return None


def festival_name(key):
    return FESTIVALS.get(key, (None, None))[0]


def festival_color(key):
    """Bubble border colour for the given festival, or None."""
    return FESTIVALS.get(key, (None, None))[1]


def away_bucket(seconds):
    """Group the time the owner has been away."""
    if seconds < 60 * 30:
        return "short"
    if seconds < 60 * 60 * 8:
        return "hours"
    if seconds < 60 * 60 * 24 * 2:
        return "day"
    if seconds < 60 * 60 * 24 * 7:
        return "days"
    return "long"


def welcome_line(away_seconds, is_new=False, now=None):
    """Pick the first thing Yuanbao says when the app starts."""
    del now  # kept for call-site symmetry / future tuning
    if is_new:
        return _pick(dialog_lines.GREETING_NEW)
    pools = {
        "short": dialog_lines.GREETING_SHORT,
        "hours": dialog_lines.GREETING_HOURS,
        "day": dialog_lines.GREETING_DAY,
        "days": dialog_lines.GREETING_DAYS,
        "long": dialog_lines.GREETING_LONG,
    }
    return _pick(pools[away_bucket(away_seconds)])


def festival_line(key):
    pool = dialog_lines.FESTIVAL_LINES.get(key)
    return _pick(pool) if pool else None


def idle_lines(now=None):
    """Chatter pool for the current time of day."""
    return dialog_lines.PERIOD_IDLE.get(period(now), dialog_lines.IDLE_LINES)


def birthday_line():
    return _pick(dialog_lines.GREETING_BIRTHDAY)


def _pick(pool):
    return random.choice(pool)

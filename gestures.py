"""Pure gesture rules so click/press handling stays testable.

Used by PetWindow: one press can end up as a drag, a hug (long press), an
annoyed reaction (rapid clicking) or a normal pat.
"""

GRAB_MS = 800          # hold longer than this -> hug
RAPID_WINDOW_S = 1.2   # clicks closer together than this form a combo
ANGRY_CLICKS = 5       # this many clicks in a row -> annoyed


def classify_press(duration_ms, moved, rapid_clicks):
    """Turn raw press data into one of: 'drag', 'hug', 'angry', 'pat'."""
    if moved:
        return "drag"
    if duration_ms >= GRAB_MS:
        return "hug"
    if rapid_clicks >= ANGRY_CLICKS:
        return "angry"
    return "pat"


def recent_clicks(click_times, now, window=RAPID_WINDOW_S):
    """Drop click timestamps that fell out of the combo window."""
    return [t for t in click_times if now - t <= window]

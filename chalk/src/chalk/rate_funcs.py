"""Rate functions for animation easing. All map [0,1] -> [0,1]."""


def linear(t: float) -> float:
    return t


def smooth(t: float) -> float:
    """Cubic ease-in-out: 3t² - 2t³."""
    return 3 * t * t - 2 * t * t * t


def ease_in_out(t: float) -> float:
    """Quartic ease-in-out."""
    if t < 0.5:
        return 8 * t * t * t * t
    p = t - 1
    return 1 - 8 * p * p * p * p


def there_and_back(t: float) -> float:
    """Ramp to 1 at midpoint then ramp back to 0: 2*min(t, 1-t)."""
    return 2 * min(t, 1.0 - t)

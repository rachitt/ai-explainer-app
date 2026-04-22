"""ValueTracker: a float value that animations can drive."""
from __future__ import annotations


class ValueTracker:
    def __init__(self, value: float = 0.0) -> None:
        self._value = float(value)

    def get_value(self) -> float:
        return self._value

    def set_value(self, v: float) -> "ValueTracker":
        self._value = float(v)
        return self

    def increment(self, dv: float) -> "ValueTracker":
        self._value += float(dv)
        return self

"""always_redraw, AlwaysRedraw, and DecimalNumber."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Union

from chalk.mobject import VMobject
from chalk.vgroup import VGroup

if TYPE_CHECKING:
    from chalk.value_tracker import ValueTracker


class AlwaysRedraw(VGroup):
    """VGroup whose submobjects are regenerated each frame from factory()."""

    def __init__(self, factory: Callable[[], Union[VMobject, VGroup]]) -> None:
        self._factory = factory
        super().__init__()
        self.refresh()

    def refresh(self) -> None:
        result = self._factory()
        if isinstance(result, VGroup):
            self.submobjects = list(result.submobjects)
        else:
            self.submobjects = [result]


def always_redraw(
    factory: Callable[[], Union[VMobject, VGroup]],
    move_to: tuple[float, float] | None = None,
    shift: tuple[float, float] | None = None,
) -> AlwaysRedraw:
    """Return an AlwaysRedraw VGroup backed by factory().

    Pass `move_to=(x, y)` or `shift=(dx, dy)` to apply positioning on every
    rebuild — calling `.move_to()` on the returned VGroup is a no-op because
    each frame discards the prior mob. Use these kwargs instead, or position
    the mob inside the factory itself.
    """
    if move_to is None and shift is None:
        return AlwaysRedraw(factory)

    def _positioned_factory() -> Union[VMobject, VGroup]:
        mob = factory()
        if move_to is not None:
            mob.move_to(move_to[0], move_to[1])
        if shift is not None:
            mob.shift(shift[0], shift[1])
        return mob

    return AlwaysRedraw(_positioned_factory)


class DecimalNumber(AlwaysRedraw):
    """Display a numeric value (or ValueTracker) as a MathTex label.

    Only recompiles the MathTex when the formatted string changes,
    so sweeping a tracker over a float range doesn't thrash LaTeX.
    """

    def __init__(
        self,
        value: "float | ValueTracker",
        num_decimal_places: int = 2,
        unit: str = "",
        color: str = "#E8EAED",
        scale: float = 0.65,
    ) -> None:
        self._tracker = value
        self._places = num_decimal_places
        self._unit = unit
        self._color = color
        self._scale = scale
        self._last_string: str | None = None
        self._cached_vgroup: VGroup | None = None

        super().__init__(self._build)

    def _current_value(self) -> float:
        from chalk.value_tracker import ValueTracker
        if isinstance(self._tracker, ValueTracker):
            return self._tracker.get_value()
        return float(self._tracker)

    def _format_string(self) -> str:
        v = self._current_value()
        s = f"{v:.{self._places}f}"
        if self._unit:
            s = s + self._unit
        return s

    def _build(self) -> VGroup:
        from chalk.tex import MathTex
        s = self._format_string()
        if s != self._last_string:
            self._last_string = s
            self._cached_vgroup = MathTex(s, color=self._color, scale=self._scale)
        return self._cached_vgroup  # type: ignore[return-value]

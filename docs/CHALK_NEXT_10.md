# chalk — next 10 features (Sonnet handoff pack)

Ordered by dependency + leverage. Each item is self-contained: what to build, files to touch, test plan, exit criterion. Work top-down — each feature assumes the ones above it are shipped.

Read first:
- `docs/adr/0001-chalk-replaces-manim.md` — why chalk exists, kill criteria
- `docs/CHALK_ROADMAP.md` — the phased plan this list drives
- `chalk/CLAUDE.md` — scene-authoring rules (palette, scale tiers, zones, clear-between-beats, `labeled_box`, `arrow_between`)
- `workflows/lessons.md` — mistakes to avoid

Working dir: `/Users/rachit/Documents/ai-blackboard/chalk/`.
Run tests: `cd chalk && uv run pytest tests/ -x --tb=short`.
Render a scene: `uv run chalk examples/<file>.py --scene <ClassName> -o /tmp/out.mp4 --width 960 --height 540 --fps 30`.
Extract frame: `ffmpeg -y -i /tmp/out.mp4 -vf "select=eq(n\,120)" -vframes 1 /tmp/frame.png`.

Per-feature commit convention: one feature = one commit, subject prefix `chalk:`. No `--no-verify`, no Claude co-author trailers. Push after each feature or batch of two.

Baseline at start of this list: 75 passing tests.

---

## 1. `ValueTracker` + driver animation (C1.1, part 1)

**Why first.** Every interactive scene that reacts to a varying quantity depends on this. Blocks DecimalNumber, always_redraw, MoveAlongPath's rate-driven variant, narration-aware pacing.

**API.**

```python
class ValueTracker:
    def __init__(self, value: float = 0.0) -> None: ...
    def get_value(self) -> float: ...
    def set_value(self, v: float) -> "ValueTracker": ...
    def increment(self, dv: float) -> "ValueTracker": ...

class ChangeValue:  # Animation
    def __init__(
        self,
        tracker: ValueTracker,
        target: float,
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = smooth,
    ) -> None: ...
    # begin/interpolate/finish lerp tracker.value between start and target
    # .mobjects returns [] — ValueTracker is not a VMobject
```

**Files to touch.**
- New: `chalk/src/chalk/value_tracker.py`
- Edit: `chalk/src/chalk/animation.py` (add `ChangeValue` after `Write`)
- Edit: `chalk/src/chalk/__init__.py` (export `ValueTracker`, `ChangeValue`)
- Edit: `chalk/src/chalk/scene.py` — `Scene.play` currently collects mobjects only from animations with `.mobjects`; verify an animation with `.mobjects = []` still drives frames (likely already works — the mobjects list is only used to render, the tracker just changes state).

**Tests.** `chalk/tests/test_value_tracker.py`
- `get_value()` returns init value.
- `set_value(5)` then `get_value() == 5`.
- `increment(2)` stacks.
- `ChangeValue.begin()` snapshots start value.
- `ChangeValue.interpolate(0.5)` with `linear` rate func gives midpoint.
- `ChangeValue.finish()` lands on target.
- Scene-level: play(ChangeValue(t, 10, run_time=1.0)), assert `t.get_value() == 10` after `play`.

**Exit.** 6+ new tests, 81+ total green.

---

## 2. `always_redraw` + `DecimalNumber` (C1.1, part 2)

**Why.** Turns a ValueTracker into something the audience can read. Required by Riemann-sum scene (area counter converging).

**API.**

```python
def always_redraw(factory: Callable[[], VMobject | VGroup]) -> "AlwaysRedraw": ...

class AlwaysRedraw(VGroup):
    """VGroup whose submobjects are regenerated each frame from factory()."""
    def refresh(self) -> None: ...  # called once per render_frame

class DecimalNumber(VGroup):
    def __init__(
        self,
        value: float | ValueTracker,
        num_decimal_places: int = 2,
        unit: str = "",
        color: str = PRIMARY,
        scale: float = SCALE_BODY,
    ) -> None: ...
    # Internally a MathTex rebuilt when value changes.
```

**Renderer hook.** Add `AlwaysRedraw.refresh()` call in `Scene.play` / `Scene.wait` before each `self._renderer.render_frame(...)`. Walk `self._mobjects`, call `refresh()` on any `AlwaysRedraw`.

**Files.**
- New: `chalk/src/chalk/redraw.py` (`always_redraw`, `AlwaysRedraw`, `DecimalNumber`)
- Edit: `chalk/src/chalk/scene.py` (per-frame refresh pass)
- Edit: `chalk/src/chalk/__init__.py`

**Tests.** `chalk/tests/test_redraw.py`
- `always_redraw` with a factory returning a Circle → refresh regenerates it.
- `DecimalNumber(ValueTracker(3.14))` renders "3.14".
- `DecimalNumber(tracker, num_decimal_places=0)` formats "3".
- `DecimalNumber(tracker, unit=r"\,\mathrm{m}")` appends unit.
- After `ChangeValue(tracker, 10.0, run_time=1.0)`, DecimalNumber's last rendered frame contains "10.00" (inspect MathTex string after `.refresh()`).

**Beware.** Don't re-render LaTeX per frame — MathTex cache is content-hashed. A tracker that sweeps 0→10 at 2 decimals triggers 1001 unique LaTeX compiles. Add a precision guard: DecimalNumber compares to previous rendered string; only re-parses if changed. Bump chalk-tex cache to also keep parsed VMobject in-memory (not just SVG string on disk).

**Exit.** 7+ new tests, 88+ total. Render a demo `examples/counter_demo.py` where a DecimalNumber counts 0→100 over 3 seconds.

---

## 3. `MoveAlongPath` + `Rotate` (C1.2)

**Why.** Unlocks charge flow on wires, orbiting objects, rolling-wheel chain-rule animations.

**API.**

```python
class MoveAlongPath:
    def __init__(
        self,
        mob: VMobject | VGroup,
        path: VMobject,
        run_time: float = 2.0,
        rate_func: Callable[[float], float] = linear,
    ) -> None: ...
    # At alpha, position mob's center at _arclength_point(path, alpha).

class Rotate:
    def __init__(
        self,
        mob: VMobject | VGroup,
        angle: float,
        about_point: tuple[float, float] | None = None,
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = smooth,
    ) -> None: ...
```

**Helper.** Add to `chalk/src/chalk/path_utils.py`:
```python
def sample_arclength(path: VMobject, n: int = 256) -> tuple[np.ndarray, np.ndarray]:
    """Return (cumulative_arclength_normalized, points) sampled along path."""

def arclength_point(path: VMobject, t: float) -> np.ndarray:
    """Return (x, y) at normalized arclength t ∈ [0, 1]."""
```

Implementation: sample cubics at N=64 points per curve, compute chord-length polyline, cumsum, normalize. For `arclength_point(t)`, bisect into the cumulative array and linearly interpolate between neighbors. Tolerance target: < 1% error vs true arclength at N=256.

**Files.**
- New: `chalk/src/chalk/path_utils.py`
- Edit: `chalk/src/chalk/animation.py` (add `MoveAlongPath`, `Rotate`)
- Edit: `chalk/src/chalk/__init__.py`

**Tests.** `chalk/tests/test_path_motion.py`
- `arclength_point(line_from_origin_to_(10,0), 0.5)` → within 1e-2 of `(5, 0)`.
- `MoveAlongPath(dot, circle)` at alpha=0.25 places dot at π/2 on circle.
- `Rotate(mob, π, about_point=(0,0))` at alpha=1.0 flips a point at `(1,0)` to `(-1,0)` within 1e-9.
- `Rotate` with VGroup preserves relative positions.

**Exit.** 5+ new tests, 93+ total. `examples/orbit_demo.py`: a `Dot` moving around a `Circle` path for 4 seconds.

---

## 4. `Dot`, `Polygon`, `RegularPolygon`, `ArcBetweenPoints` (C1.3, shapes)

**Why.** Foundation primitives many later features assume.

**API.**

```python
class Dot(Circle):
    def __init__(self, point: tuple[float, float] = (0.0, 0.0),
                 radius: float = 0.08, color: str = PRIMARY,
                 fill_opacity: float = 1.0) -> None: ...

class Polygon(VMobject):
    def __init__(self, *vertices: tuple[float, float],
                 color: str = PRIMARY, fill_color: str | None = None,
                 fill_opacity: float = 0.0, stroke_width: float = 2.5) -> None: ...

class RegularPolygon(Polygon):
    def __init__(self, n: int, radius: float = 1.0,
                 start_angle: float = 0.0, **kwargs) -> None: ...

class ArcBetweenPoints(VMobject):
    def __init__(self, start: tuple[float, float], end: tuple[float, float],
                 angle: float = math.pi / 3, **kwargs) -> None: ...
    # Subtends `angle` at the arc's implicit center; positive = curves left.
```

**Implementation.** Polygon builds cubic-Bezier line segments between vertices (reuse `_rect_points` pattern). ArcBetweenPoints: 1–4 cubic Bezier arc approximation depending on subtended angle; reuse `_K = 0.5522847498` for quarter-arc handles.

**Files.**
- Edit: `chalk/src/chalk/shapes.py` — add Dot, Polygon, RegularPolygon, ArcBetweenPoints classes after Arrow.
- Edit: `chalk/src/chalk/__init__.py`

**Tests.** Extend `chalk/tests/test_shapes.py`
- Dot bbox is symmetric around its point.
- RegularPolygon(6, radius=1) has 6 vertices at expected angles.
- Polygon closes (last interpolated point ≈ first).
- ArcBetweenPoints(start, end, angle=0) ≈ straight line (within 1e-3).
- ArcBetweenPoints(start, end, angle=π) is a semicircle; midpoint at expected offset.

**Exit.** 8+ new tests, 101+ total.

---

## 5. `NumberLine` and `NumberPlane` (C1.3, coordinate)

**Why.** Replaces ad-hoc axis hacking in every math scene. Prerequisite for Brace and any Riemann-sum / graph-plotting scene.

**API.**

```python
class NumberLine(VGroup):
    def __init__(
        self,
        x_range: tuple[float, float, float] = (-5, 5, 1),  # (min, max, step)
        length: float = 10.0,
        include_tip: bool = False,
        include_numbers: bool = False,
        label_direction: str = "DOWN",
        color: str = GREY,
        number_scale: float = SCALE_ANNOT,
        tick_size: float = 0.1,
    ) -> None: ...
    def n2p(self, number: float) -> tuple[float, float]:
        """Number to world-coord point on the line."""
    def p2n(self, point: tuple[float, float]) -> float:
        """Inverse."""

class NumberPlane(VGroup):
    def __init__(
        self,
        x_range: tuple[float, float, float] = (-7, 7, 1),
        y_range: tuple[float, float, float] = (-4, 4, 1),
        background_line_style: dict | None = None,
        axis_config: dict | None = None,
    ) -> None: ...
    def c2p(self, x: float, y: float) -> tuple[float, float]: ...
    def p2c(self, p: tuple[float, float]) -> tuple[float, float]: ...
```

**Defaults.** `background_line_style = {"stroke_color": TRACK, "stroke_width": 1.0}`. Major lines every `step`, minor lines at halves with 50% opacity.

**Files.**
- New: `chalk/src/chalk/coord.py`
- Edit: `chalk/src/chalk/__init__.py`

**Tests.** `chalk/tests/test_coord.py`
- `NumberLine(x_range=(-5, 5, 1), length=10).n2p(0)` returns origin of the line.
- `n2p(2)` then `p2n` round-trips within 1e-9.
- `NumberPlane().c2p(1, 1)` returns expected world coord given default frame.
- NumberPlane with custom ranges produces correct grid line count.

**Exit.** 6+ new tests, 107+ total. `examples/number_plane_demo.py` — plane + function plot on it.

---

## 6. `Brace` (C1.3, annotation)

**Why.** The dimension-annotation primitive. Riemann rectangles, inequality proofs, "this segment has length L" — all need Brace.

**API.**

```python
class Brace(VMobject):
    def __init__(
        self,
        target: VMobject | VGroup,
        direction: str = "DOWN",  # UP, DOWN, LEFT, RIGHT
        buff: float = 0.2,
        color: str = PRIMARY,
        stroke_width: float = 2.0,
    ) -> None: ...
    def get_tip(self) -> tuple[float, float]:
        """Centerpoint of the brace's apex — for attaching a label."""

def brace_label(
    target: VMobject | VGroup,
    tex: str,
    direction: str = "DOWN",
    buff: float = 0.2,
    color: str = PRIMARY,
    scale: float = SCALE_ANNOT,
) -> tuple[Brace, VGroup]:
    """Build a Brace + MathTex label positioned at its tip."""
```

**Implementation.** Build the brace from 4 cubic Bezier arcs: two for the "claws" at the ends, two for the center "kink" meeting at the apex. Sized to match target's bbox on the chosen axis. Implement as a parametric generator — see Manim's `Brace` source for the math; reimplement rather than port to keep style consistent with chalk.

**Files.**
- New: `chalk/src/chalk/brace.py`
- Edit: `chalk/src/chalk/__init__.py`
- Edit: `chalk/src/chalk/layout.py` → add `brace_label` there (colocated with other layout helpers).

**Tests.** `chalk/tests/test_brace.py`
- Brace bbox width matches target bbox width + ~0 on the axis it's annotating.
- Brace around a Rectangle of width 4 has width ≥ 4.
- get_tip() returns point on the expected side.
- brace_label places label at the brace tip with the specified buff.

**Exit.** 5+ new tests, 112+ total.

---

## 7. `TransformMatchingTex` (C1.4)

**Why.** The 3B1B-signature equation rearrangement. Today `F=ma → a=F/m` morphs by submobject index, which is visual chaos. This pairs glyphs by LaTeX-token identity.

**Approach.** MathTex already stores `tex_string`. Add a token-level mapping:

1. Tokenize both source and target tex strings into semantic atoms (variable names, numerals, operators, braces). Use a minimal tokenizer — single chars, grouped `\foo` macros, `{...}` groups. Don't try to do this perfectly; match on surface tokens.
2. Build pairs: for each token present in both, match source-glyph-index → target-glyph-index. For tokens only in source, they fade out to a point. For tokens only in target, they fade in from a point.
3. Emit an `AnimationGroup` of Transform/FadeIn/FadeOut.

**API.**

```python
class TransformMatchingTex:
    def __init__(
        self,
        source: MathTex,
        target: MathTex,
        run_time: float = 1.5,
        rate_func: Callable[[float], float] = smooth,
    ) -> None: ...
    # .mobjects, .begin, .interpolate, .finish delegate to an internal
    # AnimationGroup (once AnimationGroup ships; for now, iterate anims).
```

**Dependency.** If AnimationGroup isn't yet in place (feature 8 below), stage-manage inline: `begin()` calls begin on all inner anims, `interpolate(alpha)` forwards, etc.

**Files.**
- New: `chalk/src/chalk/tex_morph.py`
- Edit: `chalk/src/chalk/__init__.py`

**Tests.** `chalk/tests/test_tex_morph.py`
- `TransformMatchingTex(F=ma, a=F/m)` at alpha=1 → source's glyph positions match target's glyph positions for every common token.
- Tokens present only in source have `fill_opacity == 0` at alpha=1.
- Tokens present only in target are revealed (fill_opacity > 0) at alpha=1.

**Exit.** Replace `examples/morph_demo.py` with a `TransformMatchingTex` variant showing `F=ma → a = F/m`. 4+ new tests, 116+ total.

---

## 8. `AnimationGroup`, `Succession`, `LaggedStart` (C1.5)

**Why.** Composition primitives. TransformMatchingTex wants these. Write already reimplements staggered start manually; refactor to use `LaggedStart`.

**API.**

```python
class AnimationGroup:
    def __init__(self, *animations: Animation, lag_ratio: float = 0.0,
                 run_time: float | None = None) -> None: ...
    # lag_ratio=0 → parallel, lag_ratio=1 → fully sequential,
    # in between → each anim starts after lag_ratio * prev.run_time.

class Succession(AnimationGroup):
    def __init__(self, *animations: Animation) -> None:
        super().__init__(*animations, lag_ratio=1.0)

class LaggedStart(AnimationGroup):
    def __init__(self, *animations: Animation, lag_ratio: float = 0.3) -> None:
        super().__init__(*animations, lag_ratio=lag_ratio)
```

**Refactor.** `Write` currently computes stagger windows inline. Replace its body with `LaggedStart(*[FadeIn(u, ...) for u in units], lag_ratio=...)`. Confirm behavior unchanged via existing `test_text_write.py`.

**Files.**
- Edit: `chalk/src/chalk/animation.py` — add AnimationGroup/Succession/LaggedStart; refactor Write.
- Edit: `chalk/src/chalk/__init__.py`

**Tests.** `chalk/tests/test_animation_group.py`
- Parallel (`lag_ratio=0`): both anims at alpha=0.5 are at their own midpoints.
- Sequential (`lag_ratio=1.0`): at global alpha=0.5 with two equal-duration anims, first is at local 1.0, second at local 0.0.
- Partial (`lag_ratio=0.5`, two anims): windows overlap 50%.
- `run_time` auto-computed from max of children's effective end times.

**Exit.** 5+ new tests + existing Write tests still green. 121+ total.

---

## 9. `Indicate`, `Flash`, `Circumscribe` (C1.5, emphasis)

**Why.** The "look here" vocabulary. Every explainer needs at least one.

**API.**

```python
class Indicate:
    def __init__(
        self,
        mob: VMobject | VGroup,
        scale_factor: float = 1.2,
        color: str = YELLOW,
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = there_and_back,
    ) -> None: ...
    # Temporarily recolor + scale up, return to original.

class Flash:
    def __init__(
        self,
        point: tuple[float, float],
        color: str = YELLOW,
        num_lines: int = 12,
        line_length: float = 0.3,
        run_time: float = 0.6,
    ) -> None: ...
    # Radial burst of short lines.

class Circumscribe:
    def __init__(
        self,
        mob: VMobject | VGroup,
        shape: str = "rect",  # "rect" | "circle"
        color: str = YELLOW,
        buff: float = 0.1,
        run_time: float = 1.0,
    ) -> None: ...
    # Animated outline around mob.
```

**Implementation.** `there_and_back(t) = 2 * min(t, 1-t)` — add to `rate_funcs.py` if not present.

**Files.**
- Edit: `chalk/src/chalk/animation.py`
- Edit: `chalk/src/chalk/rate_funcs.py` — add `there_and_back` if missing.
- Edit: `chalk/src/chalk/__init__.py`

**Tests.** `chalk/tests/test_emphasis.py`
- Indicate at alpha=0 and alpha=1 → mob back to original scale + color.
- Indicate at alpha=0.5 → mob scaled by `scale_factor`, recolored.
- Flash generates `num_lines` radial lines centered at point.
- Circumscribe(shape="rect") bbox matches target's bbox + buff on all sides.

**Exit.** 6+ new tests, 127+ total.

---

## 10. `Section` bookmarks + snapshot test helper (C1.6)

**Why.** Sections enable narration sync (C3.5) and incremental re-rendering (C3.4) — but the bookmarks themselves are cheap and should land early so examples can adopt them. Snapshot helper catches visual regressions before they pile up.

**API.**

```python
class Scene:
    # ... existing ...
    def section(self, name: str) -> None:
        """Mark the current timeline position with a named bookmark."""
    @property
    def sections(self) -> list[tuple[str, int]]:
        """List of (name, frame_index) pairs emitted so far."""

# chalk/testing.py (new module)
def snapshot(
    scene_cls: type[Scene],
    at_second: float,
    width: int = 640,
    height: int = 360,
    fps: int = 30,
) -> np.ndarray:
    """Render a single frame at t seconds; return RGBA ndarray."""

def assert_snapshot(
    scene_cls: type[Scene],
    at_second: float,
    snapshot_name: str,
    update: bool = False,
) -> None:
    """Render + compare against tests/snapshots/<name>.png byte-identically."""
```

**Snapshot file layout.** `chalk/tests/snapshots/<scene_class>_<at_second>s.png`. First run with `UPDATE_SNAPSHOTS=1` env var (or `update=True`) writes the baseline.

**Render path.** Reuse FFmpegSink pattern but with a single-frame surface: run `scene.construct()` with a `FrameCapture` sink that records the frame whose cumulative time crosses `at_second`. Stop after capture.

**Files.**
- Edit: `chalk/src/chalk/scene.py` — `section` method, `sections` property, track frame index in play/wait.
- New: `chalk/src/chalk/testing.py` — `snapshot`, `assert_snapshot`, `FrameCapture` sink.
- New: `chalk/tests/snapshots/` (gitignored only if empty; otherwise checked in)
- Edit: `chalk/src/chalk/__init__.py` (export `section` via Scene; testing helpers are imported as `from chalk.testing import ...`).
- Edit: `chalk/.gitignore` — nothing; snapshot PNGs ARE checked in.

**Tests.** `chalk/tests/test_sections_snapshot.py`
- After a Scene runs a play + wait + section("beat2") + play, `scene.sections == [("beat2", expected_frame_idx)]`.
- `snapshot(SimpleScene, 0.0)` returns a valid ndarray of shape (H, W, 4).
- `assert_snapshot(SimpleScene, 1.0, "simple_1s", update=True)` writes the PNG.
- Second call with `update=False` passes byte-identically.
- Hand-break the scene's color → second call fails with a diff image dumped to `chalk/tests/snapshots/diffs/`.

**Adoption.** Add `assert_snapshot` calls for the flagship examples (newton, voltage_divider, kirchhoff, claude_code, damped_oscillation, morph_demo). These lock in visual parity before feature work continues.

**Exit.** 6+ new tests + 6 example-snapshot tests = 139+ total.

---

## Process notes for the handoff

- **Stop and ask before inventing scope.** Each of these 10 is a single commit on a clean main. If you discover a feature needs a prerequisite that isn't listed, add it as feature 11+ and flag rather than balloon the PR.
- **Every scene-breaking change ships with updated snapshot baselines in the same commit.** Don't let diffs pile up.
- **Append to `workflows/lessons.md` whenever a mistake is caught.** Format is in the file header. Keep entries ≤ 8 lines.
- **Run `uv run pytest tests/ -x --tb=short` after every feature, not at the end of the session.**
- **Render every new example.** `chalk/CLAUDE.md` requires it; every frame must look finished.
- **No Claude co-author trailers in commits.** CLAUDE.md line 59.
- **Don't amend commits.** Always create new ones if a hook fails.
- **Kill criteria still apply.** If feature 1 takes a week because ValueTracker integration blows up, stop and reconsider. ADR 0001 K1–K5 are the guardrails.

After all 10 land: Phase C1 parity floor target is 105 tests; this list projects 139+ if every sub-count is met. Gap → add to CHALK_ROADMAP Phase C1 or defer. Phase C1 exit criterion (10 calculus topics render on chalk) is separate and requires the pedagogica skill side also authored.

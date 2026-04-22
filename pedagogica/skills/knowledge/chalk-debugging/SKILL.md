---
name: chalk-debugging
version: 0.1.0
category: chalk
triggers:
  - stage:chalk-repair
  - retry:any
requires:
  - chalk-primitives@^0.1.0
token_estimate: 2800
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-21
description: >
  Error catalog + repair playbook for chalk (this repo's 2D animation renderer).
  Nine canonical failure modes with stderr fingerprints, root causes, exact fixes,
  and before/after code diffs. Loaded by the chalk-repair agent on every retry.
  Not loaded on the first codegen pass. Replaces manim-debugging since 2026-04-21
  (ADR 0001).
---

# chalk-debugging

## Purpose

When `chalk-render` fails, the orchestrator classifies the error and routes it to `chalk-repair`. Repair reads the stderr, identifies which catalog entry this is, applies the fix. This skill is the catalog.

Every time a repair succeeds on an error not in this catalog, the entry gets added. Every time a repair fails on an entry, the fix gets revised. This skill grows monotonically through Phase 1.

## When to load

- **chalk-repair — every retry.** Default mode: catalog entries only. Full-catalog mode (third attempt): entire file.
- **chalk-code — NOT on first pass.** Loading this on the happy path biases codegen toward defensive code.
- **Orchestrator — reads only the classification table** (from `error_catalog.yaml`), not the fixes.

## 1. Repair playbook

### Step 1 — Classify

Look at stderr. Find the last `Error:` or `Exception:` line before the traceback. Match against catalog fingerprints below. If multiple match, prefer the most specific.

### Step 2 — Localize

Find the line(s) in `code.py` that stderr points to. For LaTeX errors, the failing `MathTex(` call is usually the most recent caller in `construct`.

### Step 3 — Apply minimum change

Change the fewest lines that plausibly resolve the specific error. Stop.

### Step 4 — If unfamiliar error

This is a new failure mode. Proceed with the minimum change the stderr implies, and note the new failure mode in `skills_loaded` for the trace. The error will get a catalog entry after the session.

## 2. Error catalog

### E01 — stroke_color on shapes

**Classification:** `api_error`
**Fingerprint:** `TypeError.*stroke_color|unexpected keyword argument.*stroke_color`
**Symptom:** TypeError when constructing Rectangle, Circle, Line, Arrow, or Dot.
**Cause:** chalk shape constructors use `color=` for stroke, not `stroke_color=`. Manim uses `stroke_color`; chalk doesn't.
**Fix:** Replace `stroke_color=X` with `color=X`.

```python
# BEFORE
r = Rectangle(width=3.0, height=2.0, stroke_color=BLUE, fill_color=GREEN, fill_opacity=0.3)
# AFTER
r = Rectangle(width=3.0, height=2.0, color=BLUE, fill_color=GREEN, fill_opacity=0.3)
```

### E02 — move_to on VMobject

**Classification:** `api_error`
**Fingerprint:** `AttributeError.*'(Rectangle|Circle|Line|Arrow|Dot|VMobject)'.*'move_to'`
**Symptom:** AttributeError when calling `.move_to()` on a shape.
**Cause:** Only VGroup subclasses (MathTex, Text, VGroup, DecimalNumber, AlwaysRedraw) have `.move_to(x, y)`. Bare VMobject shapes use `.shift(dx, dy)`.
**Fix:** Replace `.move_to(wx, wy)` with `.shift(wx, wy)`. Coordinates must be absolute world coords, not data coords.

```python
# BEFORE (fails: 'Rectangle' object has no attribute 'move_to')
rect.move_to(wx_l + w / 2, wy_b + h / 2)
# AFTER
rect.shift(wx_l + w / 2, wy_b + h / 2)
```

### E03 — x_range on plot_function

**Classification:** `api_error`
**Fingerprint:** `TypeError.*plot_function.*x_range|unexpected keyword argument.*'x_range'`
**Symptom:** TypeError when calling `plot_function`.
**Cause:** `plot_function` uses `x_start` and `x_end` positional-ish args, not `x_range=`.
**Fix:** Replace `x_range=(a, b)` with `x_start=a, x_end=b`.

```python
# BEFORE
graph = plot_function(ax, f, x_range=(0.0, 3.0), color=BLUE)
# AFTER
graph = plot_function(ax, f, x_start=0.0, x_end=3.0, color=BLUE)
```

### E04 — ax.c2p not found

**Classification:** `api_error`
**Fingerprint:** `AttributeError.*'Axes'.*'c2p'|has no attribute 'c2p'`
**Symptom:** AttributeError on `ax.c2p(x, y)`.
**Cause:** chalk's Axes uses `to_point`, not `c2p`. Manim uses `c2p`.
**Fix:** Replace `ax.c2p(x, y)` with `ax.to_point(x, y)`. Return signature: `(wx, wy)` — a tuple of floats, not a numpy array.

```python
# BEFORE
point = ax.c2p(2, 4)
# AFTER
wx, wy = ax.to_point(2, 4)
```

### E05 — Create not in chalk

**Classification:** `import_error`
**Fingerprint:** `cannot import name 'Create'|ImportError.*Create|NameError.*Create`
**Symptom:** ImportError or NameError on `Create`.
**Cause:** chalk has no `Create` or `DrawBorderThenFill`. Manim does.
**Fix:** Replace `Create(mob)` with `FadeIn(mob, run_time=d)`.

```python
# BEFORE
self.play(Create(graph, run_time=1.2))
# AFTER
self.play(FadeIn(graph, run_time=1.2))
```

### E06 — animate.set_value not in chalk

**Classification:** `api_error`
**Fingerprint:** `AttributeError.*'ValueTracker'.*'animate'|object has no attribute 'animate'`
**Symptom:** AttributeError on `x.animate.set_value(v)`.
**Cause:** chalk has no `.animate` property. Manim does.
**Fix:** Replace with `ChangeValue(tracker, target_val, run_time=d, rate_func=smooth)`.

```python
# BEFORE
self.play(x.animate.set_value(3.0), run_time=3.0)
# AFTER
from chalk import ChangeValue
from chalk.rate_funcs import smooth
self.play(ChangeValue(x, 3.0, run_time=3.0, rate_func=smooth))
```

### E07 — VMobject subpaths type error

**Classification:** `api_error`
**Fingerprint:** `TypeError.*'int' object is not subscriptable|TypeError.*subpaths`
**Symptom:** TypeError during rendering of a manually-built VMobject.
**Cause:** Code set `m.subpaths = [0]` (an int) instead of a list of numpy arrays or the falsy default `[]`. The renderer does `for pts in subpaths:` which fails on integers.
**Fix:** Remove any `m.subpaths = [...]` assignment when manually setting `.points`. The renderer treats falsy `subpaths` as "use `mob.points` as a single subpath".

```python
# BEFORE
m = VMobject(fill_color=GREEN, fill_opacity=0.5)
m.points = np.array(pts, dtype=float)
m.subpaths = [0]   # WRONG — TypeError at render time
# AFTER
m = VMobject(fill_color=GREEN, fill_opacity=0.5)
m.points = np.array(pts, dtype=float)
# leave subpaths alone (defaults to [])
```

### E08 — missing raw string prefix on LaTeX

**Classification:** `latex_error`
**Fingerprint:** `SyntaxError.*unicode error|KeyError.*\\\\[a-z]|LaTeX.*bad escape`
**Symptom:** SyntaxError or LaTeX compilation fails because Python interprets backslash escapes.
**Cause:** LaTeX source passed as a regular Python string; `\f` → form feed, `\n` → newline, etc.
**Fix:** Add `r` prefix to every LaTeX-containing string.

```python
# BEFORE
eq = MathTex("\frac{d}{dx}", color=PRIMARY)
# AFTER
eq = MathTex(r"\frac{d}{dx}", color=PRIMARY)
```

### E09 — wildcard import from chalk

**Classification:** `import_error`
**Fingerprint:** `ImportError.*cannot import.*\*|SyntaxError.*\*.*chalk`
**Symptom:** Import failure or NameError for a symbol that should be in chalk.
**Cause:** Code uses `from chalk import *` (forbidden per chalk-code skill) or a symbol isn't in the specific import list.
**Fix:** Replace wildcard import with the explicit symbol list. Check chalk-primitives for the correct import name.

```python
# BEFORE
from chalk import *
# AFTER
from chalk import (
    Scene, MathTex, FadeIn, Write,
    ValueTracker, ChangeValue, always_redraw,
    PRIMARY, BLUE, GREY,
    SCALE_BODY, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone,
)
```

## 3. Escalation rules

- Attempt 1 (Sonnet): apply the catalog fix for the classified error.
- Attempt 2 (Sonnet): if the error changed or persisted, widen the fix to the 40-line window around the offending line.
- Attempt 3 (Opus): if still failing, full-file + full catalog. Rewrites are allowed. A simplified-but-correct scene is acceptable.

Every failed repair is a signal to update this catalog. Append a new entry or revise an existing fix. The catalog grows monotonically through Phase 1.

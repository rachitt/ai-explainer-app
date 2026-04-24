---
name: chalk-repair
version: 0.2.0
category: orchestration
triggers:
  - stage:chalk-repair
  - compile:failure
requires:
  - chalk-primitives@^0.1.0
  - chalk-debugging@^0.1.0
  - latex-for-video@^0.0.0
token_estimate: 3800
tested_against_model: claude-sonnet-4-6
owner: rachit
last_reviewed: 2026-04-22
description: >
  Repairs a failing chalk scene. Reads the prior code.py and the CompileResult
  (stderr + error_classification), loads chalk-debugging, and emits a
  replacement ChalkCode. Runs on Sonnet 4.6 for attempts 1 and 2, escalates to
  Opus 4.7 on attempt 3. Context expands per attempt: minimal error → error +
  40-line window → full file + error catalog. Capped at 3 attempts total.
  Reconciled 2026-04-22 to the trimmed roster (no spec.json / placements.json).
  Replaces manim-repair since 2026-04-21 (ADR 0001).
---

# Chalk Repair agent

## Purpose

Fix a chalk scene that failed to render. Read `scenes/<scene_id>/code.py` (the failing source), `scenes/<scene_id>/compile_attempt_<N>.json` (the `CompileResult` with `success=false`), and the scene context: the matching `SceneBeat` in `03_storyboard.json` and the `scenes/<scene_id>/script.json`. Emit a **replacement** `code.py` + `code.json` that renders successfully.

Per `docs/ARCHITECTURE.md` §12, compile retries are capped at **3 attempts** with an **expanding context window** and **model escalation** on the last attempt.

Phase 1 has no `spec.json` or `placements.json` — visual planning and layout live inside `code.py` itself (chalk-code folds them inline). Do not attempt to read those files.

## Inputs

| Attempt | Files you read | Loaded skills | Model |
|---|---|---|---|
| 1 | `code.py`, `compile_attempt_1.json` (stderr only), matching `SceneBeat` in `03_storyboard.json`, `script.json` | `chalk-primitives`, `chalk-debugging` | Sonnet 4.6 |
| 2 | same + 40-line window around offending line, `compile_attempt_2.json` | same + `latex-for-video` if latex-classified | Sonnet 4.6 |
| 3 | same + full `code.py` end-to-end + `chalk-debugging` `error_catalog.yaml` entry | same + the `chalk-*-patterns` pack named in the storyboard's `required_skills` | **Opus 4.7** |

## Output

Write (overwriting prior versions):
1. `artifacts/<job_id>/scenes/<scene_id>/code.py` — repaired Python.
2. `artifacts/<job_id>/scenes/<scene_id>/code.json` — new `ChalkCode`:
   - `producer = "chalk-repair"`, fresh `span_id`, `parent_span_id` = prior `code.json`'s `span_id`.
   - `scene_class_name`: **unchanged from prior `code.json`**.
   - `skills_loaded`: union of prior + this attempt, appending `chalk-debugging@<version>`.

## Error-classification → strategy

Use the `error_classification` from `CompileResult`:

| Classification | Common root causes | First-line fix |
|---|---|---|
| `api_error` | Wrong kwarg (`stroke_color` → `color`), missing method (`move_to` on VMobject → `shift`), wrong arg name (`x_range` → `x_start`/`x_end`) | Match the failing call to chalk-debugging catalog; apply minimal rename. |
| `import_error` | Symbol doesn't exist in chalk, or not in the import list | Check chalk-primitives import table; add the correct name. |
| `latex_error` | Missing LaTeX package, unescaped symbols, raw string missing | Move colouring out of LaTeX to chalk's color=; escape raw chars; prefix string with `r`. |
| `syntax_error` | Missing colon, bad indent, stray bracket | Locate via stderr line number; fix the minimal offending expression. |
| `geometry_error` | Zero-size shapes, out-of-frame placement, mismatched shape types in Transform | Validate width/height > 0; use `ax.to_point()` for axes-anchored coords. |
| `under_duration` | Animation finishes well before narration; `AnimationGroup(lag_ratio=r)` under-renders | Pad the beat to at least 95% of target, then increase motion duration or de-stagger the group. |
| `timeout` | Render wall-clock exceeded 300 s | Shorten/simplify animations; reduce always_redraw factory expense. |
| `other` | Read stderr literally; match against chalk-debugging catalog | Apply the catalog fix; if missing, make the minimum change the stderr implies. |

### `under_duration`

Cause: animation finishes well before narration, often because `AnimationGroup(lag_ratio=r)` compresses the real play time below the author's naive sum.

Fix recipes, in order:
1. Append `self.wait(pad_seconds)` at the beat end so total runtime is at least `0.95 × target_duration_seconds`.
2. Raise per-animation `run_time` values on the motions that carry the narration.
3. Break `AnimationGroup(lag_ratio < 1.0)` into sequential `self.play()` calls when the stagger is collapsing the beat too aggressively.

Do not pad with static frames longer than 5 seconds. If more hold time is needed, split into sub-beats with subtle motion such as fading labels or ticking emphasis pulses.

## Attempt ladder

### Attempt 1 — minimal error, Sonnet

**Produce a minimal patch.** Change the fewest lines that plausibly resolve the specific error. Do not refactor; do not rewrite the whole scene; do not adjust layout or colour.

Diagnosis → patch → stop. Examples of good attempt-1 patches:
- `stroke_color=BLUE` → `color=BLUE`
- `rect.move_to(x, y)` → `rect.shift(wx, wy)` (where wx, wy come from `ax.to_point` or layout)
- `plot_function(ax, f, x_range=(0,3))` → `plot_function(ax, f, x_start=0, x_end=3)`

### Attempt 2 — error + 40-line window, Sonnet

If attempt 1 didn't close the error, or the error changed (a second error surfaced), widen the fix. Rewrite the failing block. Do not touch anything outside the 40-line window unless stderr explicitly points there.

### Attempt 3 — full file + error catalog, Opus

Root-cause the failure. Rewrite the entire scene body if needed — subject to preserving `scene_class_name`, element ids referenced by script markers, and the storyboard's `visual_intent`.

If the error is planning-level (e.g., spec asks for an element that can't be realised), ship a simplified-but-correct scene. Phase 2's critic loop regenerates the spec; Phase 1 ships something watchable.

## What to preserve

Across all attempts:
- **`scene_class_name`** — never rename.
- **Element ids referenced by script markers** — if a marker says `show eq.secant`, the repaired code must still construct `eq_secant`.
- **Palette constants** — do not edit; chalk's named palette (`PRIMARY`, `BLUE`, `YELLOW`, `GREEN`, `RED_FILL`, `GREY`) is authoritative. Do not substitute raw hex.
- **Visual intent from the storyboard** — a simpler rendering is fine; a different scene is not.
- **Inline layout decisions in the prior `code.py`** — if a placement caused the crash (e.g. `font_size=0`, a shape centred off-frame), clamp the specific value locally; don't re-plan the whole scene's layout.

## What you may change

- Construction calls — swap primitives, fix kwargs, add missing args.
- Animation primitive choice — `Write` ↔ `FadeIn`, `Transform` ↔ `TransformMatchingTex`, etc.
- LaTeX source — drop `\color{}`, escape chars, add `r` prefix.
- Add intermediate variables where needed for clarity.

## Chalk-specific repair patterns

### `stroke_color` → `color`

chalk shape constructors use `color=` for stroke (not `stroke_color=`):
```python
# BEFORE (fails)
r = Rectangle(width=3.0, height=2.0, stroke_color=BLUE, fill_color=GREEN)
# AFTER
r = Rectangle(width=3.0, height=2.0, color=BLUE, fill_color=GREEN)
```

### `.move_to()` on VMobject shapes

Only VGroup subclasses (MathTex, Text, VGroup, DecimalNumber, AlwaysRedraw) have `.move_to()`.
Circle, Rectangle, Line, Arrow, Dot use `.shift(dx, dy)`:
```python
# BEFORE (fails: 'Rectangle' object has no attribute 'move_to')
rect.move_to(wx, wy)
# AFTER
rect.shift(wx, wy)
```

### `x_range` on `plot_function`

```python
# BEFORE (fails: got unexpected keyword argument 'x_range')
graph = plot_function(ax, f, x_range=(0.0, 3.0), color=BLUE)
# AFTER
graph = plot_function(ax, f, x_start=0.0, x_end=3.0, color=BLUE)
```

### `ax.c2p()` → `ax.to_point()`

chalk's axes use `to_point`, not `c2p`:
```python
# BEFORE (fails: 'Axes' object has no attribute 'c2p')
point = ax.c2p(2, 4)
# AFTER
wx, wy = ax.to_point(2, 4)
```

### `x.animate.set_value()` → `ChangeValue`

chalk has no `.animate` property. Use `ChangeValue`:
```python
# BEFORE (fails)
self.play(x.animate.set_value(3.0), run_time=3.0)
# AFTER
from chalk import ChangeValue
self.play(ChangeValue(x, 3.0, run_time=3.0))
```

### `Create()` → `FadeIn()`

chalk has no `Create` or `DrawBorderThenFill`:
```python
# BEFORE (fails: cannot import name 'Create' from 'chalk')
self.play(Create(graph))
# AFTER
self.play(FadeIn(graph, run_time=1.0))
```

### VMobject subpaths

When manually constructing a VMobject with `.points`, do not set `m.subpaths = [0]`. Either leave `subpaths` as `[]` (falsy, renderer uses `points` as single subpath) or set it to a list of numpy arrays:
```python
# BEFORE (TypeError: 'int' object is not subscriptable)
m.subpaths = [0]
# AFTER — just don't set subpaths at all; the renderer handles the default
# m.subpaths = []  (already the default)
```

### TransformMatchingTex — target glyphs invisible

This is a known scene.py bug **fixed in 2026-04-21** — if you see it, the chalk version is outdated. After the fix, unmatched target glyphs automatically persist. No code change needed; update chalk.

### under_duration

If a scene is rejected for running short, prefer `animated_wait_with_pulse(...)` over bare `self.wait(...)`. The pulse keeps the frame visually alive, satisfies duration accounting, and is the preferred repair recipe before you fall back to a static hold.

## Model

**Sonnet 4.6 for attempts 1 and 2. Opus 4.7 for attempt 3.**

## Validation

After writing, orchestrator runs:
```
uv run pedagogica-tools validate ChalkCode artifacts/<job_id>/scenes/<scene_id>/code.json
```

Self-check before emitting:
1. `scene_class_name` equals prior and appears as `class <NAME>(Scene):` in `code`.
2. The specific error from `compile_attempt_<N>.json.stderr` is addressed.
3. No `stroke_color=` on shapes. No `.move_to()` on bare VMobjects. No `x_range=` on `plot_function`. No `ax.c2p()`. No `Create()`.
4. `code` and `code.py` are byte-identical.

## Anti-patterns

- **Rewriting the whole scene on attempt 1** — burns a retry slot.
- **Renaming `scene_class_name`** — the render helper invokes it by name.
- **Inventing a different visual** — simplify, don't replace.
- **`try/except` around the failing call** — moves error to render time; compile passes but video is broken.
- **Ignoring `error_classification`** — each classification has a known pattern; use it.
- **Adding `x.animate.set_value()`** — chalk has no `.animate`. Use `ChangeValue`.
- **Using `stroke_color=`** — chalk uses `color=`.
- **Continuing past attempt 3** — hard fail. Don't attempt a fourth.
- **Changing PALETTE or colour constants** — chalk's named palette is authoritative; do not substitute hex.
- **Regenerating the script or re-planning the scene** — this agent fixes code only. Script edits belong to the script stage; scene re-planning belongs to chalk-code on a later run.

## Changelog

- **0.2.0** (2026-04-22) — reconciled to trimmed roster. `requires` drops `scene-spec-schema` and the deleted `color-and-typography`. Attempt table no longer reads `spec.json` / `placements.json` (they do not exist in Phase 1); instead reads the scene's storyboard beat + `script.json`. Attempt 3 loads the domain `chalk-*-patterns` pack named in `required_skills`.
- **0.1.0** (2026-04-21) — initial chalk port from manim-repair. chalk-specific repair patterns: stroke_color→color, move_to→shift, x_range→x_start/x_end, c2p→to_point, animate.set_value→ChangeValue, Create→FadeIn, VMobject.subpaths. Loads chalk-debugging instead of manim-debugging.

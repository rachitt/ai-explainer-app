---
name: manim-repair
version: 0.0.1
category: orchestration
triggers:
  - stage:manim-repair
  - compile:failure
requires:
  - scene-spec-schema@^0.1.0
  - manim-primitives@^0.0.0
  - manim-debugging@^0.0.0
  - latex-for-video@^0.0.0
  - color-and-typography@^0.1.0
token_estimate: 3600
tested_against_model: claude-sonnet-4-6
owner: rachit
last_reviewed: 2026-04-20
description: >
  Repairs a failing Manim scene. Reads the prior code.py and the CompileResult
  (stderr + error classification), loads manim-debugging, and emits a
  replacement ManimCode. Runs on Sonnet 4.6 for attempts 1 and 2, escalates to
  Opus 4.7 on attempt 3. Context expands per attempt: minimal error → error +
  40-line window → full file + error catalog. Capped at 3 attempts total; a
  fourth failure is a hard fail per docs/ARCHITECTURE.md §12.
---

# Manim Repair agent

## Purpose

Fix a Manim scene that failed to compile. Read `scenes/<scene_id>/code.py` (the failing source), `scenes/<scene_id>/compile_attempt_<N>.json` (the `CompileResult` with `success=false`), and any original inputs still live (`spec.json`, `placements.json`, `script.json`), and emit a **replacement** `code.py` + `code.json` (`ManimCode`) that, when recompiled, produces a valid scene video.

This agent is the only path back from a compile failure. The `manim-code` agent does not loop on itself — a failure there routes straight here. Conversely, this agent does not revisit pedagogy, narration, or scene planning. It fixes the code until it runs. Pedagogical or layout issues that surface as compile errors (e.g. "this LaTeX is impossible because the equation the planner asked for doesn't exist") are flagged in `skills_loaded` and left for the Phase-2 repair loop that re-invokes upstream agents.

Per `docs/ARCHITECTURE.md` §12, compile retries are capped at **3 attempts** with an **expanding context window** and a **model escalation** on the last attempt. A fourth consecutive failure is a hard fail — the orchestrator marks the scene failed, the job continues without that scene only if the Phase-2 graceful-degradation policy allows (Phase 1: hard-fail the whole job, log, exit).

## Inputs

The orchestrator invokes you with an attempt number `N ∈ {1, 2, 3}` and the following files, scoped to the attempt:

| Attempt | Files you read | Loaded skills | Model |
|---|---|---|---|
| 1 | the failing `code.py` (entire file is always provided; the expansion below is what the **prompt asks you to attend to**), `compile_attempt_1.json` stderr only, `spec.json`, `placements.json` | `scene-spec-schema`, `manim-primitives`, `manim-debugging` | Sonnet 4.6 |
| 2 | same + a 40-line window around the stderr's referenced line in `code.py`, `compile_attempt_2.json` | same + `latex-for-video` if the error is LaTeX-classified | Sonnet 4.6 |
| 3 | same + the full `code.py` read end-to-end + `manim-debugging`'s `error_catalog.yaml` entry for `error_classification` | same + `color-and-typography` + the original `manim-<domain>-patterns` pack that was loaded by `manim-code` | **Opus 4.7** |

The attempt number and the window come from the orchestrator; the intent is that attempt 1 stays cheap (Sonnet, small window) while attempt 3 pulls out the heaviest tool (Opus, full file, full catalog). See `knowledge/retry-strategy` for the routing rules.

Always-available inputs regardless of attempt:

- `artifacts/<job_id>/scenes/<scene_id>/spec.json` — what the scene is supposed to render.
- `artifacts/<job_id>/scenes/<scene_id>/placements.json` — positions, scales, z-order, font sizes. Do not re-derive; trust these.
- `artifacts/<job_id>/scenes/<scene_id>/script.json` (when present) — the spoken narration and markers; you only consult it to keep element ids consistent with what the script references.
- `artifacts/<job_id>/scenes/<scene_id>/code.py` — the failing source.
- `artifacts/<job_id>/scenes/<scene_id>/compile_attempt_<K>.json` for `K = 1..N` — every prior attempt's `CompileResult`. Previous stderrs and error classifications are signal you should not ignore on later attempts.
- `artifacts/<job_id>/scenes/<scene_id>/code.json` — prior `ManimCode.skills_loaded`, so you know what context the first-pass codegen had.
- `artifacts/<job_id>/03_storyboard.json` — the matching `SceneBeat`, for `visual_intent` when the fix requires picking between visually-equivalent rewrites.
- `artifacts/<job_id>/job_state.json` — `trace_id`.

## Output

Write (overwriting the prior versions):

1. `artifacts/<job_id>/scenes/<scene_id>/code.py` — the repaired Python. Must still be byte-identical to the `code` field of the `ManimCode` JSON.
2. `artifacts/<job_id>/scenes/<scene_id>/code.json` — new `ManimCode`:

   - Trace metadata: `trace_id` from job state, fresh `span_id`, `parent_span_id` = the previous `code.json`'s `span_id` (the failing first-pass, or the last failing repair — it's whatever produced the source you were just asked to fix), `timestamp`, `producer = "manim-repair"`, `schema_version = "0.1.0"`.
   - `scene_id`: unchanged.
   - `code`: full replacement Python, UTF-8. The prior file is overwritten — do not leave artifacts from earlier attempts in place.
   - `scene_class_name`: **unchanged from the prior `code.json`**. The render helper addresses the scene by name; renaming mid-repair breaks the compile invocation.
   - `skills_loaded`: the skills you consulted for this attempt, merged with the originals (union, de-duped). Append `manim-debugging@<version>` on every repair attempt.

The orchestrator writes a fresh `compile_attempt_<N+1>.json` after re-running the render against your output.

## Attempt ladder (the expansion rules)

The attempt-number contract is the core of this skill. Different attempts get different **context**, not different **tasks** — the task is always "make the scene compile". The expansion protects against two failure modes:

- **Cheap fixes first.** ~60% of compile failures are one-liners: a missing comma, a typo in a method name, a `MathTex` vs `Tex` confusion. Attempt 1 on Sonnet with a minimal prompt closes these without burning Opus budget.
- **Escalation avoids learned helplessness.** If attempt 1 failed because Sonnet didn't have enough context to see the root cause, attempt 2 widens the window; if attempt 2 failed because Sonnet mis-diagnosed, attempt 3 gives Opus everything.

### Attempt 1 — minimal error, Sonnet

Given: the stderr, the error classification, the full `code.py` (reference only — focus on the error).

Task: produce a minimal patch. Change the fewest lines that plausibly resolve the specific error. Do **not** refactor. Do **not** rewrite the whole scene. Do **not** adjust layout or colour.

Good attempt-1 shape:

> The stderr says `ValueError: Axes requires both x_range and y_range`. Line 22 calls `Axes(axis_config=...)` without ranges. Add `x_range=[-1, 3, 1], y_range=[-1, 5, 1]` from the spec. Nothing else changes.

Bad attempt-1 shape:

> While I was in there I noticed the graph colour could be more vibrant, so I switched it from `primary` to `variable`…

Cost of a bad attempt 1: you burn a retry slot without closing the error, and the pipeline escalates to Opus for a problem Sonnet could've nailed with discipline.

### Attempt 2 — error + 40-line window, Sonnet

Given: the stderr, both prior classifications, a 40-line source window around the offending line (typically line `L-20 .. L+20`), and the full file as reference.

Task: think harder. The minimal patch didn't work — that often means:

- The error was correctly diagnosed but the fix pattern was wrong (e.g. LaTeX packages unavailable → replaced `\color{blue}` with `\textcolor{blue}` when the right fix is to move colouring out of LaTeX entirely).
- The error was mis-diagnosed and the true cause is 10–20 lines away (e.g. an `Arrow` constructed with the wrong point type earlier that only blows up at render time).
- Two errors were present and attempt 1 only fixed one; the second surfaces as a different stderr on `compile_attempt_2.json`.

Widen what you're willing to change. You can rewrite the failing animation block; you can restructure element construction. Do **not** touch the `PALETTE` dict, the class name, or anything outside the 40-line window unless the stderr points at it directly.

### Attempt 3 — full file + error catalog, Opus

Given: everything above, the full `code.py` read end-to-end, `manim-debugging`'s `error_catalog.yaml` entry for the stderr's `error_classification`, and the `manim-<domain>-patterns` pack that was loaded by the original codegen.

Task: root-cause the failure. By the time you're here, the previous two attempts were cheap fixes that didn't work, so the error is almost certainly structural:

- Version mismatch between the code's assumed API and Manim 0.19.x (e.g. `get_graph` was renamed to `plot`).
- A missing LaTeX package the sandbox doesn't provide — fix by removing the LaTeX dependency, not by invoking the package.
- An element the spec asked for that can't be realised with the primitives available (fall back to a simpler primitive and flag).

You are allowed to rewrite the entire scene body — subject to preserving `scene_class_name`, the element ids referenced by `script.json`'s markers, and the general visual intent from the storyboard. This is the expensive attempt; make it count.

If the error is pedagogical or planning-level (e.g. the spec asks for an arrow between two graph points that don't exist in the function's domain), prefer to **ship a simplified-but-correct scene** over a pixel-perfect-but-broken one. Phase 2's critic loop will regenerate the spec; Phase 1 ships something watchable.

### After attempt 3 — hard fail

If attempt 3's `compile_attempt_4.json` is still `success: false`, do **not** attempt a fourth repair. The orchestrator hard-fails the job (`docs/ARCHITECTURE.md` §12: "Sandbox violation / Cost cap hit / Schema validation fail / LLM call timeout" ladder applies here for compile errors that won't resolve). `job_state.stages.manim_code = failed`, `terminal = true`, partial artifacts preserved.

Resumption is a single `/pedagogica resume <job_id>` with a fresh skill load; Phase 2 will re-plan the scene.

## Error-classification → strategy cheat sheet

Use the `error_classification` field on `CompileResult` to pick the fix pattern. The full catalog lives in `manim-debugging/error_catalog.yaml`; this table is the highlights.

| Classification | Common root causes | First-line fix |
|---|---|---|
| `import_error` | `from manim import X` where X was renamed in 0.19.x, or a missing standard-library import | Replace with the 0.19.x name; drop the import if symbol is no longer used. |
| `latex_error` | Missing LaTeX package (`xcolor`, `amssymb`), unescaped symbols, or mismatched `{}` | Move colouring from LaTeX to Manim's `set_color_by_tex` / `set_color`. For missing packages, rewrite without the package. |
| `geometry_error` | `Axes` / `NumberPlane` constructed without required ranges, points passed in the wrong coordinate system (screen vs axes) | Supply `x_range` / `y_range` from the spec. Use `axes.c2p(x, y)` for points in axis space, never raw numeric tuples. |
| `timing_error` | `run_time=0`, negative wait, `Transform` between objects with incompatible shapes | Clamp to `run_time >= 0.1`. For `Transform`, both objects must be `VMobject`s with compatible submobject counts; use `ReplacementTransform` if they don't. |
| `memory_error` | Too many mobjects created in a loop, or a graph sampled at too high resolution | Reduce loop bounds; drop `n=` on `Axes` / set `tips=False`. |
| `timeout` | Render wall-clock exceeded 300 s | Usually a pathological animation loop — not a code bug. Shorten / simplify rather than retrying identically. |
| `other` | Anything not covered above | Read the stderr literally. If you can't classify it, ship the minimal fix the stderr suggests and widen the error catalog in your `skills_loaded` note. |

Every repair attempt must cite which classification it addressed. Pipeline telemetry joins classification × attempt-number × outcome, which feeds the next rev of `manim-debugging`.

## What to preserve

Across all attempts, keep these invariants:

- **`scene_class_name`** — matches the prior `code.json`.
- **Element ids referenced by `script.json` markers** — if a marker says `show eq.secant`, the repaired code must still construct `eq_secant`.
- **The `PALETTE` dict** — don't edit it. If a hex value is wrong, that's a `color-and-typography` issue, not a repair issue.
- **The visual intent from the storyboard** — the repaired scene should still show a secant-to-tangent if that's what the beat is for. A minimal scene that ships is better than a missing scene; a different scene entirely is not acceptable.
- **Manim Community 0.19.x idioms** — no `manimgl`, no pre-0.18 APIs, no community-fork extras.
- **Layout placements** — `ElementPlacement.position / scale / z_order / font_size` carry through unchanged. If a placement caused the crash (e.g. font_size 0), the spec / layout is wrong and the fix is to clamp locally, not to renegotiate the layout.

## What you may change

- Element construction calls — swap `Tex` for `MathTex`, `Arrow` for `Line`, `get_graph` for `plot`, etc.
- Animation primitive choice — swap `Transform` for `ReplacementTransform`, `Write` for `Create`, etc.
- LaTeX source — drop `\color{}` in favour of Manim's colour methods; escape stray characters.
- Run-times — clamp to `[0.1, 3.0]` if the spec's value caused a `timing_error`.
- Add intermediate variables or helper lines where needed to make the fix readable.

## Model

**Sonnet 4.6 for attempts 1 and 2. Opus 4.7 for attempt 3.** The orchestrator sets this; you don't self-route. If you find yourself needing Opus-level reasoning at attempt 1, that's a signal the first-pass codegen was missing context, and the right outcome is for this attempt to fail cheaply so the escalation kicks in.

Prompt caching: attempts 2 and 3 share the bulk of their preamble (`scene-spec-schema`, `manim-primitives`, `manim-debugging`, and the domain pack) with the original `manim-code` call — cache hits are expected to be high. Opus on attempt 3 is warm-cache in the common case.

## Validation

After writing, the orchestrator runs:

```
uv run pedagogica-tools validate ManimCode artifacts/<job_id>/scenes/<scene_id>/code.json
```

Exit 1 → one re-prompt with stderr; second failure is a hard fail for the attempt (counts against the 3-attempt cap). The validator rejects the same things it does for first-pass `manim-code`; in practice the failures here are more often at the compile stage than at schema validation.

Before emitting, self-check:

1. `scene_class_name` in `code.json` equals the prior `code.json`'s value and appears as `class <NAME>(Scene):` in `code`.
2. The specific error cited in `compile_attempt_<N>.json.stderr` is addressed by a change you can point at.
3. No new raw hex literals, no new imports beyond the standard set, no new `Scene` subclasses.
4. `code` and `code.py` are byte-identical.

## Example

Following on from the `docs/SKILLS.md` §5.2 failure path. Scene 03 (`example` beat, Riemann sum) failed first-pass with:

```
stderr: "ValueError: Cannot call .get_graph() on Axes without specifying x_range and y_range"
error_classification: geometry_error
attempt_number: 1
```

### Attempt 1 (Sonnet, minimal-error)

Loaded: `scene-spec-schema`, `manim-primitives`, `manim-debugging`. Fix: `get_graph` → `plot` (renamed in 0.19.x) and supply ranges from the spec. Everything else unchanged. `skills_loaded` appends `manim-debugging@0.0.1`.

Recompile → stderr changes:

```
stderr: "LaTeX Error: File 'xcolor.sty' not found"
error_classification: latex_error
attempt_number: 2
```

### Attempt 2 (Sonnet, error + 40-line window)

Loaded: previous + `latex-for-video`. The offending line is `MathTex(r"\color{blue}{x^2}", ...)` inside the element construction block. Fix: remove `\color{}`, emit plain LaTeX, then colour via `.set_color_by_tex("x^2", PALETTE["variable"])`. Don't touch the animations or the layout.

Recompile → stderr changes:

```
stderr: "AttributeError: 'Transform' object has no attribute 'target'"
error_classification: other
attempt_number: 3
```

### Attempt 3 (Opus, full file + error catalog)

Loaded: previous + `color-and-typography` + `manim-calculus-patterns` + `manim-debugging`'s full `error_catalog.yaml` for `other`. Root cause: the scene constructs `rect_i` objects in a loop and then plays `Transform(rect_i, rect_j)` — Manim 0.19.x's `Transform` requires both objects to be added to the scene first, and the previous `Transform` in the loop has consumed `rect_i` as a target. Fix: use `ReplacementTransform` inside the loop and add `self.add(rect_i)` before the first `Transform`. Recompile → success, 5.1 s render.

`code.json` (abbreviated, trace metadata elided):

```json
{
  "scene_id": "scene_03",
  "code": "from manim import *\nimport numpy as np\n\nPALETTE = {...}\n\nclass Scene03(Scene):\n    def construct(self):\n        ...",
  "scene_class_name": "Scene03",
  "skills_loaded": [
    "scene-spec-schema@0.1.0",
    "manim-primitives@0.0.1",
    "manim-debugging@0.0.1",
    "latex-for-video@0.0.1",
    "color-and-typography@0.1.0",
    "manim-calculus-patterns@0.0.1"
  ]
}
```

Trace shows three compile events, two `manim_repair` events, and the successful attempt 3. The `xcolor` recurrence is a signal to add an entry to `manim-debugging/error_catalog.yaml` so attempt 2 of the next job that hits it lands more decisively.

## Anti-patterns

- **Rewriting the whole scene on attempt 1.** The cap is 3 attempts; spending one on a refactor burns a retry and delays the actual fix.
- **Renaming `scene_class_name`.** The render helper invokes it by name. A rename is a silent compile success + render failure ("No scene named SceneNN").
- **Inventing a different visual.** The storyboard's `visual_intent` is the contract. A simpler rendering is fine; a different scene is not.
- **Ignoring the `error_classification`.** Each classification has a known fix pattern; matching to the pattern first is faster than reasoning from stderr.
- **Bumping `run_time`s to "give Manim time to compile".** Compile time and render time are different phases. Run-time doesn't affect whether the file parses.
- **Adding `try/except` around the failing call.** That moves the error to render time; the compile passes but the scene renders wrong. The sandbox will succeed and the video will be broken.
- **Loading `manim-<domain>-patterns` from a domain other than the original.** The original codegen pack is the right one — adding `manim-linalg-patterns` to a calculus repair doesn't help, and its examples can actively mislead.
- **Skipping the classification update.** Every repair must cite which `error_classification` it addressed. Telemetry depends on this; the next rev of `manim-debugging` depends on this telemetry.
- **Continuing past attempt 3.** The cap is firm. A fourth attempt is a hard fail, not a freebie. See `docs/ARCHITECTURE.md` §12.
- **Changing `PALETTE`.** Colour-system changes are `color-and-typography`'s domain; they don't belong in a repair.
- **Regenerating spec / layout / script.** This agent fixes code only. Upstream artifacts are inputs, not outputs.

## Changelog

- **0.0.1** (2026-04-20) — initial Phase 1 draft. Sonnet 4.6 for attempts 1–2, Opus 4.7 for attempt 3. Expanding context ladder (minimal → 40-line window → full file + error catalog). Capped at 3 attempts per `docs/ARCHITECTURE.md` §12. Loads `manim-debugging` on every repair attempt. Preserves `scene_class_name`, script-referenced ids, layout placements, and `PALETTE`.

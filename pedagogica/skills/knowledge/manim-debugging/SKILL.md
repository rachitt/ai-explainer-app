---
name: manim-debugging
version: 0.1.0
category: manim
triggers:
  - stage:manim-repair
  - retry:any
requires:
  - manim-primitives@^0.1.0
token_estimate: 4300
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-21
description: >
  Error catalog + repair playbook for Manim Community 0.19.x. Eight canonical
  failure modes with stderr fingerprints, root causes, exact fixes, and before /
  after code diffs. Loaded by the Manim-repair agent on every retry. Not
  loaded on the first codegen pass — if the agent knew these errors, it
  wouldn't emit the code that triggers them. The error fingerprints drive the
  orchestrator's error_classification field in `compile_attempt_N.json`.
---

# manim-debugging

## Purpose

When `manim-render` fails, the orchestrator classifies the error and routes it to `manim-repair`. Repair's job is: read the stderr, identify which catalog entry this is, apply the fix from that entry. This skill is the catalog.

The catalog isn't exhaustive. It starts with the eight errors we expect to hit most often on Phase 1 calculus scenes, based on:
- The Manim 0.18 → 0.19 API changes that older code examples still reflect.
- LaTeX dependency issues on fresh `basictex` installs.
- Idiomatic mistakes the Manim-code agent is likely to make when given a lot of pattern examples and little explicit API reference.

Every time a repair succeeds on an error *not* in this catalog, the entry gets added (per `docs/SKILLS.md §6` version bumping rules). Every time a repair *fails* on an error that is in the catalog, the fix gets revised. This skill grows monotonically through Phase 1; by week 6 expect ~20 entries.

## When to load

- **Manim-repair — every retry.** Default mode loads just the catalog entries; "full catalog mode" (on third attempt, per `retry-strategy`) loads the whole file.
- **Manim-code — not on first pass.** Loading this skill on the happy path would bias the agent toward writing defensive code for errors it wouldn't have made.
- **Orchestrator — reads the classification table only** (§2), not the fixes. It uses the fingerprint regexes to map stderr → `error_classification`.

## Contents

Section 1 is the prose playbook — how to approach a repair. Section 2 is the catalog itself (and canonically lives in `error_catalog.yaml`, which is the machine-readable view). Section 3 is the escalation rules that feed `retry-strategy`.

## 1. Repair playbook

When you receive a failing `code.py` + stderr:

### Step 1 — Classify

Look at stderr. Find the most specific line that says what failed: usually the last `Error:` or `Exception:` line before the traceback's `raise`. Match it against the catalog fingerprints (§2). If exactly one entry matches, apply that fix. If multiple match, prefer the most specific (e.g., `LaTeX Error: File 'xcolor.sty' not found` matches both `latex-missing-package` and `latex-compile-error`; pick the former).

If no entry matches, this is a new failure mode. Proceed to step 2.

### Step 2 — Localize

Find the line(s) in `code.py` that stderr points to. For LaTeX errors, the line number in stderr is often inside Manim's own code — what you want is the most recent caller in your scene's `construct`. Grep for `MathTex(` or `Tex(` near the error.

### Step 3 — Apply the minimum change

Catalog fixes are deliberately local. Resist the urge to refactor. If the fix is "replace `.get_graph()` with `.plot()`", replace exactly that call, not every graph call. Scope matters because:
- The orchestrator's prompt-cache hit rate depends on most of `code.py` being unchanged.
- Large rewrites introduce new errors; catalog fixes are proven against their error.

### Step 4 — Verify

If you have shell access in the repair pass (Phase 1: yes, via `pedagogica-tools manim-render`), re-run and confirm it compiles. If it succeeds, the repair is done. If it fails with a *new* error, classify that one and loop. If it fails with the *same* error, the catalog entry is wrong; this is feedback for the skill (§4).

### Step 5 — Don't escalate on predictable errors

`retry-strategy` escalates Sonnet → Opus on attempt 3. That's expensive; don't trigger it for catalog-covered errors. If you're the repair agent and the error has a catalog entry, apply the fix on attempt 2 — don't signal "hard retry needed". Escalation is for errors *without* a catalog entry.

## 2. Error catalog

Each entry has:

- `id`: stable identifier for tracing.
- `fingerprint`: regex that matches stderr. Used by the orchestrator to classify.
- `classification`: one of `latex_error`, `api_version_error`, `geometry_error`, `type_error`, `scene_structure_error`, `resource_error`.
- `symptom`: what the viewer sees / what stderr actually says.
- `cause`: why it happens.
- `fix`: the exact change to make.
- `patch_example`: before / after snippet.

The machine-readable version is `error_catalog.yaml`. The prose below mirrors it.

### 2.1 `latex-missing-package` — "LaTeX Error: File 'X.sty' not found"

**Fingerprint:** `LaTeX Error: File '[\w\-]+\.sty' not found`

**Classification:** `latex_error`

**Symptom:** Manim raises `RuntimeError: latex error converting to dvi`, and the underlying `.log` file has `LaTeX Error: File 'xcolor.sty' not found` (or `relsize.sty`, `standalone.cls`, etc.).

**Cause:** Manim's LaTeX template pulls in a handful of packages that aren't in a minimal `basictex` install.

**Fix:** Install the missing package with `tlmgr`. Do **not** remove the offending `MathTex` call from the scene — that masks the problem.

```bash
sudo tlmgr install xcolor
# or for the whole Manim dependency set:
sudo tlmgr install standalone preview doublestroke relsize everysel ms \
    rsfs setspace tipa wasy wasysym xcolor jknapltx
```

**Patch (environment, not code):** `tlmgr install <package>`.

**Repair-agent note:** If `tlmgr` is not available to the repair agent (sandboxed rendering), flag with `error_classification: latex_error, needs_environment_fix: true` — the orchestrator treats this as a skip, not a retry.

### 2.2 `axes-get-graph-renamed` — `TypeError: getter() got an unexpected keyword argument 'color'` (or equivalent)

**Fingerprint:** `get_graph|getter\(\) got an unexpected keyword argument`

**Classification:** `api_version_error`

**Symptom:** On 0.19.x the exact error is usually `TypeError: Mobject.__getattr__.<locals>.getter() got an unexpected keyword argument 'color'` (because `.get_graph` is caught by Manim's attribute-as-getter dispatch and silently returned as a 0-arg getter, which then rejects the kwargs). On older / newer lines the same intent surfaces as `AttributeError: 'Axes' object has no attribute 'get_graph'`. Either way, the upstream cause is identical.

**Cause:** Stale reference material. ManimCE renamed `get_graph` → `plot` in 0.18. Old 3Blue1Brown / ManimGL code still uses `get_graph`.

**Fix:** Replace `.get_graph(` with `.plot(` at the call site. Signature is compatible.

**Patch:**

```python
# before
curve = ax.get_graph(lambda x: x**2, color=BLUE)
# after
curve = ax.plot(lambda x: x**2, color=BLUE)
```

### 2.3 `transform-missing-shape` — `Cannot call Transform on mobject with no points`

**Fingerprint:** `VMobject has no points|Transform.*shape.*mismatch|ReplacementTransform.*empty`

**Classification:** `type_error`

**Symptom:** `ValueError: VMobject has no points` from inside `Transform.__init__` or similar. Often thrown when the source of a `Transform` was never `add`ed to the scene, or was removed before the transform runs.

**Cause:** `Transform(a, b)` expects `a` to have geometry. If `a` was built but never animated in (`Create`, `Write`, or explicit `add`), it has no rendered points and the interpolation can't start.

**Fix:** Either `self.add(a)` before the transform, or animate `a` in first with `Create`/`Write`. If the intent is "place b where a would be, no intermediate animation", use `ReplacementTransform(a, b)` after `self.add(a)`.

**Patch:**

```python
# before
circle = Circle()
square = Square()
self.play(Transform(circle, square))   # circle has no points

# after
circle = Circle()
square = Square()
self.play(Create(circle))              # circle now has points
self.play(Transform(circle, square))
```

### 2.4 `c2p-on-raw-coordinates` — Elements outside frame / misaligned with axes

**Fingerprint:** `# geometry; no stderr. Detected by compositional check: mobjects are placed at scene coordinates but axes have non-default range`

**Classification:** `geometry_error`

**Symptom:** No Python error — code compiles and renders. But the rendered frame shows the dot/label off-axes or clipped. `manim-render` won't flag this; visual review / layout-agent post-check should.

**Cause:** `Dot([2, 4, 0])` places at scene coord (2, 4); if axes are `x_range=[0,10], x_length=7`, data coord (2, 4) ≠ scene coord (2, 4). Using raw coords on axes-anchored objects is the most common silent bug.

**Fix:** Route every placement through `ax.c2p(data_x, data_y)`:

**Patch:**

```python
# before
dot = Dot([2, 4, 0])                  # scene coords

# after
dot = Dot(ax.c2p(2, 4))                # data coords on the axes
```

**Repair-agent note:** This usually surfaces as "the scene looks wrong" feedback, not as a stderr. For Phase 1, the agent should grep every `Dot(`, `.move_to(`, `.next_to(` inside any scene with an `Axes` and verify it uses `c2p` when anchoring to data space.

### 2.5 `updater-leaks-past-scene` — Phantom jitter on final frame

**Fingerprint:** `# no stderr; detected post-render by frame-diff on last frame`

**Classification:** `scene_structure_error`

**Symptom:** The final frame of the rendered mp4 shows a subtle flicker: a tangent line jitters, a DecimalNumber counter wobbles between two values on the last frame. Post-hoc visual review catches this; CI doesn't.

**Cause:** Mobjects with `.add_updater` or `always_redraw` stay live during the scene's final `self.wait`. The updater is still recomputing every frame; if any input (usually a ValueTracker) has tiny numerical drift, the output jitters.

**Fix:** Call `.clear_updaters()` on every updater-bound mobject *before* the last `self.wait`:

**Patch:**

```python
# before
self.play(x.animate.set_value(3), run_time=3)
self.wait(0.5)   # dot, tangent, readout still updating

# after
self.play(x.animate.set_value(3), run_time=3)
dot.clear_updaters()
tangent.clear_updaters()
readout.clear_updaters()
self.wait(0.5)   # all frozen
```

### 2.6 `mathtex-raw-string-missing` — `KeyError: '\\f'` or garbled output

**Fingerprint:** `SyntaxError: \(unicode error\)|KeyError.*\\\\[a-z]`

**Classification:** `latex_error`

**Symptom:** Python-level SyntaxError or KeyError thrown before LaTeX even runs; or LaTeX runs but the rendered text has stray characters (e.g., a form-feed `\x0c` where `\f` was intended).

**Cause:** LaTeX source passed without `r"..."` prefix. Python interprets `"\f"` as form feed, `"\n"` as newline, etc.

**Fix:** Prefix every LaTeX-containing string with `r`.

**Patch:**

```python
# before
eq = MathTex("\frac{d}{dx}")   # Python mangles \f

# after
eq = MathTex(r"\frac{d}{dx}")
```

### 2.7 `transform-matching-tex-identical` — No animation, warning

**Fingerprint:** `TransformMatchingTex.*no matching.*`, or a no-op transform

**Classification:** `type_error`

**Symptom:** `TransformMatchingTex(src, tgt)` where `src` and `tgt` compile to identical LaTeX; warning logged, no animation runs.

**Cause:** The matcher finds every substring on both sides, nothing is "changed", so nothing animates.

**Fix:** If the transform is semantically a re-draw (e.g., rebuilding with new colours), use `ReplacementTransform(src, tgt)`. If the transform should actually animate a change, check that `tgt` is different from `src` — often a typo means `tgt` is the same equation.

**Patch:**

```python
# before
same = MathTex(r"x^2")
also_same = MathTex(r"x^2")
self.play(TransformMatchingTex(same, also_same))   # no-op

# after
self.play(ReplacementTransform(same, also_same))
# or fix the target equation if it was meant to be different
```

### 2.8 `plot-discontinuity-crash` — Rendering fails on 1/x at x=0

**Fingerprint:** `RuntimeWarning: divide by zero|ZeroDivisionError.*plot`

**Classification:** `geometry_error`

**Symptom:** `ax.plot(lambda x: 1/x)` over a range that crosses 0 crashes with a divide-by-zero, or silently draws a spurious vertical line across the discontinuity.

**Cause:** Manim samples the function at evenly spaced x-values; if one lands exactly on (or near) the singularity, it fails or produces a huge y-value that becomes a near-vertical line segment.

**Fix:** Split the plot into two pieces that don't include the singularity, and/or pass `use_smoothing=False` to reduce the artifact:

**Patch:**

```python
# before
bad = ax.plot(lambda x: 1/x, x_range=[-2, 2])     # crosses 0

# after
left = ax.plot(lambda x: 1/x, x_range=[-2, -0.1])
right = ax.plot(lambda x: 1/x, x_range=[0.1, 2])
curve = VGroup(left, right)
```

For removable discontinuities that aren't singularities, use `discontinuities=[…]`:

```python
# discontinuity at x=1
g = ax.plot(lambda x: (x**2 - 1) / (x - 1), x_range=[-2, 3],
            discontinuities=[1], use_smoothing=False)
```

## 3. Escalation rules

The repair agent loads this catalog by default. Escalation triggers when a fix from the catalog doesn't resolve the error on attempt 2:

- **Attempt 1:** Manim-code (Opus) emits `code.py`. Compile fails.
- **Attempt 2:** Manim-repair (Sonnet) loads this catalog + the original skill pack. Applies fix. Compile re-runs.
- **Attempt 3:** If attempt 2 failed, escalate to Manim-repair (Opus). Full catalog mode + entire original file + error trace + previous repair attempt.
- **Attempt 4+:** No further retries in Phase 1 (per `retry-strategy`). Job marks the scene failed, orchestrator decides whether to proceed with a placeholder or abort the job.

Full catalog mode vs. default mode: default mode passes the classified entry to the agent; full catalog mode passes every entry. The escalation is because attempts 1–2 didn't recognize the error at all, so brute-forcing the whole catalog is cheaper than inventing a fix.

## 4. How catalog entries evolve

After every failed Phase 1 scene that was eventually repaired:

1. Extract the stderr and the successful `code.py` diff from the trace.
2. If the error matched an existing catalog entry: verify the fix worked; if not, revise the `fix` section.
3. If the error matched nothing: add a new entry with id `<verb>-<short-description>` (same style as §2), fingerprint, classification, cause, fix, patch.
4. Bump `version` (patch for fix tweaks, minor for new entries).
5. Update `last_reviewed`.

The regression suite in Phase 1 week 6 is the forcing function: it runs 10 topics and surfaces every repair path actually exercised. After week 6, the catalog should cover 90%+ of real failures; gaps close through Phase 2.

## Examples

`examples/` contains three worked repair walkthroughs — each one a `before.py` that fails, an `after.py` that succeeds, and a `repair_log.md` describing the classification and fix applied.

| # | File stem | Catalog entry exercised |
|---|---|---|
| 01 | `repair_01_get_graph_rename` | `axes-get-graph-renamed` |
| 02 | `repair_02_missing_c2p` | `c2p-on-raw-coordinates` |
| 03 | `repair_03_raw_string_missing` | `mathtex-raw-string-missing` |

These are *teaching* examples (they demonstrate the before/after for a reader), not test cases. The real tests are the regression suite and the rendered outputs of the pattern libraries.

## Gotchas / anti-patterns

- **"Fixing" by removing the failing call.** Deleting a `MathTex` because it's throwing a LaTeX error is not a repair; it's a lobotomy. The scene still needs the math.
- **Refactoring during repair.** A repair pass is not a code review. Change the minimum needed to resolve the error. Save improvements for Phase 2.
- **Ignoring the classification.** If the error is `latex_error` but you change Python code, you're fixing the wrong layer. Read the stderr first.
- **Catalog drift.** If the catalog says "do X" but you keep doing Y because Y also works, the catalog needs updating. Don't work around the skill.
- **Assuming stderr points to the Python line to edit.** For LaTeX errors, the Python line is often generic Manim internals; grep for the `MathTex(`/`Tex(` call upstream.

## Changelog

- **0.1.0** (2026-04-21) — initial Phase 1 ship. Eight canonical catalog entries covering LaTeX package issues, the `get_graph → plot` 0.18 rename, pointless Transforms, c2p/coordinate confusion, updater leaks, raw-string LaTeX errors, no-op TransformMatchingTex, and 1/x-style discontinuities. Repair playbook, escalation rules, three worked repair walkthroughs.

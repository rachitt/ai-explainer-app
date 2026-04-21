---
name: manim-code
version: 0.0.1
category: orchestration
triggers:
  - stage:manim-code
requires:
  - scene-spec-schema@^0.1.0
  - manim-primitives@^0.0.0
  - latex-for-video@^0.0.0
  - color-and-typography@^0.1.0
  - manim-calculus-patterns@^0.0.0
token_estimate: 4200
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Turns a SceneSpec + LayoutResult (+ optional Script) into a runnable Manim
  Community 0.19.x Python file for a single scene. Emits ManimCode — the
  full `code.py` body, the Scene class name, and the list of skills consulted.
  Opus 4.7 model tier. Reserved for first-pass codegen; failures route to
  manim-repair rather than regenerating here.
---

# Manim Code agent

## Purpose

Read `scenes/<scene_id>/spec.json` (`SceneSpec`), `scenes/<scene_id>/placements.json` (`LayoutResult`), and (when present) `scenes/<scene_id>/script.json` (`Script`), and emit `scenes/<scene_id>/code.py` — the Python file the render sandbox will execute. Also emit `scenes/<scene_id>/code.json` (`ManimCode`) carrying the code as a string, the Scene class name, and the list of skills loaded, so downstream stages (compile, repair, trace) have a structured record.

This is the single most reasoning-intensive call in the pipeline — you are turning a small graph of semantic elements and animations into ~150–400 lines of Manim Community 0.19.x that positions, renders, colours, times, and transitions everything correctly on the first try. That is why this agent runs on Opus 4.7 and every other stage runs on Sonnet or Haiku (see `docs/SKILLS.md` §4).

You are invoked **once per scene**, on the happy path. A compile failure does **not** loop back here — it routes to `manim-repair`, which has its own skill, context-expansion ladder, and model escalation policy. Your output is first-pass.

## Inputs

- `artifacts/<job_id>/scenes/<scene_id>/spec.json` — the `SceneSpec` you are rendering. Every `SceneElement` in `elements` must become a Manim object; every `SceneAnimation` in `animations` must become a `self.play(...)` call (or a `self.wait(...)` for gaps).
- `artifacts/<job_id>/scenes/<scene_id>/placements.json` — the `LayoutResult`. Every element's `(position, scale, z_order, font_size)` comes from here, not from the spec's `properties`. If `frame_bounds_ok` is `false`, flag in `skills_loaded` but still render — the repair loop handles out-of-bounds recovery.
- `artifacts/<job_id>/scenes/<scene_id>/script.json` — the `Script`, when available. Use its `markers` to confirm element ids you reference exist; do **not** write narration into the video (TTS and captioning are separate tiers).
- `artifacts/<job_id>/03_storyboard.json` — the matching `SceneBeat` for `required_skills` (e.g. `"manim-calculus-patterns"` signals you should load that pack) and `visual_intent` for context.
- `artifacts/<job_id>/job_state.json` — for `trace_id`.

## Output

Write two sibling files:

1. `artifacts/<job_id>/scenes/<scene_id>/code.py` — the runnable Python. Executed verbatim by `pedagogica-tools manim-render` inside `sandbox-exec`. Must import from `manim` only; no filesystem or network access.
2. `artifacts/<job_id>/scenes/<scene_id>/code.json` — `ManimCode`:

   - Trace metadata: `trace_id` from job state, fresh `span_id`, `parent_span_id = layout.span_id` (read from `placements.json`), `timestamp`, `producer = "manim-code"`, `schema_version = "0.1.0"`.
   - `scene_id`: matches the spec.
   - `code`: the full contents of `code.py` as a string (UTF-8). Keep this and the `.py` file byte-identical — the compile stage reads `.py`; everything else (trace, cache, repair) reads `code.json`.
   - `scene_class_name`: the entrypoint class the sandbox will invoke. Convention: `Scene<NN>` in PascalCase, e.g. `Scene04`. Must match the class name literally defined in `code`.
   - `skills_loaded`: list of skill `name@version` strings actually consulted (`scene-spec-schema@0.1.0`, `manim-primitives@0.x`, `color-and-typography@0.1.0`, and any `manim-<domain>-patterns` loaded). Feeds the cache key and the trace.

## Manim target

- **Manim Community `0.19.x`.** `pip install manim==0.19.*`. No `manimgl`, no `manim-community<0.18`, no `ManimGL` imports.
- **Single import line.** `from manim import *` is acceptable for Phase 1 — stays legible to reviewers and matches the ecosystem's examples. Additional imports only for standard library (`numpy`, `math`).
- **One `Scene` subclass per file.** Never emit multiple scene classes; the render helper invokes one and the others go un-rendered.
- **720p target.** Do not set `config.pixel_height` / `pixel_width` in the code — the render helper passes `-qm` (720p, 30 fps). Hardcoding dimensions fights the render flag.

## File template

Lay every file out in this order. Deviating makes diffs noisy and slows the repair loop when something moves.

```python
from manim import *
import numpy as np


PALETTE = {
    "background":  "#0E1116",
    "primary":     "#E8EAED",
    "variable":    "#4FC3F7",
    "result":      "#FFD54F",
    "correct":     "#66BB6A",
    "limit_target":"#66BB6A",
    "error":       "#EF5350",
    "bad_path":    "#EF5350",
    "annotation":  "#9AA0A6",
}


class SceneNN(Scene):
    def construct(self):
        self.camera.background_color = PALETTE["background"]

        # 1. element construction
        #    one block per element from spec.elements, in spec order
        ...

        # 2. placement
        #    positions/scales/z_order/font_size from LayoutResult
        ...

        # 3. animations
        #    one self.play(...) per SceneAnimation, honoring run_after DAG
        ...

        # 4. terminal hold
        self.wait(0.3)
```

### Construction block

- **One element per block**, in the order the spec lists them. Use the element `id` (with dots replaced by underscores) as the Python variable name: `eq.f` → `eq_f`, `graph.parabola` → `graph_parabola`. Stable, grep-able, matches the spec.
- **Match the `type` to the right Manim primitive** (see `manim-primitives` for the canonical table; summary below).
- **Resolve semantic colours via `PALETTE`**; never emit raw hex directly. If the semantic name isn't in the palette, that's a `color-and-typography` miss — pick the closest and flag.

### Placement block

- For each `ElementPlacement`, call `.move_to([x, y, 0])` (Manim uses 3D coords; z = 0 for 2D scenes).
- `scale` is applied via `.scale(s)` only when `s != 1.0`. Don't emit `.scale(1.0)` calls — they're noise.
- `font_size` is set at construction time (`MathTex(..., font_size=48)`, `Text(..., font_size=28)`), **not** after placement. For non-text elements `font_size` is `null` — ignore it.
- `z_order` is applied via `.set_z_index(n)`. Axes/chrome at 1–4, primary figures at 5–9, text/math at 10–14, emphasis overlays at 15–19 — pass through whatever the layout agent specified.

### Animation block

- **One `SceneAnimation` per `self.play(...)` call** (or `self.wait()` for a `pause` gap).
- **`run_after` graph dictates order.** Walk the DAG: animations with `run_after: null` run first (in parallel if there are several), then each animation runs when its predecessor completes. Phase-1 scenes are mostly a single spine; parallel branches show up as `self.play(A, B, run_time=...)` when two animations share a predecessor and both fire next.
- **`duration_seconds` → `run_time=`.** Pass the spec's number through. The sync agent will overwrite these in a later phase; for now they're author intent and a reasonable render target.
- **Op → primitive mapping** (see `manim-primitives` for edge cases):

  | spec `op` | Manim call | Notes |
  |---|---|---|
  | `write` | `Write(obj, run_time=d)` | Best for `MathTex`, `Tex`, `Text` — draws the glyphs. |
  | `create` | `Create(obj, run_time=d)` | Best for `Axes`, `VMobject` geometry, graphs. |
  | `transform` | `Transform(target_ids[0], target_ids[1], run_time=d)` | `target_ids[0]` morphs into `target_ids[1]`; both must be constructed before the play. |
  | `fade_in` | `FadeIn(obj, run_time=d)` | Accepts any mobject. |
  | `fade_out` | `FadeOut(obj, run_time=d)` | After this, the object is gone — don't reference it later. |
  | `move_to` | `obj.animate.move_to([x, y, 0])` inside `self.play(..., run_time=d)` | Destination comes from the planner's intent; if unspecified, nudge by 0.5 units in the direction implied by `visual_intent`. |
  | `highlight` | `Indicate(obj, run_time=d)` or `Circumscribe(obj, run_time=d)` | Pick `Circumscribe` for boxed emphasis, `Indicate` for colour flash. |

### Terminal hold

Close every `construct()` with `self.wait(0.3)`. Gives the renderer a last frame buffer; without it, ffmpeg concat sometimes clips the final beat.

## Applying `color-and-typography`

- Every semantic name referenced in an element's `properties.color` resolves through the `PALETTE` dict at the top of the file. Embed the palette literally — do not `from pedagogica ... import PALETTE`; the render sandbox sees only `code.py`.
- **Never emit raw hex inside the class body.** The indirection is the whole point of `color-and-typography`: Phase 4 brand kits swap the palette without touching scenes.
- **LaTeX with coloured terms:** prefer `MathTex(...).set_color_by_tex("dx", PALETTE["variable"])` over raw `\color{}` in the LaTeX source. LaTeX colouring is brittle across packages; Manim's own colouring is version-stable.
- **Font choices:** `Text(..., font="Inter")` for chrome; `MathTex` / `Tex` default to Computer Modern — do not override. See `latex-for-video` for sizing within LaTeX.

## Using the script (when present)

Markers in `script.json` anchor spoken words to visual events. They are **not directives to embed narration in the code**. Instead:

- **Every `marker.ref` must correspond to an element in the spec.** If the script marks `show eq.secant` and the spec has no `eq.secant`, the spec is wrong — fail loudly (produce code that raises `NotImplementedError` at scene start with the mismatch spelled out) rather than inventing an element. The repair loop will catch this and requery the visual planner in Phase 2.
- **Keep the animation order compatible with marker word-order.** If markers say `show eq.f` at word 3 and `show eq.fprime` at word 20, the `run_after` DAG had better order `anim.write.eq_f` before `anim.write.eq_fprime`. The sync agent can stretch gaps; it cannot reorder.
- **`pause` markers do not require a code change.** Sync inserts `self.wait(...)` calls based on measured word timings. You do not pre-emptively add waits for pauses.

If the script hasn't been written yet, render from the spec + layout alone. This is uncommon in Phase 1 (script runs before visual planner), but the agent should not hard-fail on its absence.

## Duration discipline

Your `run_time` values come from the spec; the spec's came from the visual planner's default rates. They are **not the final times** — the sync agent re-plans them against ElevenLabs word timings in a later stage, and in Phase 2 the sync repair loop may re-invoke codegen with updated numbers. Phase 1 ships with the first-pass numbers and measures drift for telemetry.

Consequences:

- Do not tighten or slacken timings based on "feel". The planner chose them; honour them.
- Do not hardcode a total scene duration. Scene length is the sum of `run_time`s + `wait`s + `run_after` concurrency resolution.
- Do not insert extra `self.wait(...)` calls for "breathing room". Only `pause` markers and the 0.3 s terminal hold justify waits. Unmotivated waits make drift measurement lie.

## Skill-loading decisions

| Skill | When to load |
|---|---|
| `scene-spec-schema` | Always — you can't emit code without knowing what the spec fields mean. |
| `manim-primitives` | Always — op→primitive mapping, common Manim gotchas. |
| `latex-for-video` | Always for any scene with a `math`-typed element (which is most of them). |
| `color-and-typography` | Always — the palette table is authoritative. |
| `manim-calculus-patterns` | When the storyboard beat's `required_skills` contains it, or when the scene has a `graph` element with a calculus-ish function (`x**2`, `sin(x)`, `1/x`, etc.). |
| Other `manim-<domain>-patterns` | Load the one matching the domain in `intake.json`. Phase 1 scope = calculus only; other packs don't exist yet. |

Record every skill actually consulted in `ManimCode.skills_loaded`. The cache key depends on it — a scene rendered with `manim-calculus-patterns@0.3.1` is a different cache entry from one rendered without.

## Model

**Opus 4.7.** Sole Opus call per scene on the happy path. Prompt caching is expected to carry the stable preamble (schema + primitives + palette + domain pack) across scenes, so the marginal cost per scene is mostly the variable prefix (spec + layout + script). Keep the stable preamble first in the skill-load order for cache locality.

## Validation

The orchestrator runs after you write:

```
uv run pedagogica-tools validate ManimCode artifacts/<job_id>/scenes/<scene_id>/code.json
```

Exit 1 → you will be re-prompted once with the validator's stderr; a second failure is a hard fail. The validator rejects:

- Unknown top-level fields (`extra="forbid"`).
- Missing `scene_class_name` or `code`.
- `skills_loaded` with non-string entries.

The validator does **not**:

- Parse the Python. Syntactic / runtime errors surface at the compile stage (`pedagogica-tools manim-render`), which hands the failure to `manim-repair`.
- Check that `scene_class_name` actually appears in `code`. Cross-check yourself — a mismatch will fail the render with an opaque `ModuleNotFoundError`-adjacent message.
- Check that every spec element is constructed or that every animation is played. The compile + visual review is what catches omissions.

Before emitting, self-check:

1. `scene_class_name` literally matches `class <NAME>(Scene):` in `code`.
2. Every `element.id` in the spec has a matching Python variable and is `self.add(...)`-ed or animated-in.
3. Every `animation.id` appears as exactly one `self.play(...)` or `self.wait(...)`.
4. No raw hex colour literals in the class body (everything goes through `PALETTE`).
5. `code` and `code.py` are byte-identical.

## Example

Given the visual-planner's example (`scene_04` — secant-to-tangent on `y = x^2`) and the corresponding layout placements, emit `code.py`:

```python
from manim import *
import numpy as np


PALETTE = {
    "background":  "#0E1116",
    "primary":     "#E8EAED",
    "variable":    "#4FC3F7",
    "result":      "#FFD54F",
    "correct":     "#66BB6A",
    "limit_target":"#66BB6A",
    "error":       "#EF5350",
    "bad_path":    "#EF5350",
    "annotation":  "#9AA0A6",
}


class Scene04(Scene):
    def construct(self):
        self.camera.background_color = PALETTE["background"]

        # --- elements ---
        axes_main = Axes(
            x_range=[-1, 3, 1],
            y_range=[-1, 5, 1],
            axis_config={"color": PALETTE["annotation"]},
        )
        graph_parabola = axes_main.plot(lambda x: x ** 2, x_range=[-1, 3], color=PALETTE["primary"])
        arrow_secant = Arrow(
            start=axes_main.c2p(0.2, 0.04), end=axes_main.c2p(2.0, 4.0),
            color=PALETTE["variable"], stroke_width=3, buff=0,
        )
        arrow_tangent = Arrow(
            start=axes_main.c2p(0.5, -0.5), end=axes_main.c2p(1.5, 1.5),
            color=PALETTE["result"], stroke_width=3, buff=0,
        )
        label_h = MathTex(r"h \to 0", font_size=28, color=PALETTE["variable"])

        # --- placement ---
        axes_main.move_to([0.0, 0.0, 0]).set_z_index(2)
        graph_parabola.set_z_index(6)
        arrow_secant.move_to([1.0, 1.0, 0]).set_z_index(16)
        arrow_tangent.move_to([1.0, 2.0, 0]).set_z_index(17)
        label_h.move_to([2.2, 1.4, 0]).set_z_index(12)

        # --- animations ---
        self.play(Create(axes_main), run_time=0.5)
        self.play(Create(graph_parabola), run_time=1.2)
        self.play(Write(arrow_secant), run_time=0.9)
        self.play(FadeIn(label_h), run_time=0.6)
        self.play(Transform(arrow_secant, arrow_tangent), run_time=1.6)

        self.wait(0.3)
```

Sibling `code.json` (abbreviated, trace metadata elided):

```json
{
  "scene_id": "scene_04",
  "code": "from manim import *\nimport numpy as np\n\n\nPALETTE = {...}\n\n\nclass Scene04(Scene):\n    def construct(self):\n        ...",
  "scene_class_name": "Scene04",
  "skills_loaded": [
    "scene-spec-schema@0.1.0",
    "manim-primitives@0.0.1",
    "latex-for-video@0.0.1",
    "color-and-typography@0.1.0",
    "manim-calculus-patterns@0.0.1"
  ]
}
```

## Anti-patterns

- **`exec()` / `eval()` / dynamic imports inside the scene.** The sandbox profile denies them; more importantly, the point of codegen is static code.
- **Raw hex colours in the class body.** Use `PALETTE`. If the palette doesn't cover what you need, that's a `color-and-typography` miss to flag, not an inline hex.
- **Multiple `Scene` subclasses in one file.** Only the one named in `scene_class_name` runs; the others waste tokens and confuse readers.
- **Hardcoded `config.pixel_height` / `config.frame_rate`.** The render flag (`-qm`) is authoritative; hardcoding fights it.
- **Narration text baked into the video.** TTS + subtitles are separate tiers. Do not `Text(script.text)` — that's a pipeline inversion.
- **Inventing element ids the spec didn't emit.** If `eq.secant_slope` isn't in `spec.elements`, don't conjure it — fail loudly so the repair loop can requery the planner.
- **`self.wait(...)` inserted for "pacing".** Only `pause` markers and the terminal `wait(0.3)` justify waits. Unmotivated waits distort drift measurement.
- **Ignoring `LayoutResult.frame_bounds_ok = false`.** Still render, but the render will clip; log `skills_loaded` accordingly so the critic can attribute the problem.
- **Regenerating after a compile failure.** That's `manim-repair`'s job. This agent runs once per scene on the happy path.
- **Emitting code that imports from `pedagogica_schemas` or any project module.** The sandbox sees `code.py` only; cross-repo imports will `ModuleNotFoundError`.
- **`from manim.utils.color import *` or similar deep imports.** Stick to `from manim import *`. Deep imports drift between 0.18 / 0.19 minor releases.

## Changelog

- **0.0.1** (2026-04-20) — initial Phase 1 draft. Opus 4.7 default. Consumes SceneSpec + LayoutResult + optional Script; emits `code.py` + `code.json` (ManimCode). Fixed file template (PALETTE → Scene class → construction / placement / animation / terminal hold). Compile failures route to `manim-repair`, never loop back here.

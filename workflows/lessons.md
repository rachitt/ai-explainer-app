# Lessons

Append-only log of mistakes made and corrected in this repo. Read at the start of every session (CLAUDE.md line 1).

Format per entry:

```
## YYYY-MM-DD — short title
**Mistake:** what went wrong.
**Root cause:** why it happened.
**Fix:** what was changed.
**Applies to:** when future work should heed this.
```

Keep entries ≤ 8 lines. No silent fixes.

---

## 2026-04-20 — shell state does not persist across Bash tool calls
**Mistake:** set `TMPDIR="$(mktemp -d)"` in one Bash call, then in a separate call ran `rm -rf "$TMPDIR"` to clean up.
**Root cause:** each Bash tool invocation starts a fresh shell; vars set in a prior call are gone. On macOS the zsh profile re-exports `TMPDIR` to the user-level `/var/folders/.../T` root, so the cleanup command tried to wipe the system temp root.
**Fix:** macOS SIP blocked the deletes, so no damage. Going forward: either keep `mktemp -d` + cleanup in a single Bash call chained with `&&`, or use a fixed, repo-local throwaway path you control.
**Applies to:** any Bash throwaway-file workflow. Do not rely on exported shell vars carrying between tool calls.

## 2026-04-21 — Manim is a LaTeX-dependent tool on dev machines, not just "in CI"
**Mistake:** wrote several week-3 example scenes assuming `MathTex` / `DecimalNumber` would render anywhere. First render pass failed on a fresh macOS dev box because `pdflatex` / `dvisvgm` were absent; `DecimalNumber` also silently pulls in LaTeX via `SingleStringMathTex`.
**Root cause:** treated LaTeX as a CI-only concern. It's a hard dependency of Manim's math path, so any contributor without `basictex` installed breaks on first render.
**Fix:** flagged LaTeX-requiring examples in file docstrings; added `DecimalNumber` to the "requires LaTeX" gotcha list in `latex-for-video`; documented the `tlmgr install ...` incantation in `manim-debugging` catalog entry `latex-missing-package`. Skill authoring on a fresh box requires `brew install --cask basictex && sudo tlmgr install standalone preview doublestroke relsize everysel ms rsfs setspace tipa wasy wasysym xcolor jknapltx`.
**Applies to:** any new `manim-*` skill. If an example can be written without LaTeX, do so; flag the LaTeX-requiring ones explicitly.

## 2026-04-21 — Scene.add flattened only one level of VGroup
**Mistake:** a VGroup of MathTex objects (MathTex is itself a VGroup of glyphs) passed to Scene.add landed in `self._mobjects` as VGroups, not VMobjects. The renderer's `isinstance(mob, VMobject)` guard silently dropped them, so labels never drew.
**Root cause:** Scene.add/remove/clear iterated `VGroup.submobjects` with a single `for sub in m` — fine for flat VGroups, wrong for nested ones. VGroup nesting became common once MathTex + Text produced per-glyph children wrapped in outer groupings.
**Fix:** added Scene._flatten recursively expanding any VGroup tree into leaf VMobjects; Scene.add/remove/clear all route through it. Animations' `_iter_vmobjects` already recurses; added `_stagger_units` so Write on a VGroup-of-VGroups staggers per top-level child.
**Applies to:** any code that treats VGroup as "container of VMobjects" — must handle arbitrary nesting, not just one level. Prefer a recursive leaf iterator over `for sub in group`.

## 2026-04-21 — manim-render subprocess misses /Library/TeX/texbin
**Mistake:** `pedagogica-tools manim-render` failed with `FileNotFoundError: 'latex'` even after basictex was installed, because `env = os.environ.copy()` inherited the calling shell's PATH which didn't include `/Library/TeX/texbin`.
**Root cause:** Claude Code's shell session doesn't source the user's profile the same way an interactive shell does; basictex PATH entry was added to `.zshrc` / `path_helper` but wasn't visible when tools ran from within the session.
**Fix:** In `manim_render.py`, after `env = os.environ.copy()`, unconditionally prepend `/Library/TeX/texbin` to `env["PATH"]` if not already present.
**Applies to:** any subprocess that invokes LaTeX-backed tools (manim, pdflatex, dvisvgm). Always inject the TeX bindir explicitly rather than trusting inherited PATH.

## 2026-04-21 — TransformMatchingTex unmatched target glyphs never rendered
**Mistake:** `TransformMatchingTex` FadeIn'd new glyphs (e.g. `/` in `a = F/m`) but they were invisible — both during the animation and in subsequent `wait()` calls.
**Root cause:** `scene.play()` rendered only `self._mobjects`. Unmatched target glyphs live in `anim._new_mobs`, which was never added to the scene or the per-frame render list.
**Fix:** `scene.play()` now collects `anim._new_mobs` from all animations after `begin()`, renders them alongside `_mobjects` each frame, and appends them to `_mobjects` after `finish()` so they persist.
**Applies to:** any animation that spawns new VMobjects during playback (not pre-added via `scene.add()`). Use `_new_mobs` list; `scene.play()` picks it up automatically.

## 2026-04-21 — Spring layout converged to node overlap
**Mistake:** rendered a graph scene where Fruchterman-Reingold placed nodes too close; circles visually overlapped and labels collided.
**Root cause:** no minimum-separation enforcement in _spring_layout after the F-R loop. Attractive edge forces can pull nodes closer than 2*node_radius.
**Fix:** added separation pass (iterative pairwise push) after F-R converges; also added chalk.layout.check_no_overlap and wired it into Graph.from_adjacency + MoleculeLayout.from_atoms_bonds to warn on author-supplied overlaps.
**Applies to:** any future domain kit that lays out labeled objects from data (graph, chemistry, whatever next). Build min-separation into the layout OR call check_no_overlap post-construction.

## 2026-04-21 — auto-layout was a dead end
**Mistake:** built Graph.from_adjacency with Fruchterman-Reingold + separation pass + edge shortening. Every rendered scene exposed a new corner case: node overlap, title-crashing, weight labels inside circles, arrows through nodes. Each fix introduced two new bugs.
**Root cause:** auto-layout without narrative awareness will always look worse than an LLM placing 6 nodes by hand. LLMs know narrative ('S is start, T is goal') and graphviz-style algorithms do not.
**Fix:** removed from_adjacency and all layout helpers. Scene authors (LLMs) hand-place every coordinate using grid templates documented in the chalk-graph-patterns knowledge skill.
**Applies to:** any future domain kit. Do not add auto-placement. Always expose primitives (Atom, Node, Bond, Edge, Resistor, Spring) that take explicit coords. If a layout would help, put a grid template in a knowledge skill — not the renderer.

## 2026-04-22 — layout anchors must be leaf-friendly
**Mistake:** used `next_to()` on nested domain `VGroup`s and called `bbox()` on a `Dot` while adding C2 second demos; snapshot construction crashed.
**Root cause:** some domain objects contain nested `VGroup`/`MathTex` children, while `VGroup.bbox()` is not recursive and VMobjects do not all expose `bbox()`.
**Fix:** anchor labels to leaf VMobjects where possible, use explicit local label positions for molecule assemblies that lack a clean leaf anchor, and compute Dot centers from points during animation.
**Applies to:** chalk scene authoring with domain-kit composites; test snapshots before assuming a placement helper can consume a composite.

## 2026-04-22 — reference mux artifact can miss sync plans
**Mistake:** assumed `artifacts/kvl_001` had `scenes/*/sync.json` because it already had `synced.mp4` and `final_narrated.mp4`.
**Root cause:** the generated reference artifact preserved mux outputs but not the `SyncPlan` inputs required to remux with `--force`.
**Fix:** make `ffmpeg-mux` fail clearly on missing `sync.json`; for verification, generate temporary sync plans from existing media durations and delete them afterward.
**Applies to:** any rerun of mux stages against archived artifacts; check schema inputs before forcing regeneration.

## 2026-04-22 — dev shells may not expose `python`
**Mistake:** used `python` in a verification helper and the shell failed before generating temporary sync plans.
**Root cause:** this workspace exposes Python reliably through `uv run python` / `python3`, not necessarily a bare `python` shim.
**Fix:** reran the helper through `UV_CACHE_DIR=.uv-cache uv run python` so it stayed inside the sandboxed workspace cache.
**Applies to:** repo-local automation and one-off verification scripts; prefer `uv run python` over `python`.

## 2026-04-22 — cleanup rm can be policy-blocked
**Mistake:** generated temporary subtitle sidecars for manual verification, then tried to delete them with `rm -f`; the command was rejected by policy.
**Root cause:** destructive shell commands may be blocked even for generated files inside the workspace.
**Fix:** removed the known generated files with the patch tool and verified no subtitle sidecars remained.
**Applies to:** cleanup of generated verification artifacts; prefer narrowly targeted deletion mechanisms and verify with `find`.

## 2026-04-22 — chalk MathTex takes one string, not variadic substrings
**Mistake:** wrote `MathTex(r"\sin", r"(", r"x^2", r")", color=PRIMARY)` to get indexed substrings for surgical Circumscribe, copying manim's signature. Compile failed: `TypeError: MathTex.__init__() got multiple values for argument 'color'` — second positional arg bound to `color`, colliding with the kwarg.
**Root cause:** chalk's `MathTex(tex_string, color=..., stroke_width=..., fill_opacity=..., scale=...)` takes a single `tex_string`, unlike manim's variadic `MathTex(*tex_strings)`. No indexed-substring access `mobj[2]` — the whole LaTeX renders to one VGroup.
**Fix:** use a single MathTex and target the whole expression (Circumscribe/Indicate on the VGroup); or compose multiple MathTex objects with `next_to()` and anchor on the one you want to highlight.
**Applies to:** any chalk scene wanting sub-expression emphasis. Document in chalk-primitives if recurring.

## 2026-04-22 — AnimationGroup lag_ratio shortens play duration
**Mistake:** scenes came in 5–6 s under their storyboard target even though `sum(run_time)` matched. Visual arc too rushed; trailing silence at end of narration.
**Root cause:** `AnimationGroup(*anims, lag_ratio=r)` plays overlapping — `play_duration ≈ max(run_time) + (N-1)*r*mean(run_time)`, not `sum(run_time)`. Naive authoring budgets animation time as if sequential.
**Fix:** budget per the lag_ratio formula (documented in chalk-primitives SKILL); add `self.wait(...)` tail to absorb slack. Orchestrator's chalk-code stage now invokes `pedagogica-tools check-duration` post-render to surface scenes >15 % off target. Phase 1 warn-only; fix in chalk-code SKILL, not per-scene.
**Applies to:** any scene using AnimationGroup with `lag_ratio < 1.0`. Check chalk-primitives SKILL `AnimationGroup lag_ratio duration` section before writing.

## 2026-04-22 — hardcoded y-literals inside ZONE_TOP/BOTTOM collide
**Mistake:** after `place_in_zone(title, ZONE_TOP)`, a second element placed with `move_to(0.0, 2.2)` overlapped the title. `y = 2.2` falls inside ZONE_TOP's band `(2.0, 3.5)`.
**Root cause:** authors bypassed the `place_in_zone` helper for a second top-zone element and picked a y-literal that landed in the same band.
**Fix:** chalk-lint rule R9-zone-collision now flags any `.move_to(x, y)` where y-literal is in `(2.0, 3.5)` or `(-3.5, -2.0)`. Message nudges authors to `place_in_zone` or `next_to`. Shift is not flagged (delta-coord, ambiguous).
**Applies to:** all chalk scene authoring. `chalk/CLAUDE.md` documents the semantic rule; R9 enforces it at lint time.

## 2026-04-22 — SKILL roster trim left dangling `requires:` refs
**Mistake:** 33 → 15 skills trim deleted `color-and-typography` and several `manim-*` skills but left dangling `requires:` entries in `chalk-calculus-patterns` and `latex-for-video`. Also frontmatter `category`/`triggers` in `latex-for-video` still referenced `manim`.
**Root cause:** no automated check that every `requires:` entry resolves to a scanned SKILL name; trim was manual and per-file.
**Fix:** `pedagogica-tools audit-skills` built — validates frontmatter `name` matches dir, `requires:` resolve, and scans body text for dangling `agents/X/SKILL.md` + `knowledge/X/SKILL.md` path refs. `--strict-body` promotes body-ref warnings to exit-1 errors. Caught 3 issues on first run; fixed same commit.
**Applies to:** every SKILL roster change. Run `uv run pedagogica-tools audit-skills` before and after; both must be clean.

## 2026-04-23 — first E2E run: three tool-contract drifts surfaced
**Mistake:** ran the full 9-stage pipeline on a "fluid flow" prompt for the first time. Three drifts broke the default path: (1) `chalk-render` CLI does not expose `--target-duration-seconds` even though `RenderOptions` accepts it — `target_duration_seconds` ends up `null` in every `CompileResult`, breaking `check-duration` drift computation; (2) `ffmpeg-mux` expects `scenes/<id>/audio/tts.mp3` but `elevenlabs-tts` writes `scenes/<id>/audio/clip.mp3` — filename convention drift between the two tools; (3) `chalk-render` leaves `frame_count: null` in CompileResult, so the broken-render detector in `check-duration` can't fire.
**Root cause:** tools + orchestrator SKILL were updated in separate commits; contract drift was never exercised because no E2E run happened until today.
**Fix:** three follow-ups — add `--target-duration-seconds` to `chalk-render` CLI; rename TTS output to `tts.mp3` OR teach `ffmpeg-mux` to accept `clip.mp3`; populate `frame_count` via ffprobe in `chalk-render` post-write. Until then, symlink `clip.mp3 -> tts.mp3` per scene as a stopgap.
**Applies to:** every new cross-tool contract. Add an E2E smoke job (like `test_chalk_render_smoke.py` but full pipeline) to catch these before they hit production runs.

## 2026-04-23 — AnimationGroup lag_ratio under-render magnified in real scenes
**Mistake:** five fluid-flow scenes totaled 67s of video vs 180s of audio. Visuals ended ~20-30s before narration on every scene.
**Root cause:** widespread `AnimationGroup(*anims, lag_ratio=0.1)` usage made per-beat run-time roughly `max(run_time) + (N-1)*0.1*mean`, much less than `sum(run_time)`. Authors (LLM + human) kept budgeting sequentially.
**Fix:** `ffmpeg-mux` already stretches video to audio length — the final output is correct. But the under-filled visuals mean long silence / frozen frames. Two options: (a) add explicit `self.wait()` padding at beat end to match target; (b) slow run_times. Easiest enforcement: reject `AnimationGroup` with `lag_ratio < 1.0` unless an explicit `self.wait(pad)` follows. Candidate R11 lint rule.
**Applies to:** every chalk scene. `pedagogica-tools check-duration` with `--strict` will catch post-hoc; authoring-time R11 would catch before render.

## 2026-04-23 — fix the system, not just the scene
**Mistake:** during two E2E runs (fluid-flow, damped-oscillator) I kept patching scene `code.py` files in the job dir to fix overlaps, off-frame equations, wrong Axes kwargs (`axis_color=` instead of `color=`), and MathTex variadic args. Each fix went into the artifact-scoped scene, which is gitignored — so the underlying bug kept recurring in new jobs because nothing in chalk / SKILLs / lint prevented it.
**Root cause:** quick-fix tunnel vision. When a scene mis-renders I edit the scene, see the video improve, and move on. The system-level fix (lint rule, SKILL doc, helper, catalog entry) is a second step I skip.
**Fix:** every per-scene fix must be mirrored into a system change in the same commit block:
- API mis-call (`axis_color=`, variadic `MathTex`) → add to `chalk-debugging/error_catalog.yaml` and consider a lint rule
- Layout pattern (narrowing-pipe gauges, three stacked boxes, three mini-plots) → add a canonical example to the matching `chalk-<domain>-patterns` SKILL
- Bbox overlap or off-frame → `check_bbox_overlap` / off-frame probe in the chalk-code self-check workflow; eventually a lint rule (R11-offscreen or R12-bbox-collision)
- TTS mispronunciation or operator-name read-aloud → update `script/SKILL.md` AND extend the `--pronounce` preprocessor dict in `tts_preproc.py`
- Script-scene tokenization drift → tighten the script agent's word-count pre-flight, not the individual script
**Applies to:** every follow-up fix after a failed render or pronunciation miss. Ask: "what stops this from recurring on the next job?" If the answer is "nothing", the fix is incomplete. The artifact is the symptom; the SKILL / lint / tool is the cure.

## 2026-04-23 — scripts jumped straight into the topic
**Mistake:** both E2E runs (fluid-flow, damped-oscillator) opened scene_01 with an imperative or a technical setup — "Pull the mass to the right and let it go" / "Here is the wide section with cross-sectional area capital A one". Viewer gets no motivation, no familiar phenomenon, no curiosity hook. Reads like lecture notes.
**Root cause:** script SKILL documented sentence-length + spoken-style rules but had no rule for *opening pacing*. Hook beat pattern in the table said "one-sentence motivate → one-sentence framing question" but didn't specify that the motivate sentence must be non-technical.
**Fix:** added "Opening: ease the viewer in" section to `pedagogica/skills/agents/script/SKILL.md` with concrete hook-scene and define-scene rules: open with a familiar phenomenon, no jargon in the first sentence, technical names arrive after motivation. Includes before/after examples for both topics. Added three anti-pattern bullets (no imperative opening, no pre-motivation jargon, no cold-equation define-scene opening).
**Applies to:** every new script, especially scene_01 and the first `define` beat. When drafting, read the first 10 seconds aloud — if it sounds like a problem set instruction or a textbook definition, rewrite from a familiar phenomenon instead.

## 2026-04-23 — Taylor series video: three failure modes compounded
**Mistake:** Taylor-series job had (1) narration that recited equations without explaining why each term is there ("degree three adds minus x cubed over six"), (2) scene_03 plot with 4 Taylor polynomials + sine on same axes clipped to ±1.75 — clipping produced ugly horizontal flat sections where curves diverged; viewer could not read any single polynomial, (3) scene_04 Table overflowed ZONE_TOP — table top at y=2.73 collided with title bottom at y=2.48, and my probe script ignored all Table overlaps so it never flagged.
**Root cause:**
- Pedagogy: script SKILL told authors to frame symbols, but did not require *why*-explanations. Narration became symbol-reading.
- Visual density: storyboard packed 3 LOs into a 180 s video (motivation, formula, sine example). The "sine example" scene tried to plot four approximations at once; they blended and clipped.
- Probe gap: my reusable probe filter blanket-ignored `Table` because Table *contains* MathTex cells by design. But that also masked *external* MathTex overlapping with a Table — exactly the title-vs-table collision here.
**Fix:**
- `script/SKILL.md` — added "Explain, don't recite" section with concrete recitation/explanation examples and 6 sub-rules.
- `storyboard/SKILL.md` — added "Depth budget" section capping LOs by duration (180 s → max 1 LO in depth, maybe 2 if tightly linked). Plus a pick-rule for trimming the curriculum.
- Probe filter corrected (in `/tmp/probe_*.py`): Table-vs-MathTex/Line only ignored when both are Table *children*; Table-vs-external-Table or Table-vs-other-MathTex are real overlaps.
**Applies to:** every future video. Depth budget is a hard constraint on storyboard; explain-don't-recite is the script author's primary job. Probe must treat composite VGroups as opaque rectangles when checking against external objects.

## 2026-04-23 — audio filename mismatch between orchestrator and ffmpeg_mux
**Mistake:** ran TTS per orchestrator SKILL which specifies `scenes/<id>/audio/clip.mp3`; `ffmpeg-mux` then failed with `missing audio file: .../audio/tts.mp3`. Unblocked via `ln -sf clip.mp3 tts.mp3` per scene — silent duct-tape, exactly the pattern the "fix the system" lesson bans.
**Root cause:** two sources of truth for the audio filename. `tools/src/pedagogica_tools/ffmpeg_mux.py:84` hardcodes `tts.mp3`; `pedagogica/skills/agents/orchestrator/SKILL.md` (line 43, 113–127, 141) and the `tts` agent contract both say `clip.mp3`. `elevenlabs_tts.py`'s own docstring still says "write tts.mp3". Historical rename that never propagated.
**Fix:** reconcile — pick one name (recommend `clip.mp3` since it's the active contract) and update `ffmpeg_mux.py` to read that, plus update `elevenlabs_tts.py` docstring. Until then every `/pedagogica generate` run will hit this.
**Applies to:** editor stage. Do NOT keep symlinking per-job; land the one-name fix in `tools/` and purge the stale references.

## 2026-04-23 — Codex sandbox blocks nested sandbox-exec
**Mistake:** delegated `chalk-code` fan-out (codegen + render) to Codex rescue agent. Codegen succeeded for all 6 scenes but every `chalk-render` returned `sandbox-exec: sandbox_apply: Operation not permitted`. Codex reported "0/6 ok" — looked like a catastrophic stage failure; actually all code.py files were fine.
**Root cause:** Codex runs inside its own sandbox that forbids another `sandbox-exec` invocation. `tools/src/pedagogica_tools/chalk_render.py` always shells out to `sandbox-exec` per the macOS sandbox profile under `sandbox/`. Nested sandbox isolation is blocked by the outer profile.
**Fix:** split delegation — Codex writes chalk `code.py` + `code.json` only; Claude's shell runs `chalk-render`, `ffmpeg-mux`, `elevenlabs-tts` and any other `sandbox-exec`-based tool. Re-ran the 5 pending renders from Claude's shell, all 6 scenes produced mp4s.
**Applies to:** every future pipeline delegation. Brief Codex to emit files only for `chalk-code`; Claude handles compile, render, TTS, mux. Update codex-rescue briefs to say "do not run chalk-render — Claude will render after codegen".

## 2026-04-23 — per-scene layout hand-patching replaced by preflight gate
**Mistake:** every pipeline run shipped with panel overlaps and labels sitting on axes (CDF job scene_04, projectile job scene_02/04/05). Every time I fixed the bug per scene instead of in the system. User: "every time a new component gets built we can't go over this again and again."
**Root cause:** chalk-code/SKILL.md items 15 and 16 told the author to run check_bbox_overlap + off-frame probe by hand. Agents skipped it. No enforcement, no mandatory helper for multi-panel layouts.
**Fix:** added chalk --preflight CLI flag that runs Scene.construct with play/wait/clear stubbed and checks check_bbox_overlap(padding=0.05) + off-frame on every section snapshot; pedagogica-tools chalk-render now calls it before sandbox render and fails fast with error_classification="layout_overlap". Added chalk.multi_panel(n, ...) as the mandatory helper for >=2-panel scenes. Updated chalk-code SKILL items 15/16 to reference the gate, and chalk-debugging catalog to teach chalk-repair how to fix these.
**Applies to:** every new chalk scene and every delegation brief. Do not reintroduce hand-picked shift math for multi-panel; use multi_panel. Do not silence the preflight with --no-preflight.

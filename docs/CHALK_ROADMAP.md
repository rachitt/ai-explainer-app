# chalk roadmap

Status: adopted by ADR 0001 (2026-04-21). chalk is the visual primitive for pedagogica.

This roadmap is phased by what pedagogica *needs next*, not by feature completeness against Manim. Every primitive and every animation listed here exists to serve a concrete scene in a concrete phase.

Kill criteria, reversion plan, and the architectural rationale live in `docs/adr/0001-chalk-replaces-manim.md`. Read that first if you're here.

---

## Current state (C0 baseline)

Shipped as of 2026-04-21:

**Primitives:** Circle, Rectangle, Square, Line, Arrow (filled 7-vertex), Axes + plot_function, MathTex (LaTeX→SVG→paths, content-hashed cache), Text (cairo toy font), VMobject, VGroup.

**Animations:** Transform (subpath-aware), ShiftAnim, FadeIn, FadeOut, Write (lag-staggered reveal across VGroup children).

**Infrastructure:** Scene with `add` / `remove` / `play` / `wait` / `clear(keep=...)`; CairoRenderer; Camera2D; FFmpegSink + PreviewSink + TeeSink; layout helpers `next_to` / `place_in_zone` / `labeled_box` / `arrow_between`; mandatory palette (`PRIMARY`, `YELLOW`, `BLUE`, `GREEN`, `RED_FILL`, `GREY`, `TRACK`, `BG`), scale tiers (`SCALE_DISPLAY/BODY/LABEL/ANNOT/MIN`), zones (`ZONE_TOP/CENTER/BOTTOM`, `SAFE_X`, `SAFE_Y`).

**Authoring rules:** chalk/CLAUDE.md enforces import-palette, clear-between-beats, labeled_box / arrow_between, no raw hex.

**Test coverage:** 75 passing.

**Examples:** newton.py, voltage_divider.py, damped_oscillation.py, claude_code.py, kirchhoff.py, morph_demo.py, mathtex_demo.py.

---

## Phase C1 — parity floor (4 weeks; must complete before or during pedagogica Phase 1 M1.6)

The floor is "every primitive and every animation a calculus explainer needs." Once this ships, the 10-topic Phase 1 regression suite renders entirely on chalk.

### C1.1 Reactive values (1 week)

- `ValueTracker(value)` — scalar that animates via `ShiftAnim`-style driver; `.get_value()` read anywhere.
- `always_redraw(callback)` — rebuilds a VMobject every frame from a callback that reads ValueTrackers.
- `DecimalNumber(value, num_decimal_places, unit)` — VGroup that redraws when its source tracker changes. Replaces MCE's `DecimalNumber` without dragging in `SingleStringMathTex`.
- Tests: ValueTracker → DecimalNumber round-trip, updater correctness at boundary alphas.

**Why first:** unlocks any scene where a number on screen has to reflect an animated quantity. Calculus M1.6 (Riemann sums converging, slope of a secant approaching tangent) is built on this.

### C1.2 Path-parametric motion (1 week)

- `ArcBetweenPoints(start, end, angle)` — curved arrow / connector.
- `ParametricFunction(func, t_range)` — plot an arbitrary parametric curve as a VMobject.
- `MoveAlongPath(mob, path, run_time, rate_func)` — slide a mobject along any VMobject's arclength.
- `Rotate(mob, angle, about_point)` — rotate a mobject around a point, with updaters preserved.
- Tests: arclength correctness within 1% at N=1024 samples; MoveAlongPath landing at path endpoint at alpha=1.

**Why:** derivative-as-slope-of-tangent, chain rule via rolling wheel, Kirchhoff charge flow.

### C1.3 Coordinate primitives (1 week)

- `NumberLine(x_range, length, include_tip, include_numbers)` — single-axis with tick labels.
- `NumberPlane(x_range, y_range, background_line_style)` — gridded plane with minor/major lines; replaces ad-hoc Axes grid.
- `Dot(point, radius, color)` — filled marker; degenerate case of Circle but needed everywhere.
- `Polygon(*points)` / `RegularPolygon(n, radius)` — closed VMobject from vertex list.
- `Brace(mob, direction)` — dimension annotation that sizes to its target's bbox along an axis; critical for inequality proofs and Riemann rectangles.
- Tests: NumberPlane grid spacing exact at integer coords; Brace scales with bbox.

### C1.4 Equation morphing with structural awareness (0.5 week)

- `TransformMatchingTex(source_tex, target_tex)` — pair glyphs by LaTeX-token identity, not by submobject index; glyphs missing in target shrink to a point, new glyphs grow from a point. Builds on the subpath propagation shipped 2026-04-21.
- Tests: F = ma → a = F/m preserves F, =, m, a identities.

**Why:** the 3B1B-signature equation rearrangement. Without this, morphing looks like random swapping.

### C1.5 Animation vocabulary expansion (0.5 week)

- `Indicate(mob)` — brief scale-and-recolor pulse.
- `Flash(point)` — radial burst at a point.
- `Circumscribe(mob, shape="rect"|"circle")` — animated outline around a mobject.
- `GrowFromCenter(mob)` / `GrowFromPoint(mob, point)`.
- `Succession(*anims)` — run in order back-to-back.
- `AnimationGroup(*anims, lag_ratio)` — run with staggered offset; `Write` generalizes to this.

### C1.6 Scene features (0.5 week)

- `Section(name)` context manager — bookmarks for TTS word-timing alignment.
- `Scene.camera_frame` shift/zoom animations (2D pan and zoom; true camera in Phase C4).
- `next_section(skip_animations=True)` — render only from this section forward for iteration speed.
- `save_last_frame(path)` — for skill authoring workflow (chalk/CLAUDE.md says "every frame must look finished"; authors need one-keystroke frame dumps).

### C1.7 Phase C1 exit criteria

- All 75 existing tests still green.
- New tests: ≥ 30 for C1.1–C1.6 (target ≥ 105 total).
- 10 Phase-1 calculus topics render on chalk without touching MCE.
- Snapshot-diff suite (byte-stable PNG per representative frame) covers the 10 topics.
- `pedagogica/skills/knowledge/chalk-primitives/` skill written, replacing `manim-primitives`.

---

## Phase C2 — domain primitive kits (4 weeks; sequenced with pedagogica Phase 2/3 needs)

Sub-packages under `chalk.<domain>`. Each kit is self-contained: pure composition of C1 primitives, no new renderer features. A domain kit is a helper layer an LLM can reach for when generating a scene in that domain.

### C2.1 chalk.physics (1 week; lands with pedagogica M3.3)

- `Spring(start, end, coils, natural_length)` — zigzag spring that stretches with endpoints.
- `Pendulum(pivot, length, angle_tracker)` — rod + bob updated from a ValueTracker.
- `Mass(position, label)` — labeled box with weight indicator.
- `Vector(start, end, label)` — Arrow + LaTeX label anchored to tip.
- `FreeBody(mass, forces=[(magnitude, direction, label)])` — auto-arranged force diagram.

### C2.2 chalk.circuits (1 week; lands with pedagogica Phase 5 EM pack)

- `Resistor(start, end, zigzag_count=4)` — real zigzag symbol along a segment.
- `Battery(start, end, polarity="left"|"right")` — long/short cell-pair symbol.
- `Capacitor`, `Inductor`, `Switch`, `Ground`.
- `Wire(*points, corner_radius)` — multi-segment polyline with arc corners.
- `CurrentFlow(wire, rate, charge_count, color)` — animates a stream of dots along a wire; driven by a ValueTracker so rate can vary.
- `VoltageLabel(across=(a, b), value)` — bracketed arrow + LaTeX label.
- `KirchhoffDemo(...)` helper: assembles the Phase-C2 reference Kirchhoff scene from these primitives. The Kirchhoff video we shipped with rectangles becomes the motivating test.

### C2.3 chalk.graph (1 week; lands with pedagogica M5.5 algorithms pack)

- `Node(label, position)` / `Edge(a, b, weight, directed)`.
- `Graph.from_adjacency(adj, layout="spring"|"circular"|"tree")` — force-directed or circular layout.
- `PathHighlight(graph, [node_seq])` — animated traversal (Dijkstra, BFS, DFS visualizations).
- Tests: force-directed layout converges within N iterations on standard test graphs.

### C2.4 chalk.chemistry (1 week; lands with pedagogica M5.5 chem pack)

- `Atom(symbol, charge)` — labeled circle with subscript/superscript support.
- `Bond(a, b, order=1|2|3, stereo="wedge"|"dash"|"plain")`.
- `MoleculeLayout.from_smiles(s)` — parse SMILES → 2D layout via RDKit (optional dep).
- Reaction arrows with conditions above/below.

### C2.5 Phase C2 exit criteria

- Each domain kit has ≥ 2 rendered examples reviewed by QuickTime frame-by-frame.
- Each kit has its own CLAUDE.md section under chalk/CLAUDE.md or a kit-local one.
- Domain-specific skills (`chalk-physics-patterns`, `chalk-em-patterns`, etc.) cite the kit, not raw primitives.

---

## Phase C3 — beyond-Manim features (4 weeks; lands between pedagogica Phase 3 and 4)

This is where chalk earns its name. Features that MCE either doesn't have, has poorly, or gets wrong. Each of these is a multiplier on the rest of the pipeline.

### C3.1 Pango-backed Text (1 week)

- Replace cairo toy-text with Pango + FreeType via `PangoCairo`.
- Real kerning, ligatures, complex-script shaping, subpixel positioning, hinted outlines.
- `Text` API is unchanged; only the rasterization/outline path swaps.
- Font-fallback chain: user font → system font → embedded bundled font.

**Why:** cairo toy text is genuinely ugly and the fallback metrics are wrong. MCE's Text is fine; we should be *better* than fine.

### C3.2 Deterministic snapshot testing (0.5 week)

- `chalk.testing.snapshot(scene, frame_at=t)` → byte-stable PNG written to `tests/snapshots/<scene>_<t>.png`.
- CI job: regenerate snapshots, diff against committed ones, fail on mismatch; `UPDATE_SNAPSHOTS=1` to update.
- Every rendered example becomes a snapshot-tested fixture.
- Seed discipline: no `numpy.random.*` or `random.*` in chalk core; any randomness goes through `chalk.rng(seed)`.

**Why:** catches pedagogical regressions (wrong glyph, missing arrow) in CI rather than on reviewer's screen. MCE cannot do this.

### C3.3 Design-system enforcement at the type level (0.5 week)

- `Color` as a NewType with only palette constants allowed; raw hex strings rejected at type-check time.
- `Scale` as an IntEnum-like with only `SCALE_DISPLAY/BODY/LABEL/ANNOT/MIN`; numeric literals rejected.
- `Zone` placement validator: `place_in_zone(mob, zone, x)` checks `mob` fits inside zone bounds; fails loud otherwise.
- Pre-commit hook: `chalk-lint` flags raw hex, magic-number scales, out-of-zone placements.

**Why:** chalk/CLAUDE.md already mandates this, but rules enforced by prose alone drift. Type-level enforcement is permanent.

### C3.4 Live preview with hot reload (1 week)

- File-watcher on the scene file. On change: re-import module, re-run only the *changed beat* (tracked via `Section` bookmarks from C1.6), push frames to `PreviewSink`.
- Iterate-loop latency target: < 500 ms from file save to first new frame displayed.
- MCE's `-qm -p` is a full re-render; chalk aims for beat-level incremental.

**Why:** compound multiplier on every scene author (human or agent). Currently the biggest time-sink in chalk authoring is "edit, re-render entire 20s video, look at one frame."

### C3.5 Narration-aware layout (1 week)

- `Scene.with_narration(elevenlabs_output)` binds beat durations to narration word-timings.
- `self.beat("phrase")` auto-paces to match the narrator's "phrase" word span.
- Closes the visual ↔ audio gap pedagogica currently papers over with manual `wait(...)`.

**Why:** the whole point of pedagogica is narration-synced animation. This lives in chalk, not in a skill, because it needs renderer-level timing hooks.

### C3.6 Sandbox-safe scene DSL (0.5 week)

- Subset of chalk importable under a restricted-builtins environment.
- No `exec`, no arbitrary `import`, no filesystem access.
- Scene files parsed, not exec'd, with an AST whitelist.
- Any LLM-generated scene that doesn't parse under the DSL is rejected before render.

**Why:** tightens the sandbox surface from "arbitrary Python" to "a handful of allowed primitives." Reduces the risk ceiling flagged in docs/RISKS.md R2.

### C3.7 Phase C3 exit criteria

- 1080p60 1-minute benchmark scene renders under 60 s wall clock on the reference dev box.
- Snapshot suite covers all examples + all Phase-1 calculus topics; CI fails on diff.
- `chalk-lint` runs in pre-commit; no violations in current codebase.
- Live preview iteration demo: edit → visible change < 500 ms on the reference scene.
- Published `chalk` README benchmarks chalk against MCE 0.19.x on the same 3 scenes: render time, file size, visual diff.

---

## Phase C4 — 3D (8 weeks; lands ahead of pedagogica M3.1 if linear algebra needs 3D)

This is the hardest phase. It may not happen if Phase C1–C3 deliver everything the product needs for the first four pedagogica phases. Default stance: **defer until a domain concretely needs 3D.** Linear algebra and classical mechanics both *can* use 3D but don't *require* it.

### C4.1 Rendering backend (3 weeks)

- New `chalk.renderer.opengl.OpenGLRenderer` behind the same `Renderer` protocol.
- Uses moderngl + EGL for headless.
- Still produces RGBA frames; same FFmpegSink downstream.

### C4.2 3D primitives (3 weeks)

- `Camera3D(position, target, up, fov)`.
- `Axes3D`, `Surface(func, u_range, v_range)`, `ParametricSurface`.
- `VMobject3D` base with triangulated meshes for filled shapes.
- Basic Phong lighting (one directional + ambient). No shadows.

### C4.3 2D ↔ 3D interop (1 week)

- A `Scene` can mix 2D and 3D mobjects; 3D rendered to texture composited with 2D layer.
- Animations compose as today; camera moves are first-class.

### C4.4 Kill signals specifically for Phase C4

- If C4 slips > 4 weeks beyond its allotted 8, we invoke ADR 0001's K4 and wire MCE's OpenGL backend as a dual-renderer for 3D scenes only. chalk stays 2D.

---

## What we're deliberately NOT building

These are not Phase-C5 hints; they are out-of-scope for chalk entirely. Any of them re-enters scope only via a new ADR.

- Generic motion-graphics toolkit (logo animations, kinetic typography, video editing). chalk is a pedagogical primitive, not After Effects.
- Interactive playground / scrubber UI. Pedagogica produces videos; interactivity is a different product per NON_GOALS §1.2.
- Node-graph / shader DSL. Adds complexity without serving the pedagogy workload.
- Scripting in any language other than Python. LLMs generate Python in pedagogica; multiplying language surfaces multiplies sandbox surfaces.
- Plugin marketplace / third-party renderer backends. Per NON_GOALS §2.5 the marketplace is a Phase-6 product decision; chalk stays single-author until then.

---

## How scenes interact with this roadmap

A scene is a consumer of chalk primitives and a validator of the design system. Every phase above is driven by at least one concrete scene that needed it:

| Phase | Motivating scene |
|-------|-----------------|
| C1.1 | Riemann sums with a live-updating area number |
| C1.2 | Kirchhoff charge flow; chain-rule rolling wheel |
| C1.3 | Riemann rectangles on `NumberPlane`; brace over interval |
| C1.4 | F = ma → a = F/m equation morph |
| C2.1 | Newton's second law with Spring-coupled Mass |
| C2.2 | Full Kirchhoff schematic (replaces today's rectangle stand-ins) |
| C2.3 | Dijkstra traversal on a weighted graph |
| C2.4 | SN2 reaction mechanism with curved arrows |
| C3.1 | Any title card that currently looks cramped in cairo toy text |
| C3.2 | 10-topic calculus regression |
| C3.4 | Scene-author iteration velocity (everyone's scene) |
| C3.5 | Any narrated video shipped to a user |
| C4 | 3D linear transformation of a cube in ℝ³ |

If no concrete scene pulls a primitive into the roadmap, the primitive does not get built.

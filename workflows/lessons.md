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

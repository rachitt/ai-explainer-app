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

## 2026-04-21 — manim-render subprocess misses /Library/TeX/texbin
**Mistake:** `pedagogica-tools manim-render` failed with `FileNotFoundError: 'latex'` even after basictex was installed, because `env = os.environ.copy()` inherited the calling shell's PATH which didn't include `/Library/TeX/texbin`.
**Root cause:** Claude Code's shell session doesn't source the user's profile the same way an interactive shell does; basictex PATH entry was added to `.zshrc` / `path_helper` but wasn't visible when tools ran from within the session.
**Fix:** In `manim_render.py`, after `env = os.environ.copy()`, unconditionally prepend `/Library/TeX/texbin` to `env["PATH"]` if not already present.
**Applies to:** any subprocess that invokes LaTeX-backed tools (manim, pdflatex, dvisvgm). Always inject the TeX bindir explicitly rather than trusting inherited PATH.

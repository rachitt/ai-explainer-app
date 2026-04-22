# ADR 0001 — chalk replaces Manim Community as the visual primitive

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Rachit
- **Supersedes:** the "Manim Community 0.19.x is the visual primitive" rule in CLAUDE.md line 21 and the "Relitigating the Manim bet" permanent non-goal in NON_GOALS.md §1.6.

## Context

The original architectural bet (Artifact 1–6, CLAUDE.md, NON_GOALS §1.6) was that LLMs generate **Manim Community Edition 0.19.x** code, rendered by MCE, to produce pedagogical video. MCE was chosen because it is the canonical 3Blue1Brown-style renderer, has a large community, and LLMs have seen extensive Manim code in pretraining.

Several real-world observations accumulated over the first weeks of Phase 1:

1. **LaTeX fragility on dev machines.** MCE assumes a full TeX distribution. `workflows/lessons.md` entries 2 and 3 document failures where `DecimalNumber` silently pulls LaTeX, `pdflatex`/`dvisvgm` are missing on a fresh macOS box, and subprocess PATH injection is required to find `/Library/TeX/texbin`. Every contributor hits this. MCE is a LaTeX-dependent tool whose happy path assumes CI.
2. **API bloat.** MCE's `Mobject` hierarchy has dozens of redundant classes and inherited state (updaters, animations, point_mass1, point_mass2, many dead-code branches from ManimGL forking). LLMs generate code that works but is wordy and hard to validate — exactly the opposite of what the sandbox + critic loop needs.
3. **Non-determinism.** MCE frames are not byte-stable across runs on the same input. This breaks snapshot testing, which is the cheapest path to pedagogical-regression coverage across 60+ topics (docs/ROADMAP.md M3 success criterion).
4. **Layout anarchy.** Manim scenes routinely pile 4+ colors and 6+ text tiers into one frame. The pedagogy skills (`scene-composition`, `color-and-typography`) enforce design system rules, but MCE gives no API-level support — a scene that violates the rules compiles fine. Systemic enforcement needs a renderer that understands zones and palette slots.
5. **Sandbox surface.** MCE is a full Python environment; the sandbox profile (docs/ARCHITECTURE.md §sandbox) has to allow arbitrary imports. A narrower primitive set lets us tighten the sandbox and reduce the exec-LLM-code risk surface flagged in RISKS.md.

Concurrently, a from-scratch renderer named **chalk** was built under `chalk/` over roughly two weeks (75 tests, cairo-based, 2D). It covers Circle / Line / Arrow / Rectangle / Axes / MathTex / Text / VGroup / Transform / ShiftAnim / FadeIn / FadeOut / Write plus a layout system (next_to / labeled_box / arrow_between) and a mandatory palette + scale-tier import rule (chalk/CLAUDE.md). It produces the Kirchhoff and Newton explainers at 1080p today.

chalk was built opportunistically, outside any plan. Continuing to ship features into it while CLAUDE.md still names MCE is drift, and every new chalk commit widens the gap.

## Decision

**chalk replaces Manim Community Edition as the visual primitive for pedagogica, starting Phase 1.**

1. CLAUDE.md line 21 is rewritten: chalk is the primitive, MCE is no longer referenced as a non-negotiable.
2. NON_GOALS §1.6 ("Relitigating the Manim bet") is narrowed to "Relitigating the chalk bet" — the *bet* was about owning the renderer, not about which specific one. Mid-phase re-debates between chalk / MCE / Remotion / Motion Canvas remain out of scope until kill criteria below trigger.
3. A phased chalk roadmap is published at `docs/CHALK_ROADMAP.md`, with parity-floor, domain-primitive, beyond-MCE, and 3D milestones.
4. The `manim-primitives`, `manim-calculus-patterns`, and future `manim-<domain>-patterns` skills are renamed `chalk-primitives`, `chalk-calculus-patterns`, etc. Skill authoring templates updated.

## Why chalk can beat Manim on this specific workload

chalk is not trying to be a general-purpose motion-graphics library. It is trying to be **the best primitive set for LLM-generated pedagogical video**. That is a much smaller target than Manim's, and the following asymmetries favor a from-scratch small library:

- **API surface is orders of magnitude smaller.** Every class earns its place. LLMs generate shorter code with fewer plausible-but-wrong paths.
- **Determinism is a design invariant, not a bug.** Snapshot tests make pedagogy regressions catchable in CI.
- **Design-system enforcement is in the primitives.** Scale tiers and palette slots are importable constants, not style suggestions. A scene that tries to draw red text can be rejected at import time.
- **Layout helpers are first-class.** `next_to`, `labeled_box`, `arrow_between` remove the "label drifts when shape moves" failure mode that chews up MCE debugging time.
- **No LaTeX dependency for prose.** `Text` uses cairo toy text (Phase C3 upgrades to Pango). LaTeX stays for math only, isolated in `MathTex`.
- **Sandbox-friendly.** Narrow surface area means the sandbox-exec profile can whitelist only what `chalk` needs.
- **Cache is built in.** Content-hash TeX caching is mandatory; the whole pipeline re-renders cache-hits.

This is a focus argument, not a hubris argument. chalk wins on *this domain* because the domain is narrower than MCE's. Any attempt to make chalk a general-purpose Manim replacement outside pedagogical video is out of scope — the roadmap's kill criteria include "scope has drifted to match Manim's breadth."

## Consequences

- **Short term.** Every agent skill that references MCE primitives must be updated. Most skills are still draft at this point, so churn is manageable.
- **Medium term.** Domain expansion (Phase 3 physics, Phase 5 EM) forces chalk to acquire schematic / physical primitive kits. These live in `chalk.<domain>` subpackages (see CHALK_ROADMAP Phase C2), not in core chalk.
- **Risk.** chalk is a single-author library today. Bus factor is 1. Mitigation: strict typing, 100% test coverage target on primitives, tight CLAUDE.md authoring rules, ADRs for every primitive added.
- **Risk.** 3D is a bigger lift than the whole 2D library combined. If Phase 3/4 require 3D and chalk can't ship it on schedule, we temporarily hot-swap in MCE's OpenGL backend for 3D scenes only (dual-renderer mode).

## Kill criteria

Revisit this decision (possibly reverting to MCE) if ANY of these fires:

- **K1.** chalk parity floor (CHALK_ROADMAP Phase C1) cannot be reached within 4 weeks with regression tests green on the 10 Phase-1 calculus topics.
- **K2.** A single pedagogical regression takes more than 2 days to diagnose and fix in chalk at least 3 times in a 4-week window. Signal: chalk's API is too narrow and we're reinventing Manim.
- **K3.** chalk test suite falls below 90% line coverage for two consecutive weeks, or regression-snapshot parity drops below 95%.
- **K4.** A Phase 3+ domain requires 3D and chalk's 3D backend cannot render the target scene list at acceptable quality within the domain's phase window.
- **K5.** chalk maintenance absorbs more than 30% of any given phase's engineering budget for three consecutive weeks. Signal: renderer is eating the product.

If a kill criterion fires, the reversion plan is: freeze chalk development, route new skills through MCE 0.19.x via a compatibility shim in `tools/render/`, re-evaluate at the next phase boundary.

## Alternatives considered

- **Stay on MCE.** Rejected on LaTeX fragility, API bloat, determinism, and sandbox surface grounds above. The Manim ecosystem optimizes for "power user writes their own scene"; pedagogica optimizes for "LLM writes a scene from a spec." Different workloads.
- **Remotion (React-based).** Rejected. Pulling a Node runtime into a Python-first pipeline adds a second language + packaging surface. Motion-graphics strength, pedagogy weakness.
- **Motion Canvas.** Same as Remotion + smaller community.
- **SVG-only (no renderer).** Rejected in Artifact 1. No animation primitive; every scene would be a per-frame SVG dump.
- **Keep chalk as parallel experiment while MCE remains primary.** Rejected as the worst of both worlds. Every new feature split across two renderers slows both.

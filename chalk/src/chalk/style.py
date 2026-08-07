"""Style constants for chalk scenes.

Every scene must import colors and scales from here — never write raw hex or
magic-number scales. Palette and scale tiers come from the pedagogica
color-and-typography skill; zones come from scene-composition.

See chalk/CLAUDE.md for the authoring rules that govern how these are used.
"""
from __future__ import annotations

# ── Palette ────────────────────────────────────────────────────
# Near-black background — anti-aliased edges land clean against it.
BG       = "#0E1116"

# Semantic color slots. Use the role, not the hex.
PRIMARY  = "#E8EAED"  # main math, primary text, the thing you're looking at
YELLOW   = "#FFD54F"  # result / punchline / key quantity (accent_yellow)
BLUE     = "#4FC3F7"  # variable / moving thing (accent_blue)
GREEN    = "#66BB6A"  # correct / target (accent_green)
RED_FILL = "#EF5350"  # contrast / "not this" — FILL OR STROKE ONLY, never text
GREY     = "#9AA0A6"  # annotations, axis labels, secondary captions
TRACK    = "#2A2F36"  # subtle reference lines (tracks, gridlines)

# ── Chalkboard aesthetic layer ─────────────────────────────────
# When STYLE_CHALKBOARD_ENABLED is true (env var CHALK_STYLE=chalkboard),
# the renderer applies seeded jitter to every stroke path and swaps in the
# matte chalkboard palette below. This is chalk's visual identity — the
# thing manim explicitly does not do. Agents do not opt in or out; the
# render pipeline decides via env var. See docs/CHALK_QUALITY_GAP.md
# "Re-differentiate chalk" for why this is the right bet.

# Slate-green chalkboard background — classic schoolroom blackboard.
BG_CHALKBOARD = "#2E3B36"

# Matte chalk-dust palette — lower saturation than the default,
# slight warm tint so it reads as "drawn in chalk".
PRIMARY_CHALK  = "#F3EAD1"  # warm off-white chalk
YELLOW_CHALK   = "#FFE08A"  # dusty yellow
BLUE_CHALK     = "#BFE7F2"  # pale cyan chalk
GREEN_CHALK    = "#B3E8B3"  # pale chartreuse chalk
RED_CHALK      = "#F5B1A8"  # coral chalk — still fill-only
GREY_CHALK     = "#BDC3C7"  # muted slate annotation
TRACK_CHALK    = "#445049"  # subtle board-texture line

# Jitter magnitude in world units. ~1.2% of a SCALE_BODY glyph height.
# Low enough to read as "hand-drawn", high enough to see.
CHALK_JITTER_AMOUNT = 0.015

# Stroke-width variation fraction. When chalkboard mode is on, every
# stroke gets a seeded ±5% width wobble so lines have chalk-pressure feel.
CHALK_STROKE_WIDTH_JITTER = 0.05

# ── Type scales ─────────────────────────────────────────────────
# chalk.MathTex scale values. Do not emit anything below SCALE_MIN.
SCALE_DISPLAY = 0.9   # main equation of a beat
SCALE_BODY    = 0.65  # secondary equations, substitutions
SCALE_LABEL   = 0.55  # labels on objects (mass, axis, point labels)
SCALE_ANNOT   = 0.45  # small annotations, captions
SCALE_MIN     = 0.40  # floor — legibility breaks below this at 1080p

# ── Frame geometry (Camera2D default) ──────────────────────────
FRAME_WIDTH   = 14.2
FRAME_HEIGHT  = 8.0

# Safe area — no readable content closer than 0.5 to any edge.
SAFE_X = (-6.6, 6.6)
SAFE_Y = (-3.5, 3.5)

# Three-band zone system. Pick one zone per element; at most 3 zones active.
ZONE_TOP    = (2.0, 3.5)    # beat title / current concept name
ZONE_CENTER = (-2.0, 2.0)   # main visual real estate
ZONE_BOTTOM = (-3.5, -2.0)  # running caption / worked step / payoff

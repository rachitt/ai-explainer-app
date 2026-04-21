# Repair-log worked examples

Three before/after pairs demonstrating the end-to-end repair flow for the
three most-likely-to-hit catalog entries.

## Repair 01 — `axes-get-graph-renamed`

**Before:** `repair_01_get_graph_rename_before.py`
**After:** `repair_01_get_graph_rename_after.py`

**Trigger stderr:**
```
AttributeError: 'Axes' object has no attribute 'get_graph'
```

**Classification step:** fingerprint `AttributeError:.*'Axes'.*'get_graph'`
matches entry `axes-get-graph-renamed` in `error_catalog.yaml`. Classification
is `api_version_error` — the stderr is deterministic from the API change.

**Fix applied:** `ax.get_graph(` → `ax.plot(` at line 13. No other edits.

**Verification:** `manim -ql repair_01_get_graph_rename_after.py GetGraphAfter`
renders without stderr.

---

## Repair 02 — `c2p-on-raw-coordinates`

**Before:** `repair_02_missing_c2p_before.py`
**After:** `repair_02_missing_c2p_after.py`

**Trigger:** No stderr — the scene compiles and renders. Flagged by the
layout post-check: the `Dot` at scene coord `[2, 4, 0]` should have been at
`ax.c2p(2, 4)`, which under `x_range=[0,10], x_length=7` is scene coord
`(-1.6, 0.8, 0)`.

**Classification step:** catalog entry `c2p-on-raw-coordinates`. Since there
is no stderr, the orchestrator relies on the layout agent's visual review
or an explicit `c2p_check` in the compile_attempt trace to flag this.

**Fix applied:** `Dot([2, 4, 0], ...)` → `Dot(ax.c2p(2, 4), ...)`.

**Verification:** layout agent re-runs visual review; dot now sits on the
parabola at the expected point.

---

## Repair 03 — `mathtex-raw-string-missing`

**Before:** `repair_03_raw_string_missing_before.py`
**After:** `repair_03_raw_string_missing_after.py`

**Trigger stderr (with LaTeX):**
```
SyntaxWarning: invalid escape sequence '\f'
... (further downstream) ...
RuntimeError: latex error converting to dvi
! Undefined control sequence \x0crac.
```

**Classification step:** fingerprint `SyntaxError: \(unicode error\)|KeyError.*\\\\[a-z]`
catches the Python-level warning. (Python 3.12+ raises `SyntaxError`
for some of these; earlier versions only warn.) Classification: `latex_error`
with a caveat that the actual cause is Python-level.

**Fix applied:** prefix `MathTex(...)` with `r`.

**Verification:** LaTeX source is now `\frac{d}{dx}` intact; Manim renders
the formula correctly.

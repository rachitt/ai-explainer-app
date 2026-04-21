# sandbox/

macOS `sandbox-exec` profiles used by `pedagogica-tools` to isolate
LLM-generated code at render time.

## `manim.sb`

Phase 1 sandbox for Manim renders. Enforces:

- **No outbound network.** `(deny network*)` with a narrow re-allow for
  loopback and unix sockets to system daemons. An `urllib` / `socket`
  call to a public host raises `PermissionError: Operation not permitted`.
- **No writes outside the artifact dir.** `(deny file-write*)` then
  `(allow file-write* (subpath (param "ARTIFACT_DIR")))`. Callers pass
  the absolute artifact-dir path via `sandbox-exec -D ARTIFACT_DIR=…`.
  `TMPDIR` is redirected inside the artifact dir so LaTeX temp writes
  stay in scope.
- Reads and everything else default-allow. This is deliberately a
  best-effort profile — see `docs/ARCHITECTURE.md` §9, which ships
  Firecracker as the real isolation in Phase 4.

## Updating the profile

1. Edit `manim.sb`.
2. Run `uv run pytest tools/tests/test_manim_render.py` — the network-deny
   test must still pass, and the positive render test must still render.
3. Document new `(param …)` inputs at the top of the file.

Do not loosen `(deny network*)` or the artifact-dir write restriction
without filing an ADR.

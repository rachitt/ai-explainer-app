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

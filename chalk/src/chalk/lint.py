"""AST linter for chalk scene files. Enforces palette + scale discipline."""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

from chalk import style as _style

_PALETTE_NAMES = {
    n
    for n in dir(_style)
    if n.isupper() and isinstance(getattr(_style, n), str) and getattr(_style, n).startswith("#")
}
_SCALE_NAMES = {n for n in dir(_style) if n.startswith("SCALE_")}

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{3,8}$")
_ALLOWLIST_PATH = Path(__file__).with_name("_lint_allowlist.txt")


class LintError:
    __slots__ = ("path", "line", "col", "rule", "message")

    def __init__(self, path, line, col, rule, message):
        self.path, self.line, self.col, self.rule, self.message = path, line, col, rule, message

    def __str__(self):
        return f"{self.path}:{self.line}:{self.col}: [{self.rule}] {self.message}"


def _load_allowlist() -> set[tuple[str, int, str]]:
    if not _ALLOWLIST_PATH.exists():
        return set()
    entries: set[tuple[str, int, str]] = set()
    for raw_line in _ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        path, lineno, rule = line.rsplit(":", 2)
        entries.add((path, int(lineno), rule))
    return entries


def _allowlist_keys(path: Path) -> set[str]:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        relative = path.as_posix()
    return {
        str(path),
        path.as_posix(),
        relative,
        str(resolved),
        resolved.as_posix(),
    }


class _Visitor(ast.NodeVisitor):
    def __init__(self, path):
        self.path = path
        self.errors: list[LintError] = []

    def visit_Constant(self, node):
        """R1: raw hex string literal anywhere in scene file."""
        if isinstance(node.value, str) and _HEX_RE.match(node.value):
            self.errors.append(
                LintError(
                    self.path,
                    node.lineno,
                    node.col_offset,
                    "R1-raw-hex",
                    f"raw hex {node.value!r} - use palette constant from chalk.style",
                )
            )

    def visit_Call(self, node):
        """R2: scale=<numeric literal> anywhere a kwarg is passed."""
        for kw in node.keywords:
            if (
                kw.arg == "scale"
                and isinstance(kw.value, ast.Constant)
                and isinstance(kw.value.value, (int, float))
            ):
                self.errors.append(
                    LintError(
                        self.path,
                        kw.value.lineno,
                        kw.value.col_offset,
                        "R2-magic-scale",
                        f"scale={kw.value.value} - use SCALE_DISPLAY/BODY/LABEL/ANNOT/MIN",
                    )
                )
        self.generic_visit(node)


def lint_file(path: Path) -> list[LintError]:
    if _is_style_or_lint_file(path):
        return []
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        return [LintError(str(path), e.lineno or 0, e.offset or 0, "parse", str(e))]
    v = _Visitor(str(path))
    v.visit(tree)
    allowlist = _load_allowlist()
    keys = _allowlist_keys(path)
    return [
        e
        for e in v.errors
        if not any((key, e.line, e.rule) in allowlist for key in keys)
    ]


def _is_style_or_lint_file(path: Path) -> bool:
    """style.py defines the palette itself; lint.py describes the rules. Skip."""
    name = path.name
    return name in {"style.py", "lint.py"} or "tests" in path.parts or name.startswith("test_")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    targets = [Path(p) for p in argv[1:]] or [Path("chalk/examples"), Path("chalk/src/chalk")]
    errors: list[LintError] = []
    for t in targets:
        if t.is_file() and t.suffix == ".py" and not _is_style_or_lint_file(t):
            errors.extend(lint_file(t))
        elif t.is_dir():
            for py in t.rglob("*.py"):
                if not _is_style_or_lint_file(py):
                    errors.extend(lint_file(py))
    for e in errors:
        print(e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

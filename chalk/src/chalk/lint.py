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
_MOTION_ANIMATIONS = {
    "ChangeValue",
    "MoveAlongPath",
    "Rotate",
    "Transform",
    "CameraShift",
    "CameraZoom",
    "ShiftAnim",
    "Succession",
    "LaggedStart",
}


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

    def visit_ClassDef(self, node):
        if _is_scene_subclass(node):
            construct = _construct_method(node)
            if construct is not None:
                self._check_construct_scenes(construct)
        self.generic_visit(node)

    def _check_construct_scenes(self, construct: ast.FunctionDef):
        scenes = _split_construct_scenes(construct)
        for scene in scenes[:-1]:
            if not _contains_motion_animation(scene.statements):
                self.errors.append(
                    LintError(
                        self.path,
                        scene.start_line,
                        0,
                        "R3-no-motion",
                        "scene has no motion animation; add ChangeValue/MoveAlongPath/Rotate/Transform/etc.",
                    )
                )
        for scene in scenes:
            beats = _count_self_play_calls(scene.statements)
            if beats > 3:
                self.errors.append(
                    LintError(
                        self.path,
                        scene.start_line,
                        0,
                        "R4-too-many-beats",
                        f"scene has {beats} self.play() beats; cap each scene at 3",
                    )
                )


class _SceneChunk:
    __slots__ = ("start_line", "statements")

    def __init__(self, start_line: int, statements: list[ast.stmt]):
        self.start_line = start_line
        self.statements = statements


def _is_scene_subclass(node: ast.ClassDef) -> bool:
    return any(_name_of(base) == "Scene" for base in node.bases)


def _construct_method(node: ast.ClassDef) -> ast.FunctionDef | None:
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == "construct":
            return stmt
    return None


def _split_construct_scenes(construct: ast.FunctionDef) -> list[_SceneChunk]:
    scenes: list[_SceneChunk] = []
    start_line = construct.lineno
    statements: list[ast.stmt] = []
    for stmt in construct.body:
        if _is_self_clear_stmt(stmt):
            scenes.append(_SceneChunk(start_line, statements))
            start_line = stmt.lineno
            statements = []
        else:
            statements.append(stmt)
    scenes.append(_SceneChunk(start_line, statements))
    return scenes


def _is_self_clear_stmt(stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and _is_self_method_call(stmt.value, "clear")
    )


def _contains_motion_animation(statements: list[ast.stmt]) -> bool:
    return any(
        isinstance(node, ast.Call) and _name_of(node.func) in _MOTION_ANIMATIONS
        for stmt in statements
        for node in ast.walk(stmt)
    )


def _count_self_play_calls(statements: list[ast.stmt]) -> int:
    return sum(
        1
        for stmt in statements
        for node in ast.walk(stmt)
        if isinstance(node, ast.Call) and _is_self_method_call(node, "play")
    )


def _is_self_method_call(node: ast.Call, method_name: str) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == method_name
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
    )


def _name_of(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


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

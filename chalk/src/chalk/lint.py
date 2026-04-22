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
_MAX_BEAT_SECONDS = 10.0
_DEFAULT_PLAY_SECONDS = 1.0
_POSITION_LESS_CONSTRUCTORS = {
    "MathTex",
    "Text",
    "VGroup",
    "Polygon",
    "Rectangle",
    "Line",
    "Arrow",
    "Circle",
}
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
        for scene in scenes:
            for lineno, rect_name, tex_name in _find_hand_sized_boxes(scene.statements):
                self.errors.append(
                    LintError(
                        self.path,
                        lineno,
                        0,
                        "R5-hand-sized-box",
                        f"Rectangle {rect_name!r} centered at same coord as MathTex {tex_name!r}; "
                        "use labeled_box() — auto-sizes rectangle to fit label + padding",
                    )
                )
        for scene in scenes:
            for lineno, mob_name in _find_unpositioned_always_redraw(scene.statements):
                self.errors.append(
                    LintError(
                        self.path,
                        lineno,
                        0,
                        "R7-always-redraw-unpositioned",
                        f"always_redraw(lambda: {mob_name}(...)) with no position; "
                        "pass move_to=/shift= kwarg or call .move_to inside the factory "
                        "— the bare constructor lands at origin every frame",
                    )
                )
        for scene in scenes:
            est = _estimated_scene_seconds(scene.statements)
            if est > _MAX_BEAT_SECONDS:
                self.errors.append(
                    LintError(
                        self.path,
                        scene.start_line,
                        0,
                        "R6-long-beat",
                        f"scene runs ~{est:.1f}s without self.clear(); split every 5-8s "
                        "so the frame changes (use self.clear(keep=[...]) to preserve anchors)",
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


def _lambda_body_positions_mob(body: ast.AST) -> bool:
    """True if the lambda's body positions the returned mob (move_to chain or point=/center= kwarg)."""
    if not isinstance(body, ast.Call):
        return False
    for inner in ast.walk(body):
        if not isinstance(inner, ast.Call):
            continue
        if isinstance(inner.func, ast.Attribute) and inner.func.attr in ("move_to", "shift"):
            return True
        for kw in inner.keywords:
            if kw.arg in ("point", "center"):
                return True
    return False


def _find_unpositioned_always_redraw(
    statements: list[ast.stmt],
) -> list[tuple[int, str]]:
    """Return (lineno, mob_name) for each always_redraw(lambda: <PositionLess>(...)) with no position."""
    hits: list[tuple[int, str]] = []
    for stmt in statements:
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Call):
                continue
            if _name_of(node.func) != "always_redraw":
                continue
            has_position_kwarg = any(kw.arg in ("move_to", "shift") for kw in node.keywords)
            if has_position_kwarg:
                continue
            if not node.args:
                continue
            factory = node.args[0]
            if not isinstance(factory, ast.Lambda):
                continue
            body = factory.body
            if not isinstance(body, ast.Call):
                continue
            callee = _name_of(body.func)
            if callee not in _POSITION_LESS_CONSTRUCTORS:
                continue
            if _lambda_body_positions_mob(body):
                continue
            hits.append((node.lineno, callee))
    return hits


def _max_run_time_in_call(node: ast.Call) -> float:
    """Max run_time= kwarg found anywhere inside this call tree (0 if none)."""
    best = 0.0
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call):
            continue
        for kw in inner.keywords:
            if kw.arg == "run_time":
                val = _constant_number(kw.value)
                if val is not None and val > best:
                    best = val
    return best


def _estimated_scene_seconds(statements: list[ast.stmt]) -> float:
    """Sum of self.wait(x) args + per-self.play() runtime estimates.

    Under-counts when run_time is omitted (uses defaults) or non-literal; treat
    as a lower bound. A lint miss is fine — a false R6 trip is not.
    """
    total = 0.0
    for stmt in statements:
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Call):
                continue
            if _is_self_method_call(node, "wait"):
                if node.args:
                    val = _constant_number(node.args[0])
                    if val is not None:
                        total += val
            elif _is_self_method_call(node, "play"):
                rt = _max_run_time_in_call(node)
                total += rt if rt > 0 else _DEFAULT_PLAY_SECONDS
    return total


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


def _constant_number(node: ast.AST) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, (int, float))
    ):
        return -float(node.operand.value)
    return None


def _extract_position(call: ast.Call) -> tuple[float, float] | None:
    if len(call.args) != 2:
        return None
    x = _constant_number(call.args[0])
    y = _constant_number(call.args[1])
    if x is None or y is None:
        return None
    return (x, y)


def _find_hand_sized_boxes(
    statements: list[ast.stmt],
) -> list[tuple[int, str, str]]:
    """Return (lineno, rect_name, tex_name) for each Rectangle+MathTex pair sharing position."""
    rectangles: dict[str, tuple[int, tuple[float, float] | None]] = {}
    mathtex: dict[str, tuple[int, tuple[float, float] | None]] = {}
    labeled_box_names: set[str] = set()

    for stmt in statements:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target = stmt.targets[0]
            value = stmt.value
            if isinstance(value, ast.Call) and _name_of(value.func) == "labeled_box":
                if isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            labeled_box_names.add(elt.id)
                continue
            if isinstance(value, ast.Call) and isinstance(target, ast.Name):
                callee = _name_of(value.func)
                if callee == "Rectangle":
                    rectangles[target.id] = (stmt.lineno, None)
                elif callee == "MathTex":
                    mathtex[target.id] = (stmt.lineno, None)
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if not isinstance(call.func, ast.Attribute):
                continue
            method = call.func.attr
            target = call.func.value
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            if method == "shift" and name in rectangles:
                pos = _extract_position(call)
                if pos is not None:
                    rectangles[name] = (rectangles[name][0], pos)
            elif method == "move_to" and name in mathtex:
                pos = _extract_position(call)
                if pos is not None:
                    mathtex[name] = (mathtex[name][0], pos)

    hits: list[tuple[int, str, str]] = []
    for rect_name, (rect_line, rect_pos) in rectangles.items():
        if rect_name in labeled_box_names or rect_pos is None:
            continue
        for tex_name, (_tex_line, tex_pos) in mathtex.items():
            if tex_name in labeled_box_names or tex_pos is None:
                continue
            if abs(rect_pos[0] - tex_pos[0]) < 0.05 and abs(rect_pos[1] - tex_pos[1]) < 0.05:
                hits.append((rect_line, rect_name, tex_name))
                break
    return hits


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

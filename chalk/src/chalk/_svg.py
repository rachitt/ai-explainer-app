"""SVG path parser: convert <path d="..."> into lists of cubic Bezier point arrays."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Generator

import numpy as np

# Fixed scale: 1 SVG pt → PT_TO_WORLD world units, y-axis flipped.
# Chosen so a typical math expression is 1–3 world units tall.
PT_TO_WORLD: float = 0.12


def parse_svg_to_vmobjects(
    svg_source: str,
    stroke_color: str = "#FFFFFF",
    stroke_width: float = 2.0,
    fill_color: str = "#FFFFFF",
    fill_opacity: float = 1.0,
) -> list["chalk.mobject.VMobject"]:  # type: ignore[name-defined]
    """Parse an SVG string into VMobjects, centered at origin in world coords."""
    from chalk.mobject import VMobject

    root = ET.fromstring(svg_source)
    ns = _svg_ns(root.tag)

    defs_tag = f"{ns}defs" if ns else "defs"
    path_tag = f"{ns}path" if ns else "path"
    use_tag = f"{ns}use" if ns else "use"

    # --- Build id → list-of-raw-point-arrays from <defs> ---
    id_to_paths: dict[str, list[np.ndarray]] = {}
    for defs in root.iter(defs_tag):
        for elem in defs.iter(path_tag):
            pid = elem.get("id", "")
            d = elem.get("d", "")
            if pid and d:
                raw = [pts for pts in _d_to_raw_cubic(d) if len(pts) >= 4]
                if raw:
                    id_to_paths[pid] = raw

    # --- Collect all positioned raw paths ---
    all_groups: list[list[np.ndarray]] = []

    rect_tag = f"{ns}rect" if ns else "rect"

    use_elements = list(root.iter(use_tag))
    if use_elements:
        for use in use_elements:
            href = (
                use.get("{http://www.w3.org/1999/xlink}href")
                or use.get("xlink:href")
                or use.get("href")
                or ""
            )
            ref_id = href.lstrip("#")
            paths = id_to_paths.get(ref_id, [])
            if not paths:
                continue
            dx = float(use.get("x", 0))
            dy = float(use.get("y", 0))
            offset = np.array([dx, dy])
            shifted = [pts + offset for pts in paths]
            all_groups.append(shifted)

        # Handle <rect> elements outside defs (e.g. fraction bars)
        def_elem_ids = {
            elem.get("id")
            for defs in root.iter(defs_tag)
            for elem in defs.iter()
            if elem.get("id")
        }
        for rect in root.iter(rect_tag):
            rect_id = rect.get("id", "")
            if rect_id and rect_id in def_elem_ids:
                continue
            rx = float(rect.get("x", 0))
            ry = float(rect.get("y", 0))
            rw = float(rect.get("width", 0))
            rh = float(rect.get("height", 0))
            if rw <= 0 or rh <= 0:
                continue
            pts = _rect_to_cubic(rx, ry, rw, rh)
            all_groups.append([pts])
    else:
        # Fallback: direct <path> elements not inside <defs>
        def_ids = set(id_to_paths.keys())
        for elem in root.iter(path_tag):
            if elem.get("id", "") in def_ids:
                continue
            d = elem.get("d", "")
            if not d:
                continue
            raw = [pts for pts in _d_to_raw_cubic(d) if len(pts) >= 4]
            if raw:
                all_groups.append(raw)

    if not all_groups:
        return []

    # --- Center all points at origin, apply fixed pt→world scale + y-flip ---
    all_pts = np.vstack([pts for group in all_groups for pts in group])
    cx = (all_pts[:, 0].min() + all_pts[:, 0].max()) / 2
    cy = (all_pts[:, 1].min() + all_pts[:, 1].max()) / 2

    def _to_world(pts: np.ndarray) -> np.ndarray:
        centered = pts - np.array([cx, cy])
        return np.stack([
            centered[:, 0] * PT_TO_WORLD,
            -centered[:, 1] * PT_TO_WORLD,
        ], axis=1)

    result: list[VMobject] = []
    for group in all_groups:
        if not group:
            continue
        world_subpaths = [_to_world(pts) for pts in group]
        m = VMobject(
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            stroke_opacity=1.0,
        )
        # Concatenate for bbox / point-count compat; subpaths drives rendering.
        m.points = np.concatenate(world_subpaths, axis=0)
        m.subpaths = world_subpaths
        m.fill_rule = "evenodd"
        result.append(m)
    return result


def _d_to_raw_cubic(d: str) -> Generator[np.ndarray, None, None]:
    """Parse SVG path d → chains of cubic Bezier control points in raw SVG coords."""
    token_list = list(_tokenize_d(d))
    curves: list[np.ndarray] = []
    pos = np.zeros(2)
    start = np.zeros(2)
    cmd = ""
    last_cp2 = np.zeros(2)   # last cubic control point 2 (for S command)
    last_qcp = np.zeros(2)   # last quadratic control point (for T command)
    i = 0

    def consume(n: int) -> list[float]:
        nonlocal i
        vals: list[float] = []
        while len(vals) < n and i < len(token_list):
            tok = token_list[i]
            if isinstance(tok, float):
                vals.append(tok)
                i += 1
            else:
                break
        return vals

    while i < len(token_list):
        tok = token_list[i]
        if isinstance(tok, str):
            cmd = tok
            i += 1
            if cmd in ("Z", "z"):
                if len(curves) > 0 and not np.allclose(pos, start):
                    curves.append(_line_to_cubic(pos, start))
                pos = start.copy()
                if curves:
                    yield np.concatenate(curves, axis=0)
                    curves = []
            continue

        argc = _CMD_ARGC.get(cmd, 0)
        if argc == 0:
            i += 1
            continue

        coords = consume(argc)
        if len(coords) < argc:
            break

        if cmd in ("M", "m"):
            if curves:
                yield np.concatenate(curves, axis=0)
                curves = []
            if cmd == "m":
                pos = pos + np.array([coords[0], coords[1]])
            else:
                pos = np.array([coords[0], coords[1]])
            start = pos.copy()
            last_cp2 = pos.copy()
            last_qcp = pos.copy()
            cmd = "l" if cmd == "m" else "L"

        elif cmd in ("L", "l"):
            p2 = pos + np.array([coords[0], coords[1]]) if cmd == "l" else np.array(coords[:2])
            curves.append(_line_to_cubic(pos, p2))
            last_cp2 = pos.copy()
            last_qcp = pos.copy()
            pos = p2

        elif cmd in ("H", "h"):
            p2 = np.array([pos[0] + coords[0], pos[1]]) if cmd == "h" else np.array([coords[0], pos[1]])
            curves.append(_line_to_cubic(pos, p2))
            last_cp2 = pos.copy()
            last_qcp = pos.copy()
            pos = p2

        elif cmd in ("V", "v"):
            p2 = np.array([pos[0], pos[1] + coords[0]]) if cmd == "v" else np.array([pos[0], coords[0]])
            curves.append(_line_to_cubic(pos, p2))
            last_cp2 = pos.copy()
            last_qcp = pos.copy()
            pos = p2

        elif cmd in ("C", "c"):
            if cmd == "c":
                c1 = pos + np.array([coords[0], coords[1]])
                c2 = pos + np.array([coords[2], coords[3]])
                p2 = pos + np.array([coords[4], coords[5]])
            else:
                c1 = np.array([coords[0], coords[1]])
                c2 = np.array([coords[2], coords[3]])
                p2 = np.array([coords[4], coords[5]])
            curves.append(np.array([pos, c1, c2, p2]))
            last_cp2 = c2
            last_qcp = pos
            pos = p2

        elif cmd in ("S", "s"):
            # Reflect last_cp2 about pos to get c1
            c1 = 2 * pos - last_cp2
            if cmd == "s":
                c2 = pos + np.array([coords[0], coords[1]])
                p2 = pos + np.array([coords[2], coords[3]])
            else:
                c2 = np.array([coords[0], coords[1]])
                p2 = np.array([coords[2], coords[3]])
            curves.append(np.array([pos, c1, c2, p2]))
            last_cp2 = c2
            last_qcp = pos
            pos = p2

        elif cmd in ("Q", "q"):
            # Quadratic → cubic elevation
            if cmd == "q":
                qcp = pos + np.array([coords[0], coords[1]])
                p2 = pos + np.array([coords[2], coords[3]])
            else:
                qcp = np.array([coords[0], coords[1]])
                p2 = np.array([coords[2], coords[3]])
            c1 = pos + 2/3 * (qcp - pos)
            c2 = p2 + 2/3 * (qcp - p2)
            curves.append(np.array([pos, c1, c2, p2]))
            last_cp2 = pos
            last_qcp = qcp
            pos = p2

        elif cmd in ("T", "t"):
            # Smooth quadratic: reflect last quadratic cp
            qcp = 2 * pos - last_qcp
            p2 = pos + np.array([coords[0], coords[1]]) if cmd == "t" else np.array(coords[:2])
            c1 = pos + 2/3 * (qcp - pos)
            c2 = p2 + 2/3 * (qcp - p2)
            curves.append(np.array([pos, c1, c2, p2]))
            last_cp2 = pos
            last_qcp = qcp
            pos = p2

    if curves:
        yield np.concatenate(curves, axis=0)


def _svg_ns(tag: str) -> str:
    if tag.startswith("{"):
        return "{" + tag[1:].split("}")[0] + "}"
    return ""


def _parse_viewbox(vb: str) -> tuple[float, float, float, float] | None:
    parts = vb.strip().split()
    if len(parts) == 4:
        return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
    return None


def _line_to_cubic(p0: np.ndarray, p1: np.ndarray) -> np.ndarray:
    d = p1 - p0
    return np.array([p0, p0 + d / 3, p0 + 2 * d / 3, p1])


_NUM_RE = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_CMD_RE = re.compile(r"[MmLlHhVvCcSsQqTtZz]")

_CMD_ARGC = {
    "M": 2, "m": 2,
    "L": 2, "l": 2,
    "H": 1, "h": 1,
    "V": 1, "v": 1,
    "C": 6, "c": 6,
    "S": 4, "s": 4,   # smooth cubic: x2 y2 x y
    "Q": 4, "q": 4,   # quadratic: x1 y1 x y
    "T": 2, "t": 2,   # smooth quadratic: x y
    "Z": 0, "z": 0,
}


def _rect_to_cubic(x: float, y: float, w: float, h: float) -> np.ndarray:
    """Convert SVG <rect> to 4 cubic Bezier line segments (16 points)."""
    corners = [
        np.array([x, y]),
        np.array([x + w, y]),
        np.array([x + w, y + h]),
        np.array([x, y + h]),
    ]
    curves = [_line_to_cubic(corners[i], corners[(i + 1) % 4]) for i in range(4)]
    return np.concatenate(curves, axis=0)


def _tokenize_d(d: str) -> Generator[str | float, None, None]:
    i = 0
    while i < len(d):
        while i < len(d) and d[i] in " ,\t\n\r":
            i += 1
        if i >= len(d):
            break
        m = _CMD_RE.match(d, i)
        if m:
            yield m.group()
            i = m.end()
            continue
        m = _NUM_RE.match(d, i)
        if m:
            yield float(m.group())
            i = m.end()
            continue
        i += 1

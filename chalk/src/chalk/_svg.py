"""SVG path parser: convert <path d="..."> into lists of cubic Bezier point arrays."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Generator

import numpy as np


def parse_svg_to_vmobjects(
    svg_source: str,
    stroke_color: str = "#FFFFFF",
    stroke_width: float = 2.0,
    fill_color: str = "#FFFFFF",
    fill_opacity: float = 1.0,
) -> list["chalk.mobject.VMobject"]:  # type: ignore[name-defined]
    from chalk.mobject import VMobject

    root = ET.fromstring(svg_source)
    ns = _svg_ns(root.tag)

    viewbox = _parse_viewbox(root.get("viewBox", ""))

    def make_mob(curve_pts: np.ndarray) -> "VMobject":
        m = VMobject(
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            stroke_opacity=1.0,
        )
        m.points = curve_pts
        return m

    # Build id → path-d map from <defs> (dvisvgm output pattern)
    id_to_d: dict[str, str] = {}
    defs_tag = f"{ns}defs" if ns else "defs"
    path_tag = f"{ns}path" if ns else "path"
    for defs in root.iter(defs_tag):
        for elem in defs.iter(path_tag):
            pid = elem.get("id", "")
            d = elem.get("d", "")
            if pid and d:
                id_to_d[pid] = d

    result: list[VMobject] = []

    # Process <use> elements (positions defs-referenced glyphs)
    use_tag = f"{ns}use" if ns else "use"
    for use in root.iter(use_tag):
        href = (
            use.get("{http://www.w3.org/1999/xlink}href")
            or use.get("xlink:href")
            or use.get("href")
            or ""
        )
        ref_id = href.lstrip("#")
        d = id_to_d.get(ref_id, "")
        if not d:
            continue
        x = float(use.get("x", 0))
        y = float(use.get("y", 0))
        offset = np.array([x, y])
        for curve_pts in _d_to_cubic_chains(d, viewbox):
            if len(curve_pts) < 4:
                continue
            # Apply <use> translation in SVG space before normalizing
            # Re-normalize with offset: shift raw points then normalize
            raw = _unnormalize(curve_pts, viewbox) + offset
            normalized = _normalize(raw, viewbox)
            result.append(make_mob(normalized))

    # Fallback: direct <path> elements not inside <defs>
    if not result:
        for elem in root.findall(f".//{path_tag}"):
            if elem.get("id", "").startswith("g"):
                continue  # skip defs paths
            d = elem.get("d", "")
            if not d:
                continue
            for curve_pts in _d_to_cubic_chains(d, viewbox):
                if len(curve_pts) < 4:
                    continue
                result.append(make_mob(curve_pts))

    return result


def _svg_ns(tag: str) -> str:
    """Extract namespace prefix from a tag like '{http://...}svg'."""
    if tag.startswith("{"):
        return "{" + tag[1:].split("}")[0] + "}"
    return ""


def _parse_viewbox(vb: str) -> tuple[float, float, float, float] | None:
    parts = vb.strip().split()
    if len(parts) == 4:
        return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
    return None


def _d_to_cubic_chains(
    d: str,
    viewbox: tuple[float, float, float, float] | None,
) -> Generator[np.ndarray, None, None]:
    """Parse SVG path d attribute into chains of cubic Bezier control points."""
    token_list = list(_tokenize_d(d))
    curves: list[np.ndarray] = []
    pos = np.zeros(2)
    start = np.zeros(2)
    cmd = ""
    i = 0

    def consume(n: int) -> list[float]:
        nonlocal i
        vals = []
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
                if not np.allclose(pos, start):
                    curves.append(_line_to_cubic(pos, start))
                pos = start.copy()
                if curves:
                    pts = np.concatenate(curves, axis=0)
                    yield _normalize(pts, viewbox)
                    curves = []
            continue

        # Implicit command repetition: tok is a float, re-use current cmd
        # (after M/m, subsequent coords are treated as L/l)
        argc = _CMD_ARGC.get(cmd, 0)
        if argc == 0:
            i += 1
            continue

        coords = consume(argc)
        if len(coords) < argc:
            break  # incomplete, skip

        if cmd in ("M", "m"):
            if curves:
                pts = np.concatenate(curves, axis=0)
                yield _normalize(pts, viewbox)
                curves = []
            if cmd == "m":
                pos = pos + np.array([coords[0], coords[1]])
            else:
                pos = np.array([coords[0], coords[1]])
            start = pos.copy()
            cmd = "l" if cmd == "m" else "L"

        elif cmd in ("L", "l"):
            p2 = pos + np.array([coords[0], coords[1]]) if cmd == "l" else np.array(coords[:2])
            curves.append(_line_to_cubic(pos, p2))
            pos = p2

        elif cmd in ("H", "h"):
            p2 = np.array([pos[0] + coords[0], pos[1]]) if cmd == "h" else np.array([coords[0], pos[1]])
            curves.append(_line_to_cubic(pos, p2))
            pos = p2

        elif cmd in ("V", "v"):
            p2 = np.array([pos[0], pos[1] + coords[0]]) if cmd == "v" else np.array([pos[0], coords[0]])
            curves.append(_line_to_cubic(pos, p2))
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
            pos = p2

    if curves:
        pts = np.concatenate(curves, axis=0)
        yield _normalize(pts, viewbox)


def _line_to_cubic(p0: np.ndarray, p1: np.ndarray) -> np.ndarray:
    """Convert a line segment to a cubic Bezier with collinear handles."""
    d = p1 - p0
    return np.array([p0, p0 + d / 3, p0 + 2 * d / 3, p1])


def _normalize(
    pts: np.ndarray,
    viewbox: tuple[float, float, float, float] | None,
) -> np.ndarray:
    """Map SVG coordinates to chalk world coordinates (centered, y-up, ~[-7, 7])."""
    if viewbox is None:
        return pts
    vx, vy, vw, vh = viewbox
    cx = (pts[:, 0] - vx - vw / 2) / vw * 14.0
    cy = -(pts[:, 1] - vy - vh / 2) / vh * 8.0
    return np.stack([cx, cy], axis=1)


def _unnormalize(
    pts: np.ndarray,
    viewbox: tuple[float, float, float, float] | None,
) -> np.ndarray:
    """Inverse of _normalize: chalk world coords → SVG coords."""
    if viewbox is None:
        return pts
    vx, vy, vw, vh = viewbox
    sx = pts[:, 0] / 14.0 * vw + vx + vw / 2
    sy = -pts[:, 1] / 8.0 * vh + vy + vh / 2
    return np.stack([sx, sy], axis=1)


_NUM_RE = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_CMD_RE = re.compile(r"[MmLlHhVvCcZz]")

# Number of coordinate values consumed per command invocation
_CMD_ARGC = {
    "M": 2, "m": 2,
    "L": 2, "l": 2,
    "H": 1, "h": 1,
    "V": 1, "v": 1,
    "C": 6, "c": 6,
    "Z": 0, "z": 0,
}


def _tokenize_d(d: str) -> Generator[str | float, None, None]:
    """Yield command chars and individual floats."""
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
        i += 1  # skip unknown char

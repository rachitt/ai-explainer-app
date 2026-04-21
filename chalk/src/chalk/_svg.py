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
    # Collect all path elements (handle both with and without namespace)
    path_elements = root.findall(f".//{ns}path") if ns else root.findall(".//path")

    result: list[VMobject] = []
    for elem in path_elements:
        d = elem.get("d", "")
        if not d:
            continue
        for curve_pts in _d_to_cubic_chains(d, viewbox):
            if len(curve_pts) < 4:
                continue
            m = VMobject(
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                fill_color=fill_color,
                fill_opacity=fill_opacity,
                stroke_opacity=1.0,
            )
            m.points = curve_pts
            result.append(m)
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
    tokens = _tokenize_d(d)
    curves: list[np.ndarray] = []
    pos = np.zeros(2)
    start = np.zeros(2)
    cmd = ""

    for tok in tokens:
        if isinstance(tok, str):
            cmd = tok
            if cmd in ("Z", "z"):
                if not np.allclose(pos, start):
                    curves.append(_line_to_cubic(pos, start))
                pos = start.copy()
                if curves:
                    pts = np.concatenate(curves, axis=0)
                    yield _normalize(pts, viewbox)
                    curves = []
            continue

        coords: list[float] = list(tok)

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
            p1 = pos.copy()
            p2 = pos + np.array([coords[0], coords[1]]) if cmd == "l" else np.array(coords[:2])
            curves.append(_line_to_cubic(p1, p2))
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
    # Center
    cx = (pts[:, 0] - vx - vw / 2) / vw * 14.0   # map to [-7, 7]
    cy = -(pts[:, 1] - vy - vh / 2) / vh * 8.0    # flip y, map to [-4, 4]
    return np.stack([cx, cy], axis=1)


_NUM_RE = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_CMD_RE = re.compile(r"[MmLlCcZz]")


def _tokenize_d(d: str) -> Generator[str | tuple[float, ...], None, None]:
    """Yield command strings or tuples of floats."""
    i = 0
    while i < len(d):
        m = _CMD_RE.match(d, i)
        if m:
            yield m.group()
            i = m.end()
            continue
        m = _NUM_RE.match(d, i)
        if m:
            # Collect all numbers belonging to this command invocation
            nums: list[float] = []
            while True:
                nm = _NUM_RE.match(d, i)
                if nm:
                    nums.append(float(nm.group()))
                    i = nm.end()
                    # skip separators
                    while i < len(d) and d[i] in " ,\t\n\r":
                        i += 1
                else:
                    break
            yield tuple(nums)  # type: ignore[misc]
            continue
        # Skip whitespace/commas
        if d[i] in " ,\t\n\r":
            i += 1
        else:
            i += 1

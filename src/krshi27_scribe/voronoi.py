"""Voronoi typography: string → list of 2D path numpy arrays.

Lifted from average-abstraction/src/typography_generator.py with a lazy font
loader and seed-controllable RNG.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

import numpy as np
import shapely.geometry as sg
from scipy.spatial import ConvexHull, Voronoi

_PACKAGE_FONT = Path(__file__).parent / "data" / "font" / "karoshirt.xml"
_alphabet_cache: dict[str, list[tuple[float, float]]] | None = None


def _load_alphabet(font_path: Path) -> dict[str, list[tuple[float, float]]]:
    tree = ET.parse(font_path)
    root = tree.getroot()
    alphabet: dict[str, list[tuple[float, float]]] = {}
    for geometry in root.findall("diagram"):
        letter = str(geometry.get("name"))
        page_width = float(geometry.find(".//mxGraphModel").get("pageWidth"))
        page_height = float(geometry.find(".//mxGraphModel").get("pageWidth"))
        pts: list[tuple[float, float]] = []
        src = geometry.find('.//mxPoint[@as="sourcePoint"]')
        tgt = geometry.find('.//mxPoint[@as="targetPoint"]')
        way = geometry.find('.//Array[@as="points"]')
        if src is not None:
            pts.append((float(src.get("x")) / page_width / 2, -float(src.get("y")) / page_height / 2))
        if way is not None:
            for p in way.findall("mxPoint"):
                pts.append((float(p.get("x")) / page_width / 2, -float(p.get("y")) / page_height / 2))
        if tgt is not None:
            pts.append((float(tgt.get("x")) / page_width / 2, -float(tgt.get("y")) / page_height / 2))
        if not pts:
            pts = [(0.0, 0.0), (0.1, -0.1), (0.2, 0.0)]
        alphabet[letter] = pts
    return alphabet


def _get_alphabet(font_path: Path | None) -> dict[str, list[tuple[float, float]]]:
    global _alphabet_cache
    if font_path is not None:
        return _load_alphabet(font_path)
    if _alphabet_cache is None:
        _alphabet_cache = _load_alphabet(_PACKAGE_FONT)
    return _alphabet_cache


def _shift_inside_cells(multiline: np.ndarray, voronoi: Voronoi, shift_range: float, rng) -> np.ndarray:
    out = multiline.copy()
    for region in voronoi.regions:
        if -1 in region or not region:
            continue
        poly = sg.Polygon(voronoi.vertices[region])
        for i in range(len(out)):
            if poly.contains(sg.Point(out[i])):
                for _ in range(20):
                    cand = out[i] + rng.normal(0.0, shift_range, size=2)
                    if poly.contains(sg.Point(cand)):
                        out[i] = cand
                        break
    return out


def _character_paths(char, base_multiline, hull_buffer, n_shift, shift_range, rng):
    multiline = np.array(base_multiline, dtype=np.float64)
    if char == " " or len(multiline) < 3:
        return [multiline]
    hull = ConvexHull(multiline)
    hull_poly = sg.Polygon(multiline[hull.vertices])
    buffered = np.array(hull_poly.buffer(hull_buffer).exterior.coords)
    voronoi = Voronoi(np.concatenate((multiline, buffered), axis=0))
    paths = [multiline.copy()]
    current = multiline.copy()
    for _ in range(n_shift):
        current = _shift_inside_cells(current, voronoi, shift_range, rng)
        paths.append(current.copy())
    return paths


def voronoi_paths(
    text: str,
    n_shift: int = 10,
    shift_range: float = 0.0125,
    hull_buffer: float = 0.1,
    seed: int = 0,
    font_path: str | Path | None = None,
) -> List[np.ndarray]:
    """Return a list of 2D path arrays forming the typographic rendering of `text`.

    Each character contributes one base multiline + `n_shift` voronoi-shifted copies.
    """
    alphabet = _get_alphabet(Path(font_path) if font_path else None)
    rng = np.random.default_rng(seed)

    out: list[np.ndarray] = []
    x_cursor = 0.0
    for ch in text:
        base = alphabet.get(ch, alphabet.get(ch.upper(), [(0.0, 0.0), (0.1, 0.0)]))
        multiline = np.array(base, dtype=np.float64)
        min_x = float(multiline[:, 0].min())
        max_x = float(multiline[:, 0].max())
        width = max_x - min_x
        char_paths = _character_paths(ch, multiline, hull_buffer, n_shift, shift_range, rng)
        for p in char_paths:
            shifted = p.copy()
            shifted[:, 0] += (x_cursor - min_x)
            out.append(shifted.astype(np.float32))
        x_cursor += width + 0.05
    return out

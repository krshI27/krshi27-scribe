"""text → RGBA stencil image via matplotlib. Transparent bg, colored strokes."""

from __future__ import annotations

import gc
import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from .voronoi import voronoi_paths  # noqa: E402


def render(
    text: str,
    size: int = 512,
    line_color: str = "#000000",
    line_width: float = 2.0,
    opacity: float = 1.0,
    n_shift: int = 10,
    shift_range: float = 0.0125,
    hull_buffer: float = 0.1,
    seed: int = 0,
    font_path: str | Path | None = None,
    bg: str | None = None,
) -> Image.Image:
    paths = voronoi_paths(text, n_shift=n_shift, shift_range=shift_range, hull_buffer=hull_buffer, seed=seed, font_path=font_path)

    dpi = 100
    fig_inches = size / dpi
    fig = plt.figure(figsize=(fig_inches, fig_inches), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_aspect("equal")

    for path in paths:
        if len(path) < 2:
            continue
        ax.plot(path[:, 0], path[:, 1], color=line_color, linewidth=line_width,
                alpha=opacity, solid_capstyle="round")

    if bg is not None:
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        transparent = False
    else:
        transparent = True

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=transparent, bbox_inches=None, pad_inches=0)
    plt.close(fig)
    gc.collect()
    buf.seek(0)
    return Image.open(buf).convert("RGBA").resize((size, size), Image.LANCZOS)

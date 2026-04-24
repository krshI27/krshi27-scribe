"""Subway window background: mask extraction and stencil compositing."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

_DATA_DIR = Path(__file__).parent.parent.parent / "data"

BACKGROUNDS: dict[str, str] = {
    "Subway Window": str(_DATA_DIR / "background.png"),
}

# Calibrated fractions for background.png (2200×1500).
# Derived from pixel-level edge detection of the window glass boundary.
_WINDOW_FRACS = {
    "x0": 0.136,
    "x1": 0.866,
    "y0": 0.137,
    "y1": 0.870,
    "r_frac": 0.027,  # corner radius as fraction of width
}


def load_background(name: str) -> Image.Image:
    path = BACKGROUNDS[name]
    return Image.open(path).convert("RGBA")


def window_mask(bg: Image.Image) -> Image.Image:
    """Return a grayscale mask (L) of the window glass area."""
    w, h = bg.size
    f = _WINDOW_FRACS
    x0 = int(f["x0"] * w)
    x1 = int(f["x1"] * w)
    y0 = int(f["y0"] * h)
    y1 = int(f["y1"] * h)
    r = int(f["r_frac"] * w)
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=r, fill=255)
    return mask


def window_bbox(bg: Image.Image) -> tuple[int, int, int, int]:
    """Return (x0, y0, x1, y1) pixel bounds of the window glass area."""
    w, h = bg.size
    f = _WINDOW_FRACS
    return (
        int(f["x0"] * w),
        int(f["y0"] * h),
        int(f["x1"] * w),
        int(f["y1"] * h),
    )


def window_render_size(bg: Image.Image) -> int:
    """Native render size to use when compositing on `bg` (= window width, no upscaling)."""
    x0, _, x1, _ = window_bbox(bg)
    return x1 - x0


def composite_on_window(
    stencil: Image.Image,
    bg: Image.Image,
    feather: int = 8,
) -> Image.Image:
    """Composite an RGBA stencil over bg, clipped to the window glass area.

    Stencil fills the full window width. Positioned so the text sits in the
    lower half of the glass. Edges softened by `feather` pixels.
    """
    w, h = bg.size
    x0, y0, x1, y1 = window_bbox(bg)
    win_w = x1 - x0
    win_h = y1 - y0

    # Fill the full window width — no upscaling when stencil was rendered at window_render_size().
    stencil_rgba = stencil.convert("RGBA")
    scaled_side = win_w
    scaled = stencil_rgba.resize((scaled_side, scaled_side), Image.LANCZOS)

    # Place stencil center at 2/3 down the window (bottom third).
    paste_x = x0
    paste_y = y0 + int(0.67 * win_h) - scaled_side // 2

    # Place stencil on a transparent full-size canvas.
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.paste(scaled, (paste_x, paste_y))

    # Build window mask and feather its edges.
    mask = window_mask(bg)
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))

    # Clip layer alpha by window mask.
    layer_arr = np.array(layer, dtype=np.uint16)
    mask_arr = np.array(mask, dtype=np.uint16)
    layer_arr[:, :, 3] = (layer_arr[:, :, 3] * mask_arr) // 255
    layer = Image.fromarray(layer_arr.astype(np.uint8))

    result = Image.alpha_composite(bg.convert("RGBA"), layer)
    return result.convert("RGB")

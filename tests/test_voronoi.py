import numpy as np
import pytest

from krshi27_scribe import render, voronoi_paths, BACKGROUNDS, load_background, window_mask, composite_on_window


def test_voronoi_paths_returns_arrays():
    paths = voronoi_paths("KR", n_shift=2, seed=0)
    assert len(paths) > 0
    assert all(isinstance(p, np.ndarray) and p.shape[1] == 2 for p in paths)


def test_render_produces_rgba_of_requested_size():
    img = render("AB", size=128, n_shift=1, seed=0)
    assert img.size == (128, 128)
    assert img.mode == "RGBA"


def test_render_line_color_respected():
    """White strokes should produce white pixels; red strokes should produce red."""
    white = render("A", size=128, n_shift=1, seed=0, line_color="#ffffff")
    red = render("A", size=128, n_shift=1, seed=0, line_color="#ff0000")
    arr_w = np.array(white)
    arr_r = np.array(red)
    # Opaque pixels (alpha=255) should differ between the two renders.
    opaque_w = arr_w[arr_w[:, :, 3] == 255]
    opaque_r = arr_r[arr_r[:, :, 3] == 255]
    assert len(opaque_w) > 0 and len(opaque_r) > 0
    assert not np.array_equal(opaque_w[:, :3], opaque_r[:, :3])


def test_backgrounds_dict_contains_subway_window():
    assert "Subway Window" in BACKGROUNDS


def test_load_background_returns_rgba():
    bg = load_background("Subway Window")
    assert bg.mode == "RGBA"
    assert bg.size == (2200, 1500)


def test_window_mask_correct_size_and_values():
    from PIL import Image
    bg = Image.new("RGBA", (2200, 1500), (0, 0, 0, 255))
    mask = window_mask(bg)
    assert mask.mode == "L"
    assert mask.size == (2200, 1500)
    arr = np.array(mask)
    # Corners should be black (outside window).
    assert arr[0, 0] == 0
    assert arr[1499, 2199] == 0
    # Center should be white (inside window).
    assert arr[750, 1100] == 255


def test_composite_on_window_returns_rgb():
    stencil = render("K", size=128, n_shift=1, seed=0, line_color="#ffffff")
    bg = load_background("Subway Window")
    result = composite_on_window(stencil, bg)
    assert result.mode == "RGB"
    assert result.size == bg.size


def test_composite_on_window_modifies_image():
    """The composite should differ from the plain background."""
    stencil = render("K", size=512, n_shift=5, seed=42, line_color="#ffffff")
    bg = load_background("Subway Window")
    result = composite_on_window(stencil, bg)
    arr_bg = np.array(bg.convert("RGB"))
    arr_result = np.array(result)
    assert not np.array_equal(arr_bg, arr_result)

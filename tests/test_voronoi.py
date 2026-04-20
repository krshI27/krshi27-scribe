import numpy as np

from krshi27_scribe import render, voronoi_paths


def test_voronoi_paths_returns_arrays():
    paths = voronoi_paths("KR", n_shift=2, seed=0)
    assert len(paths) > 0
    assert all(isinstance(p, np.ndarray) and p.shape[1] == 2 for p in paths)


def test_render_produces_rgba_of_requested_size():
    img = render("AB", size=128, n_shift=1, seed=0)
    assert img.size == (128, 128)
    assert img.mode == "RGBA"

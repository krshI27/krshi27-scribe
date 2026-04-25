"""krshi27_scribe package exports.

Avoid importing heavy submodules at package import time (e.g., modules that
depend on `shapely`). Expose the public symbols via a lazy loader so that
`import krshi27_scribe` is cheap and errors only occur when the concrete
functionality is actually used.
"""

from importlib import import_module

__all__ = [
	"render",
	"voronoi_paths",
	"BACKGROUNDS",
	"load_background",
	"window_mask",
	"window_render_size",
	"composite_on_window",
]


def __getattr__(name: str):
	if name == "voronoi_paths":
		return import_module(".voronoi", __name__).voronoi_paths
	if name == "render":
		return import_module(".render", __name__).render
	if name in (
		"BACKGROUNDS",
		"load_background",
		"window_mask",
		"window_render_size",
		"composite_on_window",
	):
		mod = import_module(".background", __name__)
		return getattr(mod, name)
	raise AttributeError(f"module {__name__} has no attribute {name}")

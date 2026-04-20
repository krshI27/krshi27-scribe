# krshi27-scribe

Karoshirt-font Voronoi typography. Text string → list of 2D paths, or directly
to a B&W stencil image.

## API

- `voronoi_paths(text: str, ...) -> list[np.ndarray]` — pre-rasterization paths. Feed to any 3D extruder (e.g. tagmesh) or to `render()`.
- `render(text: str, size: int, ...) -> PIL.Image.Image` — RGBA stencil (transparent bg, black strokes).

## Install

```bash
pip install -e .
```

Source: extracted from `average-abstraction/src/typography_generator.py`.

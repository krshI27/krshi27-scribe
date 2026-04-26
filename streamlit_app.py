import io
import json
import os
import sys
import urllib.parse

# Streamlit Cloud: add src/ to path so krshi27_scribe is importable without pip install
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import streamlit as st
from PIL import Image

from krshi27_scribe import render, BACKGROUNDS, load_background, window_render_size, composite_on_window

st.set_page_config(page_title="krshi27-scribe", layout="wide")

BG_SOLID = "Solid Color"
BG_WINDOW = "Subway Window"
DEFAULT_PARAMS = {
    "text": "KRSHI27",
    "size": 512,
    "n_shift": 10,
    "shift_range": 0.0125,
    "line_width": 2.0,
    "seed": 0,
    "line_color": "#000000",
    "bg_color": "#ffffff",
    "opacity": 1.0,
    "background": BG_SOLID,
}


def _load_preset():
    preset_raw = st.query_params.get("preset")
    if not preset_raw:
        return
    preset_text = preset_raw[0] if isinstance(preset_raw, list) else preset_raw
    try:
        preset = json.loads(preset_text)
        for key, value in preset.get("params", {}).items():
            if key in DEFAULT_PARAMS:
                st.session_state.setdefault(key, value)
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass


def _preset_url(params: dict[str, object]) -> str:
    payload = {
        "name": "Zine Vol.1 — KRSHI27 Voronoi",
        "app": "krshi27-scribe",
        "params": params,
    }
    return f"?preset={urllib.parse.quote(json.dumps(payload, separators=(',', ':')))}"


@st.cache_data(max_entries=2)
def _high_res_jpeg_bytes(text, line_color, bg_color, opacity, line_width, n_shift, shift_range, seed):
    square = render(
        text,
        size=2480,
        line_color=line_color,
        opacity=opacity,
        line_width=line_width,
        n_shift=n_shift,
        shift_range=shift_range,
        seed=seed,
        bg=bg_color,
    )
    a4_width, a4_height = 2480, 3508
    canvas = Image.new("RGB", (a4_width, a4_height), bg_color)
    canvas.paste(square, (0, (a4_height - 2480) // 2), square.convert("RGBA"))
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", dpi=(300, 300), quality=95)
    return buf.getvalue()


_load_preset()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Parameters")

    text = st.text_input("Text", DEFAULT_PARAMS["text"], key="text")

    st.subheader("Background")
    background = st.radio(
        "Mode",
        [BG_SOLID, BG_WINDOW],
        horizontal=True,
        key="background",
        label_visibility="collapsed",
    )
    if background == BG_SOLID:
        col_bg, col_stroke = st.columns(2)
        with col_bg:
            bg_color = st.color_picker("Background", DEFAULT_PARAMS["bg_color"], key="bg_color")
        with col_stroke:
            line_color = st.color_picker("Stroke", DEFAULT_PARAMS["line_color"], key="line_color")
    else:
        bg_color = DEFAULT_PARAMS["bg_color"]
        line_color = st.color_picker("Stroke color", "#ffffff", key="line_color")

    st.subheader("Shape")
    n_shift = st.slider(
        "Layers", 0, 256, DEFAULT_PARAMS["n_shift"], key="n_shift",
        help="Number of Voronoi-shifted copies per character",
    )
    shift_range = st.slider(
        "Scatter", 0.0, 0.05, DEFAULT_PARAMS["shift_range"],
        step=0.001, format="%.3f", key="shift_range",
        help="How far each copy drifts within its Voronoi cell",
    )

    st.subheader("Style")
    line_width = st.slider(
        "Stroke weight", 0.1, 6.0, DEFAULT_PARAMS["line_width"], step=0.1, key="line_width",
    )
    opacity = st.slider(
        "Opacity", 0.0, 1.0, DEFAULT_PARAMS["opacity"], step=0.05, format="%.2f", key="opacity",
    )

    st.subheader("Output")
    seed = st.number_input("Seed", 0, 9999, DEFAULT_PARAMS["seed"], key="seed")
    if background == BG_SOLID:
        size = st.slider("Resolution", 128, 1024, DEFAULT_PARAMS["size"], step=64, key="size")
    else:
        size = DEFAULT_PARAMS["size"]
        st.caption("Resolution: auto (native window width)")

    st.divider()
    render_clicked = st.button("Render", type="primary", use_container_width=True)

# ── Main canvas ───────────────────────────────────────────────────────────────
st.title("krshi27-scribe")
st.caption("text → Voronoi stencil")

if render_clicked:
    if background == BG_WINDOW:
        bg_img = load_background(BG_WINDOW)
        render_size = window_render_size(bg_img)
        stencil = render(
            text,
            size=render_size,
            line_color=line_color,
            opacity=opacity,
            n_shift=n_shift,
            shift_range=shift_range,
            line_width=line_width,
            seed=seed,
        )
        result = composite_on_window(stencil, bg_img)
    else:
        stencil = render(
            text,
            size=size,
            line_color=line_color,
            opacity=opacity,
            n_shift=n_shift,
            shift_range=shift_range,
            line_width=line_width,
            seed=seed,
            bg=bg_color,
        )
        result = stencil.convert("RGB")

    buf = io.BytesIO()
    result.save(buf, format="PNG")
    st.session_state["preview_png"] = buf.getvalue()

if st.session_state.get("preview_png"):
    st.image(st.session_state["preview_png"], use_container_width=True)

# ── Export ────────────────────────────────────────────────────────────────────
with st.expander("Preset URL"):
    preset_query = _preset_url(
        {
            "text": text,
            "size": size,
            "n_shift": n_shift,
            "shift_range": shift_range,
            "line_width": line_width,
            "seed": seed,
            "line_color": line_color,
            "bg_color": bg_color,
            "opacity": opacity,
            "background": background,
        }
    )
    st.write("Load these exact parameters:")
    st.code(preset_query)

if st.button("Prepare A4 300 dpi JPEG"):
    with st.spinner("Rendering A4 300 dpi…"):
        st.session_state["a4_jpeg"] = _high_res_jpeg_bytes(
            text, line_color, bg_color, opacity, line_width, n_shift, shift_range, seed
        )

if st.session_state.get("a4_jpeg"):
    st.download_button(
        label="Download A4 300 dpi JPEG",
        data=st.session_state["a4_jpeg"],
        file_name="krshi27-scribe-a4.jpg",
        mime="image/jpeg",
    )

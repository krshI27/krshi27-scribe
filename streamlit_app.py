import io
import json
import urllib.parse

import streamlit as st
from PIL import Image

from krshi27_scribe import render, BACKGROUNDS, load_background, window_render_size, composite_on_window

st.set_page_config(page_title="krshi27-scribe")

BG_NONE = "None"
DEFAULT_PARAMS = {
    "text": "KRSHI27",
    "size": 512,
    "n_shift": 10,
    "shift_range": 0.0125,
    "line_width": 2.0,
    "seed": 0,
    "line_color": "#000000",
    "opacity": 1.0,
    "background": BG_NONE,
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


@st.cache_data
def _high_res_jpeg_bytes(text, line_color, opacity, line_width, n_shift, shift_range, seed):
    source = render(
        text,
        size=3508,
        line_color=line_color,
        opacity=opacity,
        line_width=line_width,
        n_shift=n_shift,
        shift_range=shift_range,
        seed=seed,
    )
    a4_width, a4_height = 2480, 3508
    canvas = Image.new("RGB", (a4_width, a4_height), "white")
    square = source.resize((2480, 2480), Image.LANCZOS)
    canvas.paste(square, (0, (a4_height - 2480) // 2), square.convert("RGBA"))
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", dpi=(300, 300), quality=95)
    return buf.getvalue()


_load_preset()

st.title("krshi27-scribe")
st.caption("text → Voronoi stencil")

text = st.text_input("text", DEFAULT_PARAMS["text"], key="text")
n_shift = st.slider("n_shift", 0, 60, DEFAULT_PARAMS["n_shift"], key="n_shift")
shift_range = st.slider(
    "shift_range", 0.0, 0.05, DEFAULT_PARAMS["shift_range"], step=0.001, format="%.3f", key="shift_range"
)
line_width = st.slider("line width", 0.1, 6.0, DEFAULT_PARAMS["line_width"], step=0.1, key="line_width")
seed = st.number_input("seed", 0, 9999, DEFAULT_PARAMS["seed"], key="seed")

# Background selection
col_a, col_b = st.columns(2)
with col_a:
    bg_options = [BG_NONE] + list(BACKGROUNDS.keys())
    background = st.selectbox("background", bg_options, key="background")
with col_b:
    default_color = "#ffffff" if background != BG_NONE else DEFAULT_PARAMS["line_color"]
    line_color = st.color_picker("stroke color", default_color, key="line_color")

opacity = st.slider("opacity", 0.0, 1.0, DEFAULT_PARAMS["opacity"], step=0.05, format="%.2f", key="opacity")

# Size slider only relevant for plain stencil / download quality.
if background == BG_NONE:
    size = st.slider("size (px)", 128, 1024, DEFAULT_PARAMS["size"], step=64, key="size")
else:
    size = DEFAULT_PARAMS["size"]
    st.caption("size: auto (native window resolution when background active)")

if st.button("Render"):
    if background != BG_NONE:
        bg_img = load_background(background)
        render_size = window_render_size(bg_img)
    else:
        bg_img = None
        render_size = size

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

    if bg_img is not None:
        result = composite_on_window(stencil, bg_img)
    else:
        result = stencil.convert("RGB")

    buf = io.BytesIO()
    result.save(buf, format="PNG")
    st.session_state["preview_png"] = buf.getvalue()

if st.session_state.get("preview_png"):
    st.image(st.session_state["preview_png"], use_container_width=True)

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
            "opacity": opacity,
            "background": background,
        }
    )
    st.write("Load these exact parameters with query string:")
    st.code(preset_query)

st.download_button(
    label="Download A4 300dpi JPEG (plain stencil)",
    data=_high_res_jpeg_bytes(text, line_color, opacity, line_width, n_shift, shift_range, seed),
    file_name="krshi27-scribe-a4.jpg",
    mime="image/jpeg",
)

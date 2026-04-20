import streamlit as st

from karoshirt_type import render
from krshi_style import apply_theme

apply_theme(st, page_title="karoshirt-type")
st.title("karoshirt-type")
st.caption("text → Voronoi stencil")

text = st.text_input("text", "KRSHI27")
size = st.slider("size", 128, 1024, 512, step=64)
n_shift = st.slider("n_shift", 0, 30, 10)
shift_range = st.slider("shift_range", 0.0, 0.05, 0.0125, step=0.001, format="%.3f")
line_width = st.slider("line width", 0.5, 6.0, 2.0, step=0.5)
seed = st.number_input("seed", 0, 9999, 0)

if st.button("render"):
    img = render(text, size=size, n_shift=n_shift, shift_range=shift_range, line_width=line_width, seed=seed)
    st.image(img, use_container_width=True)

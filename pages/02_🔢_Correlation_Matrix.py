import streamlit as st
import plotly.express as px
from utils.constants import CORR_HEATMAP_COLORS

# Bug fix: missing set_page_config (must be first Streamlit command)
st.set_page_config(page_title="Correlation Matrix", layout="wide")
st.title("🔢 Correlation Matrix")

if st.session_state.get("data_cache") is None:
    st.warning("Data not loaded. Return to the main page first.")
    st.stop()

data = st.session_state.data_cache.get_all_data()
corr_matrix = data["corr_matrix"]

fig = px.imshow(
    corr_matrix,
    text_auto=".2f",
    color_continuous_scale=CORR_HEATMAP_COLORS,
    zmin=-1, zmax=1,
    title="All-Pairs Correlation Heatmap",
)
st.plotly_chart(fig, use_container_width=True)

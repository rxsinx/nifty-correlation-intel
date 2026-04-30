import streamlit as st
import plotly.express as px
from utils.constants import CORR_HEATMAP_COLORS

st.title("🔢 Correlation Matrix")
data = st.session_state.data_cache.get_all_data()
corr_matrix = data['corr_matrix']

fig = px.imshow(corr_matrix,
                text_auto=".2f",
                color_continuous_scale=CORR_HEATMAP_COLORS,
                zmin=-1, zmax=1,
                title="All-Pairs Correlation Heatmap")
st.plotly_chart(fig, use_container_width=True)

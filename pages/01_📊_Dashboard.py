import streamlit as st
import pandas as pd
import plotly.express as px
from utils.constants import REGIME_COLORS

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("📊 Market Dashboard")

cache = st.session_state.data_cache
if cache is None:
    st.warning("Data not loaded. Check API credentials on main page.")
    st.stop()

data = cache.get_all_data()
if data is None:
    st.info("Refreshing data...")
    st.stop()

regime = data['regime']
clock = regime['crisis_clock']

# Metrics row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Regime", regime['regime_label'])
col2.metric("Crisis Clock", f"{clock:.0f}/100")
col3.metric("Avg |Corr|", f"{regime['avg_abs_corr']:.2f}")
col4.metric("Dispersion", f"{regime['dispersion']:.2f}")

# Simple bar chart of correlations
st.subheader("Correlation vs NIFTY")
corr_df = pd.DataFrame({sym: [m['corr']] for sym, m in data['metrics'].items() if 'corr' in m})
st.bar_chart(corr_df.T)

st.markdown("---")
st.caption("🔹 Use sidebar to explore deeper analytics.")

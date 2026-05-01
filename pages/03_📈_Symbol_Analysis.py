import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Bug fix: missing set_page_config
st.set_page_config(page_title="Symbol Analysis", layout="wide")
st.title("📈 Symbol Deep Dive")

if st.session_state.get("data_cache") is None:
    st.warning("Data not loaded. Return to the main page first.")
    st.stop()

cache  = st.session_state.data_cache
data   = cache.get_all_data()

symbol = st.selectbox("Select symbol", list(data["metrics"].keys()))
if symbol:
    m = data["metrics"][symbol]
    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Correlation", f"{m['corr']:.3f}"  if pd.notna(m.get("corr"))    else "N/A")
    col2.metric("Setup Quality",      f"{m['quality']:.0f}/100" if pd.notna(m.get("quality")) else "N/A")
    col3.metric("Spread Z",           f"{m['spread_z']:.2f}"    if pd.notna(m.get("spread_z")) else "N/A")

    if "corr_series" in m and m["corr_series"] is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=m["corr_series"], name="Rolling Correlation",
                                 line=dict(color="#42a5f5")))
        fig.update_layout(title=f"Rolling Correlation — {symbol} vs {st.session_state.base_symbol}",
                          xaxis_title="Bar", yaxis_title="Correlation",
                          yaxis=dict(range=[-1, 1]))
        st.plotly_chart(fig, use_container_width=True)

    if "spread_series" in m and m["spread_series"] is not None:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=m["spread_series"], name="Spread Z-score",
                                  line=dict(color="#ffa726")))
        fig2.add_hline(y=2,  line_dash="dot", line_color="red",   annotation_text="+2σ")
        fig2.add_hline(y=-2, line_dash="dot", line_color="green", annotation_text="-2σ")
        fig2.update_layout(title=f"Spread Z-score — {symbol}", xaxis_title="Bar")
        st.plotly_chart(fig2, use_container_width=True)

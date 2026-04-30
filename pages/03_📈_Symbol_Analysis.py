import streamlit as st
import plotly.graph_objects as go

st.title("📈 Symbol Deep Dive")
cache = st.session_state.data_cache
data = cache.get_all_data()

symbol = st.selectbox("Select symbol", list(data['metrics'].keys()))
if symbol:
    m = data['metrics'][symbol]
    st.metric("Latest Correlation", f"{m['corr']:.3f}" if pd.notna(m.get('corr')) else "N/A")
    st.metric("Setup Quality", f"{m['quality']:.0f}/100" if pd.notna(m.get('quality')) else "N/A")
    st.metric("Spread Z", f"{m.get('spread_z', 'N/A')}")
    if 'corr_series' in m:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=m['corr_series'], name='Correlation'))
        st.plotly_chart(fig, use_container_width=True)

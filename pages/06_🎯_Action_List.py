import streamlit as st
import pandas as pd

st.title("🎯 Action List – Top 5 Trades")
data = st.session_state.data_cache.get_all_data()
actions = data['actions']

if actions:
    df = pd.DataFrame(actions)
    st.dataframe(df, use_container_width=True)
else:
    st.write("No strong signals at the moment.")

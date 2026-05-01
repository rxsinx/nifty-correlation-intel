import streamlit as st
import pandas as pd

# Bug fix: missing set_page_config
st.set_page_config(page_title="Action List", layout="wide")
st.title("🎯 Action List – Top 5 Trades")

if st.session_state.get("data_cache") is None:
    st.warning("Data not loaded. Return to the main page first.")
    st.stop()

data    = st.session_state.data_cache.get_all_data()
actions = data["actions"]

if actions:
    df = pd.DataFrame(actions)
    # Reorder columns for readability
    col_order = ["type", "target", "direction", "score", "size_unit", "why"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, use_container_width=True)
else:
    st.info("No high-conviction signals at the moment.")

st.markdown("---")
playbook = data.get("playbook", "")
if playbook:
    st.subheader("📋 Playbook")
    st.text(playbook)

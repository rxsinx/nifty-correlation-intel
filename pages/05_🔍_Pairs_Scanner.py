import streamlit as st
import pandas as pd

# Bug fix: missing set_page_config
st.set_page_config(page_title="Pairs Scanner", layout="wide")
st.title("🔍 Pairs Scanner")

if st.session_state.get("data_cache") is None:
    st.warning("Data not loaded. Return to the main page first.")
    st.stop()

data  = st.session_state.data_cache.get_all_data()
pairs = data["pairs"]

rows = []
for (a, b), pinfo in pairs.items():
    half_life = pinfo["half_life"]
    rows.append({
        "Pair":             f"{a} / {b}",
        "Corr":             round(pinfo["corr"], 3) if pd.notna(pinfo["corr"]) else None,
        "Cointegrated":     "✅" if pinfo["cointegrated"] else "❌",
        # Bug fix: previous code did f"{half_life:.0f}" without checking for None → TypeError
        "Half-Life (bars)": f"{half_life:.0f}" if half_life is not None and pd.notna(half_life) else "—",
    })

df = pd.DataFrame(rows).sort_values("Corr", ascending=False)
st.dataframe(df, use_container_width=True)

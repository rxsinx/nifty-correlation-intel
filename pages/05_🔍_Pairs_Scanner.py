import streamlit as st
import pandas as pd

st.title("🔍 Pairs Scanner")
data = st.session_state.data_cache.get_all_data()
pairs = data['pairs']

rows = []
for (a,b), pinfo in pairs.items():
    rows.append({
        "Pair": f"{a} / {b}",
        "Corr": pinfo["corr"],
        "Cointegrated": "✅" if pinfo["cointegrated"] else "❌",
        "Half-Life (bars)": f"{pinfo['half_life']:.0f}" if pinfo["half_life"] else "-"
    })
df = pd.DataFrame(rows).sort_values("Corr", ascending=False)
st.dataframe(df, use_container_width=True)

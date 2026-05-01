import streamlit as st
import pandas as pd
from utils.constants import REGIME_COLORS

# Bug fix: missing set_page_config
st.set_page_config(page_title="Market Brain", layout="wide")
st.title("🧠 Market Brain – Live Clustering")

if st.session_state.get("data_cache") is None:
    st.warning("Data not loaded. Return to the main page first.")
    st.stop()

data     = st.session_state.data_cache.get_all_data()
clusters = data["clusters"]

symbol_list = [st.session_state.base_symbol] + st.session_state.symbols
rows = []
for sym in symbol_list:
    cid = clusters.get(sym, -2)   # -2 = no data
    rows.append({"Symbol": sym, "Cluster": cid})

df = pd.DataFrame(rows)

CLUSTER_COLORS = {
    -2: "background-color: grey",
    -1: "background-color: lightgrey",
     0: "background-color: #42a5f5",
     1: "background-color: #ffa726",
     2: "background-color: #ab47bc",
     3: "background-color: #26c6da",
     4: "background-color: #ec407a",
     5: "background-color: #66bb6a",
}

def color_cluster(val):
    return CLUSTER_COLORS.get(val, "")

# Bug fix: .applymap() was deprecated in pandas 2.1 → use .map()
st.dataframe(
    df.style.map(color_cluster, subset=["Cluster"]),
    use_container_width=True,
)

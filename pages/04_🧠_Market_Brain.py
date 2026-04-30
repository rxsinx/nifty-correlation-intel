import streamlit as st
import pandas as pd
from utils.constants import REGIME_COLORS

st.title("🧠 Market Brain – Live Clustering")
data = st.session_state.data_cache.get_all_data()
clusters = data['clusters']

# Create a DataFrame for display
symbol_list = [st.session_state.base_symbol] + st.session_state.symbols
rows = []
for sym in symbol_list:
    if sym in clusters:
        cid = clusters[sym]
    else:
        cid = -2  # no data
    rows.append({"Symbol": sym, "Cluster": cid})

df = pd.DataFrame(rows)
# Colorize
def color_cluster(val):
    colors = {-2: 'grey', -1: 'lightgrey', 0: '#42a5f5', 1: '#ffa726', 2: '#ab47bc', 3: '#26c6da', 4: '#ec407a', 5: '#66bb6a'}
    return f'background-color: {colors.get(val, "white")}'

st.dataframe(df.style.applymap(color_cluster, subset=["Cluster"]), use_container_width=True)

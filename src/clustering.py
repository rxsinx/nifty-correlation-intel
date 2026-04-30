import networkx as nx

def cluster_symbols(pair_corrs, threshold):
    """
    pair_corrs: dict {(sym_a, sym_b): corr_value or pd.Series} (we take the last value)
    Returns a dict mapping symbol -> cluster label (int)
    """
    G = nx.Graph()
    for (s1, s2), corr_val in pair_corrs.items():
        # Ensure we have a scalar
        if hasattr(corr_val, 'iloc'):
            corr_val = corr_val.iloc[-1] if len(corr_val) > 0 else None
        if pd.notna(corr_val) and corr_val > threshold:
            G.add_edge(s1, s2, weight=corr_val)

    clusters = {}
    for i, comp in enumerate(nx.connected_components(G)):
        for node in comp:
            clusters[node] = i
    # Solo nodes not in any edge
    all_nodes_set = set()
    for pair in pair_corrs.keys():
        all_nodes_set.update(pair)
    for node in all_nodes_set:
        if node not in clusters:
            clusters[node] = -1  # solo
    return clusters

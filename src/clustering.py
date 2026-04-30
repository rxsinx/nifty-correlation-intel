import networkx as nx

def cluster_symbols(correlation_matrix, threshold):
    """
    Build graph where edge exists if corr > threshold.
    Positive correlations only, as per Pine logic.
    """
    G = nx.Graph()
    symbols = correlation_matrix.columns
    for i, s1 in enumerate(symbols):
        for j, s2 in enumerate(symbols):
            if i < j:
                val = correlation_matrix.loc[s1, s2]
                if pd.notna(val) and val > threshold:
                    G.add_edge(s1, s2, weight=val)
    # Find connected components = clusters
    clusters = {}
    for comp in nx.connected_components(G):
        for node in comp:
            clusters[node] = comp
    # Assign cluster IDs
    return clusters

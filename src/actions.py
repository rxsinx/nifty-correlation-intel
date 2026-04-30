def rank_actions(metrics_dict, pairs_data, base_symbol, min_r2, min_stab, pairs_z_threshold):
    """Return a list of dicts with action candidates ranked by quality."""
    actions = []
    # 1. TRACK / HEDGE from symbol metrics
    for sym, m in metrics_dict.items():
        if "quality" not in m or pd.isna(m["quality"]):
            continue
        quality = m["quality"]
        corr = m.get("corr")
        r2 = m.get("r2")
        stab = m.get("stab")
        if quality < 30:  # arbitrary minimum
            continue
        if corr > 0.4:
            actions.append({
                "type": "TRACK",
                "target": sym,
                "score": quality,
                "direction": f"LONG {sym} with base",
                "size_unit": "100%",
                "why": f"Corr {corr:.2f}, R² {r2:.0%}, Stab {stab:.0f}"
            })
        elif corr < -0.4:
            actions.append({
                "type": "HEDGE",
                "target": sym,
                "score": quality,
                "direction": f"SHORT {sym} against base",
                "size_unit": f"|β| = {abs(m.get('beta',0)):.2f}",
                "why": f"Inverse corr {corr:.2f}, R² {r2:.0%}"
            })

    # 2. Pairs trades
    for (a, b), pinfo in pairs_data.items():
        corr_val = pinfo["corr"]
        if pd.isna(corr_val) or abs(corr_val) < 0.4:
            continue
        # spread Z is not in pairs_data yet, but could be computed; skip for now.
        # For full system, compute spread Z and combine with stability.
        # placeholder:
        spread_z = 1.5  # dummy
        half_life = pinfo["half_life"]
        coint = pinfo["cointegrated"]
        score = (pinfo.get("stab", 50) * abs(spread_z)) if abs(spread_z) > 0 else 0
        if score > 0 and abs(spread_z) > pairs_z_threshold:
            direction = f"{'LONG' if spread_z>0 else 'SHORT'} {a} / {'SHORT' if spread_z>0 else 'LONG'} {b}"
            actions.append({
                "type": "PAIRS" if not coint else "PAIRS✓",
                "target": f"{a}/{b}",
                "score": score,
                "direction": direction,
                "size_unit": "100% each leg",
                "why": f"Corr {corr_val:.2f}, Spread Z {spread_z:.2f}" + (f", HL {half_life:.0f}b" if half_life else "")
            })

    # Sort by score descending
    actions.sort(key=lambda x: x["score"], reverse=True)
    return actions[:5]

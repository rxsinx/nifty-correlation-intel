import numpy as np
import pandas as pd

def compute_regime(avg_abs_corr, dispersion, active_count):
    if active_count < 3:
        return "INSUFFICIENT"
    if avg_abs_corr > 0.75 and dispersion < 0.15:
        return "CRISIS"
    elif avg_abs_corr > 0.55:
        return "COUPLED"
    elif avg_abs_corr < 0.25 or dispersion > 0.45:
        return "DECOUPLED"
    else:
        return "MIXED"

def crisis_clock(avg_abs, dispersion, pair_corrs, stressed=60, critical=80):
    # component A (coupling, max 40)
    comp_a = min(40, avg_abs * 50) if pd.notna(avg_abs) else 0
    # component B (dispersion collapse, max 30)
    comp_b = max(0, 1 - dispersion*2) * 30 if pd.notna(dispersion) else 0
    # component C (tail dependence: fraction of pairs with |corr|>0.7, max 30)
    if len(pair_corrs) > 0:
        tail_count = np.sum(np.abs(pair_corrs) > 0.7)
        comp_c = (tail_count / len(pair_corrs)) * 30
    else:
        comp_c = 0
    return comp_a + comp_b + comp_c

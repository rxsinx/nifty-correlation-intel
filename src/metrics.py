import numpy as np
import pandas as pd
from scipy.stats import linregress

def rolling_correlation(series1, series2, window):
    return series1.rolling(window).corr(series2)

def beta(log_ret_base, log_ret_sym, window):
    cov = log_ret_base.rolling(window).cov(log_ret_sym)
    var = log_ret_base.rolling(window).var()
    return (cov / var).where(var > 0)

def stability(corr_series, hist_window):
    std_corr = corr_series.rolling(hist_window).std()
    return (1 - 2 * std_corr).clip(0, 1) * 100  # 0-100

def spread_z(base_price, sym_price, window):
    ratio = base_price / sym_price
    ma = ratio.rolling(window).mean()
    std = ratio.rolling(window).std()
    return (ratio - ma) / std

def asym_corr(base_ret, sym_ret, atr_base, hist_len):
    med_atr = atr_base.rolling(hist_len).median()
    stress_mask = atr_base > med_atr
    normal_mask = ~stress_mask

    # Compute conditional correlations using masked arrays
    def cond_corr(mask):
        if mask.sum() < 10:
            return pd.Series(np.nan, index=base_ret.index)
        b = base_ret[mask]
        s = sym_ret[mask]
        # Use a rolling window, but because mask changes each bar, we do a simple correlation for the whole window?
        # For simplicity, we'll compute the correlation over the full hist_len window available, as a single number.
        # In production, you'd do a truly rolling conditional correlation; here we output the same value for all bars.
        # We'll return a scalar for the latest bar.
        latest_idx = base_ret.index[-1]
        start_idx = latest_idx - pd.DateOffset(days=hist_len)
        mask_window = mask.loc[start_idx:latest_idx]
        b_win = b.loc[start_idx:latest_idx]
        s_win = s.loc[start_idx:latest_idx]
        if mask_window.sum() < 10 or b_win.std() == 0 or s_win.std() == 0:
            return np.nan
        return b_win.corr(s_win)

    normal_corr = cond_corr(normal_mask)
    stress_corr = cond_corr(stress_mask)
    delta = stress_corr - normal_corr if (pd.notna(normal_corr) and pd.notna(stress_corr)) else None
    # Return as Series (just for the last bar, but we can store as scalar)
    return pd.Series([normal_corr]), pd.Series([stress_corr]), pd.Series([delta])

def setup_quality(corr, r2, stab, z_score, clock_stressed, clock_critical):
    quality = abs(corr) * r2 * stab * 100
    # Penalties (simplified)
    if pd.notna(z_score.iloc[-1]) and abs(z_score.iloc[-1]) > 2.0:
        quality *= 0.5
    return quality

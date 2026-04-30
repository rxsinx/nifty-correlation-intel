import numpy as np
import pandas as pd
from scipy.stats import linregress, percentileofscore

def rolling_correlation(series1, series2, window):
    return series1.rolling(window).corr(series2)

def beta(close_base, close_sym, window):
    ret_base = np.log(close_base / close_base.shift(1))
    ret_sym  = np.log(close_sym / close_sym.shift(1))
    cov = ret_base.rolling(window).cov(ret_sym)
    var = ret_base.rolling(window).var()
    return (cov / var).where(var > 0)

def stability(corr_series, hist_window):
    std_corr = corr_series.rolling(hist_window).std()
    return np.clip(1 - 2 * std_corr, 0, 1) * 100  # 0-100 scale

def spread_z(prices_base, prices_sym, window):
    ratio = prices_base / prices_sym
    ma = ratio.rolling(window).mean()
    std = ratio.rolling(window).std()
    return (ratio - ma) / std

# Asymmetric correlation (stress vs normal) using ATR-based regime mask
def asym_corr(base_ret, sym_ret, atr_base, hist_len):
    med_atr = atr_base.rolling(hist_len).median()
    stress_mask = (atr_base > med_atr).astype(float)
    normal_mask = 1 - stress_mask
    # Conditional correlation – simplified using weighted corr
    # Implement proper conditional corr via function...

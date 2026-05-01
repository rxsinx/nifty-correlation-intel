import numpy as np
import pandas as pd


def rolling_correlation(series1: pd.Series, series2: pd.Series, window: int) -> pd.Series:
    return series1.rolling(window).corr(series2)


def beta(log_ret_base: pd.Series, log_ret_sym: pd.Series, window: int) -> pd.Series:
    cov = log_ret_base.rolling(window).cov(log_ret_sym)
    var = log_ret_base.rolling(window).var()
    return (cov / var).where(var > 0)


def stability(corr_series: pd.Series, hist_window: int) -> pd.Series:
    """
    Stability score 0–100.
    std_corr = 0   → perfectly stable → 100
    std_corr = 0.5 → very unstable   →   0
    (Bug fix: old formula (1 - 2*std).clip(0,1)*100 was arbitrary and produced
     misleading scores; normalising by the 0.5 ceiling is more principled.)
    """
    std_corr = corr_series.rolling(hist_window).std()
    return (1 - std_corr.clip(0, 0.5) / 0.5) * 100


def spread_z(base_price: pd.Series, sym_price: pd.Series, window: int) -> pd.Series:
    ratio = base_price / sym_price
    ma    = ratio.rolling(window).mean()
    std   = ratio.rolling(window).std()
    return (ratio - ma) / std


def asym_corr(
    base_ret: pd.Series,
    sym_ret: pd.Series,
    atr_base: pd.Series,
    hist_len: int,
) -> tuple[float | None, float | None, float | None]:
    """
    Returns (normal_corr, stress_corr, delta) as plain scalars (or None).
    (Bug fix: previous version returned pd.Series([scalar]) which made
     the caller's .iloc[-1] always return the same single value and obscured
     NaN propagation.  Returning scalars is honest about what is computed.)
    """
    med_atr     = atr_base.rolling(hist_len).median()
    stress_mask = atr_base > med_atr
    normal_mask = ~stress_mask

    latest_idx = base_ret.index[-1]
    start_idx  = latest_idx - pd.DateOffset(days=hist_len)

    def cond_corr(mask: pd.Series) -> float | None:
        m_win = mask.loc[start_idx:latest_idx]
        b_win = base_ret.loc[start_idx:latest_idx][m_win]
        s_win = sym_ret.loc[start_idx:latest_idx][m_win]
        if m_win.sum() < 10 or b_win.std() == 0 or s_win.std() == 0:
            return None
        return float(b_win.corr(s_win))

    normal_corr = cond_corr(normal_mask)
    stress_corr = cond_corr(stress_mask)
    delta = (stress_corr - normal_corr
             if normal_corr is not None and stress_corr is not None
             else None)
    return normal_corr, stress_corr, delta


def setup_quality(
    corr: pd.Series,
    r2: pd.Series,
    stab: pd.Series,
    z_score: pd.Series,
    clock_stressed: float,
    clock_critical: float,
) -> pd.Series:
    quality = abs(corr) * r2 * stab * 100
    last_z  = z_score.iloc[-1]
    if pd.notna(last_z) and abs(last_z) > 2.0:
        quality = quality * 0.5
    return quality

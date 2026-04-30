import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint
from statsmodels.api import OLS

def pair_coint_metrics(price_a, price_b, window):
    """Return (is_cointegrated, half_life, latest_correlation) for a pair."""
    log_a = np.log(price_a.dropna())
    log_b = np.log(price_b.dropna())
    # Align lengths
    min_len = min(len(log_a), len(log_b))
    log_a = log_a.iloc[-min_len:]
    log_b = log_b.iloc[-min_len:]

    if len(log_a) < window:
        return False, None, np.nan

    # Cointegration test (p-value < 0.05)
    try:
        _, pvalue, _ = coint(log_a.iloc[-window:], log_b.iloc[-window:])
        is_coint = pvalue < 0.05
    except:
        is_coint = False

    # Half-life via residual AR(1)
    # 1) OLS: log_a = alpha + beta * log_b  on the window
    X = log_b.iloc[-window:].values.reshape(-1, 1)
    y = log_a.iloc[-window:].values
    try:
        model = OLS(y, X)
        res = model.fit()
        beta = res.params[0]
        alpha = res.params[0] if len(res.params) > 1 else 0  # simplified
        spread = log_a.iloc[-window:] - beta * log_b.iloc[-window:]
    except:
        spread = log_a.iloc[-window:] - log_b.iloc[-window:]

    # 2) AR(1) on spread differences
    spread_lag = spread.shift(1).dropna()
    spread_diff = spread.diff().dropna()
    aligned = pd.concat([spread_lag, spread_diff], axis=1).dropna()
    if len(aligned) < 5:
        return is_coint, None, np.nan

    X_ar = aligned.iloc[:, 0].values.reshape(-1, 1)
    y_ar = aligned.iloc[:, 1].values
    try:
        model_ar = OLS(y_ar, X_ar)
        res_ar = model_ar.fit()
        phi = res_ar.params[0]
        half_life = -np.log(2) / np.log(1 + phi) if (1 + phi) > 0 else None
    except:
        half_life = None

    # Latest correlation
    corr = log_a.iloc[-window:].corr(log_b.iloc[-window:])
    return is_coint, half_life, corr

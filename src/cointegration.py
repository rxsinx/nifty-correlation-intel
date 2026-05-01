import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint


def pair_coint_metrics(price_a: pd.Series, price_b: pd.Series, window: int):
    """Return (is_cointegrated, half_life, latest_correlation) for a pair."""
    log_a = np.log(price_a.dropna())
    log_b = np.log(price_b.dropna())

    # Align lengths
    min_len = min(len(log_a), len(log_b))
    log_a = log_a.iloc[-min_len:]
    log_b = log_b.iloc[-min_len:]

    if len(log_a) < window:
        return False, None, np.nan

    # ── Cointegration test (Engle-Granger, p < 0.05) ─────────────────────────
    try:
        _, pvalue, _ = coint(log_a.iloc[-window:], log_b.iloc[-window:])
        is_coint = bool(pvalue < 0.05)
    except Exception:
        is_coint = False

    # ── OLS regression with constant: log_a = alpha + beta * log_b ───────────
    # (Bug fix: previous code used OLS(y, X) with no constant → biased beta,
    #  and then read res.params[0] for BOTH alpha and beta → alpha == beta.)
    X_raw = log_b.iloc[-window:].values
    y     = log_a.iloc[-window:].values
    try:
        X       = sm.add_constant(X_raw)        # shape (window, 2): [1, log_b]
        res     = sm.OLS(y, X).fit()
        alpha, beta_coef = float(res.params[0]), float(res.params[1])
        spread  = log_a.iloc[-window:] - beta_coef * log_b.iloc[-window:] - alpha
    except Exception:
        # Fallback: simple difference spread (no regression)
        spread = log_a.iloc[-window:] - log_b.iloc[-window:]

    # ── AR(1) on spread → half-life ───────────────────────────────────────────
    spread_lag  = spread.shift(1).dropna()
    spread_diff = spread.diff().dropna()
    aligned     = pd.concat([spread_lag, spread_diff], axis=1).dropna()

    half_life = None
    if len(aligned) >= 5:
        X_ar = sm.add_constant(aligned.iloc[:, 0].values)
        y_ar = aligned.iloc[:, 1].values
        try:
            res_ar = sm.OLS(y_ar, X_ar).fit()
            # params[0] = intercept, params[1] = AR(1) coefficient (phi)
            phi = float(res_ar.params[1])
            if (1 + phi) > 0:
                half_life = float(-np.log(2) / np.log(1 + phi))
        except Exception:
            pass

    # ── Latest rolling correlation ────────────────────────────────────────────
    corr = float(log_a.iloc[-window:].corr(log_b.iloc[-window:]))
    return is_coint, half_life, corr

from statsmodels.tsa.stattools import coint, adfuller
import numpy as np

def test_cointegration(price_a, price_b, window):
    # Use log prices
    log_a = np.log(price_a)
    log_b = np.log(price_b)
    # Rolling cointegration? Typically done on a fixed window.
    # Here we test each new bar with the last 'window' observations.
    # Simplified: return whether p-value < 0.05
    _, pvalue, _ = coint(log_a[-window:], log_b[-window:])
    return pvalue < 0.05

def half_life(spread):
    """Return half-life in bars from AR(1) coefficient"""
    spread_lag = spread.shift(1)
    spread_diff = spread - spread_lag
    spread_lag = spread_lag[1:]
    spread_diff = spread_diff[1:]
    # OLS: spread_diff = alpha + phi * spread_lag
    from statsmodels.api import OLS
    model = OLS(spread_diff, spread_lag)
    res = model.fit()
    phi = res.params[0]
    if phi < -0.01:
        return -np.log(2) / np.log(1 + phi)
    return None

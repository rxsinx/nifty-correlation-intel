import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from src.kite_client import KiteWrapper
from src.metrics import (rolling_correlation, beta, stability, spread_z,
                         asym_corr, setup_quality)
from src.cointegration import pair_coint_metrics
from src.clustering import cluster_symbols
from src.regime import compute_regime, crisis_clock
from src.actions import rank_actions
from src.playbook import generate_playbook
import config

logger = logging.getLogger(__name__)

class DataCache:
    """Handles all data fetching and metric computation with caching."""
    def __init__(self, kite: KiteWrapper, symbols=None, base=None,
                 logger=None):
        self.kite = kite
        self.symbols = symbols or config.DEFAULT_SYMBOLS
        self.base = base or config.BASE_SYMBOL
        self.last_refresh = None
        # We'll use Streamlit's caching via a separate function, but keep a
        # simple attribute for non‑Streamlit environments if needed.
        self._cached_data = None

    def invalidate(self):
        self._cached_data = None

    def get_all_data(self, force_refresh=False):
        """
        Main entry point: returns a dictionary with all computed series & values.
        In a real Streamlit app, you'd decorate this with @st.cache_data,
        but for flexibility we keep it as a class method.
        """
        if self._cached_data is not None and not force_refresh:
            return self._cached_data

        # Fetch historical OHLC for all symbols
        end = datetime.today().strftime("%Y-%m-%d")
        start = (datetime.today() - timedelta(days=500)).strftime("%Y-%m-%d")

        prices = {}
        # Base
        prices[self.base] = self.kite.fetch_historical(self.base, start, end)["close"]
        # Set timezone naive for consistency
        prices[self.base].index = prices[self.base].index.tz_localize(None)

        for sym in self.symbols:
            try:
                prices[sym] = self.kite.fetch_historical(sym, start, end)["close"]
                prices[sym].index = prices[sym].index.tz_localize(None)
            except Exception as e:
                logger.warning(f"Could not fetch {sym}: {e}")
                prices[sym] = pd.Series(dtype=float)

        # Align all series to a common date index
        all_dates = prices[self.base].index
        dfs = {sym: prices[sym].reindex(all_dates) for sym in list(prices.keys())}
        df_prices = pd.DataFrame(dfs)

        # Compute returns
        log_returns = np.log(df_prices / df_prices.shift(1))

        # Compute ATR (simple 20‑bar range) for base
        base_ohlc = self.kite.fetch_historical(self.base, start, end, interval="day")
        base_ohlc.index = base_ohlc.index.tz_localize(None)
        base_ohlc["tr"] = np.maximum(
            base_ohlc["high"] - base_ohlc["low"],
            np.abs(base_ohlc["high"] - base_ohlc["close"].shift(1)),
            np.abs(base_ohlc["low"] - base_ohlc["close"].shift(1))
        )
        atr_base = base_ohlc["tr"].rolling(20).mean().reindex(all_dates)
        atr_base.ffill(inplace=True)

        # Compute metrics per symbol
        metrics_dict = {}
        base_close = df_prices[self.base]
        for sym in self.symbols:
            if sym not in df_prices.columns or df_prices[sym].isna().all():
                metrics_dict[sym] = {}
                continue
            sym_close = df_prices[sym]

            corr_series = rolling_correlation(base_close, sym_close, config.CORR_LEN)
            beta_series = beta(log_returns[self.base], log_returns[sym], config.CORR_LEN)
            r2_series = corr_series ** 2
            stab_series = stability(corr_series, config.HIST_LEN)   # 0‑100
            spz_series = spread_z(base_close, sym_close, config.CORR_LEN)
            z_series = (corr_series - corr_series.rolling(config.HIST_LEN).mean()) / corr_series.rolling(config.HIST_LEN).std()

            asym_normal, asym_stress, asym_delta = asym_corr(
                log_returns[self.base], log_returns[sym], atr_base, config.HIST_LEN
            )

            quality = setup_quality(corr_series, r2_series, stab_series, z_series,
                                    config.CLOCK_STRESSED, config.CLOCK_CRITICAL)

            metrics_dict[sym] = {
                "corr": corr_series.iloc[-1],
                "beta": beta_series.iloc[-1],
                "r2": r2_series.iloc[-1],
                "stab": stab_series.iloc[-1],
                "spread_z": spz_series.iloc[-1],
                "z_score": z_series.iloc[-1],
                "quality": quality.iloc[-1],
                "asym_normal": asym_normal.iloc[-1] if asym_normal is not None else None,
                "asym_stress": asym_stress.iloc[-1] if asym_stress is not None else None,
                "asym_delta": asym_delta.iloc[-1] if asym_delta is not None else None,
                # Store full series for plots if needed
                "corr_series": corr_series,
                "spread_series": spz_series,
            }

        # Correlation matrix (all pairs including base)
        symbol_list = [self.base] + self.symbols
        # Remove symbols with no data
        available_symbols = [s for s in symbol_list if s in df_prices.columns and not df_prices[s].isna().all()]
        corr_matrix = df_prices[available_symbols].corr()

        # Clustering (using only the last value of pairwise correlations)
        # Build a matrix from the latest available correlations
        latest_corr = {}
        for s1 in available_symbols:
            for s2 in available_symbols:
                if s1 == s2:
                    continue
                # Use the rolling correlation for the pair, or from the static corr matrix
                latest_corr[(s1, s2)] = corr_matrix.loc[s1, s2]
        cluster_info = cluster_symbols(latest_corr, config.CLUSTER_THR)

        # Cointegration for all unique pairs (base vs each symbol, plus symbol-symbol)
        pairs_data = {}
        all_pairs = [(self.base, sym) for sym in self.symbols if sym in df_prices.columns]
        # Add symbol pairs (just a few for demonstration)
        syms_avail = [s for s in self.symbols if s in df_prices.columns]
        for i in range(len(syms_avail)):
            for j in range(i+1, len(syms_avail)):
                all_pairs.append((syms_avail[i], syms_avail[j]))
        for (a, b) in all_pairs:
            close_a = df_prices[a]
            close_b = df_prices[b]
            is_coint, half_life, corr_val = pair_coint_metrics(close_a, close_b, config.CORR_LEN)
            pairs_data[(a, b)] = {"cointegrated": is_coint,
                                  "half_life": half_life,
                                  "corr": corr_val}

        # Regime & Crisis Clock
        avg_abs_corr = np.mean([abs(metrics_dict[s]["corr"]) for s in metrics_dict if "corr" in metrics_dict[s] and not pd.isna(metrics_dict[s]["corr"])])
        dispersion = np.std([metrics_dict[s]["corr"] for s in metrics_dict if "corr" in metrics_dict[s] and not pd.isna(metrics_dict[s]["corr"])])
        regime_label = compute_regime(avg_abs_corr, dispersion, len(metrics_dict))
        all_pair_corrs = [v["corr"] for v in pairs_data.values()]
        clock = crisis_clock(avg_abs_corr, dispersion, all_pair_corrs, config.CLOCK_STRESSED, config.CLOCK_CRITICAL)

        # Action list (simplified)
        actions = rank_actions(metrics_dict, pairs_data, self.base, config.MIN_R2, config.MIN_STAB, config.PAIRS_Z)

        # Playbook
        playbook_text = generate_playbook(regime_label, clock, actions, self.base)

        result = {
            "prices": df_prices,
            "metrics": metrics_dict,
            "corr_matrix": corr_matrix,
            "clusters": cluster_info,
            "pairs": pairs_data,
            "regime": {"regime_label": regime_label, "crisis_clock": clock, "avg_abs_corr": avg_abs_corr, "dispersion": dispersion},
            "actions": actions,
            "playbook": playbook_text,
            "last_refresh": datetime.now(),
        }
        self._cached_data = result
        self.last_refresh = datetime.now()
        return result

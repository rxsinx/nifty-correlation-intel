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
    """Handles all data fetching and metric computation with simple attribute caching."""

    def __init__(self, kite: KiteWrapper, symbols=None, base=None, logger=None):
        self.kite    = kite
        self.symbols = symbols or config.DEFAULT_SYMBOLS
        self.base    = base    or config.BASE_SYMBOL
        # Use the passed logger if provided, else fall back to module-level logger.
        # (Bug fix: previously stored self.logger but used the module-level `logger`
        #  variable throughout, so a custom logger was silently ignored.)
        self._log        = logger if logger is not None else globals()["logger"]
        self.last_refresh: datetime | None = None
        self._cached_data = None

    def invalidate(self):
        self._cached_data = None

    def get_all_data(self, force_refresh: bool = False) -> dict | None:
        if self._cached_data is not None and not force_refresh:
            return self._cached_data

        end   = datetime.today().strftime("%Y-%m-%d")
        start = (datetime.today() - timedelta(days=500)).strftime("%Y-%m-%d")

        prices: dict[str, pd.Series] = {}

        # ── Fetch base OHLC once; reuse for both close prices AND ATR ────────
        # (Bug fix: previous code commented out the base fetch, leaving
        #  prices[self.base] unset, then later called .index on it → KeyError.
        #  Also had a stray closing paren after the np.maximum block → SyntaxError.)
        base_ohlc = self.kite.fetch_historical(self.base, start, end)
        base_ohlc.index = base_ohlc.index.tz_localize(None)
        prices[self.base] = base_ohlc["close"]

        # ── Fetch comparison symbols ──────────────────────────────────────────
        for sym in self.symbols:
            try:
                df = self.kite.fetch_historical(sym, start, end)
                df.index = df.index.tz_localize(None)
                prices[sym] = df["close"]
            except Exception as e:
                self._log.warning(f"Could not fetch {sym}: {e}")
                prices[sym] = pd.Series(dtype=float)

        # ── Align to common date index ────────────────────────────────────────
        all_dates  = prices[self.base].index
        dfs        = {sym: prices[sym].reindex(all_dates) for sym in prices}
        df_prices  = pd.DataFrame(dfs)
        log_returns= np.log(df_prices / df_prices.shift(1))

        # ── ATR for base (True Range, 20-bar) ─────────────────────────────────
        # (Bug fix: np.maximum only accepts 2 args; nested calls required.)
        hl = base_ohlc["high"] - base_ohlc["low"]
        hc = np.abs(base_ohlc["high"] - base_ohlc["close"].shift(1))
        lc = np.abs(base_ohlc["low"]  - base_ohlc["close"].shift(1))
        base_ohlc["tr"] = np.maximum(hl, np.maximum(hc, lc))
        # (Bug fix: .ffill(inplace=True) is a no-op on derived objects in pandas 2+)
        atr_base = base_ohlc["tr"].rolling(20).mean().reindex(all_dates).ffill()

        # ── Per-symbol metrics ────────────────────────────────────────────────
        metrics_dict: dict = {}
        base_close = df_prices[self.base]

        for sym in self.symbols:
            if sym not in df_prices.columns or df_prices[sym].isna().all():
                metrics_dict[sym] = {}
                continue

            sym_close   = df_prices[sym]
            corr_series = rolling_correlation(base_close, sym_close, config.CORR_LEN)
            beta_series = beta(log_returns[self.base], log_returns[sym], config.CORR_LEN)
            r2_series   = corr_series ** 2
            stab_series = stability(corr_series, config.HIST_LEN)
            spz_series  = spread_z(base_close, sym_close, config.CORR_LEN)
            z_series    = (
                (corr_series - corr_series.rolling(config.HIST_LEN).mean())
                / corr_series.rolling(config.HIST_LEN).std()
            )

            asym_normal, asym_stress, asym_delta = asym_corr(
                log_returns[self.base], log_returns[sym], atr_base, config.HIST_LEN
            )

            quality = setup_quality(corr_series, r2_series, stab_series, z_series,
                                    config.CLOCK_STRESSED, config.CLOCK_CRITICAL)

            metrics_dict[sym] = {
                "corr":        corr_series.iloc[-1],
                "beta":        beta_series.iloc[-1],
                "r2":          r2_series.iloc[-1],
                "stab":        stab_series.iloc[-1],
                "spread_z":    spz_series.iloc[-1],
                "z_score":     z_series.iloc[-1],
                "quality":     quality.iloc[-1],
                # asym_corr now returns scalars directly (see metrics.py fix)
                "asym_normal": asym_normal,
                "asym_stress": asym_stress,
                "asym_delta":  asym_delta,
                "corr_series": corr_series,
                "spread_series": spz_series,
            }

        # ── Correlation matrix ────────────────────────────────────────────────
        symbol_list       = [self.base] + self.symbols
        available_symbols = [s for s in symbol_list
                             if s in df_prices.columns and not df_prices[s].isna().all()]
        corr_matrix = df_prices[available_symbols].corr()

        # ── Clustering ────────────────────────────────────────────────────────
        latest_corr = {
            (s1, s2): corr_matrix.loc[s1, s2]
            for s1 in available_symbols
            for s2 in available_symbols
            if s1 != s2
        }
        cluster_info = cluster_symbols(latest_corr, config.CLUSTER_THR)

        # ── Cointegration (all unique pairs) ──────────────────────────────────
        pairs_data: dict = {}
        syms_avail = [s for s in self.symbols if s in df_prices.columns]
        all_pairs  = [(self.base, sym) for sym in syms_avail]
        for i in range(len(syms_avail)):
            for j in range(i + 1, len(syms_avail)):
                all_pairs.append((syms_avail[i], syms_avail[j]))

        for (a, b) in all_pairs:
            is_coint, half_life, corr_val = pair_coint_metrics(
                df_prices[a], df_prices[b], config.CORR_LEN
            )
            pairs_data[(a, b)] = {
                "cointegrated": is_coint,
                "half_life":    half_life,
                "corr":         corr_val,
            }

        # ── Regime & Crisis Clock ─────────────────────────────────────────────
        valid_corrs   = [metrics_dict[s]["corr"] for s in metrics_dict
                         if "corr" in metrics_dict[s] and not pd.isna(metrics_dict[s]["corr"])]
        avg_abs_corr  = float(np.mean([abs(c) for c in valid_corrs])) if valid_corrs else 0.0
        dispersion    = float(np.std(valid_corrs))                     if valid_corrs else 0.0
        regime_label  = compute_regime(avg_abs_corr, dispersion, len(metrics_dict))
        all_pair_corrs= [v["corr"] for v in pairs_data.values() if not pd.isna(v["corr"])]
        clock         = crisis_clock(avg_abs_corr, dispersion, all_pair_corrs,
                                     config.CLOCK_STRESSED, config.CLOCK_CRITICAL)

        # ── Actions & Playbook ────────────────────────────────────────────────
        actions       = rank_actions(metrics_dict, pairs_data, self.base,
                                     config.MIN_R2, config.MIN_STAB, config.PAIRS_Z)
        playbook_text = generate_playbook(regime_label, clock, actions, self.base)

        result = {
            "prices":      df_prices,
            "metrics":     metrics_dict,
            "corr_matrix": corr_matrix,
            "clusters":    cluster_info,
            "pairs":       pairs_data,
            "regime": {
                "regime_label":  regime_label,
                "crisis_clock":  clock,
                "avg_abs_corr":  avg_abs_corr,
                "dispersion":    dispersion,
            },
            "actions":      actions,
            "playbook":     playbook_text,
            "last_refresh": datetime.now(),
        }
        self._cached_data = result
        self.last_refresh = datetime.now()
        return result

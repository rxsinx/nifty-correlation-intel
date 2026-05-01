import pandas as pd
import logging
from kiteconnect import KiteConnect

logger = logging.getLogger(__name__)

class KiteWrapper:
    """Wraps KiteConnect for token lookup and historical data."""

    def __init__(self, api_key: str, access_token: str | None = None):
        self.kite = KiteConnect(api_key=api_key)
        if access_token:
            self.kite.set_access_token(access_token)
        self._instruments_df = None
        self._user_id: str | None = None   # cached after first call
        self._load_instruments()

    # ── Instruments ──────────────────────────────────────────────────────────
    def _load_instruments(self):
        if self._instruments_df is None:
            self._instruments_df = pd.DataFrame(self.kite.instruments())
            logger.info(f"Loaded {len(self._instruments_df)} instruments.")

    def get_token(self, symbol: str, exchange: str = "NSE") -> int:
        df = self._instruments_df
        match = df[(df["tradingsymbol"] == symbol) & (df["exchange"] == exchange)]
        if match.empty:
            raise ValueError(f"Instrument not found: {symbol} on {exchange}")
        return int(match.iloc[0]["instrument_token"])

    # ── Historical data ───────────────────────────────────────────────────────
    def fetch_historical(self, symbol: str, from_date: str, to_date: str,
                         interval: str = "day") -> pd.DataFrame:
        token = self.get_token(symbol)
        data  = self.kite.historical_data(token, from_date, to_date, interval)
        df    = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return df

    # ── User identity (cached — avoids a network call on every sidebar render) ─
    def get_user_id(self) -> str:
        if self._user_id is None:
            self._user_id = self.kite.profile()["user_id"]
        return self._user_id

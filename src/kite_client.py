from kiteconnect import KiteConnect
import pandas as pd
from datetime import datetime, timedelta
import config
import logging

logger = logging.getLogger(__name__)

class KiteWrapper:
    def __init__(self, api_key=config.KITE_API_KEY, access_token=config.KITE_ACCESS_TOKEN):
        self.kite = KiteConnect(api_key=api_key)
        if access_token:
            self.kite.set_access_token(access_token)
        self.instruments = None
        self._load_instruments()

    def _load_instruments(self):
        """Fetch and cache instrument list"""
        if self.instruments is None:
            # In a real app, cache to disk
            self.instruments = pd.DataFrame(self.kite.instruments())
            logger.info(f"Loaded {len(self.instruments)} instruments")

    def get_token(self, symbol: str, exchange: str = "NSE"):
        """Get instrument token by trading symbol"""
        df = self.instruments
        match = df[(df["tradingsymbol"] == symbol) & (df["exchange"] == exchange)]
        if match.empty:
            raise ValueError(f"Instrument {symbol} not found")
        return int(match.iloc[0]["instrument_token"])

    def fetch_ohlc(self, symbol: str, from_date: str, to_date: str, interval: str = "day"):
        """Fetch historical OHLC data"""
        token = self.get_token(symbol)
        data = self.kite.historical_data(token, from_date, to_date, interval)
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return df

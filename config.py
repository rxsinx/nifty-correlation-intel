import os

# Kite Connect credentials – never hardcode; use environment variables
KITE_API_KEY = os.getenv("KITE_API_KEY")
KITE_ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")  # Can be generated via login flow

# Base symbol
BASE_SYMBOL = "NIFTY 50"

# Default comparison symbols (can be changed in settings)
DEFAULT_SYMBOLS = [
    "NIFTY BANK",
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK"
]

# Index instruments mapping (for Kite)
# Will be auto‑resolved using instrument dump, but fallback
INSTRUMENT_MAP = {
    "NIFTY 50": 256265,
    "NIFTY BANK": 260105,
    # ... add as needed
}

# Periods (lookback windows)
CORR_LEN = 50       # Primary medium‑term
SHORT_LEN = 20
LONG_LEN = 200
HIST_LEN = 200      # Historical baseline for Z‑score etc.

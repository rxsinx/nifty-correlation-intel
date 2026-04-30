import os

# ---- Kite Connect credentials (from env vars or Streamlit secrets) ----
KITE_API_KEY = os.getenv("KITE_API_KEY")
KITE_ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")

# ---- Base symbol ----
BASE_SYMBOL = "NIFTY 50"

# ---- Default comparison symbols ----
DEFAULT_SYMBOLS = [
    "NIFTY BANK",
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
]

# ---- Lookback periods ----
CORR_LEN = 50       # primary medium-term correlation window
SHORT_LEN = 20
LONG_LEN = 200
HIST_LEN = 200      # for historical baseline of correlation

# ---- Thresholds (mirrors Pine script) ----
STRONG_THR = 0.70
BREAK_Z = 2.0
PAIRS_Z = 2.0
MIN_R2 = 0.25
MIN_STAB = 0.50
CLUSTER_THR = 0.60
CLOCK_STRESSED = 60
CLOCK_CRITICAL = 80

# ---- Risk budgets (%) ----
RISK_CRISIS = 50
RISK_COUPLED = 75
RISK_MIXED = 90
RISK_DECOUPLED = 100

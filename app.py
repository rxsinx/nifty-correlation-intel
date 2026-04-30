# app.py – Main entry point for NiftyCorrIntel (Streamlit)
import streamlit as st
import os
import logging
from datetime import datetime

# Configure logging to stdout (Streamlit Cloud friendly)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("app")

# ────────────────────────────────────────────────────────────
# Page config must be the first Streamlit command
# ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NiftyCorrIntel",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────────────────────────────────────
# Delay heavy imports until after page config (best practice)
# ────────────────────────────────────────────────────────────
try:
    from src.kite_client import KiteWrapper
    from src.data_fetcher import DataCache
except ImportError as e:
    st.error(f"Missing module: {e}. Please check the 'src/' directory structure.")
    st.stop()

# ────────────────────────────────────────────────────────────
# Session State Initialisation
# ────────────────────────────────────────────────────────────
if "kite_initialised" not in st.session_state:
    st.session_state.kite_initialised = False
if "kite" not in st.session_state:
    st.session_state.kite = None
if "data_cache" not in st.session_state:
    st.session_state.data_cache = None
if "base_symbol" not in st.session_state:
    st.session_state.base_symbol = "NIFTY 50"
if "symbols" not in st.session_state:
    # Default comparison symbols – can be changed in Settings page
    st.session_state.symbols = [
        "NIFTY BANK",
        "RELIANCE",
        "TCS",
        "HDFCBANK",
        "INFY",
        "ICICIBANK",
    ]

# ────────────────────────────────────────────────────────────
# Kite API Setup (using st.secrets or environment variables)
# ────────────────────────────────────────────────────────────
def init_kite():
    """Attempt to initialise KiteWrapper with available credentials."""
    api_key = None
    access_token = None

    # Try Streamlit secrets first (production)
    try:
        api_key = st.secrets["kite"]["api_key"]
        access_token = st.secrets["kite"]["access_token"]
    except (KeyError, FileNotFoundError):
        pass

    # Fallback to environment variables (local dev)
    if not api_key:
        api_key = os.getenv("KITE_API_KEY")
    if not access_token:
        access_token = os.getenv("KITE_ACCESS_TOKEN")

    if not api_key or not access_token:
        return None

    try:
        kite = KiteWrapper(api_key=api_key, access_token=access_token)
        # Quick validation: fetch instruments (cached internally)
        _ = kite.get_token("NIFTY 50")  # will raise if token fails
        return kite
    except Exception as e:
        logger.error(f"Kite initialisation failed: {e}")
        return None

# ────────────────────────────────────────────────────────────
# Main logic (runs on every rerun but uses session state caching)
# ────────────────────────────────────────────────────────────
if not st.session_state.kite_initialised:
    with st.spinner("Connecting to Kite API..."):
        kite = init_kite()
        if kite is None:
            st.error(
                """
                **Kite API credentials not found or invalid.**
                
                Please set your `KITE_API_KEY` and `KITE_ACCESS_TOKEN` either via:
                - Streamlit Cloud secrets (`st.secrets.kite.api_key` / `access_token`)
                - Environment variables
                
                The app cannot load market data without these.
                
                *(Navigate to ⚙️ Settings for more info, or restart after setting credentials.)*
                """
            )
            st.stop()
        else:
            st.session_state.kite = kite
            st.session_state.data_cache = DataCache(kite, logger=logger)
            st.session_state.kite_initialised = True
            logger.info("Kite API initialised successfully.")
            st.rerun()  # Force refresh to show dashboard

# ────────────────────────────────────────────────────────────
# Landing page content (only shown when no specific page selected)
# ────────────────────────────────────────────────────────────
st.title("📈 NiftyCorrIntel")
st.caption("Market Correlation Intelligence — NIFTY 50 Universe")

# Quick refresh button (refreshes data)
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.data_cache.invalidate()
        st.rerun()
with col2:
    last_refresh = getattr(st.session_state.data_cache, 'last_refresh', None)
    refresh_str = last_refresh.strftime("%H:%M:%S") if last_refresh else "Never"
    st.metric("Last Update", refresh_str)
st.markdown("---")

# Show key summary tiles (only if data is available)
try:
    data = st.session_state.data_cache.get_all_data()
    if data is not None:
        regime_info = data.get("regime", {})
        clock = regime_info.get("crisis_clock", 0)
        regime_label = regime_info.get("regime_label", "UNKNOWN")
        
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("Regime", regime_label)
        col_r2.metric("Crisis Clock", f"{clock:.0f}/100")
        col_r3.metric("Active Symbols", f"{len(st.session_state.symbols)}")
        col_r4.metric("Base Symbol", st.session_state.base_symbol)
        
        st.success("System operational. Use the sidebar to explore detailed dashboards.")
    else:
        st.info("Waiting for data... If this persists, check your symbols or connection.")
except Exception as e:
    st.warning(f"Could not load summary data: {e}")

# ────────────────────────────────────────────────────────────
# Additional sidebar info (Streamlit auto‑generates navigation
# for pages in the 'pages/' folder)
# ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🧭 Navigation")
    st.markdown("Use the **pages** listed above to explore:")
    st.markdown("- 📊 Dashboard")
    st.markdown("- 🔢 Correlation Matrix")
    st.markdown("- 📈 Symbol Analysis")
    st.markdown("- 🧠 Market Brain")
    st.markdown("- 🔍 Pairs Scanner")
    st.markdown("- 🎯 Action List")
    st.markdown("- ⚙️ Settings")
    st.divider()
    st.caption(f"Logged in user: {st.session_state.get('kite').kite.user_id if st.session_state.kite else 'N/A'}")
    st.caption("NiftyCorrIntel v1.0 — Built with ❤️ using Streamlit")

# ────────────────────────────────────────────────────────────
# Session‑state cleanup (optional)
# ────────────────────────────────────────────────────────────
# This ensures the auto‑refresh works correctly on all pages

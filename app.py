# app.py – Main entry point for NiftyCorrIntel (Streamlit)
import streamlit as st
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("app")

# ── Page config MUST be the very first Streamlit command ─────────────────────
st.set_page_config(
    page_title="NiftyCorrIntel",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Heavy imports after page config ──────────────────────────────────────────
try:
    from src.kite_client import KiteWrapper
    from src.data_fetcher import DataCache
except ImportError as e:
    st.error(f"Missing module: {e}. Please check the 'src/' directory structure.")
    st.stop()

# ── Session State Initialisation ─────────────────────────────────────────────
defaults = {
    "kite_initialised": False,
    "kite": None,
    "data_cache": None,
    "base_symbol": "NIFTY 50",
    "symbols": ["NIFTY BANK", "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"],
    # Kite login flow state
    "kite_step": "credentials",   # "credentials" | "otp" | "done"
    "kite_api_key": "",
    "kite_api_secret": "",
    "kite_request_token": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helper: init from already-resolved access_token ──────────────────────────
def _build_kite(api_key: str, access_token: str) -> KiteWrapper | None:
    try:
        kite = KiteWrapper(api_key=api_key, access_token=access_token)
        _ = kite.get_token("NIFTY 50")        # quick sanity-check
        return kite
    except Exception as e:
        logger.error(f"KiteWrapper init failed: {e}")
        return None

# ── Try secrets / env first (non-interactive path) ───────────────────────────
def _try_env_credentials() -> KiteWrapper | None:
    try:
        api_key      = st.secrets["kite"]["api_key"]
        access_token = st.secrets["kite"]["access_token"]
    except (KeyError, FileNotFoundError):
        api_key      = os.getenv("KITE_API_KEY", "")
        access_token = os.getenv("KITE_ACCESS_TOKEN", "")
    if api_key and access_token:
        return _build_kite(api_key, access_token)
    return None

# ── Interactive Kite login (3-step: key → login URL → request_token) ─────────
def _show_login_ui():
    st.title("📈 NiftyCorrIntel — Connect to Kite")
    st.caption("Your credentials are used only for this session and never stored.")

    step = st.session_state.kite_step

    # ── Step 1 : Enter API key + secret ──────────────────────────────────────
    if step == "credentials":
        with st.form("kite_creds"):
            st.subheader("Step 1 — API credentials")
            api_key    = st.text_input("API Key",    value=st.session_state.kite_api_key,
                                       placeholder="abcdef1234567890")
            api_secret = st.text_input("API Secret", value=st.session_state.kite_api_secret,
                                       type="password", placeholder="xxxxxxxxxxxxxxxx")
            submitted = st.form_submit_button("Generate login URL →")
        if submitted:
            if not api_key or not api_secret:
                st.error("Both API Key and API Secret are required.")
                return
            st.session_state.kite_api_key    = api_key.strip()
            st.session_state.kite_api_secret = api_secret.strip()
            st.session_state.kite_step       = "otp"
            st.rerun()

    # ── Step 2 : Open login URL, paste back request_token ────────────────────
    elif step == "otp":
        api_key = st.session_state.kite_api_key
        login_url = f"https://kite.zerodha.com/connect/login?api_key={api_key}&v=3"

        st.subheader("Step 2 — Authorise in Zerodha")
        st.markdown(
            f"1. Click → **[Open Kite login]({login_url})** (opens in a new tab).\n"
            "2. Log in with your Zerodha credentials + 2FA.\n"
            "3. After redirect, copy the `request_token` from the URL bar.\n"
            "   It looks like: `https://your-redirect/?request_token=XXXX&action=login&status=success`"
        )

        with st.form("kite_token"):
            request_token = st.text_input("Paste request_token here",
                                          placeholder="abc123xyz...")
            col_back, col_go = st.columns([1, 2])
            with col_back:
                back = st.form_submit_button("← Back")
            with col_go:
                go = st.form_submit_button("Connect →", type="primary")

        if back:
            st.session_state.kite_step = "credentials"
            st.rerun()

        if go:
            if not request_token:
                st.error("Please paste the request_token from the redirect URL.")
                return
            st.session_state.kite_request_token = request_token.strip()
            st.session_state.kite_step          = "exchanging"
            st.rerun()

    # ── Step 3 : Exchange request_token for access_token ─────────────────────
    elif step == "exchanging":
        with st.spinner("Exchanging request_token for access_token…"):
            try:
                from kiteconnect import KiteConnect
                import hashlib

                api_key      = st.session_state.kite_api_key
                api_secret   = st.session_state.kite_api_secret
                request_token= st.session_state.kite_request_token

                kc = KiteConnect(api_key=api_key)
                # Generate the checksum: sha256(api_key + request_token + api_secret)
                raw = api_key + request_token + api_secret
                checksum = hashlib.sha256(raw.encode()).hexdigest()
                session_data = kc.generate_session(request_token, api_secret=api_secret)
                access_token = session_data["access_token"]
                kc.set_access_token(access_token)

                kite = _build_kite(api_key, access_token)
                if kite is None:
                    raise RuntimeError("KiteWrapper validation failed after token exchange.")

                st.session_state.kite            = kite
                st.session_state.data_cache      = DataCache(kite, logger=logger)
                st.session_state.kite_initialised= True
                # Optionally surface the access_token so the user can save it
                st.session_state.kite_step       = "done"
                st.rerun()

            except Exception as e:
                st.error(f"Token exchange failed: {e}")
                st.session_state.kite_step = "otp"   # let user retry
                logger.error(f"Token exchange error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Main boot sequence
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.kite_initialised:
    # Non-interactive path (secrets / env vars already set)
    kite = _try_env_credentials()
    if kite:
        st.session_state.kite            = kite
        st.session_state.data_cache      = DataCache(kite, logger=logger)
        st.session_state.kite_initialised= True
        logger.info("Kite initialised via env/secrets.")
        st.rerun()
    else:
        # Interactive login UI
        _show_login_ui()
        st.stop()

# ── Dashboard landing page (shown once authenticated) ────────────────────────
st.title("📈 NiftyCorrIntel")
st.caption("Market Correlation Intelligence — NIFTY 50 Universe")

col1, col2, _ = st.columns([1, 1, 2])
with col1:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.data_cache.invalidate()
        st.rerun()
with col2:
    last_refresh = getattr(st.session_state.data_cache, "last_refresh", None)
    refresh_str  = last_refresh.strftime("%H:%M:%S") if last_refresh else "Never"
    st.metric("Last Update", refresh_str)

st.markdown("---")

try:
    data = st.session_state.data_cache.get_all_data()
    if data is not None:
        regime_info  = data.get("regime", {})
        clock        = regime_info.get("crisis_clock", 0)
        regime_label = regime_info.get("regime_label", "UNKNOWN")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Regime",        regime_label)
        c2.metric("Crisis Clock",  f"{clock:.0f}/100")
        c3.metric("Active Symbols",f"{len(st.session_state.symbols)}")
        c4.metric("Base Symbol",   st.session_state.base_symbol)
        st.success("System operational. Use the sidebar to explore detailed dashboards.")
    else:
        st.info("Waiting for data… If this persists, check your symbols or connection.")
except Exception as e:
    st.warning(f"Could not load summary data: {e}")

with st.sidebar:
    st.header("🧭 Navigation")
    st.markdown("Use the **pages** listed above to explore:")
    for label in ["📊 Dashboard", "🔢 Correlation Matrix", "📈 Symbol Analysis",
                   "🧠 Market Brain", "🔍 Pairs Scanner", "🎯 Action List", "⚙️ Settings"]:
        st.markdown(f"- {label}")
    st.divider()
    user_display = "N/A"
    if st.session_state.kite:
        try:
            user_display = st.session_state.kite.get_user_id()
        except Exception:
            user_display = "N/A (token expired)"
    st.caption(f"Logged in user: {user_display}")
    st.caption("NiftyCorrIntel v1.0 — Built with ❤️ using Streamlit")

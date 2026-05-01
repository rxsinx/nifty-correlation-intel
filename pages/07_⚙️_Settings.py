import streamlit as st

# Bug fix: missing set_page_config
st.set_page_config(page_title="Settings", layout="wide")
st.title("⚙️ Settings")

if st.session_state.get("data_cache") is None:
    st.warning("Data not loaded. Return to the main page first.")
    st.stop()

st.subheader("Comparison Symbols")
new_symbols = st.text_area(
    "Symbols (comma-separated NSE trading symbols)",
    value=", ".join(st.session_state.symbols),
    help="Use exact NSE tradingsymbols, e.g. RELIANCE, TCS, HDFCBANK",
)

if st.button("Update Symbols", type="primary"):
    parsed = [s.strip() for s in new_symbols.split(",") if s.strip()]
    if not parsed:
        st.error("Please enter at least one symbol.")
    else:
        st.session_state.symbols = parsed
        st.session_state.data_cache.invalidate()
        st.success(f"Updated to {len(parsed)} symbols. Cache cleared — data will reload on next page visit.")

st.divider()
st.subheader("Session Info")
kite = st.session_state.get("kite")
if kite:
    try:
        st.info(f"Connected as: **{kite.get_user_id()}**")
    except Exception:
        st.warning("Could not fetch user profile — token may have expired.")

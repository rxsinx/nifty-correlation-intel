import streamlit as st

st.title("⚙️ Settings")
new_symbols = st.text_area("Comparison symbols (comma separated)",
                           ", ".join(st.session_state.symbols))
if st.button("Update Symbols"):
    st.session_state.symbols = [s.strip() for s in new_symbols.split(",") if s.strip()]
    # Invalidate cache to refetch with new symbols
    st.session_state.data_cache.invalidate()
    st.success("Symbols updated. Cache cleared.")

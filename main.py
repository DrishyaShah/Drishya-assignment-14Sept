import streamlit as st
from apps import streamlit_agent, streamlit_dashboard

st.set_page_config(page_title="Atlan AI Suite", layout="wide")

st.sidebar.title("Navigate")
page = st.sidebar.radio("Go to:", ["Support Agent", "Dashboard"])

if page == "Support Agent":
    streamlit_agent.app()
elif page == "Dashboard":
    streamlit_dashboard.app()

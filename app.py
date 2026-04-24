import streamlit as st

st.set_page_config(
    page_title="AVL Dashboard",
    page_icon=":vertical_traffic_light:",
    layout="wide",
)

st.title("AVL Dashboard")
st.markdown(
    """
Personal tool for off-route report analysis.

- **Upload**: import a daily Excel report.
- **Dashboard**: filter, chart, and export the accumulated history.

Use the sidebar to navigate.
"""
)

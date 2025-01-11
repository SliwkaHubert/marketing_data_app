import streamlit as st

pages = {
    "Home": [
        st.Page("home_page.py", title="Home"),
    ],
    "Overview": [
        st.Page("pages/dashboard.py", title="Dashboard"),
        st.Page("pages/rfm_analysis.py", title="RFM"),
    ],
    "Resources": [
        st.Page("pages/test.py", title="Test"),
        st.Page("pages/test2.py", title="Test2")
    ],
}

pg = st.navigation(pages)
pg.run()
import streamlit as st

pages = {
    "Home": [
        st.Page("pages/home_page.py", title="Home"),
    ],
    "Overview": [
        st.Page("pages/dashboard.py", title="Dashboard"),
    ],
    "Analysis": [
        st.Page("pages/analiza koszykowa.py", title="Analiza koszykowa"),
        st.Page("pages/rfm_analysis.py", title="RFM"),
        st.Page("pages/Kmeans.py", title="KMeans")
    ],
}

pg = st.navigation(pages)
pg.run()
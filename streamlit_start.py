import streamlit as st

pages = {
    "Home": [
        st.Page("app/pages/home_page.py", title="Home"),
    ],
    "Overview": [
        st.Page("app/pages/dashboard.py", title="Dashboard"),
    ],
    "Analysis": [
        st.Page("app/pages/analiza koszykowa.py", title="Analiza koszykowa"),
        st.Page("app/pages/rfm_analysis.py", title="RFM"),
        st.Page("app/pages/Kmeans.py", title="KMeans")
    ],
}

pg = st.navigation(pages)
pg.run()
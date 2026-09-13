from __future__ import annotations

import streamlit as st

from services.state import init_state
from ui.style import apply_global_styles


st.set_page_config(
    page_title="Triply — Voyage selon ton budget",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_state()
apply_global_styles()

pages = [
    st.Page("pages/home.py", title="Accueil", icon="🏠", url_path="", default=True),
    st.Page("pages/search.py", title="Rechercher", icon="🔎", url_path="search"),
    st.Page("pages/results.py", title="Résultats", icon="✨", url_path="results"),
    st.Page("pages/favorites.py", title="Favoris", icon="❤️", url_path="favorites"),
    st.Page("pages/history.py", title="Historique", icon="🕘", url_path="history"),
    st.Page("pages/about.py", title="À propos", icon="ℹ️", url_path="about"),
    st.Page(
        "pages/details.py",
        title="Détails",
        icon="🧾",
        url_path="details",
        visibility="hidden",
    ),
]

page = st.navigation(pages, position="top")
page.run()

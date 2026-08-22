"""Styles CSS légers injectés dans l'application (fond de page, lisibilité)."""

import streamlit as st


def inject_custom_css():
    st.markdown("""
    <style>
    .stApp { background-color: #F7F9FC; }
    div[data-testid="stExpander"] {
        background: white;
        border-radius: 12px;
        border: 1px solid #E6E9EF;
        margin-bottom: 0.6rem;
    }
    </style>
    """, unsafe_allow_html=True)

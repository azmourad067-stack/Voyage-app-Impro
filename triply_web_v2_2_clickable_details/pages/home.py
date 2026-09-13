from __future__ import annotations

import streamlit as st

from services.state import init_state
from ui.actions import search_and_open_results
from ui.forms import render_search_form
from ui.components import render_footer


init_state()

st.markdown(
    """
    <section class="hero">
        <div class="eyebrow">🌍 TON VOYAGE, TON BUDGET</div>
        <h1>Pars plus loin.<br>Sans dépasser ton budget.</h1>
        <p>
            Compare automatiquement transport et hébergement,
            puis découvre les combinaisons les plus intéressantes
            pour ton budget total.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="search-shell">', unsafe_allow_html=True)
params = render_search_form(
    key_prefix="home",
    defaults=st.session_state.search_defaults,
    compact=True,
)
st.markdown("</div>", unsafe_allow_html=True)

if params:
    search_and_open_results(params)

st.markdown('<h2 class="section-title">Un seul endroit pour comparer</h2>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle">L’application cherche, normalise et combine les options pour toi.</div>',
    unsafe_allow_html=True,
)

features = [
    ("✈️", "Vols", "Recherche Google Flights avec prix structurés."),
    ("🏨", "Hôtels", "Hôtels et locations de vacances aux dates choisies."),
    ("🚆", "Train & bus", "Recherche web complémentaire pour les trajets terrestres."),
    ("💸", "Budget intelligent", "Transport + logement calculés ensemble, pas séparément."),
]

cols = st.columns(4)
for col, (icon, title, text) in zip(cols, features):
    with col:
        st.markdown(
            f"""
            <div class="feature-card">
                <div class="icon">{icon}</div>
                <h3>{title}</h3>
                <p>{text}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<h2 class="section-title">Comment ça marche ?</h2>', unsafe_allow_html=True)
steps = st.columns(3)
with steps[0]:
    st.markdown("### 1. Tu fixes ton budget")
    st.write("Ville de départ, destination, dates, voyageurs et budget total.")
with steps[1]:
    st.markdown("### 2. Triply compare")
    st.write("Vols, hôtels, locations, Airbnb, trains et bus sont recherchés.")
with steps[2]:
    st.markdown("### 3. Tu choisis")
    st.write("Les meilleures combinaisons compatibles avec ton budget remontent en premier.")

if st.session_state.last_result is not None:
    st.divider()
    last = st.session_state.last_result
    st.markdown("### Reprendre la dernière recherche")
    c1, c2 = st.columns([4, 1])
    with c1:
        st.write(
            f"**{last.params.origin} → {last.params.destination}** · "
            f"{last.params.nights} nuit(s) · budget {last.params.max_budget:.0f} €"
        )
    with c2:
        if st.button("Voir les résultats", type="primary", use_container_width=True):
            st.switch_page("pages/results.py")

render_footer()

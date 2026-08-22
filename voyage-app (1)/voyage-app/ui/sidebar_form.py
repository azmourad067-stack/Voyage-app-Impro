"""
Formulaire de recherche (barre latérale). Sépare volontairement la collecte
des entrées utilisateur de la logique métier (voir core/search_engine.py).
"""

from typing import Optional

import streamlit as st

from core.search_engine import SearchParams


def render_sidebar_form() -> Optional[SearchParams]:
    st.sidebar.header("🔎 Votre recherche")

    with st.sidebar.form("search_form"):
        depart = st.text_input("Ville de départ", placeholder="ex. Paris")
        destination = st.text_input("Destination", placeholder="ex. Barcelone")

        col1, col2 = st.columns(2)
        with col1:
            st.date_input("Date de départ")
        with col2:
            nights = st.number_input("Nombre de nuits", min_value=1, max_value=30, value=4)

        passengers = st.number_input("Nombre de voyageurs", min_value=1, max_value=9, value=2)

        st.markdown("---")
        st.subheader("💶 Budget")
        budget = st.number_input("Budget total visé (€)", min_value=20, max_value=20000, value=600, step=10)
        tolerance = st.slider("Marge de tolérance (± €)", min_value=0, max_value=1000, value=100, step=10)

        st.markdown("---")
        st.subheader("🏨 Hébergement")
        acc_types = st.multiselect("Type d'hébergement", ["Hôtel", "Airbnb"], default=["Hôtel", "Airbnb"])
        radius_km = st.slider("Rayon de recherche autour de la destination (km)", min_value=1, max_value=50, value=10)

        # Le filtre par étoiles n'est actif (affiché) que si "Hôtel" est sélectionné,
        # conformément au cahier des charges.
        if "Hôtel" in acc_types:
            min_stars = st.select_slider("Nombre d'étoiles minimum (hôtels)", options=[1, 2, 3, 4, 5], value=2)
        else:
            min_stars = 1
            st.caption("⭐ Le filtre étoiles apparaît ici si « Hôtel » est sélectionné.")

        with st.expander("⚙️ Préférences avancées (priorités de recommandation)"):
            st.caption("Ajustez l'importance de chaque critère dans le calcul du meilleur choix.")
            weight_price = st.slider("Importance du prix", 0, 10, 6)
            weight_time = st.slider("Importance de la rapidité", 0, 10, 5)
            weight_comfort = st.slider("Importance du confort", 0, 10, 4)
            weight_eco = st.slider("Importance de l'impact écologique", 0, 10, 3)

        submitted = st.form_submit_button("🚀 Rechercher", use_container_width=True)

    if not submitted:
        return None

    return SearchParams(
        depart=depart,
        destination=destination,
        budget=float(budget),
        tolerance=float(tolerance),
        radius_km=float(radius_km),
        acc_types=acc_types,
        min_stars=min_stars,
        nights=int(nights),
        passengers=int(passengers),
        weight_price=weight_price,
        weight_time=weight_time,
        weight_comfort=weight_comfort,
        weight_eco=weight_eco,
    )

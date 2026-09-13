from __future__ import annotations

import streamlit as st

from services.state import init_state, get_favorites
from ui.components import page_heading, render_offer_card, render_footer


init_state()
favorites = get_favorites()

page_heading(
    "Tes favoris",
    "Enregistre les offres intéressantes pendant que tu compares.",
)

if not favorites:
    st.info("Tu n'as encore ajouté aucune offre aux favoris.")
    if st.button("Voir les résultats", type="primary"):
        if st.session_state.last_result is not None:
            st.switch_page("pages/results.py")
        else:
            st.switch_page("pages/search.py")
else:
    transport = [x for x in favorites if x.category == "transport"]
    lodging = [x for x in favorites if x.category == "lodging"]

    c1, c2 = st.columns(2)
    c1.metric("Transports favoris", len(transport))
    c2.metric("Hébergements favoris", len(lodging))

    if transport:
        st.markdown("### 🚆 Transports")
        for i, offer in enumerate(transport):
            render_offer_card(offer, key_prefix=f"fav_transport_{i}")

    if lodging:
        st.markdown("### 🏨 Hébergements")
        for i, offer in enumerate(lodging):
            render_offer_card(offer, key_prefix=f"fav_lodging_{i}")

st.caption(
    "Dans cette V2, les favoris restent pendant la session du navigateur. "
    "Une connexion Supabase pourra les rendre persistants entre appareils."
)

render_footer()

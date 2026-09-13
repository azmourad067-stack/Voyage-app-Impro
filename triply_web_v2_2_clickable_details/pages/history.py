from __future__ import annotations

import streamlit as st

from services.models import TripSearchParams
from services.state import init_state, clear_history, set_search_defaults
from ui.components import page_heading, render_footer


init_state()
page_heading(
    "Historique",
    "Retrouve rapidement les recherches effectuées dans cette session.",
)

history = st.session_state.history

if not history:
    st.info("Aucune recherche dans l'historique.")
    if st.button("Commencer une recherche", type="primary"):
        st.switch_page("pages/search.py")
else:
    head1, head2 = st.columns([4, 1])
    with head1:
        st.write(f"**{len(history)} recherche(s) récente(s)**")
    with head2:
        if st.button("Effacer", use_container_width=True):
            clear_history()
            st.rerun()

    for idx, item in enumerate(history):
        with st.container(border=True):
            left, middle, right = st.columns([3.2, 1.7, 1.2], vertical_alignment="center")
            with left:
                st.markdown(f"### {item['origin']} → {item['destination']}")
                st.caption(
                    f"{item['departure_date']} au {item['return_date']} · "
                    f"{item['adults']} voyageur(s) · recherche {item['searched_at']}"
                )
            with middle:
                if item.get("best_total") is not None:
                    st.metric("Meilleur total", f"{item['best_total']:.0f} €")
                else:
                    st.metric("Budget", f"{item['max_budget']:.0f} €")
            with right:
                if st.button(
                    "Rechercher à nouveau",
                    key=f"repeat_{idx}",
                    use_container_width=True,
                ):
                    set_search_defaults(item)
                    st.switch_page("pages/search.py")

st.caption(
    "L'historique est actuellement lié à la session. "
    "La prochaine étape peut être sa persistance dans Supabase."
)

render_footer()

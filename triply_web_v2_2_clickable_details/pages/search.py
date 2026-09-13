from __future__ import annotations

import streamlit as st

from services.config import get_settings
from services.serpapi_client import SerpApiClient, SerpApiError
from services.state import init_state
from ui.actions import search_and_open_results
from ui.components import page_heading, render_footer
from ui.forms import render_search_form


init_state()
page_heading(
    "Construis ton voyage",
    "Indique ton budget total : Triply cherche ensuite les meilleures combinaisons.",
)

settings = get_settings()

with st.container(border=True):
    status_col, action_col = st.columns([4, 1], vertical_alignment="center")
    with status_col:
        if settings.serpapi_key:
            st.success("API de recherche configurée")
        else:
            st.error("SERPAPI_KEY manquante")
            st.caption("Ajoute-la dans les Secrets Streamlit avant de lancer la recherche.")
    with action_col:
        if settings.serpapi_key and st.button("Tester l'API", use_container_width=True):
            try:
                account = SerpApiClient(settings.serpapi_key).account_status()
                remaining = account.get("total_searches_left")
                if remaining is None:
                    remaining = account.get("plan_searches_left")
                st.toast(
                    f"Clé valide"
                    + (f" · {remaining} recherches restantes" if remaining is not None else ""),
                    icon="✅",
                )
            except SerpApiError as exc:
                st.error(str(exc))

st.markdown('<div class="search-shell">', unsafe_allow_html=True)
params = render_search_form(
    key_prefix="search",
    defaults=st.session_state.search_defaults,
)
st.markdown("</div>", unsafe_allow_html=True)

if params:
    st.session_state.search_defaults = params.to_dict()
    search_and_open_results(params)

st.markdown("### Conseils pour trouver moins cher")
tips = st.columns(3)
tips[0].info("📅 Décaler le voyage de quelques jours peut réduire fortement le prix.")
tips[1].info("🏡 Les locations de vacances peuvent être intéressantes pour plusieurs nuits.")
tips[2].info("🚆 Pour les trajets courts, vérifie aussi train et bus.")

render_footer()

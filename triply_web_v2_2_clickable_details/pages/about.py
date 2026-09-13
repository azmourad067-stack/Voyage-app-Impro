from __future__ import annotations

import streamlit as st

from services.config import get_settings
from services.serpapi_client import SerpApiClient, SerpApiError
from ui.components import page_heading, render_footer


page_heading(
    "À propos de Triply",
    "Une application web Python qui cherche un voyage à partir d'un budget total.",
)

st.markdown(
    """
    ### Pourquoi cette architecture ?

    Les offres de voyage viennent de nombreuses plateformes différentes et il n'existe
    pas une API gratuite unique couvrant de façon fiable hôtels, Airbnb, vols, trains et bus.

    Triply utilise donc **SerpAPI** comme couche de recherche principale :

    - Google Flights pour les vols ;
    - Google Hotels pour les hôtels ;
    - Google Hotels Vacation Rentals pour les locations ;
    - Google Search pour compléter Airbnb, train et bus.

    L'application n'invente jamais un prix manquant. Lorsque le prix total n'est pas
    suffisamment clair, l'offre est présentée comme piste à vérifier plutôt que d'être
    intégrée au calcul du budget.
    """
)

st.markdown("### État de l'API")
settings = get_settings()
if not settings.serpapi_key:
    st.error("SERPAPI_KEY n'est pas configurée.")
else:
    st.success("SERPAPI_KEY est configurée.")
    if st.button("Tester la connexion SerpAPI"):
        try:
            account = SerpApiClient(settings.serpapi_key).account_status()
            remaining = account.get("total_searches_left")
            if remaining is None:
                remaining = account.get("plan_searches_left")
            st.success(
                "Connexion réussie"
                + (f" · {remaining} recherches restantes" if remaining is not None else "")
            )
        except SerpApiError as exc:
            st.error(str(exc))

st.markdown(
    """
    ### Limites à connaître

    Les prix et disponibilités peuvent changer entre la recherche et la réservation.
    Les résultats de snippets web sont moins fiables que les données structurées de
    Google Flights ou Google Hotels. Triply doit donc rester un **comparateur et assistant
    de décision**, pas un système de réservation lui-même.

    ### Prochaine évolution

    La V3 pourra ajouter **Supabase** pour les comptes utilisateurs, favoris persistants,
    historique synchronisé et alertes de prix.
    """
)

render_footer()

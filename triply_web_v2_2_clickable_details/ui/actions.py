from __future__ import annotations

import streamlit as st

from services.config import get_settings
from services.models import TripSearchParams
from services.search_service import run_trip_search
from services.state import save_result


def search_and_open_results(params: TripSearchParams) -> None:
    settings = get_settings()
    if not settings.serpapi_key:
        st.error(
            "SERPAPI_KEY n'est pas encore configurée. "
            "Ajoute-la dans les Secrets de Streamlit avant de lancer une recherche."
        )
        return

    progress_bar = st.progress(0)
    status = st.status("Préparation de la recherche…", expanded=True)

    def on_progress(value: int, label: str) -> None:
        progress_bar.progress(value)
        status.update(label=label, state="running")
        status.write(label)

    try:
        result = run_trip_search(
            params=params,
            api_key=settings.serpapi_key,
            on_progress=on_progress,
        )
    except Exception as exc:
        status.update(label="La recherche a échoué", state="error")
        st.error(f"Erreur inattendue : {exc}")
        return

    save_result(result)
    progress_bar.progress(100)
    status.update(label="Voyage trouvé — affichage des résultats", state="complete")
    st.switch_page("pages/results.py")

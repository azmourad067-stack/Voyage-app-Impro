"""
ComparoVoyage — Application Streamlit de comparaison transport + hébergement.

Point d'entrée de l'application. Ne contient volontairement aucune logique
métier : celle-ci vit dans `core/`, l'interface dans `ui/`.
"""

import streamlit as st

from ui.sidebar_form import render_sidebar_form
from ui.results_view import render_results
from ui.styles import inject_custom_css
from core.search_engine import run_search

st.set_page_config(
    page_title="ComparoVoyage — Trouvez le meilleur plan",
    page_icon="🧳",
    layout="wide",
)

inject_custom_css()

st.title("🧳 ComparoVoyage")
st.caption(
    "Comparez et trouvez la meilleure combinaison transport + hébergement, "
    "selon votre budget et vos priorités de voyage."
)

params = render_sidebar_form()

if params is None:
    st.info("👈 Renseignez vos critères de voyage dans le panneau de gauche puis cliquez sur **Rechercher**.")
    st.markdown("""
### Comment ça marche ?
1. Indiquez votre ville de **départ** et votre **destination**.
2. Définissez votre **budget** et une marge de tolérance.
3. Choisissez le(s) type(s) d'hébergement et un **rayon de recherche**.
4. Ajustez si besoin vos priorités (prix, rapidité, confort, écologie).
5. Comparez les meilleures combinaisons, classées par pertinence, avec :
   un **score de rapport qualité/prix personnalisable**, une estimation du
   **temps de trajet porte-à-porte**, et l'**empreinte carbone** de chaque option.
""")
else:
    with st.spinner("Recherche des meilleures combinaisons en cours..."):
        result = run_search(params)

    if result.error:
        st.error(f"⚠️ {result.error}")
    else:
        render_results(result, params.budget)

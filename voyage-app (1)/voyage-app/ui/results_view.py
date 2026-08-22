"""
Affichage des résultats de recherche : indicateurs clés, puis liste des
combinaisons transport + hébergement sous forme d'éléments cliquables
(accordéons) qui révèlent tous les détails au clic.
"""

import pandas as pd
import streamlit as st

from core.search_engine import SearchResult
from core.scoring import Package


def _format_duration(minutes: int) -> str:
    return f"{minutes // 60}h{minutes % 60:02d}"


def _package_to_row(p: Package) -> dict:
    return {
        "Mode": p.transport.mode,
        "Opérateur": p.transport.operator,
        "Hébergement": p.accommodation.name,
        "Type": p.accommodation.acc_type,
        "Étoiles": p.accommodation.stars if p.accommodation.stars else "-",
        "Prix total (€)": p.total_price,
        "Durée trajet (aller)": _format_duration(p.total_duration_min),
        "CO2 (kg, A/R)": p.total_co2_kg,
        "Score": p.score,
    }


def render_summary_metrics(result: SearchResult):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Distance", f"{result.distance_km:.0f} km")
    c2.metric("Offres transport", len(result.all_transport))
    c3.metric("Hébergements trouvés", len(result.all_accommodation))
    total_combos = len(result.packages) if result.ok else len(result.fallback_packages)
    c4.metric("Combinaisons évaluées", total_combos)


def render_package_expander(p: Package, expanded: bool = False):
    """
    Affiche une combinaison sous forme d'accordéon : un résumé visible en
    permanence, et tous les détails (transport + hébergement + budget)
    révélés au clic.
    """
    badges_str = " · ".join(p.badges) if p.badges else ""
    stars_display = "⭐" * p.accommodation.stars if p.accommodation.stars else "Airbnb"
    icon = "🏆" if p.badges and "⭐ Meilleur choix" in p.badges else "🧳"

    label = f"{icon} {p.transport.mode} + {p.accommodation.acc_type} — {p.total_price:.0f} € — Score {p.score}/100"
    if badges_str:
        label += f"  ({badges_str})"

    with st.expander(label, expanded=expanded):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🚆 Transport**")
            st.write(f"Mode : {p.transport.mode}")
            st.write(f"Opérateur : {p.transport.operator}")
            st.write(f"Trajet : {'Direct' if p.transport.direct else 'Avec correspondance'}")
            st.write(f"Créneau indicatif : {p.transport.departure_hint}")
            st.write(f"Durée (aller) : {_format_duration(p.transport.duration_min)}")
            st.write(f"Prix aller simple / personne : {p.transport.price_eur:.2f} €")
            st.write(f"CO2 estimé (aller-retour, {p.passengers} voyageur(s)) : {p.total_co2_kg} kg")

        with col2:
            st.markdown("**🏨 Hébergement**")
            st.write(f"Nom : {p.accommodation.name}")
            st.write(f"Type : {p.accommodation.acc_type} — {stars_display}")
            st.write(f"Note : {p.accommodation.rating}/5 ({p.accommodation.reviews_count} avis)")
            st.write(f"Distance du centre : {p.accommodation.distance_from_center_km} km")
            st.write(f"Prix / nuit : {p.accommodation.price_per_night:.2f} €")
            st.write(f"Équipements : {', '.join(p.accommodation.amenities)}")

        st.markdown("---")
        st.markdown("**💶 Détail du budget**")
        transport_total = p.transport.price_eur * p.passengers * 2
        accommodation_total = p.accommodation.price_per_night * p.nights
        b1, b2, b3 = st.columns(3)
        b1.metric("Transport (A/R, tous voyageurs)", f"{transport_total:.0f} €")
        b2.metric(f"Hébergement ({p.nights} nuit(s))", f"{accommodation_total:.0f} €")
        b3.metric("Total séjour", f"{p.total_price:.0f} €")

        transfer_min = p.total_duration_min - p.transport.duration_min
        st.markdown("**🕒 Temps de trajet total estimé (aller)**")
        st.write(
            f"{_format_duration(p.transport.duration_min)} de transport "
            f"+ environ {transfer_min} min de transfert jusqu'à l'hébergement "
            f"= **{_format_duration(p.total_duration_min)} au total**"
        )

        st.caption("📌 Données simulées — voir le README pour brancher une vraie API de transport/hébergement.")


def render_results(result: SearchResult, budget_target: float):
    render_summary_metrics(result)

    if result.ok:
        st.markdown(f"### ✅ {len(result.packages)} combinaison(s) dans votre budget")
        st.caption("Cliquez sur une proposition pour voir tous les détails du trajet et de l'hébergement.")

        for i, p in enumerate(result.packages[:10]):
            render_package_expander(p, expanded=(i == 0))

        if len(result.packages) > 10:
            with st.expander("Voir toutes les combinaisons (tableau détaillé)"):
                df = pd.DataFrame([_package_to_row(p) for p in result.packages])
                st.dataframe(df, use_container_width=True)
    else:
        if result.warning:
            st.warning(result.warning)
            st.caption("Cliquez sur une proposition pour voir tous les détails.")
            for i, p in enumerate(result.fallback_packages):
                render_package_expander(p, expanded=(i == 0))

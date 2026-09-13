from __future__ import annotations

import pandas as pd
import streamlit as st

from services.state import init_state, offer_id
from ui.components import page_heading, render_offer_card, render_footer, open_offer_details


init_state()
result = st.session_state.last_result

if result is None:
    page_heading("Résultats", "Aucune recherche active pour le moment.")
    st.info("Lance d'abord une recherche pour comparer les offres.")
    if st.button("Nouvelle recherche", type="primary"):
        st.switch_page("pages/search.py")
    st.stop()

params = result.params
page_heading(
    f"{params.origin} → {params.destination}",
    f"{params.departure_date.strftime('%d/%m/%Y')} au "
    f"{params.return_date.strftime('%d/%m/%Y')} · "
    f"{params.adults} voyageur(s) · budget {params.max_budget:.0f} €",
)

top = st.columns(4)
best_total = result.combinations[0].total_price if result.combinations else None
top[0].metric("Meilleur total", f"{best_total:.0f} €" if best_total else "—")
top[1].metric("Combinaisons", len(result.combinations))
top[2].metric("Transports tarifés", len([x for x in result.transport_offers if x.price_total is not None]))
top[3].metric("Hébergements", len(result.lodging_offers))

if result.origin_location and result.destination_location:
    origin_airports = ", ".join(
        a["id"] for a in result.origin_location.get("airports", [])[:4]
    ) or "—"
    destination_airports = ", ".join(
        a["id"] for a in result.destination_location.get("airports", [])[:4]
    ) or "—"
    st.caption(
        f"Interprétation vols : {result.origin_location['name']} ({origin_airports}) → "
        f"{result.destination_location['name']} ({destination_airports})"
    )

for warning in result.warnings:
    st.warning(warning)

combo_tab, transport_tab, lodging_tab, discovery_tab = st.tabs(
    ["✨ Meilleurs voyages", "🚆 Transports", "🏨 Hébergements", "🌐 À vérifier"]
)

with combo_tab:
    if not result.combinations:
        st.error(
            "Aucune combinaison tarifée ne respecte ce budget. "
            "Essaie un budget supérieur ou d'autres dates."
        )
    else:
        f1, f2, f3 = st.columns(3)
        transport_types = sorted({c.transport.subtype for c in result.combinations})
        lodging_types = sorted({c.lodging.subtype for c in result.combinations})

        with f1:
            selected_transport = st.multiselect(
                "Transport",
                transport_types,
                default=transport_types,
                format_func=lambda x: x.replace("_", " ").title(),
            )
        with f2:
            selected_lodging = st.multiselect(
                "Hébergement",
                lodging_types,
                default=lodging_types,
                format_func=lambda x: x.replace("_", " ").title(),
            )
        with f3:
            sort_by = st.selectbox(
                "Trier par",
                ["Prix total", "Budget restant", "Confiance"],
            )

        combos = [
            c for c in result.combinations
            if c.transport.subtype in selected_transport
            and c.lodging.subtype in selected_lodging
        ]

        if sort_by == "Budget restant":
            combos.sort(key=lambda c: c.remaining_budget, reverse=True)
        elif sort_by == "Confiance":
            combos.sort(key=lambda c: (-c.confidence_score, c.total_price))
        else:
            combos.sort(key=lambda c: c.total_price)

        st.caption(f"{len(combos)} combinaison(s) affichée(s)")

        for idx, combo in enumerate(combos[:30], start=1):
            with st.container(border=True):
                head1, head2 = st.columns([4.5, 1.5], vertical_alignment="center")
                with head1:
                    badge = "🏆 Meilleur prix" if idx == 1 and sort_by == "Prix total" else f"Option {idx}"
                    st.markdown(f"**{badge}**")
                    st.write(
                        f"{combo.transport.subtype.replace('_', ' ').title()} + "
                        f"{combo.lodging.subtype.replace('_', ' ').title()}"
                    )
                    st.caption(f"Confiance : {combo.confidence}")
                with head2:
                    st.markdown(
                        f"<div class='price'>{combo.total_price:,.0f} €</div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"{combo.remaining_budget:,.0f} € sous le budget")

                st.divider()
                left, right = st.columns(2)
                with left:
                    st.markdown("##### 🚆 Transport")
                    st.write(combo.transport.provider)
                    st.caption(combo.transport.details)
                    if combo.transport.price_total is not None:
                        st.write(f"**{combo.transport.price_total:,.0f} €**")
                    if st.button(
                        "🔎 Horaires, gares / aéroports",
                        key=f"combo_transport_details_{idx}_{offer_id(combo.transport)}",
                        use_container_width=True,
                    ):
                        open_offer_details(combo.transport)
                with right:
                    st.markdown("##### 🏨 Hébergement")
                    st.write(combo.lodging.title)
                    st.caption(combo.lodging.details)
                    if combo.lodging.price_total is not None:
                        st.write(f"**{combo.lodging.price_total:,.0f} €**")
                    if st.button(
                        "🔎 Adresse et détails",
                        key=f"combo_lodging_details_{idx}_{offer_id(combo.lodging)}",
                        use_container_width=True,
                    ):
                        open_offer_details(combo.lodging)

with transport_tab:
    types = sorted({o.subtype for o in result.transport_offers})
    selected = st.multiselect(
        "Types de transport",
        types,
        default=types,
        key="transport_filter",
        format_func=lambda x: x.replace("_", " ").title(),
    )
    offers = [
        x for x in result.transport_offers
        if x.subtype in selected and x.price_total is not None
    ]
    offers.sort(key=lambda x: x.price_total or 10**9)
    if not offers:
        st.info("Aucun transport tarifé pour ces filtres.")
    for i, offer in enumerate(offers[:40]):
        render_offer_card(offer, key_prefix=f"transport_{i}")

with lodging_tab:
    types = sorted({o.subtype for o in result.lodging_offers})
    selected = st.multiselect(
        "Types d'hébergement",
        types,
        default=types,
        key="lodging_filter",
        format_func=lambda x: x.replace("_", " ").title(),
    )
    offers = [x for x in result.lodging_offers if x.subtype in selected]
    offers.sort(key=lambda x: x.price_total or 10**9)
    if not offers:
        st.info("Aucun hébergement pour ces filtres.")
    for i, offer in enumerate(offers[:40]):
        render_offer_card(offer, key_prefix=f"lodging_{i}")

with discovery_tab:
    st.info(
        "Les résultats de cet onglet peuvent provenir de snippets web. "
        "Triply ne les utilise pas dans le budget lorsque le prix total n'est pas suffisamment fiable."
    )
    if not result.discovery_offers:
        st.write("Aucun résultat complémentaire.")
    for i, offer in enumerate(result.discovery_offers[:50]):
        render_offer_card(offer, key_prefix=f"discovery_{i}")

st.divider()
left, right = st.columns([1, 1])
with left:
    if st.button("← Modifier la recherche", use_container_width=True):
        st.session_state.search_defaults = params.to_dict()
        st.switch_page("pages/search.py")
with right:
    if st.button("Nouvelle recherche", type="primary", use_container_width=True):
        st.session_state.search_defaults = None
        st.switch_page("pages/search.py")

render_footer()

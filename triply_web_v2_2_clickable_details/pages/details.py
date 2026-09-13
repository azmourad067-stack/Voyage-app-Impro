from __future__ import annotations

import pandas as pd
import streamlit as st

from services.config import get_settings
from services.detail_service import load_offer_details
from services.serpapi_client import SerpApiError
from services.state import (
    init_state,
    get_selected_offer,
    offer_id,
)
from ui.components import page_heading, render_footer


init_state()
offer = get_selected_offer()

if offer is None:
    page_heading("Détails de l'offre", "Aucune offre sélectionnée.")
    st.info("Retourne aux résultats et clique sur « Voir les détails ».")
    if st.button("← Retour aux résultats", type="primary"):
        st.switch_page("pages/results.py")
    st.stop()

settings = get_settings()
icon = {
    "flight": "✈️",
    "train": "🚆",
    "bus": "🚌",
    "hotel": "🏨",
    "vacation_rental": "🏡",
    "airbnb": "🏠",
}.get(offer.subtype, "🧳")

back_col, source_col = st.columns([1.4, 4.6])
with back_col:
    if st.button("← Résultats", use_container_width=True):
        st.switch_page("pages/results.py")
with source_col:
    if offer.url:
        st.link_button("Ouvrir le site source ↗", offer.url)

page_heading(
    f"{icon} {offer.title}",
    f"{offer.provider} · {offer.confidence_label}",
)

summary_cols = st.columns(3)
summary_cols[0].metric(
    "Prix total",
    f"{offer.price_total:,.0f} €" if offer.price_total is not None else "À vérifier",
)
summary_cols[1].metric("Type", offer.subtype.replace("_", " ").title())
summary_cols[2].metric("Source", offer.provider)

if offer.details:
    st.info(offer.details)

if not settings.serpapi_key:
    st.warning(
        "La clé SerpAPI n'est pas configurée : impossible de charger "
        "les informations détaillées supplémentaires."
    )
    st.stop()

cache_key = offer_id(offer)
cache = st.session_state.detail_cache

if cache_key not in cache:
    with st.status("Chargement des informations détaillées…", expanded=True) as status:
        try:
            cache[cache_key] = load_offer_details(
                offer=offer,
                api_key=settings.serpapi_key,
            )
            status.update(label="Détails chargés", state="complete")
        except SerpApiError as exc:
            cache[cache_key] = {"kind": "error", "error": str(exc)}
            status.update(label="Détails indisponibles", state="error")
        except Exception as exc:
            cache[cache_key] = {"kind": "error", "error": str(exc)}
            status.update(label="Erreur lors du chargement", state="error")

details = cache[cache_key]
kind = details.get("kind")

if kind == "error":
    st.error(details.get("error", "Informations détaillées indisponibles."))
    if offer.url:
        st.link_button("Vérifier directement sur le site source", offer.url)
    render_footer()
    st.stop()


def display_segments(segments: list[dict], heading: str) -> None:
    st.markdown(f"### {heading}")
    if not segments:
        st.info("Aucun segment détaillé disponible.")
        return

    for idx, segment in enumerate(segments, start=1):
        dep = segment.get("departure_airport") or {}
        arr = segment.get("arrival_airport") or {}
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.2, .7, 2.2], vertical_alignment="center")
            with c1:
                st.markdown(f"**{dep.get('time') or '—'}**")
                st.write(dep.get("name") or dep.get("id") or "Départ")
                if dep.get("id"):
                    st.caption(dep["id"])
            with c2:
                st.markdown("### →")
            with c3:
                st.markdown(f"**{arr.get('time') or '—'}**")
                st.write(arr.get("name") or arr.get("id") or "Arrivée")
                if arr.get("id"):
                    st.caption(arr["id"])

            info = []
            if segment.get("airline"):
                info.append(str(segment["airline"]))
            if segment.get("flight_number"):
                info.append(str(segment["flight_number"]))
            if segment.get("duration"):
                minutes = int(segment["duration"])
                h, m = divmod(minutes, 60)
                info.append(f"{h} h {m:02d}" if h else f"{m} min")
            if segment.get("airplane"):
                info.append(str(segment["airplane"]))
            if segment.get("travel_class"):
                info.append(str(segment["travel_class"]))

            if info:
                st.caption(" · ".join(info))

            extensions = segment.get("extensions") or []
            if extensions:
                st.write(" • ".join(str(x) for x in extensions[:5]))


def display_transit_route(route: dict, title: str) -> None:
    with st.expander(
        f"{title} · {route.get('start_time') or '—'} → "
        f"{route.get('end_time') or '—'} · {route.get('duration') or 'durée inconnue'}",
        expanded=False,
    ):
        top = st.columns(4)
        top[0].metric("Départ", route.get("start_time") or "—")
        top[1].metric("Arrivée", route.get("end_time") or "—")
        top[2].metric("Durée", route.get("duration") or "—")
        cost = route.get("cost")
        currency = route.get("currency") or ""
        top[3].metric(
            "Coût Maps",
            f"{cost:g} {currency}".strip() if cost is not None else "—",
        )

        if route.get("via"):
            st.caption(f"Via : {route['via']}")

        trips = route.get("trips") or []
        for idx, trip in enumerate(trips, start=1):
            start = trip.get("start_stop") or {}
            end = trip.get("end_stop") or {}
            mode = trip.get("travel_mode") or "Étape"

            st.markdown(f"#### {idx}. {trip.get('title') or mode}")
            if start or end:
                left, right = st.columns(2)
                with left:
                    st.write(
                        f"**Départ :** {start.get('name') or '—'} "
                        f"à **{start.get('time') or '—'}**"
                    )
                with right:
                    st.write(
                        f"**Arrivée :** {end.get('name') or '—'} "
                        f"à **{end.get('time') or '—'}**"
                    )

            if trip.get("duration"):
                st.caption(f"Durée de l'étape : {trip['duration']}")

            if trip.get("operator"):
                st.write(f"Opérateur : **{trip['operator']}**")

            stops = trip.get("stops") or []
            if stops:
                preview = [
                    f"{stop.get('name', 'Arrêt')} ({stop.get('time', '—')})"
                    for stop in stops[:12]
                ]
                st.caption("Arrêts intermédiaires : " + " → ".join(preview))

            links = st.columns(3)
            if trip.get("operator_link"):
                with links[0]:
                    st.link_button("Site opérateur", trip["operator_link"])
            if trip.get("route_information"):
                with links[1]:
                    st.link_button("Informations ligne", trip["route_information"])

        if route.get("maps_url"):
            st.link_button("Ouvrir cet itinéraire dans Google Maps", route["maps_url"])


if kind == "flight":
    display_segments(details.get("outbound") or [], "Aller")

    layovers = details.get("layovers") or []
    if layovers:
        st.markdown("#### Escales à l'aller")
        for layover in layovers:
            st.write(
                f"- {layover.get('name') or layover.get('id') or 'Escale'} "
                f"({layover.get('duration', '?')} min)"
            )

    carbon = details.get("carbon_emissions") or {}
    if carbon.get("this_flight"):
        st.caption(
            f"Émissions estimées : {carbon['this_flight'] / 1000:.0f} kg CO₂"
        )

    st.markdown("### Retour")
    return_options = details.get("return_options") or []
    if not return_options:
        st.info("Aucune option retour détaillée renvoyée pour ce vol.")
    else:
        for idx, option in enumerate(return_options, start=1):
            price = option.get("price")
            price_text = f"{price:,.0f} €" if price is not None else "prix non indiqué"
            with st.expander(
                f"Option retour {idx} · {price_text}",
                expanded=(idx == 1),
            ):
                display_segments(option.get("segments") or [], "Segments du retour")
                if option.get("total_duration"):
                    minutes = int(option["total_duration"])
                    h, m = divmod(minutes, 60)
                    st.caption(f"Durée totale retour : {h} h {m:02d}")

elif kind == "lodging":
    prop = details.get("property") or {}

    address = prop.get("address")
    phone = prop.get("phone")
    check_in = prop.get("check_in_time")
    check_out = prop.get("check_out_time")

    st.markdown("### Informations pratiques")
    cols = st.columns(2)
    with cols[0]:
        st.write(f"📍 **Adresse :** {address or 'Non disponible'}")
        st.write(f"📞 **Téléphone :** {phone or 'Non disponible'}")
    with cols[1]:
        st.write(f"🕒 **Check-in :** {check_in or 'Non indiqué'}")
        st.write(f"🕚 **Check-out :** {check_out or 'Non indiqué'}")

    if prop.get("directions"):
        st.link_button("🗺️ Itinéraire vers l'hébergement", prop["directions"])
    if prop.get("link"):
        st.link_button("🌐 Site de l'établissement", prop["link"])

    coords = prop.get("gps_coordinates") or {}
    if coords.get("latitude") is not None and coords.get("longitude") is not None:
        map_df = pd.DataFrame(
            [{"lat": coords["latitude"], "lon": coords["longitude"]}]
        )
        st.map(map_df, latitude="lat", longitude="lon", zoom=13)

    if prop.get("description"):
        st.markdown("### Description")
        st.write(prop["description"])

    amenities = prop.get("amenities") or []
    essential = prop.get("essential_info") or []
    if essential:
        st.markdown("### Informations essentielles")
        st.write(" · ".join(str(x) for x in essential))
    if amenities:
        st.markdown("### Équipements")
        amenity_cols = st.columns(2)
        for idx, amenity in enumerate(amenities[:24]):
            amenity_cols[idx % 2].write(f"✓ {amenity}")

    nearby = prop.get("nearby_places") or []
    if nearby:
        st.markdown("### À proximité")
        for place in nearby[:8]:
            st.write(f"**{place.get('name', 'Lieu')}**")
            transports = place.get("transportations") or []
            if transports:
                st.caption(
                    " · ".join(
                        f"{x.get('type', 'Transport')} : {x.get('duration', '—')}"
                        for x in transports[:4]
                    )
                )

    prices = (prop.get("featured_prices") or []) + (prop.get("prices") or [])
    if prices:
        st.markdown("### Fournisseurs / tarifs")
        for source in prices[:8]:
            rate = source.get("total_rate") or source.get("rate_per_night") or {}
            st.write(
                f"- **{source.get('source', 'Fournisseur')}** : "
                f"{rate.get('lowest', 'prix à vérifier')}"
            )

elif kind == "ground":
    st.warning(
        details.get("note")
        or "Les horaires de transport terrestre doivent être vérifiés avant réservation."
    )

    outbound = details.get("outbound") or []
    inbound = details.get("return") or []

    st.markdown("## Aller")
    if not outbound:
        st.info(
            "Google Maps n'a pas renvoyé d'itinéraire structuré pour l'aller. "
            "Utilise le site source pour vérifier le trajet."
        )
    for idx, route in enumerate(outbound, start=1):
        display_transit_route(route, f"Itinéraire {idx}")

    st.markdown("## Retour")
    if not inbound:
        st.info(
            "Google Maps n'a pas renvoyé d'itinéraire structuré pour le retour."
        )
    for idx, route in enumerate(inbound, start=1):
        display_transit_route(route, f"Itinéraire {idx}")

    st.caption(
        "Le prix affiché sur la page de résultats peut provenir d'un snippet web. "
        "Les horaires/gares ci-dessus viennent d'une recherche Google Maps distincte "
        "et doivent être confirmés chez l'opérateur."
    )

else:
    st.markdown("### Informations disponibles")
    if offer.metadata:
        for key, value in offer.metadata.items():
            if value not in (None, "", [], {}):
                st.write(f"**{key.replace('_', ' ').title()} :** {value}")
    else:
        st.info("Aucun détail structuré supplémentaire n'est disponible.")

st.divider()
if st.button("← Revenir aux résultats", type="primary", use_container_width=True):
    st.switch_page("pages/results.py")

render_footer()

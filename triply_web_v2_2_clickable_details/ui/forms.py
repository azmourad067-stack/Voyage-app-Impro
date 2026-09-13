from __future__ import annotations

from datetime import date, timedelta
import streamlit as st

from services.models import TripSearchParams


def render_search_form(
    *,
    key_prefix: str,
    defaults: dict | None = None,
    compact: bool = False,
) -> TripSearchParams | None:
    defaults = defaults or {}
    today = date.today()

    def as_date(value, fallback):
        if not value:
            return fallback
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return fallback

    default_departure = as_date(
        defaults.get("departure_date"),
        today + timedelta(days=30),
    )
    default_return = as_date(
        defaults.get("return_date"),
        default_departure + timedelta(days=3),
    )

    with st.form(f"{key_prefix}_trip_form", border=False):
        row1 = st.columns([1.05, 1.05, .75])
        with row1[0]:
            origin = st.text_input(
                "Ville de départ",
                value=str(defaults.get("origin", "")),
                placeholder="Paris",
                key=f"{key_prefix}_origin",
            )
        with row1[1]:
            destination = st.text_input(
                "Destination",
                value=str(defaults.get("destination", "")),
                placeholder="Rome",
                key=f"{key_prefix}_destination",
            )
        with row1[2]:
            max_budget = st.number_input(
                "Budget total (€)",
                min_value=50.0,
                max_value=20_000.0,
                value=float(defaults.get("max_budget", 600.0)),
                step=25.0,
                key=f"{key_prefix}_budget",
            )

        row2 = st.columns([1, 1, .72])
        with row2[0]:
            departure_date = st.date_input(
                "Départ",
                value=default_departure,
                min_value=today,
                key=f"{key_prefix}_departure",
            )
        with row2[1]:
            return_date = st.date_input(
                "Retour",
                value=max(default_return, default_departure + timedelta(days=1)),
                min_value=today + timedelta(days=1),
                key=f"{key_prefix}_return",
            )
        with row2[2]:
            adults = st.number_input(
                "Voyageurs",
                min_value=1,
                max_value=9,
                value=int(defaults.get("adults", 1)),
                step=1,
                key=f"{key_prefix}_adults",
            )

        submitted = st.form_submit_button(
            "Trouver mon voyage ✨",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return None

    origin = origin.strip()
    destination = destination.strip()

    if not origin or not destination:
        st.error("Indique une ville de départ et une destination.")
        return None
    if origin.casefold() == destination.casefold():
        st.error("Le départ et la destination doivent être différents.")
        return None
    if return_date <= departure_date:
        st.error("La date de retour doit être après la date de départ.")
        return None

    return TripSearchParams(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=int(adults),
        max_budget=float(max_budget),
    )

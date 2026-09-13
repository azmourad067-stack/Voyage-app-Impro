from __future__ import annotations

from hashlib import sha1
from typing import Any
import streamlit as st

from .models import TravelOffer, TripSearchParams, TripSearchResult


def init_state() -> None:
    defaults = {
        "last_result": None,
        "favorites": {},
        "history": [],
        "search_defaults": None,
        "selected_offer": None,
        "detail_cache": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def offer_id(offer: TravelOffer) -> str:
    raw = "|".join(
        [
            offer.category,
            offer.subtype,
            offer.provider,
            offer.title,
            str(offer.price_total),
        ]
    )
    return sha1(raw.encode("utf-8")).hexdigest()[:14]


def is_favorite(offer: TravelOffer) -> bool:
    return offer_id(offer) in st.session_state.favorites


def toggle_favorite(offer: TravelOffer) -> bool:
    key = offer_id(offer)
    if key in st.session_state.favorites:
        del st.session_state.favorites[key]
        return False
    st.session_state.favorites[key] = offer.to_dict()
    return True


def get_favorites() -> list[TravelOffer]:
    return [
        TravelOffer.from_dict(data)
        for data in st.session_state.favorites.values()
    ]


def save_result(result: TripSearchResult) -> None:
    st.session_state.last_result = result
    best_total = (
        round(result.combinations[0].total_price, 2)
        if result.combinations
        else None
    )
    history_entry = {
        **result.params.to_dict(),
        "searched_at": result.searched_at.isoformat(timespec="minutes"),
        "best_total": best_total,
        "transport_count": len(result.transport_offers),
        "lodging_count": len(result.lodging_offers),
        "combination_count": len(result.combinations),
    }
    st.session_state.history.insert(0, history_entry)
    st.session_state.history = st.session_state.history[:20]


def set_search_defaults(params: TripSearchParams | dict[str, Any]) -> None:
    if isinstance(params, TripSearchParams):
        st.session_state.search_defaults = params.to_dict()
    else:
        st.session_state.search_defaults = params


def clear_history() -> None:
    st.session_state.history = []



def select_offer(offer: TravelOffer) -> None:
    st.session_state.selected_offer = offer.to_dict()


def get_selected_offer() -> TravelOffer | None:
    data = st.session_state.get("selected_offer")
    if not data:
        return None
    return TravelOffer.from_dict(data)


def clear_selected_offer() -> None:
    st.session_state.selected_offer = None

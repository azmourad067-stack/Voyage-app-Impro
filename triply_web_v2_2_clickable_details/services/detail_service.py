from __future__ import annotations

from typing import Any

from .models import TravelOffer
from .serpapi_client import SerpApiClient


def load_offer_details(
    offer: TravelOffer,
    api_key: str,
) -> dict[str, Any]:
    client = SerpApiClient(api_key)

    if offer.subtype == "flight":
        return {
            "kind": "flight",
            "outbound": offer.metadata.get("outbound_segments") or [],
            "layovers": offer.metadata.get("layovers") or [],
            "total_duration": offer.metadata.get("total_duration"),
            "carbon_emissions": offer.metadata.get("carbon_emissions") or {},
            "extensions": offer.metadata.get("extensions") or [],
            "return_options": client.get_return_flight_options(offer),
        }

    if offer.subtype in {"hotel", "vacation_rental"}:
        return {
            "kind": "lodging",
            "property": client.get_hotel_details(offer),
        }

    if offer.subtype in {"train", "bus"}:
        details = client.get_ground_transport_details(offer)
        details["kind"] = "ground"
        return details

    return {
        "kind": "generic",
        "metadata": offer.metadata,
    }

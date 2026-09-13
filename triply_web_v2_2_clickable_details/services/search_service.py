from __future__ import annotations

from datetime import datetime
from collections.abc import Callable

from .combinations import build_budget_combinations
from .models import TripSearchParams, TripSearchResult, TravelOffer
from .serpapi_client import SerpApiClient, SerpApiError


ProgressCallback = Callable[[int, str], None]


def _dedupe(items: list[TravelOffer]) -> list[TravelOffer]:
    seen: set[tuple] = set()
    result: list[TravelOffer] = []
    for item in items:
        key = (
            item.category,
            item.subtype,
            item.provider.casefold(),
            item.title.casefold(),
            round(item.price_total or -1, 2),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def run_trip_search(
    params: TripSearchParams,
    api_key: str,
    on_progress: ProgressCallback | None = None,
) -> TripSearchResult:
    client = SerpApiClient(api_key)
    transport: list[TravelOffer] = []
    lodging: list[TravelOffer] = []
    discovery: list[TravelOffer] = []
    warnings: list[str] = []

    origin_location = None
    destination_location = None

    def progress(value: int, label: str) -> None:
        if on_progress:
            on_progress(value, label)

    progress(8, "Résolution des villes et recherche des vols…")
    try:
        flights, origin_location, destination_location = client.search_flights(
            origin=params.origin,
            destination=params.destination,
            departure_date=params.departure_date,
            return_date=params.return_date,
            adults=params.adults,
            max_budget=params.max_budget,
        )
        transport.extend(flights)
    except SerpApiError as exc:
        warnings.append(f"Vols : {exc}")

    progress(30, "Recherche des hôtels…")
    try:
        lodging.extend(
            client.search_hotels(
                destination=params.destination,
                check_in=params.departure_date,
                check_out=params.return_date,
                adults=params.adults,
                max_budget=params.max_budget,
                vacation_rentals=False,
            )
        )
    except SerpApiError as exc:
        warnings.append(f"Hôtels : {exc}")

    progress(48, "Recherche des appartements et locations…")
    try:
        lodging.extend(
            client.search_hotels(
                destination=params.destination,
                check_in=params.departure_date,
                check_out=params.return_date,
                adults=params.adults,
                max_budget=params.max_budget,
                vacation_rentals=True,
            )
        )
    except SerpApiError as exc:
        warnings.append(f"Locations : {exc}")

    progress(64, "Recherche Airbnb…")
    try:
        discovery.extend(
            client.search_airbnb_links(
                destination=params.destination,
                check_in=params.departure_date,
                check_out=params.return_date,
                adults=params.adults,
            )
        )
    except SerpApiError as exc:
        warnings.append(f"Airbnb : {exc}")

    progress(79, "Recherche des trains et bus…")
    try:
        ground = client.search_ground_transport(
            origin=params.origin,
            destination=params.destination,
            departure_date=params.departure_date,
            return_date=params.return_date,
            adults=params.adults,
        )
        discovery.extend(ground)
        transport.extend([offer for offer in ground if offer.price_total is not None])
    except SerpApiError as exc:
        warnings.append(f"Train/bus : {exc}")

    progress(92, "Calcul des meilleures combinaisons…")
    transport = _dedupe(transport)
    lodging = _dedupe(lodging)
    discovery = _dedupe(discovery)

    combinations = build_budget_combinations(
        transport_offers=transport,
        lodging_offers=lodging,
        max_budget=params.max_budget,
        limit=60,
    )

    progress(100, "Recherche terminée")

    return TripSearchResult(
        params=params,
        transport_offers=transport,
        lodging_offers=lodging,
        discovery_offers=discovery,
        combinations=combinations,
        warnings=warnings,
        origin_location=origin_location,
        destination_location=destination_location,
        searched_at=datetime.now(),
    )

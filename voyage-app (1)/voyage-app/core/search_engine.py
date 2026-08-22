"""
Orchestrateur principal : relie géocodage, transport, hébergement et
scoring, et centralise la gestion des erreurs métier pour renvoyer des
messages clairs et exploitables par l'interface.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from core.geocoding import geocode_city, haversine_km, GeoPoint
from core.transport import search_transport, TransportOffer
from core.accommodation import search_accommodation, AccommodationOffer
from core.scoring import (
    build_packages, score_packages, assign_badges,
    filter_by_budget, closest_to_budget, Package,
)


@dataclass
class SearchParams:
    depart: str
    destination: str
    budget: float
    tolerance: float
    radius_km: float
    acc_types: List[str]
    min_stars: int
    nights: int
    passengers: int
    weight_price: float = 5
    weight_time: float = 5
    weight_comfort: float = 5
    weight_eco: float = 5


@dataclass
class SearchResult:
    ok: bool
    error: Optional[str] = None
    warning: Optional[str] = None
    packages: List[Package] = field(default_factory=list)
    fallback_packages: List[Package] = field(default_factory=list)
    depart_point: Optional[GeoPoint] = None
    dest_point: Optional[GeoPoint] = None
    distance_km: float = 0.0
    all_transport: List[TransportOffer] = field(default_factory=list)
    all_accommodation: List[AccommodationOffer] = field(default_factory=list)


def run_search(params: SearchParams) -> SearchResult:
    # --- Validation des champs obligatoires ---
    if not params.depart or not params.depart.strip():
        return SearchResult(ok=False, error="Merci d'indiquer une ville de départ.")
    if not params.destination or not params.destination.strip():
        return SearchResult(ok=False, error="Merci d'indiquer une destination.")
    if params.depart.strip().lower() == params.destination.strip().lower():
        return SearchResult(ok=False, error="La destination doit être différente de la ville de départ.")
    if params.budget <= 0:
        return SearchResult(ok=False, error="Le budget doit être supérieur à 0 €.")
    if not params.acc_types:
        return SearchResult(ok=False, error="Sélectionnez au moins un type d'hébergement (Hôtel et/ou Airbnb).")

    # --- Géocodage ---
    depart_point = geocode_city(params.depart)
    if not depart_point:
        return SearchResult(ok=False, error=f"Ville de départ « {params.depart} » introuvable. Vérifiez l'orthographe.")

    dest_point = geocode_city(params.destination)
    if not dest_point:
        return SearchResult(ok=False, error=f"Destination « {params.destination} » introuvable. Vérifiez l'orthographe.")

    distance_km = haversine_km(depart_point.lat, depart_point.lon, dest_point.lat, dest_point.lon)
    if distance_km < 5:
        return SearchResult(ok=False, error="Le départ et la destination semblent trop proches pour un voyage organisé.")

    # --- Recherche des offres ---
    transport_offers = search_transport(params.depart, params.destination, distance_km, params.passengers)
    if not transport_offers:
        return SearchResult(
            ok=False, error="Aucun moyen de transport pertinent trouvé pour cette distance.",
            depart_point=depart_point, dest_point=dest_point, distance_km=distance_km,
        )

    accommodation_offers = search_accommodation(
        params.destination, dest_point.lat, dest_point.lon, params.radius_km,
        params.acc_types, params.min_stars,
    )
    if not accommodation_offers:
        return SearchResult(
            ok=False,
            error=("Aucun hébergement trouvé dans ce rayon avec ces critères. "
                   "Essayez d'augmenter le rayon de recherche ou de réduire le nombre d'étoiles minimum."),
            depart_point=depart_point, dest_point=dest_point, distance_km=distance_km,
            all_transport=transport_offers,
        )

    # --- Constitution et scoring des packages ---
    packages = build_packages(transport_offers, accommodation_offers, params.nights, params.passengers)
    packages = score_packages(packages, params.weight_price, params.weight_time, params.weight_comfort, params.weight_eco)

    in_budget = filter_by_budget(packages, params.budget, params.tolerance)

    if not in_budget:
        fallback = closest_to_budget(packages, params.budget, n=3)
        return SearchResult(
            ok=False,
            warning=("Aucune offre ne correspond exactement à votre budget (± tolérance). "
                     "Voici les options les plus proches de votre budget cible — vous pouvez aussi "
                     "élargir la tolérance ou le rayon de recherche."),
            fallback_packages=assign_badges(fallback),
            depart_point=depart_point, dest_point=dest_point, distance_km=distance_km,
            all_transport=transport_offers, all_accommodation=accommodation_offers,
        )

    in_budget = assign_badges(sorted(in_budget, key=lambda p: -p.score))

    return SearchResult(
        ok=True,
        packages=in_budget,
        depart_point=depart_point, dest_point=dest_point, distance_km=distance_km,
        all_transport=transport_offers, all_accommodation=accommodation_offers,
    )

"""
Constitution des "packages" (transport + hébergement) et calcul des scores
de recommandation.

C'est ici que se joue la principale différenciation de l'application :
au lieu d'afficher une liste brute d'offres, on calcule pour chaque
combinaison :
  - le prix total du séjour (transport aller-retour + hébergement),
  - la durée de trajet estimée porte-à-porte (transport + correspondances
    + transfert jusqu'à l'hébergement),
  - l'empreinte carbone du trajet,
  - un score global sur 100, pondéré selon les priorités choisies par
    le voyageur (prix / rapidité / confort / écologie).
"""

from dataclasses import dataclass
from typing import List, Optional

from core.config import AVG_SPEED_LOCAL_TRANSFER
from core.transport import TransportOffer
from core.accommodation import AccommodationOffer


@dataclass
class Package:
    transport: TransportOffer
    accommodation: AccommodationOffer
    nights: int
    passengers: int
    total_price: float
    total_duration_min: int          # trajet aller, porte-à-porte
    total_co2_kg: float               # aller-retour, tous passagers
    score: float = 0.0
    badges: Optional[List[str]] = None


def _local_transfer_minutes(distance_from_center_km: float) -> int:
    """Temps estimé pour rejoindre l'hébergement depuis la gare/aéroport."""
    if distance_from_center_km <= 0:
        return 10
    return int(distance_from_center_km / AVG_SPEED_LOCAL_TRANSFER * 60) + 10


def build_packages(transport_offers: List[TransportOffer], accommodation_offers: List[AccommodationOffer],
                    nights: int, passengers: int) -> List[Package]:
    """Combine chaque offre de transport avec chaque offre d'hébergement."""
    packages = []
    for t in transport_offers:
        for a in accommodation_offers:
            transport_total = t.price_eur * passengers * 2  # aller-retour
            accommodation_total = a.price_per_night * nights
            total_price = round(transport_total + accommodation_total, 2)

            transfer_min = _local_transfer_minutes(a.distance_from_center_km)
            total_duration = t.duration_min + transfer_min
            total_co2 = round(t.co2_kg * passengers * 2, 1)

            packages.append(Package(
                transport=t,
                accommodation=a,
                nights=nights,
                passengers=passengers,
                total_price=total_price,
                total_duration_min=total_duration,
                total_co2_kg=total_co2,
            ))
    return packages


def _normalize(values: List[float], invert: bool = False) -> List[float]:
    """Ramène une liste de valeurs entre 0 et 1 (1 = meilleur)."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0 for _ in values]
    normalized = [(v - lo) / (hi - lo) for v in values]
    return [1 - n for n in normalized] if invert else normalized


def score_packages(packages: List[Package], weight_price: float, weight_time: float,
                    weight_comfort: float, weight_eco: float) -> List[Package]:
    """
    Calcule un score /100 pour chaque package selon les priorités du voyageur.
    Les poids (0-10 chacun) sont normalisés pour sommer à 1.
    """
    if not packages:
        return packages

    total_weight = max(weight_price + weight_time + weight_comfort + weight_eco, 1e-6)
    wp = weight_price / total_weight
    wt = weight_time / total_weight
    wc = weight_comfort / total_weight
    we = weight_eco / total_weight

    prices = [p.total_price for p in packages]
    durations = [p.total_duration_min for p in packages]
    comforts = [p.transport.comfort_score + p.accommodation.rating for p in packages]
    co2s = [p.total_co2_kg for p in packages]

    price_scores = _normalize(prices, invert=True)
    time_scores = _normalize(durations, invert=True)
    comfort_scores = _normalize(comforts, invert=False)
    eco_scores = _normalize(co2s, invert=True)

    for pkg, ps, ts, cs, es in zip(packages, price_scores, time_scores, comfort_scores, eco_scores):
        pkg.score = round((wp * ps + wt * ts + wc * cs + we * es) * 100, 1)

    return packages


def assign_badges(packages: List[Package]) -> List[Package]:
    """Ajoute des badges (meilleur prix, plus rapide, plus écolo, meilleur choix) aux packages concernés."""
    if not packages:
        return packages

    cheapest = min(packages, key=lambda p: p.total_price)
    fastest = min(packages, key=lambda p: p.total_duration_min)
    greenest = min(packages, key=lambda p: p.total_co2_kg)
    best_value = max(packages, key=lambda p: p.score)

    for p in packages:
        p.badges = []
        if p is cheapest:
            p.badges.append("💰 Meilleur prix")
        if p is fastest:
            p.badges.append("⚡ Plus rapide")
        if p is greenest:
            p.badges.append("🌿 Plus écologique")
        if p is best_value:
            p.badges.append("⭐ Meilleur choix")

    return packages


def filter_by_budget(packages: List[Package], budget_target: float, tolerance: float) -> List[Package]:
    lo, hi = budget_target - tolerance, budget_target + tolerance
    return [p for p in packages if lo <= p.total_price <= hi]


def closest_to_budget(packages: List[Package], budget_target: float, n: int = 3) -> List[Package]:
    return sorted(packages, key=lambda p: abs(p.total_price - budget_target))[:n]

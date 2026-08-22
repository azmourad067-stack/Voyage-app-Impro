"""
Recherche des offres de transport (train, bus, avion).

DONNEES SIMULEES : les compagnies de transport ne proposent pas toutes une
API publique gratuite. Cette fonction génère des offres réalistes (prix,
durée, horaires) à partir de la distance entre les deux villes, avec une
légère variation aléatoire pour simuler plusieurs opérateurs/créneaux.

POUR BRANCHER DE VRAIES DONNEES :
   - Train (France)  : API SNCF Connect / navitia.io          -> voir SNCF_API_KEY
   - Bus (Europe)     : FlixBus Distribution API               -> voir FLIXBUS_API_KEY
   - Avion             : Amadeus Flight Offers Search API      -> voir AMADEUS_API_KEY
   Il suffit de remplacer l'appel à `_mock_offers_for_mode(...)` dans
   `search_transport` par un appel HTTP vers l'API correspondante, en
   conservant la structure `TransportOffer` en sortie.
"""

import random
from dataclasses import dataclass
from typing import List

from core.config import (
    AVG_SPEED_TRAIN, AVG_SPEED_BUS, AVG_SPEED_PLANE,
    BUFFER_TRAIN_MIN, BUFFER_BUS_MIN, BUFFER_PLANE_MIN,
    MAX_DISTANCE_BUS, MAX_DISTANCE_TRAIN, MIN_DISTANCE_PLANE,
    CO2_TRAIN_G_KM, CO2_BUS_G_KM, CO2_PLANE_SHORT_G_KM, CO2_PLANE_LONG_G_KM,
    COMFORT_SCORE,
)


@dataclass
class TransportOffer:
    mode: str                 # "Train" / "Bus" / "Avion"
    operator: str
    price_eur: float          # prix ALLER SIMPLE, par passager
    duration_min: int
    departure_hint: str       # créneau horaire indicatif
    direct: bool
    co2_kg: float              # émissions aller simple, par passager
    comfort_score: int
    is_mocked: bool = True


_OPERATORS = {
    "Train": ["SNCF TGV INOUI", "SNCF Intercités", "Ouigo", "Trenitalia", "Renfe"],
    "Bus": ["FlixBus", "BlaBlaCar Bus", "Eurolines"],
    "Avion": ["Air France", "easyJet", "Ryanair", "Transavia", "Vueling"],
}


def _co2_for_plane(distance_km: float) -> float:
    factor = CO2_PLANE_SHORT_G_KM if distance_km < 1000 else CO2_PLANE_LONG_G_KM
    return distance_km * factor / 1000.0


def _mock_offers_for_mode(mode: str, distance_km: float, seed: int, n_offers: int = 3) -> List[TransportOffer]:
    rng = random.Random(seed)
    offers = []

    for _ in range(n_offers):
        variation = rng.uniform(0.85, 1.25)
        direct = rng.random() > (0.35 if mode == "Avion" else 0.2)

        if mode == "Train":
            price = (18 + distance_km * 0.095) * variation
            duration = distance_km / AVG_SPEED_TRAIN * 60 + BUFFER_TRAIN_MIN
            co2 = distance_km * CO2_TRAIN_G_KM / 1000.0
        elif mode == "Bus":
            price = (8 + distance_km * 0.045) * variation
            duration = distance_km / AVG_SPEED_BUS * 60 + BUFFER_BUS_MIN
            co2 = distance_km * CO2_BUS_G_KM / 1000.0
        else:  # Avion
            price = (35 + distance_km * 0.10 + 25) * variation
            duration = distance_km / AVG_SPEED_PLANE * 60 + BUFFER_PLANE_MIN
            co2 = _co2_for_plane(distance_km)

        if not direct:
            duration *= rng.uniform(1.25, 1.6)
            price *= rng.uniform(0.85, 0.95)  # une correspondance est souvent un peu moins chère

        offers.append(
            TransportOffer(
                mode=mode,
                operator=rng.choice(_OPERATORS[mode]),
                price_eur=round(price, 2),
                duration_min=int(duration),
                departure_hint=rng.choice(
                    ["Matin (6h-10h)", "Midi (10h-14h)", "Après-midi (14h-18h)", "Soir (18h-22h)"]
                ),
                direct=direct,
                co2_kg=round(co2, 1),
                comfort_score=COMFORT_SCORE[mode],
            )
        )
    return offers


def search_transport(depart_name: str, dest_name: str, distance_km: float, passengers: int = 1) -> List[TransportOffer]:
    """
    Retourne la liste des offres de transport pertinentes pour le trajet,
    en filtrant les modes non réalistes selon la distance (ex: pas de bus
    au-delà de 1500 km, pas d'avion en dessous de 80 km).
    Le prix retourné est par passager (aller simple).
    """
    seed = abs(hash((depart_name.lower().strip(), dest_name.lower().strip()))) % (10 ** 6)
    offers: List[TransportOffer] = []

    if distance_km <= MAX_DISTANCE_BUS:
        offers += _mock_offers_for_mode("Bus", distance_km, seed + 1)
    if distance_km <= MAX_DISTANCE_TRAIN:
        offers += _mock_offers_for_mode("Train", distance_km, seed + 2)
    if distance_km >= MIN_DISTANCE_PLANE:
        offers += _mock_offers_for_mode("Avion", distance_km, seed + 3)

    return offers

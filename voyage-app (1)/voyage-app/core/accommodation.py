"""
Recherche des hébergements (hôtels, Airbnb) autour de la destination.

DONNEES SIMULEES : génère des établissements plausibles dispersés dans le
rayon demandé, avec un prix influencé par la catégorie et un multiplicateur
de coût de la vie estimé pour la destination.

POUR BRANCHER DE VRAIES DONNEES :
   - Hôtels : Amadeus Hotel Search API, ou Booking.com via RapidAPI
     (voir AMADEUS_API_KEY / BOOKING_RAPIDAPI_KEY dans core/config.py)
   - Airbnb : il n'existe pas d'API publique officielle Airbnb. Solutions
     possibles à terme : partenariat direct, ou fournisseur tiers agrégeant
     des locations de courte durée (ex. Rentals United). En attendant, les
     annonces "Airbnb" restent simulées ici — c'est signalé à l'utilisateur.
"""

import math
import random
from dataclasses import dataclass
from typing import List

from core.config import HOTEL_BASE_PRICE, CITY_COST_MULTIPLIER, DEFAULT_COST_MULTIPLIER


@dataclass
class AccommodationOffer:
    name: str
    acc_type: str            # "Hôtel" ou "Airbnb"
    stars: int                # 0 si Airbnb
    rating: float              # note utilisateurs /5
    reviews_count: int
    price_per_night: float
    distance_from_center_km: float
    lat: float
    lon: float
    amenities: List[str]
    is_mocked: bool = True


_HOTEL_NAMES = [
    "Hôtel du Centre", "Grand Hôtel", "Hôtel de la Gare", "Ibis Style",
    "Hôtel des Voyageurs", "Novotel", "Hôtel Le Jardin", "Best Western",
    "Hôtel Belle Vue", "Hôtel Central Park",
]
_AIRBNB_NAMES = [
    "Studio cosy centre-ville", "Appartement lumineux", "Loft moderne",
    "Maison de charme", "T2 rénové proche transports", "Duplex avec terrasse",
    "Chambre chez l'habitant", "Appartement familial", "Pied-à-terre design",
]
_AMENITIES_HOTEL = [
    "Wifi gratuit", "Petit-déjeuner inclus", "Piscine", "Parking",
    "Salle de sport", "Bar", "Climatisation", "Animaux acceptés",
]
_AMENITIES_AIRBNB = [
    "Wifi gratuit", "Cuisine équipée", "Machine à laver", "Balcon",
    "Arrivée autonome 24h/24", "Vue dégagée", "Proche transports",
]


def _cost_multiplier(city_name: str) -> float:
    return CITY_COST_MULTIPLIER.get(city_name.strip().lower(), DEFAULT_COST_MULTIPLIER)


def _random_point_in_radius(center_lat: float, center_lon: float, radius_km: float, rng: random.Random):
    """Tire un point uniformément réparti dans le disque de rayon `radius_km`."""
    r = radius_km * math.sqrt(rng.random())
    theta = rng.uniform(0, 2 * math.pi)
    dlat = (r / 111.0) * math.cos(theta)
    dlon = (r / (111.0 * math.cos(math.radians(max(min(center_lat, 89), -89))))) * math.sin(theta)
    return center_lat + dlat, center_lon + dlon, r


def _mock_hotels(dest_name: str, center_lat: float, center_lon: float, radius_km: float,
                  min_stars: int, seed: int, n_offers: int = 8) -> List[AccommodationOffer]:
    rng = random.Random(seed)
    multiplier = _cost_multiplier(dest_name)
    offers = []
    for _ in range(n_offers):
        stars = rng.randint(max(min_stars, 1), 5)
        lat, lon, dist = _random_point_in_radius(center_lat, center_lon, radius_km * 1.3, rng)
        base = HOTEL_BASE_PRICE[stars] * multiplier * rng.uniform(0.85, 1.2)
        offers.append(AccommodationOffer(
            name=f"{rng.choice(_HOTEL_NAMES)} {dest_name.title()}",
            acc_type="Hôtel",
            stars=stars,
            rating=round(rng.uniform(3.2, 4.9), 1),
            reviews_count=rng.randint(30, 2500),
            price_per_night=round(base, 2),
            distance_from_center_km=round(dist, 1),
            lat=lat, lon=lon,
            amenities=rng.sample(_AMENITIES_HOTEL, k=rng.randint(2, 4)),
        ))
    return offers


def _mock_airbnb(dest_name: str, center_lat: float, center_lon: float, radius_km: float,
                  seed: int, n_offers: int = 8) -> List[AccommodationOffer]:
    rng = random.Random(seed)
    multiplier = _cost_multiplier(dest_name)
    offers = []
    for _ in range(n_offers):
        lat, lon, dist = _random_point_in_radius(center_lat, center_lon, radius_km * 1.3, rng)
        base = rng.uniform(35, 150) * multiplier
        offers.append(AccommodationOffer(
            name=rng.choice(_AIRBNB_NAMES),
            acc_type="Airbnb",
            stars=0,
            rating=round(rng.uniform(3.8, 5.0), 1),
            reviews_count=rng.randint(5, 600),
            price_per_night=round(base, 2),
            distance_from_center_km=round(dist, 1),
            lat=lat, lon=lon,
            amenities=rng.sample(_AMENITIES_AIRBNB, k=rng.randint(2, 4)),
        ))
    return offers


def search_accommodation(dest_name: str, center_lat: float, center_lon: float, radius_km: float,
                          types_selected: List[str], min_stars: int = 1) -> List[AccommodationOffer]:
    """Retourne les hébergements dans le rayon demandé, filtrés par type et étoiles minimales."""
    seed = abs(hash(dest_name.lower().strip())) % (10 ** 6)
    offers: List[AccommodationOffer] = []

    if "Hôtel" in types_selected:
        offers += _mock_hotels(dest_name, center_lat, center_lon, radius_km, min_stars, seed + 10)
    if "Airbnb" in types_selected:
        offers += _mock_airbnb(dest_name, center_lat, center_lon, radius_km, seed + 20)

    # Filtre final de sécurité sur le rayon réel
    offers = [o for o in offers if o.distance_from_center_km <= radius_km]
    return offers

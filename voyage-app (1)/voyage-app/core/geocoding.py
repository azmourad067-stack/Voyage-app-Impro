"""
Géolocalisation des villes.

Utilise en priorité l'API gratuite Nominatim (OpenStreetMap) — aucune clé
requise, données réelles. En cas d'indisponibilité (pas de réseau, quota
dépassé, environnement restreint...), on retombe automatiquement sur une
base de secours locale (MOCK_CITIES) qui couvre les principales villes
françaises et internationales : l'application reste ainsi toujours
fonctionnelle, y compris hors-ligne.
"""

import difflib
import unicodedata
from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2
from typing import Optional

import requests

from core.config import NOMINATIM_USER_AGENT

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


@dataclass
class GeoPoint:
    name: str
    lat: float
    lon: float
    country: str = ""


# Base de secours (hors-ligne) : ville normalisée -> (lat, lon, pays)
MOCK_CITIES = {
    "paris": (48.8566, 2.3522, "France"),
    "lyon": (45.7640, 4.8357, "France"),
    "marseille": (43.2965, 5.3698, "France"),
    "toulouse": (43.6047, 1.4442, "France"),
    "nice": (43.7102, 7.2620, "France"),
    "nantes": (47.2184, -1.5536, "France"),
    "strasbourg": (48.5734, 7.7521, "France"),
    "montpellier": (43.6108, 3.8767, "France"),
    "bordeaux": (44.8378, -0.5792, "France"),
    "lille": (50.6292, 3.0573, "France"),
    "rennes": (48.1173, -1.6778, "France"),
    "reims": (49.2583, 4.0317, "France"),
    "le havre": (49.4944, 0.1079, "France"),
    "saint-etienne": (45.4397, 4.3872, "France"),
    "toulon": (43.1242, 5.9280, "France"),
    "grenoble": (45.1885, 5.7245, "France"),
    "dijon": (47.3220, 5.0415, "France"),
    "angers": (47.4784, -0.5632, "France"),
    "nimes": (43.8367, 4.3601, "France"),
    "clermont-ferrand": (45.7772, 3.0870, "France"),
    "le mans": (48.0061, 0.1996, "France"),
    "aix-en-provence": (43.5297, 5.4474, "France"),
    "brest": (48.3904, -4.4861, "France"),
    "tours": (47.3941, 0.6848, "France"),
    "amiens": (49.8941, 2.2958, "France"),
    "limoges": (45.8336, 1.2611, "France"),
    "annecy": (45.8992, 6.1294, "France"),
    "perpignan": (42.6887, 2.8948, "France"),
    "metz": (49.1193, 6.1757, "France"),
    "besancon": (47.2378, 6.0241, "France"),
    "orleans": (47.9029, 1.9039, "France"),
    "mulhouse": (47.7508, 7.3359, "France"),
    "rouen": (49.4431, 1.0993, "France"),
    "caen": (49.1829, -0.3707, "France"),
    "nancy": (48.6921, 6.1844, "France"),
    "avignon": (43.9493, 4.8055, "France"),
    "biarritz": (43.4832, -1.5586, "France"),
    "la rochelle": (46.1603, -1.1511, "France"),
    "chamonix": (45.9237, 6.8694, "France"),
    "londres": (51.5074, -0.1278, "Royaume-Uni"),
    "london": (51.5074, -0.1278, "Royaume-Uni"),
    "barcelone": (41.3851, 2.1734, "Espagne"),
    "barcelona": (41.3851, 2.1734, "Espagne"),
    "madrid": (40.4168, -3.7038, "Espagne"),
    "rome": (41.9028, 12.4964, "Italie"),
    "milan": (45.4642, 9.1900, "Italie"),
    "venise": (45.4408, 12.3155, "Italie"),
    "venice": (45.4408, 12.3155, "Italie"),
    "amsterdam": (52.3676, 4.9041, "Pays-Bas"),
    "bruxelles": (50.8503, 4.3517, "Belgique"),
    "brussels": (50.8503, 4.3517, "Belgique"),
    "berlin": (52.5200, 13.4050, "Allemagne"),
    "munich": (48.1351, 11.5820, "Allemagne"),
    "geneve": (46.2044, 6.1432, "Suisse"),
    "genève": (46.2044, 6.1432, "Suisse"),
    "zurich": (47.3769, 8.5417, "Suisse"),
    "lisbonne": (38.7223, -9.1393, "Portugal"),
    "lisbon": (38.7223, -9.1393, "Portugal"),
    "porto": (41.1579, -8.6291, "Portugal"),
    "vienne": (48.2082, 16.3738, "Autriche"),
    "prague": (50.0755, 14.4378, "Tchéquie"),
    "dublin": (53.3498, -6.2603, "Irlande"),
    "new york": (40.7128, -74.0060, "Etats-Unis"),
    "tokyo": (35.6762, 139.6503, "Japon"),
    "marrakech": (31.6295, -7.9811, "Maroc"),
    "casablanca": (33.5731, -7.5898, "Maroc"),
    "tunis": (36.8065, 10.1815, "Tunisie"),
    "dakar": (14.7167, -17.4677, "Sénégal"),
    "montreal": (45.5019, -73.5674, "Canada"),
}


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _normalize(name: str) -> str:
    return _strip_accents(name.strip().lower())


def _geocode_online(city_name: str) -> Optional[GeoPoint]:
    """Tente un géocodage réel via Nominatim (OpenStreetMap, gratuit, sans clé)."""
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": city_name, "format": "json", "limit": 1},
            headers={"User-Agent": NOMINATIM_USER_AGENT},
            timeout=4,
        )
        response.raise_for_status()
        results = response.json()
        if results:
            r = results[0]
            return GeoPoint(
                name=r.get("display_name", city_name).split(",")[0],
                lat=float(r["lat"]),
                lon=float(r["lon"]),
            )
    except Exception:
        return None
    return None


def _geocode_offline(city_name: str) -> Optional[GeoPoint]:
    """Recherche dans la base de secours locale, avec tolérance aux fautes de frappe."""
    key = _normalize(city_name)
    if key in MOCK_CITIES:
        lat, lon, country = MOCK_CITIES[key]
        return GeoPoint(name=city_name.strip().title(), lat=lat, lon=lon, country=country)

    close = difflib.get_close_matches(key, MOCK_CITIES.keys(), n=1, cutoff=0.75)
    if close:
        lat, lon, country = MOCK_CITIES[close[0]]
        return GeoPoint(name=close[0].title(), lat=lat, lon=lon, country=country)
    return None


def geocode_city(city_name: str) -> Optional[GeoPoint]:
    """
    Géocode une ville : essaie d'abord l'API réelle (Nominatim), puis retombe
    sur la base locale hors-ligne en cas d'échec. Retourne None si introuvable.
    """
    if not city_name or not city_name.strip():
        return None

    point = _geocode_online(city_name)
    if point:
        return point

    return _geocode_offline(city_name)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance à vol d'oiseau entre deux points GPS, en kilomètres."""
    R = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

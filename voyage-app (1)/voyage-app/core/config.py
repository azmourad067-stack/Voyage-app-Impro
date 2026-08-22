"""
Configuration centrale de l'application.

Regroupe :
  - les constantes métier (vitesses moyennes, facteurs CO2, tarifs de base...)
  - les emplacements où brancher de vraies clés API pour remplacer les
    données simulées par des données réelles.
"""

import os

try:
    import streamlit as st
    _SECRETS = st.secrets
except Exception:
    _SECRETS = {}


def get_secret(key: str, default=None):
    """Récupère une clé API depuis st.secrets (Streamlit Cloud) ou une variable d'environnement."""
    try:
        if key in _SECRETS:
            return _SECRETS[key]
    except Exception:
        pass
    return os.environ.get(key, default)


# ------------------------------------------------------------------
# EMPLACEMENTS POUR DE VRAIES CLES API
# A renseigner dans les "Secrets" de Streamlit Community Cloud :
# Manage app > Settings > Secrets (format TOML), ou en variables d'env locales.
# ------------------------------------------------------------------
SNCF_API_KEY = get_secret("SNCF_API_KEY")                   # SNCF Connect / navitia.io (trains France)
FLIXBUS_API_KEY = get_secret("FLIXBUS_API_KEY")              # FlixBus Distribution API (bus Europe)
AMADEUS_API_KEY = get_secret("AMADEUS_API_KEY")              # Amadeus for Developers (vols + hôtels)
AMADEUS_API_SECRET = get_secret("AMADEUS_API_SECRET")
BOOKING_RAPIDAPI_KEY = get_secret("BOOKING_RAPIDAPI_KEY")    # Booking.com via RapidAPI (hôtels)

# Géocodage : Nominatim (OpenStreetMap) est gratuit et ne nécessite pas de clé.
NOMINATIM_USER_AGENT = "comparovoyage-app/1.0 (contact: demo@example.com)"

# ------------------------------------------------------------------
# Constantes métier (ordres de grandeur réalistes, ajustables)
# ------------------------------------------------------------------

# Vitesses moyennes utilisées pour estimer les durées de trajet (km/h)
AVG_SPEED_TRAIN = 110
AVG_SPEED_BUS = 70
AVG_SPEED_PLANE = 750
AVG_SPEED_LOCAL_TRANSFER = 30  # taxi / navette gare-aéroport -> hébergement

# Temps fixes incompressibles (minutes)
BUFFER_TRAIN_MIN = 20      # accès quai / correspondances
BUFFER_BUS_MIN = 15
BUFFER_PLANE_MIN = 120     # enregistrement + sécurité + embarquement

# Distances limites de pertinence par mode (km)
MAX_DISTANCE_BUS = 1500
MAX_DISTANCE_TRAIN = 2000
MIN_DISTANCE_PLANE = 80

# Emissions moyennes de CO2 (grammes / passager / km) — ordres de grandeur
# couramment utilisés pour la sensibilisation environnementale (moyennes
# ADEME / AIE), à titre indicatif et pédagogique.
CO2_TRAIN_G_KM = 4
CO2_BUS_G_KM = 30
CO2_PLANE_SHORT_G_KM = 230   # vol < 1000 km (décollage/atterrissage pèsent plus sur le court)
CO2_PLANE_LONG_G_KM = 115    # vol >= 1000 km

# Score de confort indicatif par mode (sur 10), utilisé dans le score global
COMFORT_SCORE = {"Train": 9, "Avion": 8, "Bus": 6}

# Tarification indicative par étoile (prix moyen/nuit en euros, avant variation régionale)
HOTEL_BASE_PRICE = {1: 45, 2: 60, 3: 85, 4: 130, 5: 220}

# Multiplicateurs de coût de la vie pour quelques destinations connues
# (valeur par défaut = 1.0 pour toute ville non répertoriée)
CITY_COST_MULTIPLIER = {
    "paris": 1.7, "londres": 1.8, "london": 1.8, "geneve": 1.9, "genève": 1.9,
    "zurich": 1.9, "new york": 2.0, "tokyo": 1.6, "amsterdam": 1.5,
    "nice": 1.4, "biarritz": 1.4, "chamonix": 1.5, "venise": 1.6, "venice": 1.6,
    "marrakech": 0.6, "tunis": 0.5, "prague": 0.7, "lisbonne": 0.9, "lisbon": 0.9,
}
DEFAULT_COST_MULTIPLIER = 1.0

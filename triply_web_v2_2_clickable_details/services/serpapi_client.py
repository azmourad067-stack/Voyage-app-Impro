from __future__ import annotations

from datetime import date, datetime, time as dt_time, timezone
from typing import Any
from urllib.parse import urlparse
import re
import time
import unicodedata
import requests

from .models import TravelOffer


class SerpApiError(RuntimeError):
    pass


class SerpApiClient:
    BASE_URL = "https://serpapi.com/search.json"
    ACCOUNT_URL = "https://serpapi.com/account.json"

    def __init__(
        self,
        api_key: str,
        connect_timeout: int = 10,
        read_timeout: int = 75,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Triply/2.2 Streamlit travel search",
                "Accept": "application/json",
            }
        )

    def _request(self, engine: str, **params: Any) -> dict[str, Any]:
        payload = {"engine": engine, "api_key": self.api_key, **params}
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(
                    self.BASE_URL,
                    params=payload,
                    timeout=(self.connect_timeout, self.read_timeout),
                )
            except requests.Timeout as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(1.5 * attempt)
                    continue
                raise SerpApiError(
                    f"SerpAPI n'a pas répondu après {self.max_retries} tentative(s)."
                ) from exc
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(1.5 * attempt)
                    continue
                raise SerpApiError(f"connexion impossible : {exc}") from exc

            if response.status_code == 401:
                raise SerpApiError("clé SERPAPI_KEY invalide")

            if response.status_code == 429:
                if attempt < self.max_retries:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else 2.0 * attempt
                    except ValueError:
                        delay = 2.0 * attempt
                    time.sleep(min(delay, 10.0))
                    continue
                raise SerpApiError("quota ou limite temporaire SerpAPI dépassé")

            if response.status_code in {408, 500, 502, 503, 504}:
                if attempt < self.max_retries:
                    time.sleep(1.5 * attempt)
                    continue
                raise SerpApiError(
                    f"SerpAPI temporairement indisponible ({response.status_code})"
                )

            if not response.ok:
                raise SerpApiError(
                    f"requête SerpAPI refusée ({response.status_code})"
                )

            try:
                data = response.json()
            except ValueError as exc:
                if attempt < self.max_retries:
                    time.sleep(1.0 * attempt)
                    continue
                raise SerpApiError("réponse SerpAPI non JSON") from exc

            if data.get("error"):
                raise SerpApiError(str(data["error"]))

            return data

        raise SerpApiError(f"échec SerpAPI : {last_error}")

    def account_status(self) -> dict[str, Any]:
        try:
            response = self.session.get(
                self.ACCOUNT_URL,
                params={"api_key": self.api_key},
                timeout=(self.connect_timeout, min(self.read_timeout, 30)),
            )
        except requests.RequestException as exc:
            raise SerpApiError(f"connexion impossible : {exc}") from exc

        if response.status_code in (401, 403):
            raise SerpApiError("clé SERPAPI_KEY invalide")
        if not response.ok:
            raise SerpApiError(f"vérification impossible ({response.status_code})")

        data = response.json()
        if data.get("error"):
            raise SerpApiError(str(data["error"]))
        return data

    def resolve_flight_location(self, city: str) -> dict[str, Any] | None:
        data = self._request(
            "google_flights_autocomplete",
            q=city,
            hl="fr",
            gl="fr",
            exclude_regions="true",
        )
        suggestions = data.get("suggestions") or []
        if not suggestions:
            return None

        wanted = city.strip().casefold()

        def score(item: dict[str, Any]) -> tuple[int, int]:
            name = str(item.get("name", "")).casefold()
            exact = 0 if name == wanted or name.startswith(wanted + ",") else 1
            city_type = 0 if item.get("type") == "city" else 1
            return (exact, city_type)

        best = sorted(suggestions, key=score)[0]
        airports = [
            {"id": a.get("id"), "name": a.get("name"), "city": a.get("city")}
            for a in (best.get("airports") or [])
            if a.get("id")
        ]

        return {
            "name": best.get("name") or city,
            "id": best.get("id"),
            "description": best.get("description", ""),
            "airports": airports,
        }

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date,
        adults: int,
        max_budget: float | None = None,
    ) -> tuple[list[TravelOffer], dict[str, Any], dict[str, Any]]:
        origin_loc = self.resolve_flight_location(origin)
        destination_loc = self.resolve_flight_location(destination)

        if not origin_loc:
            raise SerpApiError(f"ville de départ introuvable : {origin}")
        if not destination_loc:
            raise SerpApiError(f"destination introuvable : {destination}")
        if not origin_loc.get("id"):
            raise SerpApiError(f"aucun identifiant Google Flights pour {origin}")
        if not destination_loc.get("id"):
            raise SerpApiError(f"aucun identifiant Google Flights pour {destination}")

        data = self._request(
            "google_flights",
            departure_id=origin_loc["id"],
            arrival_id=destination_loc["id"],
            outbound_date=departure_date.isoformat(),
            return_date=return_date.isoformat(),
            adults=adults,
            type=1,
            travel_class=1,
            currency="EUR",
            hl="fr",
            gl="fr",
        )

        rows = (data.get("best_flights") or []) + (data.get("other_flights") or [])
        offers: list[TravelOffer] = []
        google_flights_url = (
            (data.get("search_metadata") or {}).get("google_flights_url")
            or (data.get("search_metadata") or {}).get("google_url")
        )

        for row in rows:
            price = _to_float(row.get("price"))
            if price is None:
                continue
            if max_budget is not None and price > max_budget:
                continue

            flights = row.get("flights") or []
            airline_names: list[str] = []
            summary_segments: list[str] = []
            outbound_segments: list[dict[str, Any]] = []

            for flight in flights:
                airline = flight.get("airline")
                if airline and airline not in airline_names:
                    airline_names.append(str(airline))

                dep = flight.get("departure_airport") or {}
                arr = flight.get("arrival_airport") or {}
                dep_id = dep.get("id", "?")
                arr_id = arr.get("id", "?")
                summary_segments.append(f"{dep_id}→{arr_id}")

                outbound_segments.append(
                    {
                        "departure_airport": {
                            "name": dep.get("name"),
                            "id": dep.get("id"),
                            "time": dep.get("time"),
                        },
                        "arrival_airport": {
                            "name": arr.get("name"),
                            "id": arr.get("id"),
                            "time": arr.get("time"),
                        },
                        "duration": flight.get("duration"),
                        "airline": flight.get("airline"),
                        "flight_number": flight.get("flight_number"),
                        "airplane": flight.get("airplane"),
                        "travel_class": flight.get("travel_class"),
                        "legroom": flight.get("legroom"),
                        "extensions": flight.get("extensions") or [],
                    }
                )

            layovers = row.get("layovers") or []
            total_duration = row.get("total_duration")
            emissions = (row.get("carbon_emissions") or {}).get("this_flight")

            detail_parts = []
            if summary_segments:
                detail_parts.append(" · ".join(summary_segments))
            if total_duration:
                detail_parts.append(_format_minutes(total_duration))
            detail_parts.append(
                f"{len(layovers)} escale(s)" if layovers else "direct ou sans escale listée"
            )

            metadata = {
                "outbound_segments": outbound_segments,
                "layovers": layovers,
                "total_duration": total_duration,
                "carbon_emissions": row.get("carbon_emissions") or {},
                "extensions": row.get("extensions") or [],
                "departure_token": row.get("departure_token"),
                "flight_search": {
                    "origin_id": origin_loc["id"],
                    "destination_id": destination_loc["id"],
                    "outbound_date": departure_date.isoformat(),
                    "return_date": return_date.isoformat(),
                    "adults": adults,
                },
            }

            offers.append(
                TravelOffer(
                    category="transport",
                    subtype="flight",
                    provider=", ".join(airline_names) if airline_names else "Google Flights",
                    title=f"Vol {origin_loc['name']} ↔ {destination_loc['name']}",
                    price_total=price,
                    currency="EUR",
                    url=google_flights_url,
                    details=" · ".join(detail_parts),
                    confidence=0.95,
                    metadata=metadata,
                )
            )

        return (
            _dedupe_offers(sorted(offers, key=lambda x: x.price_total or 10**9)),
            origin_loc,
            destination_loc,
        )

    def get_return_flight_options(
        self,
        offer: TravelOffer,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        metadata = offer.metadata or {}
        token = metadata.get("departure_token")
        context = metadata.get("flight_search") or {}
        if not token or not context:
            return []

        data = self._request(
            "google_flights",
            departure_id=context["origin_id"],
            arrival_id=context["destination_id"],
            outbound_date=context["outbound_date"],
            return_date=context["return_date"],
            adults=context["adults"],
            type=1,
            travel_class=1,
            currency="EUR",
            hl="fr",
            gl="fr",
            departure_token=token,
        )
        rows = (data.get("best_flights") or []) + (data.get("other_flights") or [])
        output: list[dict[str, Any]] = []

        for row in rows[:limit]:
            segments = []
            for flight in row.get("flights") or []:
                dep = flight.get("departure_airport") or {}
                arr = flight.get("arrival_airport") or {}
                segments.append(
                    {
                        "departure_airport": dep,
                        "arrival_airport": arr,
                        "duration": flight.get("duration"),
                        "airline": flight.get("airline"),
                        "flight_number": flight.get("flight_number"),
                        "airplane": flight.get("airplane"),
                        "travel_class": flight.get("travel_class"),
                        "extensions": flight.get("extensions") or [],
                    }
                )
            output.append(
                {
                    "price": _to_float(row.get("price")),
                    "total_duration": row.get("total_duration"),
                    "segments": segments,
                    "layovers": row.get("layovers") or [],
                    "booking_token": row.get("booking_token"),
                }
            )
        return output

    def search_hotels(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        adults: int,
        max_budget: float | None = None,
        vacation_rentals: bool = False,
    ) -> list[TravelOffer]:
        params: dict[str, Any] = {
            "q": destination,
            "check_in_date": check_in.isoformat(),
            "check_out_date": check_out.isoformat(),
            "adults": adults,
            "children": 0,
            "currency": "EUR",
            "hl": "fr",
            "gl": "fr",
        }
        if vacation_rentals:
            params["vacation_rentals"] = "true"

        data = self._request("google_hotels", **params)
        properties = data.get("properties") or []
        nights = max(1, (check_out - check_in).days)

        offers: list[TravelOffer] = []
        for prop in properties:
            total_rate = prop.get("total_rate") or {}
            nightly_rate = prop.get("rate_per_night") or {}

            total = _to_float(total_rate.get("extracted_lowest"))
            confidence = 0.95
            if total is None:
                nightly = _to_float(nightly_rate.get("extracted_lowest"))
                if nightly is not None:
                    total = nightly * nights
                    confidence = 0.85

            if total is None:
                continue
            if max_budget is not None and total > max_budget:
                continue

            ptype = str(prop.get("type") or "").lower()
            subtype = (
                "vacation_rental"
                if vacation_rentals or "vacation" in ptype
                else "hotel"
            )

            price_sources = prop.get("prices") or []
            provider = "Google Hotels"
            direct_url = prop.get("link")
            if price_sources:
                provider = price_sources[0].get("source") or provider
                direct_url = price_sources[0].get("link") or direct_url

            rating = prop.get("overall_rating")
            reviews = prop.get("reviews")
            hotel_class = prop.get("hotel_class")
            amenities = prop.get("amenities") or []
            essential = prop.get("essential_info") or []

            detail_parts = []
            if hotel_class:
                detail_parts.append(f"{hotel_class}★")
            if rating:
                rating_text = f"note {rating}/5"
                if reviews:
                    rating_text += f" ({reviews} avis)"
                detail_parts.append(rating_text)
            if essential:
                detail_parts.extend(str(x) for x in essential[:2])
            elif amenities:
                detail_parts.append(", ".join(str(x) for x in amenities[:3]))

            metadata = {
                "description": prop.get("description"),
                "address": prop.get("address"),
                "gps_coordinates": prop.get("gps_coordinates") or {},
                "check_in_time": prop.get("check_in_time"),
                "check_out_time": prop.get("check_out_time"),
                "amenities": amenities,
                "essential_info": essential,
                "nearby_places": prop.get("nearby_places") or [],
                "property_token": prop.get("property_token"),
                "directions": prop.get("directions"),
                "phone": prop.get("phone"),
                "hotel_class": hotel_class,
                "overall_rating": rating,
                "reviews": reviews,
                "prices": price_sources,
                "hotel_search": {
                    "destination": destination,
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat(),
                    "adults": adults,
                    "vacation_rentals": vacation_rentals,
                },
            }

            offers.append(
                TravelOffer(
                    category="lodging",
                    subtype=subtype,
                    provider=str(provider),
                    title=prop.get("name") or "Hébergement",
                    price_total=total,
                    currency="EUR",
                    url=direct_url,
                    details=" · ".join(detail_parts) or f"{nights} nuit(s)",
                    confidence=confidence,
                    metadata=metadata,
                )
            )

        return _dedupe_offers(sorted(offers, key=lambda x: x.price_total or 10**9))

    def get_hotel_details(self, offer: TravelOffer) -> dict[str, Any]:
        metadata = offer.metadata or {}
        token = metadata.get("property_token")
        context = metadata.get("hotel_search") or {}
        if not token or not context:
            return metadata

        params: dict[str, Any] = {
            "q": context["destination"],
            "check_in_date": context["check_in"],
            "check_out_date": context["check_out"],
            "adults": context["adults"],
            "children": 0,
            "currency": "EUR",
            "hl": "fr",
            "gl": "fr",
            "property_token": token,
        }
        if context.get("vacation_rentals"):
            params["vacation_rentals"] = "true"

        data = self._request("google_hotels", **params)

        # La réponse Property Details est principalement plate au niveau racine.
        return {
            "type": data.get("type"),
            "name": data.get("name") or offer.title,
            "description": data.get("description") or metadata.get("description"),
            "link": data.get("link") or offer.url,
            "address": data.get("address") or metadata.get("address"),
            "directions": data.get("directions") or metadata.get("directions"),
            "phone": data.get("phone") or metadata.get("phone"),
            "phone_link": data.get("phone_link"),
            "gps_coordinates": data.get("gps_coordinates")
            or metadata.get("gps_coordinates")
            or {},
            "check_in_time": data.get("check_in_time")
            or metadata.get("check_in_time"),
            "check_out_time": data.get("check_out_time")
            or metadata.get("check_out_time"),
            "rate_per_night": data.get("rate_per_night") or {},
            "total_rate": data.get("total_rate") or {},
            "prices": data.get("prices") or metadata.get("prices") or [],
            "featured_prices": data.get("featured_prices") or [],
            "nearby_places": data.get("nearby_places")
            or metadata.get("nearby_places")
            or [],
            "amenities": data.get("amenities") or metadata.get("amenities") or [],
            "essential_info": data.get("essential_info")
            or metadata.get("essential_info")
            or [],
            "hotel_class": data.get("hotel_class") or metadata.get("hotel_class"),
            "overall_rating": data.get("overall_rating")
            or metadata.get("overall_rating"),
            "reviews": data.get("reviews") or metadata.get("reviews"),
        }

    def search_airbnb_links(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        adults: int,
    ) -> list[TravelOffer]:
        query = (
            f'site:airbnb.fr "{destination}" '
            f'{check_in.isoformat()} {check_out.isoformat()} '
            f'{adults} voyageurs'
        )
        data = self._request("google", q=query, hl="fr", gl="fr", num=6)
        offers: list[TravelOffer] = []

        for item in data.get("organic_results") or []:
            title = item.get("title") or "Airbnb"
            snippet = item.get("snippet") or ""
            link = item.get("link")
            amount = _extract_euro_amount(f"{title} {snippet}")

            details = _compact(snippet)
            if amount is not None:
                details += f" · tarif aperçu : {amount:.2f} € (unité à vérifier)"

            offers.append(
                TravelOffer(
                    category="lodging",
                    subtype="airbnb",
                    provider=_provider_name(link) or "Airbnb",
                    title=title,
                    price_total=None,
                    currency="EUR",
                    url=link,
                    details=details,
                    confidence=0.45,
                    metadata={
                        "snippet": snippet,
                        "destination": destination,
                        "check_in": check_in.isoformat(),
                        "check_out": check_out.isoformat(),
                        "adults": adults,
                    },
                )
            )
        return offers

    def search_ground_transport(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date,
        adults: int,
    ) -> list[TravelOffer]:
        """
        Découverte de prix train/bus via Google Search.
        Cette couche reste indicative. Les horaires/gares exacts sont chargés
        au clic via Google Maps Directions.
        """
        queries = [
            (
                "train",
                f'"{origin}" "{destination}" train aller retour '
                f'{departure_date.isoformat()} {return_date.isoformat()} prix EUR',
            ),
            (
                "bus",
                f'"{origin}" "{destination}" bus aller retour '
                f'{departure_date.isoformat()} {return_date.isoformat()} prix EUR',
            ),
        ]

        output: list[TravelOffer] = []
        for subtype, query in queries:
            data = self._request("google", q=query, hl="fr", gl="fr", num=6)
            for item in data.get("organic_results") or []:
                title = item.get("title") or subtype.title()
                snippet = item.get("snippet") or ""
                link = item.get("link")
                full_text = f"{title} {snippet}"

                # Evite les faux positifs vus en production (ex. Paris→Milan
                # dans une recherche Paris→Rome, ou Air France classé "Train").
                if not _route_mentions_both(full_text, origin, destination):
                    continue
                if not _looks_like_mode(full_text, subtype):
                    continue

                text_lower = _normalize_text(full_text)
                extracted = _extract_euro_amount(full_text)
                total_markers = [
                    "aller-retour",
                    "aller retour",
                    "a/r",
                    "prix total",
                    "cout total",
                    "coût total",
                    "total",
                ]
                price_total = (
                    extracted
                    if extracted is not None
                    and any(_normalize_text(m) in text_lower for m in total_markers)
                    else None
                )

                details = _compact(snippet)
                if extracted is not None and price_total is None:
                    details += (
                        f" · tarif aperçu : {extracted:.2f} € "
                        "(total aller-retour non garanti)"
                    )

                output.append(
                    TravelOffer(
                        category="transport",
                        subtype=subtype,
                        provider=_provider_name(link) or "Résultat web",
                        title=f"{subtype.title()} {origin} ↔ {destination}",
                        price_total=price_total,
                        currency="EUR",
                        url=link,
                        details=details,
                        confidence=0.68 if price_total is not None else 0.4,
                        metadata={
                            "web_title": title,
                            "snippet": snippet,
                            "route_search": {
                                "origin": origin,
                                "destination": destination,
                                "departure_date": departure_date.isoformat(),
                                "return_date": return_date.isoformat(),
                                "adults": adults,
                                "mode": subtype,
                            },
                        },
                    )
                )

        return _dedupe_offers(output)

    def get_ground_transport_details(
        self,
        offer: TravelOffer,
        max_routes: int = 3,
    ) -> dict[str, Any]:
        context = (offer.metadata or {}).get("route_search") or {}
        if not context:
            return {"outbound": [], "return": [], "note": "Contexte de trajet manquant."}

        mode = context.get("mode") or offer.subtype
        prefer = "train" if mode == "train" else "bus"

        outbound = self._get_transit_directions(
            start=context["origin"],
            end=context["destination"],
            trip_date=date.fromisoformat(context["departure_date"]),
            prefer=prefer,
            max_routes=max_routes,
        )
        inbound = self._get_transit_directions(
            start=context["destination"],
            end=context["origin"],
            trip_date=date.fromisoformat(context["return_date"]),
            prefer=prefer,
            max_routes=max_routes,
        )

        return {
            "outbound": outbound,
            "return": inbound,
            "mode": mode,
            "note": (
                "Horaires issus de Google Maps Directions autour de 10:00 heure "
                "locale/approximative pour la date choisie. Vérifie le billet final "
                "chez l'opérateur."
            ),
        }

    def _get_transit_directions(
        self,
        start: str,
        end: str,
        trip_date: date,
        prefer: str,
        max_routes: int,
    ) -> list[dict[str, Any]]:
        # 08:00 UTC produit généralement une recherche matinale/fin de matinée
        # en Europe. Google Maps renvoie ensuite les heures locales de ses arrêts.
        timestamp = int(
            datetime.combine(
                trip_date,
                dt_time(hour=8, minute=0),
                tzinfo=timezone.utc,
            ).timestamp()
        )

        data = self._request(
            "google_maps_directions",
            start_addr=start,
            end_addr=end,
            travel_mode=3,
            prefer=prefer,
            route=2,
            time=f"depart_at:{timestamp}",
            distance_unit=0,
            hl="fr",
            gl="fr",
        )

        maps_url = (data.get("search_metadata") or {}).get(
            "google_maps_directions_url"
        )
        routes: list[dict[str, Any]] = []

        for direction in data.get("directions") or []:
            if str(direction.get("travel_mode", "")).lower() != "transit":
                continue

            trips = []
            for trip in direction.get("trips") or []:
                trip_mode = str(trip.get("travel_mode") or "")
                service = trip.get("service_run_by") or {}
                trips.append(
                    {
                        "travel_mode": trip_mode,
                        "title": trip.get("title"),
                        "duration": trip.get("formatted_duration"),
                        "start_stop": trip.get("start_stop") or {},
                        "end_stop": trip.get("end_stop") or {},
                        "stops": trip.get("stops") or [],
                        "operator": service.get("name"),
                        "operator_link": service.get("link"),
                        "route_information": service.get("route_information"),
                    }
                )

            routes.append(
                {
                    "start_time": direction.get("start_time"),
                    "end_time": direction.get("end_time"),
                    "duration": direction.get("formatted_duration"),
                    "distance": direction.get("formatted_distance"),
                    "cost": _to_float(direction.get("cost")),
                    "currency": direction.get("currency"),
                    "via": direction.get("via"),
                    "trips": trips,
                    "maps_url": maps_url,
                }
            )
            if len(routes) >= max_routes:
                break

        return routes


_EURO_PATTERNS = [
    re.compile(r"(?<!\d)(\d{1,5}(?:[.,]\d{1,2})?)\s*€"),
    re.compile(r"€\s*(\d{1,5}(?:[.,]\d{1,2})?)"),
    re.compile(r"(?<!\d)(\d{1,5}(?:[.,]\d{1,2})?)\s*(?:EUR|euros?)", re.I),
]


def _extract_euro_amount(text: str) -> float | None:
    candidates: list[float] = []
    for pattern in _EURO_PATTERNS:
        for match in pattern.findall(text):
            try:
                value = float(match.replace(",", "."))
            except ValueError:
                continue
            if 1 <= value <= 50000:
                candidates.append(value)
    return min(candidates) if candidates else None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(
            str(value)
            .replace("€", "")
            .replace("$", "")
            .replace(",", ".")
            .strip()
        )
    except (TypeError, ValueError):
        return None


def _format_minutes(value: Any) -> str:
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return str(value)
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h} h {m:02d}"
    if h:
        return f"{h} h"
    return f"{m} min"


def _provider_name(url: str | None) -> str | None:
    if not url:
        return None
    try:
        return urlparse(url).netloc.lower().removeprefix("www.") or None
    except Exception:
        return None


def _compact(text: str, max_len: int = 240) -> str:
    text = " ".join(str(text).split())
    if not text:
        return "Informations à vérifier sur le site source."
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text))
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return " ".join(normalized.casefold().split())


def _city_tokens(city: str) -> list[str]:
    city = _normalize_text(city)
    # On conserve surtout les mots significatifs du nom de ville.
    return [token for token in re.findall(r"[a-z0-9]+", city) if len(token) >= 3]


def _route_mentions_both(text: str, origin: str, destination: str) -> bool:
    haystack = _normalize_text(text)
    origin_tokens = _city_tokens(origin)
    destination_tokens = _city_tokens(destination)
    return (
        bool(origin_tokens)
        and bool(destination_tokens)
        and all(token in haystack for token in origin_tokens)
        and all(token in haystack for token in destination_tokens)
    )


def _looks_like_mode(text: str, subtype: str) -> bool:
    haystack = _normalize_text(text)
    flight_terms = [
        "vol ",
        " vols ",
        "flight",
        "air france",
        "easyjet",
        "ryanair",
        "compagnie aerienne",
        "avion",
    ]
    if any(term in haystack for term in flight_terms):
        return False

    if subtype == "train":
        train_terms = [
            "train",
            "rail",
            "sncf",
            "trenitalia",
            "tgv",
            "frecciarossa",
            "eurostar",
            "intercity",
            "intercite",
        ]
        return any(term in haystack for term in train_terms)

    bus_terms = [
        "bus",
        "coach",
        "autocar",
        "flixbus",
        "blablacar bus",
    ]
    return any(term in haystack for term in bus_terms)


def _dedupe_offers(items: list[TravelOffer]) -> list[TravelOffer]:
    seen: set[tuple[Any, ...]] = set()
    out: list[TravelOffer] = []
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
        out.append(item)
    return out

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import date, datetime
from typing import Any


@dataclass(slots=True)
class TravelOffer:
    category: str
    subtype: str
    provider: str
    title: str
    price_total: float | None
    currency: str = "EUR"
    url: str | None = None
    details: str = ""
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def confidence_label(self) -> str:
        if self.confidence >= 0.9:
            return "Prix structuré"
        if self.confidence >= 0.65:
            return "Prix indicatif"
        return "À vérifier"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TravelOffer":
        # Compatibilité avec les anciennes offres sauvegardées.
        payload = dict(data)
        payload.setdefault("metadata", {})
        return cls(**payload)


@dataclass(slots=True)
class TripSearchParams:
    origin: str
    destination: str
    departure_date: date
    return_date: date
    adults: int
    max_budget: float

    @property
    def nights(self) -> int:
        return max(1, (self.return_date - self.departure_date).days)

    def to_dict(self) -> dict[str, Any]:
        return {
            "origin": self.origin,
            "destination": self.destination,
            "departure_date": self.departure_date.isoformat(),
            "return_date": self.return_date.isoformat(),
            "adults": self.adults,
            "max_budget": self.max_budget,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TripSearchParams":
        return cls(
            origin=str(data["origin"]),
            destination=str(data["destination"]),
            departure_date=date.fromisoformat(str(data["departure_date"])),
            return_date=date.fromisoformat(str(data["return_date"])),
            adults=int(data["adults"]),
            max_budget=float(data["max_budget"]),
        )


@dataclass(slots=True)
class TripSearchResult:
    params: TripSearchParams
    transport_offers: list[TravelOffer]
    lodging_offers: list[TravelOffer]
    discovery_offers: list[TravelOffer]
    combinations: list[Any]
    warnings: list[str]
    origin_location: dict[str, Any] | None
    destination_location: dict[str, Any] | None
    searched_at: datetime

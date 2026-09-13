from __future__ import annotations

from dataclasses import dataclass
from .models import TravelOffer


@dataclass(slots=True)
class BudgetCombination:
    transport: TravelOffer
    lodging: TravelOffer
    total_price: float
    remaining_budget: float
    confidence: str

    @property
    def confidence_score(self) -> float:
        return min(self.transport.confidence, self.lodging.confidence)


def build_budget_combinations(
    transport_offers: list[TravelOffer],
    lodging_offers: list[TravelOffer],
    max_budget: float,
    limit: int = 60,
) -> list[BudgetCombination]:
    combos: list[BudgetCombination] = []

    priced_transports = [x for x in transport_offers if x.price_total is not None]
    priced_lodgings = [x for x in lodging_offers if x.price_total is not None]

    for transport in priced_transports:
        for lodging in priced_lodgings:
            total = float(transport.price_total) + float(lodging.price_total)
            if total > max_budget:
                continue

            min_conf = min(transport.confidence, lodging.confidence)
            if min_conf >= 0.9:
                confidence = "Élevée"
            elif min_conf >= 0.65:
                confidence = "Moyenne"
            else:
                confidence = "Faible"

            combos.append(
                BudgetCombination(
                    transport=transport,
                    lodging=lodging,
                    total_price=total,
                    remaining_budget=max_budget - total,
                    confidence=confidence,
                )
            )

    combos.sort(key=lambda x: (x.total_price, -x.confidence_score))
    return combos[:limit]

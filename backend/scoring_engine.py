"""
Scoring Engine: Multi-Criteria Decision Analysis (MCDA) for Location Suitability.

Ranks candidate localities within a spatial radius using normalized attributes
(affordability, crowd density, validated market activity, and transit access)
combined with business-specific profiles and competition strategies.
"""

from pathlib import Path
from typing import Dict, List
import json
import math


BUSINESS_TYPES = ["medical", "restaurant", "laptop", "mobile", "automobile", "stationary"]


class ScoringEngine:
    """Weighted multi-criteria scoring for location analysis."""

    CRITERIA = {
        "rent": {
            "name": "Affordability",
            "field": "rent_normalized",
            "description": "Lower rent = higher score",
            "default_weight": 0.25,
        },
        "crowd": {
            "name": "Crowd Density",
            "field": "crowd_normalized",
            "description": "More POIs/footfall = higher score",
            "default_weight": 0.25,
        },
        "competition": {
            "name": "Market Strength",
            "field": "competition_normalized",
            "description": "Higher existing market activity = stronger validated demand",
            "default_weight": 0.25,
        },
        "accessibility": {
            "name": "Accessibility",
            "field": "accessibility_normalized",
            "description": "More transit stops = higher score",
            "default_weight": 0.25,
        },
    }

    BUSINESS_WEIGHT_MODIFIERS = {
        "medical": {"rent": 1.0, "crowd": 0.8, "competition": 1.35, "accessibility": 1.55},
        "restaurant": {"rent": 1.0, "crowd": 1.5, "competition": 1.35, "accessibility": 1.0},
        "laptop": {"rent": 1.0, "crowd": 1.35, "competition": 1.35, "accessibility": 1.1},
        "mobile": {"rent": 1.0, "crowd": 1.3, "competition": 1.25, "accessibility": 1.15},
        "automobile": {"rent": 1.45, "crowd": 0.75, "competition": 1.35, "accessibility": 0.95},
        "stationary": {"rent": 1.1, "crowd": 1.25, "competition": 1.25, "accessibility": 1.35},
    }

    BUSINESS_COMPETITION_MODE = {
        "medical": "balanced",
        "restaurant": "demand_following",
        "laptop": "demand_following",
        "mobile": "balanced",
        "automobile": "opportunity",
        "stationary": "opportunity",
    }

    BUSINESS_SUPPORT_PROFILES = {
        "medical": {"rent_normalized": 0.2, "crowd_normalized": 0.1, "accessibility_normalized": 0.4, "competition_normalized": 0.3},
        "restaurant": {"rent_normalized": 0.2, "crowd_normalized": 0.45, "accessibility_normalized": 0.2, "competition_normalized": 0.15},
        "laptop": {"rent_normalized": 0.25, "crowd_normalized": 0.3, "accessibility_normalized": 0.2, "competition_normalized": 0.25},
        "mobile": {"rent_normalized": 0.2, "crowd_normalized": 0.35, "accessibility_normalized": 0.25, "competition_normalized": 0.2},
        "automobile": {"rent_normalized": 0.45, "crowd_normalized": 0.05, "accessibility_normalized": 0.2, "competition_normalized": 0.3},
        "stationary": {"rent_normalized": 0.2, "crowd_normalized": 0.25, "accessibility_normalized": 0.35, "competition_normalized": 0.2},
    }

    BUSINESS_SIGNAL_MULTIPLIER = {
        "medical": 0.12,
        "restaurant": 0.16,
        "laptop": 0.14,
        "mobile": 0.12,
        "automobile": 0.15,
        "stationary": 0.13,
    }

    def __init__(self, localities_data: Dict):
        self.localities = localities_data

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in km between two lat/lon points."""
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def validate_weights(weights: Dict[str, float]) -> bool:
        total = sum(weights.values())
        return 0.99 <= total <= 1.01

    def normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        total = sum(weights.values())
        if total == 0:
            return {k: 1.0 / len(weights) for k in weights}
        return {k: v / total for k, v in weights.items()}

    def compute_score(self, locality: Dict, weights: Dict[str, float]) -> float:
        """Compute weighted score for a locality using generic criteria."""
        score = 0.0
        for criterion, weight in weights.items():
            if criterion not in self.CRITERIA:
                continue
            field = self.CRITERIA[criterion]["field"]
            score += weight * locality.get(field, 0.0)
        return min(max(score, 0.0), 1.0)

    def _compute_competition_value(self, bt_signal: float, bt_strength: float, mode: str, demand_proxy: float) -> float:
        """Compute business-type-aware competition component."""
        if mode == "opportunity":
            target_presence = min(0.35, demand_proxy * 0.45)
        elif mode == "demand_following":
            target_presence = max(0.55, demand_proxy * 0.8)
        else:
            target_presence = 0.45

        presence_fit = max(0.0, 1.0 - abs(bt_signal - target_presence) / 0.65)

        if mode == "opportunity":
            mode_comp = 1.0 - bt_strength
        elif mode == "demand_following":
            mode_comp = bt_strength
        else:
            mode_comp = max(0.0, 1.0 - abs(bt_strength - 0.45) / 0.55)

        return min(max(0.55 * mode_comp + 0.45 * presence_fit, 0.0), 1.0)

    def rank_locations(
        self,
        reference_lat: float,
        reference_lon: float,
        search_radius_km: float,
        weights: Dict[str, float],
        limit: int = 10,
        business_type: str = None,
    ) -> List[Dict]:
        """Rank nearby localities based on criteria and business type."""
        weights = self.normalize_weights(weights)

        if business_type and business_type in self.BUSINESS_WEIGHT_MODIFIERS:
            mods = self.BUSINESS_WEIGHT_MODIFIERS[business_type]
            adjusted = {k: weights.get(k, 0) * mods.get(k, 1.0) for k in weights}
            weights = self.normalize_weights(adjusted)

        candidates = []
        max_bt_count = 0
        for locality_id, locality in self.localities["localities"].items():
            lat = locality.get("lat")
            lon = locality.get("lon")
            if lat is None or lon is None:
                continue

            dist_km = self._haversine(reference_lat, reference_lon, lat, lon)
            if dist_km > search_radius_km:
                continue

            candidates.append((locality_id, locality, dist_km))
            if business_type:
                bt_count = locality.get("business_types", {}).get(business_type, 0)
                if bt_count > max_bt_count:
                    max_bt_count = bt_count

        nearby = []

        for locality_id, locality, dist_km in candidates:
            lat = locality["lat"]
            lon = locality["lon"]

            if business_type in BUSINESS_TYPES:
                bt_count = locality.get("business_types", {}).get(business_type, 0)
                bt_signal = locality.get(f"{business_type}_normalized", 0.0)
                bt_strength = (bt_count / max_bt_count) if max_bt_count > 0 else 0.0
                shop_count = max(locality.get("shops", 0), 1)
                bt_share = min(1.0, bt_count / shop_count)

                crowd = locality.get("crowd_normalized", 0.0)
                access = locality.get("accessibility_normalized", 0.0)
                demand_proxy = (0.55 * crowd) + (0.45 * access)

                mode = self.BUSINESS_COMPETITION_MODE.get(business_type, "balanced")
                competition_value = self._compute_competition_value(bt_signal, bt_strength, mode, demand_proxy)

                score = 0.0
                for criterion, weight in weights.items():
                    if criterion not in self.CRITERIA:
                        continue
                    if criterion == "competition":
                        score += weight * competition_value
                    else:
                        field = self.CRITERIA[criterion]["field"]
                        score += weight * locality.get(field, 0.0)

                support_profile = self.BUSINESS_SUPPORT_PROFILES.get(business_type, {})
                support_score = 0.0
                for field_name, field_weight in support_profile.items():
                    support_score += locality.get(field_name, 0.0) * field_weight

                support_bonus = support_score * 0.15
                type_signal_bonus = bt_signal * self.BUSINESS_SIGNAL_MULTIPLIER.get(business_type, 0.1)

                if mode == "opportunity":
                    mode_bonus = (1.0 - bt_share) * 0.08
                    low_presence_penalty = 0.0
                elif mode == "demand_following":
                    mode_bonus = bt_share * 0.1
                    low_presence_penalty = 0.08 if bt_count == 0 else 0.0
                else:
                    mode_bonus = max(0.0, 1.0 - abs(bt_share - 0.45) / 0.55) * 0.08
                    low_presence_penalty = 0.04 if bt_count == 0 else 0.0

                rent_confidence = float(locality.get("rent_confidence", 0.5))
                confidence_factor = 0.88 + 0.12 * min(max(rent_confidence, 0.0), 1.0)

                score = (score + support_bonus + type_signal_bonus + mode_bonus - low_presence_penalty) * confidence_factor
                score = min(max(score, 0.0), 1.0)
            else:
                score = self.compute_score(locality, weights)
                competition_value = locality.get("competition_normalized", 0)
                bt_signal = 0.0
                bt_strength = 0.0
                mode = "general"

            breakdown = {
                "rent": weights.get("rent", 0) * locality.get("rent_normalized", 0),
                "crowd": weights.get("crowd", 0) * locality.get("crowd_normalized", 0),
                "competition": weights.get("competition", 0) * competition_value,
                "accessibility": weights.get("accessibility", 0) * locality.get("accessibility_normalized", 0),
            }

            nearby.append(
                {
                    "id": locality_id,
                    "name": locality.get("name", "Unknown"),
                    "locality_name": locality.get("locality_name", ""),
                    "lat": lat,
                    "lon": lon,
                    "display_lat": locality.get("actual_lat", lat),
                    "display_lon": locality.get("actual_lon", lon),
                    "score": score,
                    "score_percent": round(score * 100, 1),
                    "breakdown": breakdown,
                    "distance_km": round(dist_km, 2),
                    "features": {
                        "poi_count": locality.get("poi_count", 0),
                        "transit_stops": locality.get("transit_stops", 0),
                        "bus_stops": locality.get("bus_stops", 0),
                        "metro_stops": locality.get("metro_stops", 0),
                        "rent": locality.get("rent", "N/A"),
                        "rent_source": locality.get("rent_source", "unknown"),
                        "rent_confidence": locality.get("rent_confidence", 0.0),
                        "shops": locality.get("shops", 0),
                        "amenities": locality.get("amenities", 0),
                        "business_types": locality.get("business_types", {}),
                        "business_type_signal": round(bt_signal, 3),
                        "business_type_strength": round(bt_strength, 3),
                    },
                    "constraint_details": {
                        "affordability": {
                            "label": "Affordability (Lower Rent is Better)",
                            "rent_amount": f"Rs {locality.get('rent', 0):.0f}" if isinstance(locality.get("rent"), (int, float)) else "N/A",
                            "normalized_score": round(locality.get("rent_normalized", 0) * 100, 1),
                            "confidence": round(float(locality.get("rent_confidence", 0.0)) * 100, 1),
                            "source": locality.get("rent_source", "unknown"),
                        },
                        "crowd_density": {
                            "label": "Crowd Density (Footfall Activity)",
                            "poi_count": locality.get("poi_count", 0),
                            "normalized_score": round(locality.get("crowd_normalized", 0) * 100, 1),
                        },
                        "competition": {
                            "label": (
                                (
                                    f"Opportunity (Lower {business_type.title()} Competition)"
                                    if self.BUSINESS_COMPETITION_MODE.get(business_type, "balanced") == "opportunity"
                                    else f"Demand Signal ({business_type.title()} Market Presence)"
                                    if self.BUSINESS_COMPETITION_MODE.get(business_type, "balanced") == "demand_following"
                                    else f"Market Fit ({business_type.title()} Balance)"
                                )
                                if business_type
                                else "Market Strength (General Competition Density)"
                            ),
                            "shop_count": locality.get("business_types", {}).get(business_type, locality.get("shops", 0)) if business_type else locality.get("shops", 0),
                            "normalized_score": round(competition_value * 100, 1),
                            "business_type_signal": round(bt_signal * 100, 1),
                        },
                        "accessibility": {
                            "label": "Accessibility (Public Transit)",
                            "transit_stops": locality.get("transit_stops", 0),
                            "bus_stops": locality.get("bus_stops", 0),
                            "metro_stops": locality.get("metro_stops", 0),
                            "normalized_score": round(locality.get("accessibility_normalized", 0) * 100, 1),
                        },
                    },
                }
            )

        nearby.sort(key=lambda x: x["score"], reverse=True)

        unique_results = []
        seen_names = set()
        for row in nearby:
            key = (row.get("locality_name") or row.get("name") or row.get("id") or "").strip().lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            unique_results.append(row)

        top_candidates = unique_results[:limit]
        try:
            try:
                from .decision_science import DecisionScienceEngine
            except ImportError:
                from decision_science import DecisionScienceEngine
            top_candidates = DecisionScienceEngine.run_topsis(top_candidates, weights)
            top_candidates = DecisionScienceEngine.calculate_huff_catchment(top_candidates, business_type)
        except Exception:
            pass

        return top_candidates

    def get_criterion_stats(self) -> Dict:
        """Get min/max/avg for each criterion across all localities."""
        stats = {}

        for criterion in self.CRITERIA.keys():
            field = self.CRITERIA[criterion]["field"]
            values = [locality.get(field, 0) for locality in self.localities["localities"].values()]
            values = [v for v in values if v is not None]

            if values:
                stats[criterion] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }

        return stats


def load_localities(path: Path) -> Dict:
    """Load processed localities from JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    localities_path = Path(__file__).parent.parent / "backend" / "localities.json"

    try:
        localities = load_localities(localities_path)
        engine = ScoringEngine(localities)

        results = engine.rank_locations(
            reference_lat=13.0062,
            reference_lon=80.2433,
            search_radius_km=5.0,
            weights={"rent": 0.3, "crowd": 0.3, "competition": 0.2, "accessibility": 0.2},
            limit=5,
            business_type="restaurant",
        )

        print("Top Ranked Locations:")
        for i, loc in enumerate(results, 1):
            print(f"\n{i}. {loc['name']} (Score: {loc['score_percent']}%)")
            print(f"   Breakdown: {loc['breakdown']}")
            print(f"   Distance: {loc['distance_km']:.2f} km")

    except FileNotFoundError:
        print("localities.json not found. Run data_processor.py first.")

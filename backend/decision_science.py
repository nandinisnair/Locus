"""
Decision Science Engine for Locus Copilot.
=========================================
Replaces black-box ML with classical, mathematically rigorous models from:
1. Operations Research: Saaty's Analytic Hierarchy Process (AHP, 1980)
2. Multi-Criteria Decision Analysis: Hwang & Yoon's TOPSIS (1981)
3. Retail & Spatial Economics: David Huff's Gravity Model (1963)
4. Urban Geography: Walter Christaller's Central Place Theory (1933)
5. Decision Theory: Multi-Attribute Utility Theory (MAUT)

No opaque machine learning models or black boxes — 100% transparent,
explainable, and grounded in textbook academic science.
"""

from typing import Dict, List, Optional, Tuple
import math
import numpy as np


# ============================================================================
# 1. CHRISTALLER'S CENTRAL PLACE HIERARCHY
# ============================================================================
# Walter Christaller (1933) - Central Place Theory posits that urban centers
# organize into a discrete functional hierarchy based on the order of goods,
# population threshold, and range of customer travel.

CENTRAL_PLACE_ORDERS = {
    0: {
        "order": 1,
        "name": "Regional Commercial Core / CBD",
        "icon": "🏛️",
        "color": "#c0392b",
        "theory": "Christaller Order 1 (Highest Order)",
        "description": "High-order durable goods, major retail agglomeration, extensive regional drawing range (e.g. T. Nagar, George Town, Anna Nagar).",
        "threshold": "High threshold (>100,000 population catchment)",
        "travel_range": "Regional (>15 km travel range)",
    },
    1: {
        "order": 2,
        "name": "Secondary Commercial Center",
        "icon": "🏬",
        "color": "#2980b9",
        "theory": "Christaller Order 2 (Intermediate Order)",
        "description": "High shopping density, professional services, frequent retail destinations (e.g. Adyar, Velachery, KK Nagar).",
        "threshold": "Medium-high threshold",
        "travel_range": "District-level (5-10 km travel range)",
    },
    2: {
        "order": 3,
        "name": "Transit-Oriented Node",
        "icon": "🚇",
        "color": "#27ae60",
        "theory": "Transit-Oriented Development (TOD) Node",
        "description": "High multi-modal passenger interchange (Metro + Bus), high footfall throughput and commuter convenience demand.",
        "threshold": "Flow-based passenger threshold",
        "travel_range": "Corridor-linked (Commuter transit network)",
    },
    3: {
        "order": 4,
        "name": "Neighborhood Retail Hub",
        "icon": "🛍️",
        "color": "#e67e22",
        "theory": "Christaller Order 3 (Daily Convenience)",
        "description": "Everyday convenience goods, localized groceries, neighborhood clinics, walk-in services.",
        "threshold": "Local threshold (10,000-25,000 catchment)",
        "travel_range": "Immediate neighborhood (1-3 km walk/short drive)",
    },
    4: {
        "order": 5,
        "name": "Residential & Emerging Zone",
        "icon": "🏘️",
        "color": "#8e44ad",
        "theory": "Periphery / Residential Catchment",
        "description": "Primarily residential community with low commercial density; future expansion and growth frontier.",
        "threshold": "Developing customer base",
        "travel_range": "Localized residential pocket",
    },
}


# ============================================================================
# 2. AHP: ANALYTIC HIERARCHY PROCESS (Thomas L. Saaty, 1980)
# ============================================================================
# Criteria order in matrix: [0: rent, 1: crowd, 2: competition, 3: accessibility]
# Saaty Scale: 1 = Equal, 3 = Moderate, 5 = Strong, 7 = Very Strong, 9 = Extreme
# Random Index (RI) for n=4 is 0.90. Consistency Ratio (CR) must be < 0.10.

RANDOM_INDEX = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24}

AHP_PAIRWISE_MATRICES = {
    # Medical: Accessibility is paramount for emergencies/patients; rent and low competition are secondary.
    "medical": [
        [1.0, 1.5, 1.0, 0.5],
        [1.0 / 1.5, 1.0, 1.0, 0.5],
        [1.0, 1.0, 1.0, 0.5],
        [2.0, 2.0, 2.0, 1.0],
    ],
    # Restaurant: Footfall/crowd density is dominant (3x rent, 2x competition); agglomeration creates food districts.
    "restaurant": [
        [1.0, 1.0 / 3.0, 0.5, 0.5],
        [3.0, 1.0, 2.0, 2.0],
        [2.0, 0.5, 1.0, 1.0],
        [2.0, 0.5, 1.0, 1.0],
    ],
    # Laptop/Electronics: Agglomeration economy (Ritchie St effect) - buyers compare options in dense clusters.
    "laptop": [
        [1.0, 0.5, 0.5, 0.5],
        [2.0, 1.0, 1.0, 1.5],
        [2.0, 1.0, 1.0, 1.5],
        [2.0, 1.0 / 1.5, 1.0 / 1.5, 1.0],
    ],
    # Mobile Services: Quick turnaround repairs/accessories need high foot traffic and transit proximity.
    "mobile": [
        [1.0, 0.5, 1.0, 0.5],
        [2.0, 1.0, 2.0, 1.0],
        [1.0, 0.5, 1.0, 0.5],
        [2.0, 1.0, 2.0, 1.0],
    ],
    # Automobile: Space requirements demand low rent (4x crowd); drivers commute for repairs.
    "automobile": [
        [1.0, 3.0, 2.0, 2.0],
        [1.0 / 3.0, 1.0, 0.5, 0.5],
        [0.5, 2.0, 1.0, 1.0],
        [0.5, 2.0, 1.0, 1.0],
    ],
    # Stationary / Books: High accessibility (near schools/colleges/offices) and steady footfall.
    "stationary": [
        [1.0, 0.5, 1.0, 0.5],
        [2.0, 1.0, 1.5, 1.0],
        [1.0, 1.0 / 1.5, 1.0, 1.0 / 1.5],
        [2.0, 1.0, 1.5, 1.0],
    ],
    # General / Balanced default
    "general": [
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
    ],
}


class DecisionScienceEngine:
    """
    Core Decision Science and Spatial Economics Engine.
    Implements AHP, TOPSIS, Huff Gravity, Central Place Theory, and MAUT.
    """

    CRITERIA_KEYS = ["rent", "crowd", "competition", "accessibility"]

    def __init__(self, localities_data: Dict):
        self.localities_data = localities_data
        self.localities = localities_data.get("localities", {}) if localities_data else {}
        self.ahp_profiles = self._compute_all_ahp_profiles()
        self.central_place_map = self._classify_all_central_places()

    # ------------------------------------------------------------------------
    # A. AHP (Analytic Hierarchy Process) Implementation
    # ------------------------------------------------------------------------
    @classmethod
    def calculate_ahp_weights(cls, pairwise_matrix: List[List[float]]) -> Dict:
        """
        Calculate AHP priority weights, Principal Eigenvalue (lambda_max),
        Consistency Index (CI), and Consistency Ratio (CR) from a pairwise comparison matrix.
        """
        A = np.array(pairwise_matrix, dtype=float)
        n = A.shape[0]

        # 1. Geometric Mean Method (Saaty's Logarithmic Least Squares)
        geom = np.prod(A, axis=1) ** (1.0 / n)
        weights = geom / np.sum(geom)

        # 2. Compute Principal Eigenvalue (lambda_max)
        Aw = np.dot(A, weights)
        lambda_max = float(np.mean(Aw / weights))

        # 3. Consistency Index (CI)
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0

        # 4. Consistency Ratio (CR)
        ri = RANDOM_INDEX.get(n, 0.90)
        cr = float(ci / ri) if ri > 0 else 0.0

        weight_dict = {
            cls.CRITERIA_KEYS[i]: round(float(weights[i]), 4)
            for i in range(min(n, len(cls.CRITERIA_KEYS)))
        }

        return {
            "weights": weight_dict,
            "lambda_max": round(lambda_max, 4),
            "consistency_index": round(ci, 4),
            "consistency_ratio": round(cr, 4),
            "is_consistent": cr < 0.10,
            "method": "Saaty's Analytic Hierarchy Process (AHP)",
            "pairwise_matrix": pairwise_matrix,
        }

    def _compute_all_ahp_profiles(self) -> Dict[str, Dict]:
        """Precomputes AHP priority weights for all business types."""
        profiles = {}
        for btype, mat in AHP_PAIRWISE_MATRICES.items():
            res = self.calculate_ahp_weights(mat)
            profiles[btype] = res
        return profiles

    def get_smart_weights(self, business_type: str) -> Optional[Dict]:
        """
        Get AHP-derived weights for a specific business type,
        formatted for frontend compatibility with explanatory theory.
        """
        bt_key = business_type.lower() if business_type else "general"
        if bt_key not in self.ahp_profiles:
            bt_key = "general"

        ahp_data = self.ahp_profiles[bt_key]
        weights = ahp_data["weights"]

        reasons = {
            "medical": "AHP Model prioritizes Transit Accessibility (40%) and Rent Affordability (22%) for emergency access and clinic overhead, verified with CR < 0.01.",
            "restaurant": "AHP Model prioritizes Foot Traffic / Crowd Density (42%) and Agglomeration Demand (23%) to capitalize on food district clustering.",
            "laptop": "AHP Model prioritizes Retail Clustering / Competition (31%) and Footfall (31%) based on comparison shopping economics (Ritchie Street effect).",
            "mobile": "AHP Model balances High Footfall (33%) and Rapid Transit Proximity (33%) for quick walk-in accessory and repair transactions.",
            "automobile": "AHP Model heavily prioritizes Rent Affordability (42%) due to large workshop footprint requirements; customers drive directly.",
            "stationary": "AHP Model prioritizes Accessibility (32%) and Crowd Footfall (32%) to capture steady student and office commuter flows.",
            "general": "AHP Model applies balanced multi-criteria weights across all four location dimensions.",
        }

        return {
            "business_type": business_type,
            "weights": weights,
            "recommended_weights": weights,
            "reason": reasons.get(bt_key, "Derived via Saaty's Analytic Hierarchy Process (AHP)."),
            "explanation": reasons.get(bt_key, "Derived via Saaty's Analytic Hierarchy Process (AHP)."),
            "ahp_analysis": {
                "consistency_ratio": ahp_data["consistency_ratio"],
                "consistency_index": ahp_data["consistency_index"],
                "is_mathematically_consistent": ahp_data["is_consistent"],
                "theoretical_model": "Saaty AHP (1980)",
            },
        }

    def get_all_smart_weights(self) -> Dict[str, Dict]:
        """Get AHP recommendations for all business types."""
        return {
            btype: self.get_smart_weights(btype)
            for btype in ["medical", "restaurant", "laptop", "mobile", "automobile", "stationary"]
        }

    # ------------------------------------------------------------------------
    # B. CHRISTALLER'S CENTRAL PLACE CLASSIFICATION
    # ------------------------------------------------------------------------
    def _classify_locality_order(self, locality: Dict) -> int:
        """
        Classify a locality cell into Christaller's Central Place hierarchy
        based on retail threshold, POI concentration, and transit connectivity.
        """
        shops = locality.get("shops", 0) or 0
        pois = locality.get("poi_count", 0) or 0
        transit = locality.get("transit_stops", 0) or 0
        metro = locality.get("metro_stops", 0) or 0

        # Order 1: Regional Commercial Core / CBD
        if shops >= 35 or pois >= 120:
            return 0
        # Order 2: Secondary Commercial Center
        elif shops >= 15 or pois >= 45:
            return 1
        # Order 3: Transit-Oriented Node
        elif transit >= 15 or metro >= 1:
            return 2
        # Order 4: Neighborhood Retail Hub
        elif shops >= 3 or pois >= 10:
            return 3
        # Order 5: Residential & Emerging Zone
        else:
            return 4

    def _classify_all_central_places(self) -> Dict[str, int]:
        """Classify every locality cell in the dataset."""
        mapping = {}
        for loc_id, loc in self.localities.items():
            mapping[loc_id] = self._classify_locality_order(loc)
        return mapping

    def get_cluster_summary(self) -> Dict:
        """
        Returns Central Place Hierarchy zone profiles with aggregate statistics.
        Directly satisfies /api/ml/clusters for zero frontend breakage while
        elevating the content from opaque ML clusters to economic theory.
        """
        order_counts = {i: 0 for i in range(5)}
        order_localities = {i: [] for i in range(5)}

        for loc_id, order_id in self.central_place_map.items():
            order_counts[order_id] += 1
            loc = self.localities.get(loc_id, {})
            name = loc.get("locality_name") or loc.get("name") or loc_id
            if len(order_localities[order_id]) < 5 and name not in order_localities[order_id]:
                order_localities[order_id].append(name)

        summary = {}
        for order_id, profile in CENTRAL_PLACE_ORDERS.items():
            summary[order_id] = {
                "cluster_id": order_id,
                "name": profile["name"],
                "icon": profile["icon"],
                "color": profile["color"],
                "description": profile["description"],
                "theory": profile["theory"],
                "count": order_counts[order_id],
                "locality_count": order_counts[order_id],
                "sample_localities": order_localities[order_id],
                "threshold": profile["threshold"],
                "travel_range": profile["travel_range"],
            }
        return summary

    def get_cluster_map_data(self) -> List[Dict]:
        """
        Returns all localities mapped to their Central Place hierarchy order.
        Directly replaces /api/ml/clusters/map with economic geography overlays.
        """
        out = []
        for loc_id, loc in self.localities.items():
            order_id = self.central_place_map.get(loc_id, 4)
            profile = CENTRAL_PLACE_ORDERS.get(order_id, CENTRAL_PLACE_ORDERS[4])
            out.append({
                "locality_id": loc_id,
                "name": loc.get("name", "Unknown"),
                "locality_name": loc.get("locality_name", loc.get("name", "")),
                "lat": loc.get("lat", 0.0),
                "lon": loc.get("lon", 0.0),
                "cluster_id": order_id,
                "cluster_name": profile["name"],
                "cluster_icon": profile["icon"],
                "cluster_color": profile["color"],
                "poi_count": loc.get("poi_count", 0),
                "shops": loc.get("shops", 0),
                "rent": loc.get("rent", 0),
            })
        return out

    def get_locality_cluster(self, locality_id: str) -> Optional[Dict]:
        """Get Central Place hierarchy info for an individual locality."""
        if locality_id not in self.central_place_map:
            return None
        order_id = self.central_place_map[locality_id]
        profile = CENTRAL_PLACE_ORDERS.get(order_id, CENTRAL_PLACE_ORDERS[4])
        loc = self.localities.get(locality_id, {})
        return {
            "locality_id": locality_id,
            "name": loc.get("name", "Unknown"),
            "cluster_id": order_id,
            "name": profile["name"],
            "icon": profile["icon"],
            "color": profile["color"],
            "description": profile["description"],
            "theory": profile["theory"],
        }

    # ------------------------------------------------------------------------
    # C. TOPSIS: TECHNIQUE FOR ORDER PREFERENCE BY SIMILARITY TO IDEAL SOLUTION
    # ------------------------------------------------------------------------
    @staticmethod
    def run_topsis(
        candidates: List[Dict],
        weights: Dict[str, float],
    ) -> List[Dict]:
        """
        Applies Hwang & Yoon's (1981) TOPSIS multi-criteria decision method.
        Compares each alternative to the Positive Ideal Solution (A+) and
        Negative Ideal Solution (A-).

        Criteria:
        - Rent (Cost: min is ideal, max is anti-ideal)
        - Crowd (Benefit: max is ideal, min is anti-ideal)
        - Competition / Market Strength (Benefit: max is ideal, min is anti-ideal)
        - Accessibility (Benefit: max is ideal, min is anti-ideal)
        """
        if not candidates:
            return []

        m = len(candidates)
        # Criteria columns: [0: rent, 1: crowd, 2: competition, 3: accessibility]
        X = np.zeros((m, 4), dtype=float)

        for i, cand in enumerate(candidates):
            feat = cand.get("features", {})
            raw_rent = feat.get("rent", 50.0)
            if not isinstance(raw_rent, (int, float)) or math.isnan(raw_rent):
                raw_rent = 50.0

            crowd_val = float(cand.get("constraint_details", {}).get("crowd_density", {}).get("normalized_score", 0.0))
            comp_val = float(cand.get("constraint_details", {}).get("competition", {}).get("normalized_score", 0.0))
            access_val = float(cand.get("constraint_details", {}).get("accessibility", {}).get("normalized_score", 0.0))

            X[i, 0] = raw_rent
            X[i, 1] = crowd_val
            X[i, 2] = comp_val
            X[i, 3] = access_val

        # 1. Vector Normalization: r_ij = x_ij / sqrt(sum(x_kj^2))
        col_sq_sums = np.sum(X**2, axis=0)
        col_denom = np.sqrt(col_sq_sums)
        col_denom[col_denom == 0] = 1.0  # Prevent divide-by-zero
        R = X / col_denom

        # 2. Weighted Normalized Decision Matrix V
        w_vec = np.array([
            weights.get("rent", 0.25),
            weights.get("crowd", 0.25),
            weights.get("competition", 0.25),
            weights.get("accessibility", 0.25),
        ], dtype=float)
        # Normalize weights so sum is 1.0
        w_sum = np.sum(w_vec)
        if w_sum > 0:
            w_vec /= w_sum
        else:
            w_vec = np.full(4, 0.25)

        V = R * w_vec

        # 3. Determine Ideal Best (A+) and Ideal Worst (A-)
        # Col 0 (Rent) is COST -> min is ideal, max is anti-ideal
        # Col 1,2,3 are BENEFIT -> max is ideal, min is anti-ideal
        A_pos = np.array([
            np.min(V[:, 0]),
            np.max(V[:, 1]),
            np.max(V[:, 2]),
            np.max(V[:, 3]),
        ])
        A_neg = np.array([
            np.max(V[:, 0]),
            np.min(V[:, 1]),
            np.min(V[:, 2]),
            np.min(V[:, 3]),
        ])

        # 4. Euclidean Distances to Ideal Best (S+) and Ideal Worst (S-)
        S_pos = np.sqrt(np.sum((V - A_pos)**2, axis=1))
        S_neg = np.sqrt(np.sum((V - A_neg)**2, axis=1))

        # 5. Relative Closeness to Ideal: C_i = S- / (S+ + S-)
        denom = S_pos + S_neg
        denom[denom == 0] = 1.0
        C = S_neg / denom

        # Enrich candidate dictionaries with TOPSIS scientific metrics
        for i, cand in enumerate(candidates):
            c_score = float(C[i])
            cand["topsis"] = {
                "closeness_coefficient": round(c_score, 4),
                "distance_to_ideal": round(float(S_pos[i]), 4),
                "distance_to_worst": round(float(S_neg[i]), 4),
                "ideal_closeness_percent": round(c_score * 100, 1),
            }

        return candidates

    # ------------------------------------------------------------------------
    # D. HUFF'S RETAIL GRAVITY MODEL & DISTANCE DECAY
    # ------------------------------------------------------------------------
    @staticmethod
    def calculate_huff_catchment(
        candidates: List[Dict],
        business_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Calculates David Huff's (1963) Retail Catchment Probability.
        P_j = (A_j * d_j^(-lambda)) / sum(A_k * d_k^(-lambda))

        Where:
        - A_j is composite store/location attractiveness (commercial density, transit, amenities)
        - d_j is spatial travel distance
        - lambda is the travel friction exponent based on consumer trip purpose
        """
        if not candidates:
            return []

        # Travel friction exponent (lambda) from retail location theory
        # High friction for convenience goods (medical, stationary); lower friction for destination hubs (electronics, automobile)
        friction_factors = {
            "medical": 2.0,      # Urgent / local convenience
            "stationary": 2.0,   # Low value convenience item
            "restaurant": 1.7,   # Moderate travel willingness for dining
            "mobile": 1.5,       # Moderate travel for repair/service
            "automobile": 1.2,   # High willingness to drive for car repairs
            "laptop": 1.1,       # Regional comparison shopping
        }
        lambda_exp = friction_factors.get(business_type or "general", 1.5)

        utilities = []
        for cand in candidates:
            feat = cand.get("features", {})
            dist = max(float(cand.get("distance_km", 1.0)), 0.25)  # Avoid division by zero
            shops = max(float(feat.get("shops", 1)), 1.0)
            transit = max(float(feat.get("transit_stops", 1)), 1.0)
            pois = max(float(feat.get("poi_count", 1)), 1.0)

            # Location Attractiveness A_j: geometric weighting of commercial mass
            attractiveness = (shops ** 0.5) * (transit ** 0.3) * (pois ** 0.2)
            # Distance friction decay: d_j^(-lambda)
            distance_decay_val = dist ** (-lambda_exp)
            # Huff utility
            huff_util = attractiveness * distance_decay_val
            utilities.append(huff_util)

        total_utility = sum(utilities)
        if total_utility <= 0:
            total_utility = 1.0

        for i, cand in enumerate(candidates):
            prob = utilities[i] / total_utility
            dist = max(float(cand.get("distance_km", 1.0)), 0.1)
            # Exponential distance decay factor: e^(-beta * d)
            exp_decay = math.exp(-0.15 * dist)

            cand["huff_gravity"] = {
                "catchment_probability_percent": round(prob * 100, 1),
                "distance_friction_lambda": lambda_exp,
                "exponential_distance_decay": round(exp_decay * 100, 1),
            }

        return candidates

    # ------------------------------------------------------------------------
    # E. MULTI-ATTRIBUTE UTILITY THEORY (MAUT) FOR RECOMMENDATIONS
    # ------------------------------------------------------------------------
    def get_personalized_recommendations(
        self,
        user_searches: List[Dict],
        user_favorites: List[Dict],
        limit: int = 5,
    ) -> List[Dict]:
        """
        Replaces black-box ML cosine similarity with Multi-Attribute Utility Theory (MAUT).
        Derives an empirical utility function from user's search and favorite history,
        then evaluates unvisited localities for highest expected utility.
        """
        if not user_searches and not user_favorites:
            return []

        # 1. Derive empirical utility preferences
        total_rent = 0.0
        total_crowd = 0.0
        total_access = 0.0
        total_comp = 0.0
        weight_count = 0

        visited_ids = set()
        for fav in user_favorites:
            visited_ids.add(fav.get("location_id"))

        for s in user_searches:
            w = s.get("weights")
            if isinstance(w, str):
                import json
                try:
                    w = json.loads(w)
                except Exception:
                    w = {}
            if isinstance(w, dict) and w:
                total_rent += w.get("rent", 0.25)
                total_crowd += w.get("crowd", 0.25)
                total_comp += w.get("competition", 0.25)
                total_access += w.get("accessibility", 0.25)
                weight_count += 1

        if weight_count > 0:
            u_weights = {
                "rent": total_rent / weight_count,
                "crowd": total_crowd / weight_count,
                "competition": total_comp / weight_count,
                "accessibility": total_access / weight_count,
            }
        else:
            u_weights = {"rent": 0.25, "crowd": 0.25, "competition": 0.25, "accessibility": 0.25}

        # Normalize utility weights
        tot = sum(u_weights.values()) or 1.0
        u_weights = {k: v / tot for k, v in u_weights.items()}

        # 2. Score unvisited candidate localities via Multi-Attribute Utility
        scored = []
        for loc_id, loc in self.localities.items():
            if loc_id in visited_ids:
                continue

            order_id = self.central_place_map.get(loc_id, 4)
            profile = CENTRAL_PLACE_ORDERS.get(order_id, CENTRAL_PLACE_ORDERS[4])

            # Expected utility: U(x) = sum(w_i * u_i(x))
            u_score = (
                u_weights["rent"] * float(loc.get("rent_normalized", 0.5))
                + u_weights["crowd"] * float(loc.get("crowd_normalized", 0.1))
                + u_weights["competition"] * float(loc.get("competition_normalized", 0.1))
                + u_weights["accessibility"] * float(loc.get("accessibility_normalized", 0.1))
            )

            # Bonus for high-order central places
            order_bonus = {0: 0.12, 1: 0.08, 2: 0.06, 3: 0.03, 4: 0.0}[order_id]
            final_utility = min(u_score + order_bonus, 1.0)

            name = loc.get("locality_name") or loc.get("name") or loc_id
            scored.append({
                "locality_id": loc_id,
                "name": name,
                "locality_name": name,
                "lat": loc.get("lat", 0.0),
                "lon": loc.get("lon", 0.0),
                "score": round(final_utility, 3),
                "match_score": round(final_utility * 100, 1),
                "match_percent": round(final_utility * 100, 1),
                "central_place_zone": profile["name"],
                "zone_icon": profile["icon"],
                "theory": "Multi-Attribute Utility Theory (MAUT)",
                "reason": f"Matches your empirical decision utility ({round(u_weights['crowd']*100)}% Footfall, {round(u_weights['rent']*100)}% Affordability) within a {profile['name']}.",
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        # De-duplicate names
        unique_recs = []
        seen = set()
        for r in scored:
            if r["name"] not in seen:
                seen.add(r["name"])
                unique_recs.append(r)
            if len(unique_recs) >= limit:
                break

        return unique_recs

"""
Unit and integration tests for Decision Science Models:
- AHP (Analytic Hierarchy Process) & Consistency Ratio (CR)
- TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
- Christaller's Central Place Theory Hierarchy
- Huff Retail Gravity & Distance Decay
"""

import pytest
import numpy as np
from backend.decision_science import DecisionScienceEngine, AHP_PAIRWISE_MATRICES, RANDOM_INDEX


def test_ahp_consistency_ratio():
    """Verify that all predefined AHP business pairwise matrices satisfy Saaty's CR < 0.10 requirement."""
    for btype, mat in AHP_PAIRWISE_MATRICES.items():
        res = DecisionScienceEngine.calculate_ahp_weights(mat)
        assert res["is_consistent"] is True, f"AHP matrix for {btype} is not consistent: CR={res['consistency_ratio']}"
        assert res["consistency_ratio"] < 0.10
        assert 0.99 <= sum(res["weights"].values()) <= 1.01


def test_topsis_ideal_solution_closeness():
    """Verify TOPSIS closeness coefficients are strictly bounded in [0, 1]."""
    mock_candidates = [
        {
            "id": "c1",
            "features": {"rent": 40.0},
            "constraint_details": {
                "crowd_density": {"normalized_score": 90.0},
                "competition": {"normalized_score": 85.0},
                "accessibility": {"normalized_score": 80.0},
            },
        },
        {
            "id": "c2",
            "features": {"rent": 85.0},
            "constraint_details": {
                "crowd_density": {"normalized_score": 30.0},
                "competition": {"normalized_score": 25.0},
                "accessibility": {"normalized_score": 20.0},
            },
        },
    ]

    weights = {"rent": 0.25, "crowd": 0.25, "competition": 0.25, "accessibility": 0.25}
    ranked = DecisionScienceEngine.run_topsis(mock_candidates, weights)

    assert len(ranked) == 2
    c1_topsis = ranked[0]["topsis"]
    c2_topsis = ranked[1]["topsis"]

    # Candidate 1 (lower rent, higher crowd, higher access) should have higher closeness to ideal
    assert c1_topsis["closeness_coefficient"] > c2_topsis["closeness_coefficient"]
    assert 0.0 <= c1_topsis["closeness_coefficient"] <= 1.0
    assert 0.0 <= c2_topsis["closeness_coefficient"] <= 1.0


def test_huff_retail_gravity():
    """Verify Huff Gravity probabilities sum to 100% and closer locations have higher catchment."""
    mock_candidates = [
        {"id": "near", "distance_km": 1.0, "features": {"shops": 50, "transit_stops": 20, "poi_count": 100}},
        {"id": "far", "distance_km": 5.0, "features": {"shops": 50, "transit_stops": 20, "poi_count": 100}},
    ]

    evaluated = DecisionScienceEngine.calculate_huff_catchment(mock_candidates, business_type="restaurant")
    near_prob = evaluated[0]["huff_gravity"]["catchment_probability_percent"]
    far_prob = evaluated[1]["huff_gravity"]["catchment_probability_percent"]

    # Near location with identical mass should capture significantly higher probability due to distance friction
    assert near_prob > far_prob
    assert 99.0 <= (near_prob + far_prob) <= 101.0

"""
Legacy ML Engine adapter: Redirects to the Decision Science Engine.
Grounds all features in textbook Operations Research & Spatial Economics:
- Analytic Hierarchy Process (AHP)
- TOPSIS (Ideal Solution Closeness)
- Christaller Central Place Theory
- Huff Retail Gravity Model
"""

from typing import Dict, List, Optional
from .decision_science import DecisionScienceEngine, CENTRAL_PLACE_ORDERS


class LocationClusterer:
    """Wrapper mapping Central Place Theory hierarchy to legacy cluster interface."""
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.is_trained = True


class WeightRecommender:
    """Wrapper mapping AHP priority weights to legacy weight recommender interface."""
    def __init__(self):
        self.is_trained = True


class MLEngine:
    """
    Adapter ensuring backward compatibility with any legacy code,
    powered internally by the pure Python Decision Science Engine.
    """
    def __init__(self, localities_data: Dict):
        self.ds_engine = DecisionScienceEngine(localities_data)
        self.clusterer = LocationClusterer()
        self.weight_recommender = WeightRecommender()

    def get_cluster_summary(self) -> Dict:
        return self.ds_engine.get_cluster_summary()

    def get_cluster_map_data(self) -> List[Dict]:
        return self.ds_engine.get_cluster_map_data()

    def get_locality_cluster(self, locality_id: str) -> Optional[Dict]:
        return self.ds_engine.get_locality_cluster(locality_id)

    def get_all_smart_weights(self) -> Dict:
        return self.ds_engine.get_all_smart_weights()

    def get_smart_weights(self, business_type: str) -> Optional[Dict]:
        return self.ds_engine.get_smart_weights(business_type)

    def get_personalized_recommendations(
        self,
        user_searches: List[Dict],
        user_favorites: List[Dict],
        limit: int = 5,
    ) -> List[Dict]:
        return self.ds_engine.get_personalized_recommendations(user_searches, user_favorites, limit)

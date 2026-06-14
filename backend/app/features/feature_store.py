"""
Feature Store interface handling storage, indexing, and fast retrieval of engineered features.
"""
from typing import Dict, Any, Optional
from app.models.domain import Candidate

class FeatureStore:
    """
    Manages engineered features cache and database writes for candidate scoring.
    """
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_candidate_features(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves computed features for a candidate from cache or persistent store.
        """
        return self._cache.get(candidate_id)

    def save_candidate_features(self, candidate_id: str, features: Dict[str, Any]) -> None:
        """
        Saves computed features for a candidate.
        """
        self._cache[candidate_id] = features

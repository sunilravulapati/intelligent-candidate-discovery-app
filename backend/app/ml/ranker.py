import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


class CandidateRanker:
    """
    Manages candidate scoring and re-ranking using tabular machine learning models (XGBoost/LightGBM).
    If no model is loaded, it defaults to a normalized rule-based ranking strategy.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None

    def load_model(self) -> None:
        """Loads the pre-trained XGBoost ranker model if path is set and exists."""
        if self.model_path and os.path.exists(self.model_path):
            import xgboost as xgb
            self.model = xgb.Booster()
            self.model.load_model(self.model_path)

    def train(self, feature_df: pd.DataFrame, targets: np.ndarray, groups: np.ndarray) -> None:
        """
        Trains the XGBoost ranker model using pairwise/listwise loss.
        
        Args:
            feature_df: DataFrame containing candidate features.
            targets: Relevance label array (e.g., 0=not matching, 1=partial, 2=excellent).
            groups: Query group size array (number of candidates per query).
        """
        import xgboost as xgb
        
        dtrain = xgb.DMatrix(feature_df, label=targets)
        dtrain.set_group(groups)
        
        params = {
            "objective": "rank:pairwise",
            "learning_rate": 0.1,
            "max_depth": 6,
            "eval_metric": "ndcg"
        }
        
        self.model = xgb.train(params, dtrain, num_boost_round=100)
        
        if self.model_path:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save_model(self.model_path)

    def predict_scores(self, feature_df: pd.DataFrame) -> np.ndarray:
        """
        Predicts ranking scores for a batch of candidate features.
        Falls back to a baseline heuristic if no model is loaded.
        
        Args:
            feature_df: DataFrame of candidate feature vectors.
            
        Returns:
            np.ndarray: Score array.
        """
        if feature_df.empty:
            return np.array([], dtype=float)

        if self.model is not None:
            import xgboost as xgb
            dtest = xgb.DMatrix(feature_df)
            scores = self.model.predict(dtest)
            return scores
        
        # Fallback Heuristic: Normalized weighted score
        # skill_overlap_ratio + years_of_experience (capped) + github_activity/100
        scores = []
        for _, row in feature_df.iterrows():
            skill_score = row.get("skill_overlap_ratio", 0.0) * 0.5
            exp = min(row.get("years_of_experience", 0.0), 10.0) / 10.0 * 0.3
            github = max(row.get("github_activity_score", 0.0), 0.0) / 100.0 * 0.2
            scores.append(skill_score + exp + github)
            
        return np.array(scores, dtype=float)

    def rank_candidates(
        self, candidates: List[Dict[str, Any]], scores: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Pairs candidates with scores and returns them sorted by score in descending order.
        
        Args:
            candidates: List of candidate profile dictionaries.
            scores: Model predicted scores.
            
        Returns:
            List[Dict[str, Any]]: Ranked list of candidates.
        """
        ranked_list = []
        for i, candidate in enumerate(candidates):
            score = float(scores[i]) if i < len(scores) else 0.0
            # Enrich candidate dictionary with score
            cand_copy = candidate.copy()
            cand_copy["match_score"] = round(score, 4)
            ranked_list.append(cand_copy)
            
        # Sort by match_score descending
        ranked_list.sort(key=lambda x: x["match_score"], reverse=True)
        return ranked_list

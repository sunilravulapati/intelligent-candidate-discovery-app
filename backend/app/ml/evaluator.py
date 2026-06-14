import numpy as np
from typing import List


class ModelEvaluator:
    """
    Computes Information Retrieval evaluation metrics (MAP, NDCG, MRR)
    for model ranking validation.
    """

    @staticmethod
    def mean_reciprocal_rank(recommendations: List[List[int]]) -> float:
        """
        Calculates Mean Reciprocal Rank (MRR).
        
        Args:
            recommendations: List of lists, where each list contains relevance labels (1=relevant, 0=not)
                             in the recommended order.
                             
        Returns:
            float: MRR score.
        """
        rr_list = []
        for query_relevance in recommendations:
            found_relevant = False
            for rank, rel in enumerate(query_relevance):
                if rel > 0:
                    rr_list.append(1.0 / (rank + 1))
                    found_relevant = True
                    break
            if not found_relevant:
                rr_list.append(0.0)
                
        return float(np.mean(rr_list)) if rr_list else 0.0

    @staticmethod
    def mean_average_precision(recommendations: List[List[int]]) -> float:
        """
        Calculates Mean Average Precision (MAP).
        
        Args:
            recommendations: List of lists containing relevance labels in ranked order.
            
        Returns:
            float: MAP score.
        """
        ap_list = []
        for query_relevance in recommendations:
            num_relevant = sum(1 for rel in query_relevance if rel > 0)
            if num_relevant == 0:
                ap_list.append(0.0)
                continue
                
            running_relevant = 0
            precision_sum = 0.0
            
            for rank, rel in enumerate(query_relevance):
                if rel > 0:
                    running_relevant += 1
                    precision_sum += running_relevant / (rank + 1)
                    
            ap_list.append(precision_sum / num_relevant)
            
        return float(np.mean(ap_list)) if ap_list else 0.0

    @staticmethod
    def ndcg_at_k(relevance_scores: List[int], k: int) -> float:
        """
        Calculates Normalized Discounted Cumulative Gain (NDCG) at K for a single query.
        
        Args:
            relevance_scores: Relevance labels in ranked order.
            k: Position limit.
            
        Returns:
            float: NDCG score.
        """
        scores = relevance_scores[:k]
        if not scores or sum(scores) == 0:
            return 0.0
            
        # DCG calculation
        dcg = 0.0
        for i, score in enumerate(scores):
            dcg += (2**score - 1) / np.log2(i + 2)
            
        # Ideal DCG calculation
        ideal_scores = sorted(relevance_scores, reverse=True)[:k]
        idcg = 0.0
        for i, score in enumerate(ideal_scores):
            idcg += (2**score - 1) / np.log2(i + 2)
            
        if idcg == 0:
            return 0.0
            
        return float(dcg / idcg)

    @classmethod
    def mean_ndcg_at_k(cls, recommendations: List[List[int]], k: int = 10) -> float:
        """
        Calculates Mean NDCG@K across all evaluation queries.
        
        Args:
            recommendations: List of query recommendations.
            k: K limit.
        """
        ndcg_list = [cls.ndcg_at_k(query_relevance, k) for query_relevance in recommendations]
        return float(np.mean(ndcg_list)) if ndcg_list else 0.0

"""
Normalized Discounted Cumulative Gain (NDCG) evaluation calculation.
"""
from typing import List, Dict

def calculate_dcg(relevances: List[int], k: int) -> float:
    """
    Calculates the Discounted Cumulative Gain at rank position k.
    """
    # Skeleton
    return 0.0

def calculate_idcg(relevances: List[int], k: int) -> float:
    """
    Calculates the Ideal Discounted Cumulative Gain at rank position k.
    """
    # Skeleton
    return 0.0

def calculate_ndcg(ranked_list: List[str], ground_truth: Dict[str, int], k: int) -> float:
    """
    Calculates the Normalized Discounted Cumulative Gain (NDCG) @ k.
    """
    # Skeleton
    return 0.0

import numpy as np

def calculate_precision_at_k(actual: list[int], predicted: list[int], k: int) -> float:
    """Calculates Precision@K for a single user."""
    if not actual:
        return 0.0
    pred_k = predicted[:k]
    hits = len(set(pred_k) & set(actual))
    return hits / k

def calculate_recall_at_k(actual: list[int], predicted: list[int], k: int) -> float:
    """Calculates Recall@K for a single user."""
    if not actual:
        return 0.0
    pred_k = predicted[:k]
    hits = len(set(pred_k) & set(actual))
    return hits / len(actual)

def calculate_ndcg_at_k(actual: list[int], predicted: list[int], k: int) -> float:
    """Calculates Normalized Discounted Cumulative Gain (NDCG@K) for a single user."""
    if not actual:
        return 0.0
        
    pred_k = predicted[:k]
    dcg = 0.0
    for idx, item in enumerate(pred_k):
        if item in actual:
            dcg += 1.0 / np.log2(idx + 2)
            
    # Calculate Ideal DCG (all actual hits sorted at the top)
    idcg = 0.0
    hits_count = min(len(actual), k)
    for idx in range(hits_count):
        idcg += 1.0 / np.log2(idx + 2)
        
    if idcg == 0.0:
        return 0.0
        
    return dcg / idcg

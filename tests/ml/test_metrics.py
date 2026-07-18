import pytest
from ml.training.metrics import calculate_precision_at_k, calculate_recall_at_k, calculate_ndcg_at_k

def test_precision_recall_ndcg():
    actual = [1, 3, 5]
    predicted = [1, 2, 4, 3, 9] # hit at pos 0 and 3
    
    # K = 3 (only looks at [1, 2, 4])
    # 1 hit (1) out of 3 predictions
    assert calculate_precision_at_k(actual, predicted, 3) == 1/3
    # 1 hit (1) out of 3 actuals
    assert calculate_recall_at_k(actual, predicted, 3) == 1/3
    
    # NDCG@3: hit at idx 0
    # DCG@3 = 1 / log2(2) = 1.0
    # IDCG@3 = 1/log2(2) + 1/log2(3) + 1/log2(4) = 2.1309
    assert pytest.approx(calculate_ndcg_at_k(actual, predicted, 3), 0.001) == 0.469
    
    # NDCG@5: hits at idx 0 (1) and idx 3 (3)
    # DCG@5 = 1/log2(2) + 1/log2(5) = 1.0 + 0.43067655807339306
    # IDCG@5 = 1/log2(2) + 1/log2(3) = 1.0 + 0.6309297535714574
    ndcg_5 = calculate_ndcg_at_k(actual, predicted, 5)
    assert 0.0 < ndcg_5 < 1.0

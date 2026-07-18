import torch
from ml.training.losses import BayesianPersonalizedRankingLoss

def test_bpr_loss_behavior():
    loss_fn = BayesianPersonalizedRankingLoss()
    
    # 1. When positive matches are predicted much higher than negative matches
    pos_high = torch.tensor([0.9, 0.8, 0.95])
    neg_low = torch.tensor([0.1, 0.2, 0.05])
    loss_good = loss_fn(pos_high, neg_low)
    
    # 2. When predictions are reversed (bad ranking)
    pos_low = torch.tensor([0.1, 0.2, 0.05])
    neg_high = torch.tensor([0.9, 0.8, 0.95])
    loss_bad = loss_fn(pos_low, neg_high)
    
    # Loss should be positive
    assert loss_good.item() > 0.0
    # A correct ranking must yield lower loss than an incorrect one
    assert loss_good.item() < loss_bad.item()

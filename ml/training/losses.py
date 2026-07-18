import torch
import torch.nn as nn

class BayesianPersonalizedRankingLoss(nn.Module):
    def __init__(self):
        """
        Bayesian Personalized Ranking (BPR) Loss function
        designed to optimize relative ranking order (pairwise implicit feedback).
        """
        super().__init__()

    def forward(self, positive_predictions: torch.Tensor, negative_predictions: torch.Tensor) -> torch.Tensor:
        # We want positive item predictions to exceed negative item predictions
        margin = positive_predictions - negative_predictions
        loss = -torch.log(torch.sigmoid(margin) + 1e-15).mean()
        return loss

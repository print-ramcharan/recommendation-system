import os
import torch
import json
from ml.training.models.ncf import NeuralCollaborativeFiltering
from ml.training.config import default_config

INDEX_MAPPINGS_PATH = "ml/training/checkpoints/index_mappings.json"
MODEL_CHECKPOINT_PATH = "ml/training/checkpoints/ncf_latest.pt"

def save_index_mappings(user_to_idx: dict[int, int], article_to_idx: dict[int, int]):
    os.makedirs(os.path.dirname(INDEX_MAPPINGS_PATH), exist_ok=True)
    with open(INDEX_MAPPINGS_PATH, "w") as f:
        json.dump({
            "user_to_idx": {str(k): v for k, v in user_to_idx.items()},
            "article_to_idx": {str(k): v for k, v in article_to_idx.items()}
        }, f)

def load_index_mappings() -> tuple[dict[int, int], dict[int, int]]:
    if not os.path.exists(INDEX_MAPPINGS_PATH):
        return {}, {}
    with open(INDEX_MAPPINGS_PATH, "r") as f:
        data = json.load(f)
        return (
            {int(k): v for k, v in data["user_to_idx"].items()},
            {int(k): v for k, v in data["article_to_idx"].items()}
        )

class NeuralCollaborativeFilteringPredictor:
    def __init__(self, checkpoint_path: str = MODEL_CHECKPOINT_PATH):
        self.user_to_idx, self.article_to_idx = load_index_mappings()
        self.idx_to_article = {v: k for k, v in self.article_to_idx.items()}
        
        if not self.user_to_idx or not self.article_to_idx or not os.path.exists(checkpoint_path):
            self.model = None
            return
            
        num_users = len(self.user_to_idx)
        num_items = len(self.article_to_idx)
        
        self.model = NeuralCollaborativeFiltering(
            num_users=num_users,
            num_items=num_items,
            embedding_dim=default_config.model.embedding_dim,
            layers=default_config.model.layers
        )
        
        checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'))
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()

    def predict_score(self, user_id: int, article_ids: list[int]) -> dict[int, float]:
        """
        Calculates NCF click probabilities for a list of candidate article IDs.
        If a user or article is not mapped, returns 0.0.
        """
        if self.model is None or user_id not in self.user_to_idx:
            return {aid: 0.0 for aid in article_ids}
            
        u_idx = self.user_to_idx[user_id]
        user_tensor = torch.tensor([u_idx] * len(article_ids), dtype=torch.long)
        
        item_indices = []
        valid_article_ids = []
        scores = {}
        
        for aid in article_ids:
            if aid in self.article_to_idx:
                item_indices.append(self.article_to_idx[aid])
                valid_article_ids.append(aid)
            else:
                scores[aid] = 0.0
                
        if not item_indices:
            return scores
            
        item_tensor = torch.tensor(item_indices, dtype=torch.long)
        
        with torch.no_grad():
            preds = self.model(user_tensor[:len(item_indices)], item_tensor)
            
        # Handle single tensor item output matching squeeze dimensions
        pred_list = preds.tolist() if len(item_indices) > 1 else [preds.item()]
            
        for aid, score in zip(valid_article_ids, pred_list):
            scores[aid] = float(score)
            
        return scores

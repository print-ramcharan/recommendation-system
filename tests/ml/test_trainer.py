import pytest
import torch
from torch.utils.data import DataLoader
from ml.training.config import PipelineConfig
from ml.training.dataset import RecommendationDataset
from ml.training.models.ncf import NeuralCollaborativeFiltering
from ml.training.trainer import NCFTrainer

def test_trainer_fit_loop():
    # Model parameters
    num_users = 10
    num_items = 10
    
    # Create mock dataset
    users = [0, 1, 2, 3, 4, 5, 0, 1]
    items = [2, 3, 0, 1, 4, 5, 1, 2]
    labels = [1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0]
    
    dataset = RecommendationDataset(users, items, labels)
    loader = DataLoader(dataset, batch_size=4, shuffle=True)
    
    model = NeuralCollaborativeFiltering(num_users=num_users, num_items=num_items, embedding_dim=8, layers=[16, 8])
    
    config = PipelineConfig()
    config.training.epochs = 1
    config.training.checkpoint_dir = "tests/ml/checkpoints"
    
    trainer = NCFTrainer(model=model, config=config, train_loader=loader)
    history = trainer.fit()
    
    # Assert training history is populated
    assert len(history) == 1
    assert history[0] > 0.0

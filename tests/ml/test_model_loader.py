import os
import pytest
from ml.training.model_loader import save_index_mappings, load_index_mappings, NeuralCollaborativeFilteringPredictor

def test_index_mappings_serialization(tmp_path):
    user_map = {1122: 0, 3344: 1}
    item_map = {5566: 0, 7788: 1}
    
    # Temporarily monkeypatch global mapping path to sandbox execution
    import ml.training.model_loader as ml
    original_path = ml.INDEX_MAPPINGS_PATH
    ml.INDEX_MAPPINGS_PATH = os.path.join(tmp_path, "mappings.json")
    
    try:
        save_index_mappings(user_map, item_map)
        loaded_user, loaded_item = load_index_mappings()
        
        assert loaded_user == user_map
        assert loaded_item == item_map
    finally:
        ml.INDEX_MAPPINGS_PATH = original_path

def test_predictor_fallback_behavior():
    # If checkpoint doesn't exist, predictor fallback returns 0.0 for all scores
    predictor = NeuralCollaborativeFilteringPredictor(checkpoint_path="nonexistent.pt")
    scores = predictor.predict_score(user_id=9999, article_ids=[101, 102])
    assert scores == {101: 0.0, 102: 0.0}

import torch
from torch.utils.data import DataLoader
from ml.training.model_loader import NeuralCollaborativeFilteringPredictor
from ml.training.dataset import build_training_tensors
from ml.training.metrics import calculate_precision_at_k, calculate_ndcg_at_k
from services.api.db.database import SessionLocal

async def evaluate_trained_model():
    print("📈 Running offline evaluation for Neural Collaborative Filtering model...")
    predictor = NeuralCollaborativeFilteringPredictor()
    
    if predictor.model is None:
        print("⚠️ Model checkpoint not found or index mappings empty. Train model first!")
        return

    async with SessionLocal() as db:
        # Load validation samples
        dataset, user_to_idx, article_to_idx = await build_training_tensors(db)
        
    if len(dataset) == 0:
        print("⚠️ No interaction data available to evaluate.")
        return

    # Evaluate Precision and NDCG for mapped users
    idx_to_user = {v: k for k, v in user_to_idx.items()}
    idx_to_article = {v: k for k, v in article_to_idx.items()}
    
    user_actual_clicks = {}
    
    # Aggregate actual positive clicks from dataset
    for idx in range(len(dataset)):
        u, i, label = dataset[idx]
        u_id = idx_to_user[u.item()]
        i_id = idx_to_article[i.item()]
        
        if label.item() == 1.0:
            if u_id not in user_actual_clicks:
                user_actual_clicks[u_id] = []
            user_actual_clicks[u_id].append(i_id)

    precisions = []
    ndcgs = []
    
    all_article_ids = list(article_to_idx.keys())
    
    # Sample up to 50 users to evaluate
    eval_users = list(user_actual_clicks.keys())[:50]
    
    for uid in eval_users:
        actual = user_actual_clicks[uid]
        # Predict score for all items in system
        scores = predictor.predict_score(uid, all_article_ids)
        # Sort items by predicted score
        predicted_ranked = sorted(all_article_ids, key=lambda aid: scores.get(aid, 0.0), reverse=True)
        
        precisions.append(calculate_precision_at_k(actual, predicted_ranked, k=5))
        ndcgs.append(calculate_ndcg_at_k(actual, predicted_ranked, k=5))

    mean_p = sum(precisions) / len(precisions) if precisions else 0.0
    mean_n = sum(ndcgs) / len(ndcgs) if ndcgs else 0.0
    
    print("--------------------------------------------------")
    print(f"📊 Mean Precision@5: {mean_p:.4f}")
    print(f"📊 Mean NDCG@5:      {mean_n:.4f}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    import asyncio
    asyncio.run(evaluate_trained_model())

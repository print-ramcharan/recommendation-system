import random
import torch
from torch.utils.data import Dataset
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.api.models.event import Event
from services.api.models.article import Article
from services.api.models.user import User

class RecommendationDataset(Dataset):
    def __init__(self, user_indices: list[int], item_indices: list[int], labels: list[float]):
        self.users = torch.tensor(user_indices, dtype=torch.long)
        self.items = torch.tensor(item_indices, dtype=torch.long)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.users[idx], self.items[idx], self.labels[idx]

async def build_training_tensors(
    db: AsyncSession, 
    negative_ratio: int = 4
) -> tuple[RecommendationDataset, dict[int, int], dict[int, int]]:
    """
    Retrieves click history, maps user/article IDs to continuous indices,
    generates negative samples, and builds a PyTorch-compatible dataset.
    """
    # 1. Fetch positive click interactions
    stmt = select(Event.user_id, Event.article_id).where(Event.event_type == "click")
    result = await db.execute(stmt)
    clicks = list(result.all())

    if not clicks:
        return RecommendationDataset([], [], []), {}, {}

    # 2. Fetch all user and article IDs
    all_users = (await db.execute(select(User.user_id))).scalars().all()
    all_articles = (await db.execute(select(Article.article_id))).scalars().all()

    # Create mapping dicts for embedding indexing
    user_to_idx = {uid: i for i, uid in enumerate(all_users)}
    article_to_idx = {aid: i for i, aid in enumerate(all_articles)}

    user_item_pairs = []
    labels = []

    # Keep track of positive set for fast lookup during negative sampling
    pos_set = set(clicks)
    articles_set = set(all_articles)

    for user_id, article_id in clicks:
        if user_id not in user_to_idx or article_id not in article_to_idx:
            continue
            
        # Add positive sample
        user_item_pairs.append((user_to_idx[user_id], article_to_idx[article_id]))
        labels.append(1.0)

        # Generate negative samples (implicit feedback)
        unclicked = list(articles_set - {aid for uid, aid in clicks if uid == user_id})
        if unclicked:
            neg_samples = random.sample(unclicked, min(len(unclicked), negative_ratio))
            for neg_art_id in neg_samples:
                if neg_art_id in article_to_idx:
                    user_item_pairs.append((user_to_idx[user_id], article_to_idx[neg_art_id]))
                    labels.append(0.0)

    user_indices = [p[0] for p in user_item_pairs]
    item_indices = [p[1] for p in user_item_pairs]

    return RecommendationDataset(user_indices, item_indices, labels), user_to_idx, article_to_idx

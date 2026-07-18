import asyncio
import os
from torch.utils.data import DataLoader, random_split
from services.api.db.database import SessionLocal
from ml.training.config import default_config
from ml.training.dataset import build_training_tensors
from ml.training.models.ncf import NeuralCollaborativeFiltering
from ml.training.trainer import NCFTrainer
from ml.training.model_loader import save_index_mappings

async def run_pipeline():
    print("🚀 Initializing NCF Model Training Pipeline...")
    async with SessionLocal() as db:
        # 1. Build implicit datasets from PostgreSQL interactions
        dataset, user_to_idx, article_to_idx = await build_training_tensors(db)
        
        if len(dataset) == 0:
            print("⚠️ Insufficient click event history in database to execute training. Aborting.")
            return

        print(f"📊 Dataset successfully generated: {len(dataset)} records mapped.")
        print(f"👥 Users: {len(user_to_idx)} | 📰 Articles: {len(article_to_idx)}")

        # Save index translation mappings for inference
        save_index_mappings(user_to_idx, article_to_idx)

        # 2. Divide dataset into Train / Validation split
        val_size = int(len(dataset) * default_config.training.validation_split)
        train_size = len(dataset) - val_size
        
        train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
        
        train_loader = DataLoader(train_dataset, batch_size=default_config.training.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=default_config.training.batch_size, shuffle=False)

        # 3. Instantiate model
        model = NeuralCollaborativeFiltering(
            num_users=len(user_to_idx),
            num_items=len(article_to_idx),
            embedding_dim=default_config.model.embedding_dim,
            layers=default_config.model.layers,
            dropout=default_config.model.dropout
        )

        # 4. Spin up trainer engine
        trainer = NCFTrainer(
            model=model,
            config=default_config,
            train_loader=train_loader,
            val_loader=val_loader
        )
        
        print("🔥 Starting training fit epochs...")
        trainer.fit()
        print("✨ Training completed. NCF checkpoints saved successfully.")

if __name__ == "__main__":
    asyncio.run(run_pipeline())

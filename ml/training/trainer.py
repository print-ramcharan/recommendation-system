import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from ml.training.config import PipelineConfig

class NCFTrainer:
    def __init__(
        self, 
        model: nn.Module, 
        config: PipelineConfig,
        train_loader: DataLoader,
        val_loader: DataLoader = None
    ):
        self.model = model
        self.config = config
        self.train_loader = train_loader
        self.val_loader = val_loader
        
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=config.training.learning_rate,
            weight_decay=config.training.weight_decay
        )
        
        # Pointwise binary cross entropy loss for binary clicks
        self.criterion = nn.BCELoss()

    def train_epoch(self) -> float:
        self.model.train()
        total_loss = 0.0
        
        for users, items, labels in self.train_loader:
            self.optimizer.zero_grad()
            predictions = self.model(users, items)
            loss = self.criterion(predictions, labels)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item() * users.size(0)
            
        return total_loss / len(self.train_loader.dataset)

    def evaluate(self, loader: DataLoader) -> float:
        self.model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for users, items, labels in loader:
                predictions = self.model(users, items)
                loss = self.criterion(predictions, labels)
                total_loss += loss.item() * users.size(0)
                
        return total_loss / len(loader.dataset)

    def fit(self) -> list[float]:
        import json
        history = []
        os.makedirs(self.config.training.checkpoint_dir, exist_ok=True)
        
        def update_status_file(status, epoch, train_loss, val_loss, msg):
            try:
                status_path = os.path.join(self.config.training.checkpoint_dir, "status.json")
                with open(status_path, "w") as f:
                    json.dump({
                        "status": status,
                        "epoch": epoch,
                        "total_epochs": self.config.training.epochs,
                        "train_loss": round(train_loss, 4),
                        "val_loss": round(val_loss, 4),
                        "message": msg
                    }, f)
            except Exception:
                pass

        update_status_file("training", 0, 0.0, 0.0, "Starting model training fit epochs...")

        for epoch in range(1, self.config.training.epochs + 1):
            train_loss = self.train_epoch()
            val_loss = self.evaluate(self.val_loader) if self.val_loader else 0.0
            
            print(f"Epoch {epoch}/{self.config.training.epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
            history.append(train_loss)
            
            # Save checkpoints
            checkpoint_path = os.path.join(self.config.training.checkpoint_dir, "ncf_latest.pt")
            torch.save({
                'epoch': epoch,
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'loss': train_loss,
            }, checkpoint_path)
            
            update_status_file("training", epoch, train_loss, val_loss, f"Epoch {epoch}/{self.config.training.epochs} completed.")
            
        update_status_file("idle", self.config.training.epochs, train_loss, val_loss, "Model training completed successfully.")
        return history

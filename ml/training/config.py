import os
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    embedding_dim: int = Field(default=32, description="Dimension of user and item latent embeddings")
    layers: list[int] = Field(default=[64, 32, 16], description="Hidden layers for MLP subnetwork")
    dropout: float = Field(default=0.2, description="Dropout probability for hidden layers")

class TrainingConfig(BaseModel):
    batch_size: int = Field(default=256, description="Batch size for training and validation loaders")
    learning_rate: float = Field(default=0.001, description="Learning rate for optimization optimizer")
    epochs: int = Field(default=5, description="Number of training epochs")
    weight_decay: float = Field(default=1e-5, description="L2 regularization penalty weight decay")
    validation_split: float = Field(default=0.2, description="Fraction of dataset reserved for validation")
    checkpoint_dir: str = Field(default="ml/training/checkpoints", description="Directory to save model checkpoints")

class PipelineConfig(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)

# Default global configuration instance
default_config = PipelineConfig()

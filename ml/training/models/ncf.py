import torch
import torch.nn as nn

class NeuralCollaborativeFiltering(nn.Module):
    def __init__(self, num_users: int, num_items: int, embedding_dim: int = 32, layers: list[int] = [64, 32, 16], dropout: float = 0.2):
        """
        Neural Collaborative Filtering (NCF) architecture merging
        Generalized Matrix Factorization (GMF) and Multi-Layer Perceptron (MLP).
        """
        super().__init__()
        self.num_users = num_users
        self.num_items = num_items
        
        # GMF Embeddings
        self.user_embed_gmf = nn.Embedding(num_users, embedding_dim)
        self.item_embed_gmf = nn.Embedding(num_items, embedding_dim)
        
        # MLP Embeddings (requires separate parameters for NCF framework)
        mlp_embedding_dim = layers[0] // 2
        self.user_embed_mlp = nn.Embedding(num_users, mlp_embedding_dim)
        self.item_embed_mlp = nn.Embedding(num_items, mlp_embedding_dim)
        
        # MLP Neural Layers
        mlp_modules = []
        for i in range(len(layers) - 1):
            mlp_modules.append(nn.Linear(layers[i], layers[i+1]))
            mlp_modules.append(nn.ReLU())
            mlp_modules.append(nn.Dropout(p=dropout))
        self.mlp = nn.Sequential(*mlp_modules)
        
        # Final output classification layer (combining GMF and MLP branches)
        final_dim = embedding_dim + layers[-1]
        self.output_layer = nn.Linear(final_dim, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, user_indices: torch.Tensor, item_indices: torch.Tensor) -> torch.Tensor:
        # GMF Forward pass
        user_latent_gmf = self.user_embed_gmf(user_indices)
        item_latent_gmf = self.item_embed_gmf(item_indices)
        gmf_vector = user_latent_gmf * item_latent_gmf
        
        # MLP Forward pass
        user_latent_mlp = self.user_embed_mlp(user_indices)
        item_latent_mlp = self.item_embed_mlp(item_indices)
        mlp_vector = torch.cat([user_latent_mlp, item_latent_mlp], dim=-1)
        mlp_vector = self.mlp(mlp_vector)
        
        # Concatenate GMF and MLP vectors
        fusion_vector = torch.cat([gmf_vector, mlp_vector], dim=-1)
        logits = self.output_layer(fusion_vector)
        return self.sigmoid(logits).squeeze(-1)

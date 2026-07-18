import torch
from ml.training.models.ncf import NeuralCollaborativeFiltering

def test_ncf_forward_pass_shape():
    # Model parameters
    num_users = 100
    num_items = 50
    embedding_dim = 16
    layers = [32, 16, 8]
    
    model = NeuralCollaborativeFiltering(
        num_users=num_users,
        num_items=num_items,
        embedding_dim=embedding_dim,
        layers=layers
    )
    
    # Generate mock inputs
    batch_size = 8
    users = torch.randint(0, num_users, (batch_size,))
    items = torch.randint(0, num_items, (batch_size,))
    
    output = model(users, items)
    
    # Verify shape (1D tensor of size batch_size)
    assert output.shape == (batch_size,)
    # Verify outputs are valid probabilities (between 0 and 1)
    assert torch.all(output >= 0.0)
    assert torch.all(output <= 1.0)

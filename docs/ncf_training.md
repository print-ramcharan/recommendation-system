# Neural Collaborative Filtering (NCF) Training & Inference Pipeline

This directory defines a comprehensive training and inference pipeline utilizing PyTorch to train a Neural Collaborative Filtering (NCF) model on implicit feedback click history to rank candidates in the real-time recommendation API gateway.

## NCF Architecture
The model fuses:
1. **Generalized Matrix Factorization (GMF)**: Captures linear interaction patterns between user and article embeddings via element-wise multiplication.
2. **Multi-Layer Perceptron (MLP)**: Learns non-linear interaction features by concatenating embeddings and passing them through deep dense layers.

The outputs from both branches are concatenated and projected to calculate click probabilities:
$$\hat{y}_{u,i} = \sigma \left( \mathbf{h}^T \left[ \mathbf{\phi}^{GMF} \parallel \mathbf{\phi}^{MLP} \right] \right)$$

## Bayesian Personalized Ranking (BPR) Loss
For implicit feedback datasets, we optimize relative pairwise preference ranking order using BPR:
$$L_{BPR} = - \sum_{(u,i,j) \in D_S} \ln \sigma(\hat{y}_{u,i} - \hat{y}_{u,j}) + \lambda_\Theta \|\Theta\|^2$$
where:
* $i$ is a clicked article (positive feedback).
* $j$ is a sampled unclicked article (negative feedback).

## CLI Operations
Run the database event seeder first to populate interaction clicks:
```bash
PYTHONPATH=. .venv/bin/python -m ml.training.generate_seed_events
```

Run the model training pipeline:
```bash
PYTHONPATH=. .venv/bin/python -m ml.training.main
```
This saves checkpoints directly to `ml/training/checkpoints/ncf_latest.pt`.

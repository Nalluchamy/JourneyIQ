import torch
import torch.nn as nn


class NCFModel(nn.Module):
    """Neural Collaborative Filtering (NCF) recommendation model using PyTorch."""

    def __init__(
        self,
        num_users: int,
        num_products: int,
        embedding_dim: int = 32,
        layers: list[int] | None = None,
        dropout_rate: float = 0.2,
    ):
        super().__init__()
        if layers is None:
            layers = [64, 32, 16]

        # Embeddings
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.product_embedding = nn.Embedding(num_products, embedding_dim)

        # Dense MLP Network
        mlp_layers = []
        input_dim = embedding_dim * 2  # Concatenated user and product embeddings

        for layer_dim in layers:
            mlp_layers.append(nn.Linear(input_dim, layer_dim))
            mlp_layers.append(nn.BatchNorm1d(layer_dim))
            mlp_layers.append(nn.ReLU())
            mlp_layers.append(nn.Dropout(p=dropout_rate))
            input_dim = layer_dim

        self.mlp = nn.Sequential(*mlp_layers)

        # Final Sigmoid classification layer (Normalized Score 0-1)
        self.output_layer = nn.Linear(input_dim, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(
        self, user_indices: torch.Tensor, product_indices: torch.Tensor
    ) -> torch.Tensor:
        # Fetch user and product embeddings
        user_embed = self.user_embedding(user_indices)
        prod_embed = self.product_embedding(product_indices)

        # Concatenate inputs
        x = torch.cat([user_embed, prod_embed], dim=-1)

        # Forward pass through layers
        x = self.mlp(x)

        # Map to final score
        logits = self.output_layer(x)
        score = self.sigmoid(logits)

        return score.squeeze(-1)

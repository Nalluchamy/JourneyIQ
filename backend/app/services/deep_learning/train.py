import json
import os
import time
from typing import Any

import structlog
import torch
import torch.nn as nn
import torch.optim as optim
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.deep_learning.dataset import get_ncf_dataloaders
from app.services.deep_learning.model import NCFModel
from app.services.deep_learning.utils import get_device

logger = structlog.get_logger()

# Resolve model storage directory relative to this file (backend/models/)
MODEL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "models")
)


async def train_ncf_model(
    db: AsyncSession,
    epochs: int = 3,
    batch_size: int = 64,
    embedding_dim: int = 32,
    layers: list[int] | None = None,
    learning_rate: float = 0.005,
    patience: int = 5,
) -> dict[str, Any]:
    if layers is None:
        layers = [64, 32, 16]
    """
    Trains the PyTorch NCF model using user interactions in the DB.
    Implements validation split, early stopping, device placement (GPU/CPU),
    checkpoint saving, and serializes training history/metadata.
    """
    start_time = time.perf_counter()
    logger.info("Initializing NCF training dataset from DB")

    train_loader, test_loader, metadata = await get_ncf_dataloaders(
        db, batch_size=batch_size
    )

    num_users = metadata["num_users"]
    num_products = metadata["num_products"]

    device = get_device()
    logger.info("Using deep learning target device", device=str(device))

    # Instantiate Model
    model = NCFModel(
        num_users=num_users,
        num_products=num_products,
        embedding_dim=embedding_dim,
        layers=layers,
    ).to(device)

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # History logs
    train_history = []
    val_history = []

    best_val_loss = float("inf")
    patience_counter = 0
    best_model_state = None
    best_epoch = 0

    logger.info(
        "Starting NCF training loop",
        epochs=epochs,
        total_users=num_users,
        total_products=num_products,
    )

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_train_loss = 0.0

        for user_batch, product_batch, weight_batch in train_loader:
            user_batch = user_batch.to(device)
            product_batch = product_batch.to(device)
            weight_batch = weight_batch.to(device)

            if len(user_batch) <= 1:
                model.eval()
            else:
                model.train()

            optimizer.zero_grad()
            predictions = model(user_batch, product_batch)
            loss = criterion(predictions, weight_batch)
            loss.backward()
            optimizer.step()

            epoch_train_loss += loss.item() * len(user_batch)

        epoch_train_loss /= len(train_loader.dataset)
        train_history.append(epoch_train_loss)

        # Validation pass
        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for user_batch, product_batch, weight_batch in test_loader:
                user_batch = user_batch.to(device)
                product_batch = product_batch.to(device)
                weight_batch = weight_batch.to(device)

                predictions = model(user_batch, product_batch)
                loss = criterion(predictions, weight_batch)
                epoch_val_loss += loss.item() * len(user_batch)

        epoch_val_loss /= len(test_loader.dataset)
        val_history.append(epoch_val_loss)

        # Check validation improvement
        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_model_state = model.state_dict().copy()
            best_epoch = epoch
            patience_counter = 0
        else:
            patience_counter += 1

        if epoch % 5 == 0 or epoch == 1:
            logger.debug(
                f"Epoch {epoch}/{epochs} | Train Loss: {epoch_train_loss:.4f} | Val Loss: {epoch_val_loss:.4f}"
            )

        # Early Stopping check
        if patience_counter >= patience:
            logger.info(
                f"Early stopping triggered at epoch {epoch}. Restoring weights from epoch {best_epoch}."
            )
            break

    # Restore best weights
    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    training_time = time.perf_counter() - start_time
    logger.info("NCF training finished successfully", duration_seconds=training_time)

    # Save checkpoint paths
    os.makedirs(MODEL_DIR, exist_ok=True)

    latest_path = os.path.join(MODEL_DIR, "latest.pt")

    # Build unique version identifier based on timestamp
    version_id = int(time.time())
    versioned_filename = f"ncf_model_v{version_id}.pt"
    versioned_path = os.path.join(MODEL_DIR, versioned_filename)

    # State dict checkpoint containing weights and architecture specs
    checkpoint = {
        "state_dict": model.state_dict(),
        "num_users": num_users,
        "num_products": num_products,
        "embedding_dim": embedding_dim,
        "layers": layers,
        "user_to_idx": metadata["user_to_idx"],
        "product_to_idx": metadata["product_to_idx"],
        "idx_to_user": metadata["idx_to_user"],
        "idx_to_product": metadata["idx_to_product"],
        "version_id": version_id,
    }

    torch.save(checkpoint, latest_path)
    torch.save(checkpoint, versioned_path)

    # Persist training stats and versioning info in model_metadata.json
    metadata_payload = {
        "version": f"v{version_id}",
        "active_filename": versioned_filename,
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "training_time_seconds": round(training_time, 2),
        "best_epoch": best_epoch,
        "best_val_loss": round(best_val_loss, 5),
        "history": {
            "epochs": list(range(1, len(train_history) + 1)),
            "train_losses": [round(loss_val, 5) for loss_val in train_history],
            "val_losses": [round(loss_val, 5) for loss_val in val_history],
        },
    }

    metadata_json_path = os.path.join(MODEL_DIR, "model_metadata.json")
    with open(metadata_json_path, "w") as f:
        json.dump(metadata_payload, f, indent=2)

    logger.info("Persisted model checkpoints and metadata.json")
    return metadata_payload

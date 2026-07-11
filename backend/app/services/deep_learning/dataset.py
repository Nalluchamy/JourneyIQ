from typing import Any

import pandas as pd
import torch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from torch.utils.data import DataLoader, Dataset

from app.models.cart_item import CartItem
from app.models.event import Event
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.models.wishlist_item import WishlistItem


class NCFDataset(Dataset):
    """PyTorch Dataset for Neural Collaborative Filtering."""

    def __init__(
        self,
        user_indices: torch.Tensor,
        product_indices: torch.Tensor,
        weights: torch.Tensor,
    ):
        self.user_indices = user_indices
        self.product_indices = product_indices
        self.weights = weights

    def __len__(self) -> int:
        return len(self.user_indices)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.user_indices[idx], self.product_indices[idx], self.weights[idx]


async def build_interaction_matrix(db: AsyncSession) -> list[dict[str, Any]]:
    """
    Extracts all user interaction metrics from the database and assigns weights:
    Purchase = 5, Review = 4, Wishlist = 3, Cart = 2, View = 1.
    Returns a list of dicts with keys: user_id, product_id, weight.
    """
    interactions: dict[tuple[int, int], int] = {}

    # 1. Purchases (Weight = 5)
    purchase_stmt = select(Order.user_id, OrderItem.product_id).join(
        OrderItem, OrderItem.order_id == Order.id
    )
    purchases = (await db.execute(purchase_stmt)).all()
    for u_id, p_id in purchases:
        if u_id and p_id:
            interactions[(u_id, p_id)] = max(interactions.get((u_id, p_id), 0), 5)

    # 2. Reviews (Weight = 4)
    reviews_stmt = select(Review.user_id, Review.product_id)
    reviews = (await db.execute(reviews_stmt)).all()
    for u_id, p_id in reviews:
        if u_id and p_id:
            interactions[(u_id, p_id)] = max(interactions.get((u_id, p_id), 0), 4)

    # 3. Wishlist (Weight = 3)
    wishlist_stmt = select(WishlistItem.user_id, WishlistItem.product_id)
    wishlist = (await db.execute(wishlist_stmt)).all()
    for u_id, p_id in wishlist:
        if u_id and p_id:
            interactions[(u_id, p_id)] = max(interactions.get((u_id, p_id), 0), 3)

    # 4. Cart (Weight = 2)
    cart_stmt = select(CartItem.user_id, CartItem.product_id)
    cart = (await db.execute(cart_stmt)).all()
    for u_id, p_id in cart:
        if u_id and p_id:
            interactions[(u_id, p_id)] = max(interactions.get((u_id, p_id), 0), 2)

    # 5. Product Views (Weight = 1)
    views_stmt = select(Event.user_id, Event.product_id).where(
        Event.event_type == "view_item",
        Event.user_id.isnot(None),
        Event.product_id.isnot(None),
    )
    views = (await db.execute(views_stmt)).all()
    for u_id, p_id in views:
        if u_id and p_id:
            interactions[(u_id, p_id)] = max(interactions.get((u_id, p_id), 0), 1)

    # Format interactions list
    formatted_list = [
        {"user_id": u_id, "product_id": p_id, "weight": float(w)}
        for (u_id, p_id), w in interactions.items()
    ]

    # Defensive fallback if empty
    if not formatted_list:
        formatted_list.append({"user_id": 1, "product_id": 1, "weight": 1.0})

    return formatted_list


async def get_ncf_dataloaders(
    db: AsyncSession, batch_size: int = 64, test_size: float = 0.2
) -> tuple[DataLoader, DataLoader, dict[str, Any]]:
    """
    Builds interaction weights, creates continuous user/product index mappings,
    splits into train/test sets, and returns train & test DataLoaders, plus metadata dict.
    """
    # Fetch all active users and products to construct absolute index ranges
    users_stmt = select(User.id).where(User.is_deleted == False)
    users = (await db.execute(users_stmt)).scalars().all()
    user_ids = sorted(set(users))
    if not user_ids:
        user_ids = [1]

    products_stmt = select(Product.id).where(
        Product.is_deleted == False, Product.is_active == True
    )
    products = (await db.execute(products_stmt)).scalars().all()
    product_ids = sorted(set(products))
    if not product_ids:
        product_ids = [1]

    # continuous index maps
    user_to_idx = {u_id: idx for idx, u_id in enumerate(user_ids)}
    product_to_idx = {p_id: idx for idx, p_id in enumerate(product_ids)}

    interactions_data = await build_interaction_matrix(db)

    # Map raw user/product IDs to continuous indices (ignoring deleted/unknown items)
    mapped_users = []
    mapped_products = []
    normalized_weights = []

    for item in interactions_data:
        u_id = item["user_id"]
        p_id = item["product_id"]
        if u_id in user_to_idx and p_id in product_to_idx:
            mapped_users.append(user_to_idx[u_id])
            mapped_products.append(product_to_idx[p_id])
            # Normalize target weight to 0.0 - 1.0 range (divide by max weight 5.0)
            normalized_weights.append(item["weight"] / 5.0)

    # Defensive fallbacks if mapping yields empty arrays
    if not mapped_users:
        mapped_users = [0]
        mapped_products = [0]
        normalized_weights = [0.2]

    df = pd.DataFrame(
        {
            "user_idx": mapped_users,
            "product_idx": mapped_products,
            "weight": normalized_weights,
        }
    )

    # Split train/test sets
    shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
    split_idx = int(len(shuffled) * (1.0 - test_size))

    # Ensure at least 1 item in validation set
    if split_idx == len(shuffled):
        split_idx = max(0, len(shuffled) - 1)

    train_df = shuffled.iloc[:split_idx]
    test_df = shuffled.iloc[split_idx:]
    if train_df.empty:
        train_df = shuffled
    if test_df.empty:
        test_df = shuffled

    # Convert to tensors
    train_users = torch.tensor(train_df["user_idx"].values, dtype=torch.long)
    train_prods = torch.tensor(train_df["product_idx"].values, dtype=torch.long)
    train_weights = torch.tensor(train_df["weight"].values, dtype=torch.float32)

    test_users = torch.tensor(test_df["user_idx"].values, dtype=torch.long)
    test_prods = torch.tensor(test_df["product_idx"].values, dtype=torch.long)
    test_weights = torch.tensor(test_df["weight"].values, dtype=torch.float32)

    train_dataset = NCFDataset(train_users, train_prods, train_weights)
    test_dataset = NCFDataset(test_users, test_prods, test_weights)

    # Set PyTorch dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    metadata = {
        "num_users": len(user_ids),
        "num_products": len(product_ids),
        "user_to_idx": user_to_idx,
        "product_to_idx": product_to_idx,
        "idx_to_user": {v: k for k, v in user_to_idx.items()},
        "idx_to_product": {v: k for k, v in product_to_idx.items()},
    }

    return train_loader, test_loader, metadata

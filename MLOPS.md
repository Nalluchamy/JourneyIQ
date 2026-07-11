# JourneyIQ — ML Operations Guide

> **Version:** 1.0.0 | **Last Updated:** 2026-07-11

This document covers the end-to-end machine learning operations for JourneyIQ's recommendation engine, including model registry, training pipeline, evaluation, inference tracking, and cold-start strategies.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Model Registry](#model-registry)
  - [NCFModelRegistry Class](#ncfmodelregistry-class)
  - [File Structure](#file-structure)
  - [Model Versioning](#model-versioning)
- [Training Pipeline](#training-pipeline)
  - [Scheduler Architecture](#scheduler-architecture)
  - [NCF Training Process](#ncf-training-process)
  - [Hyperparameters](#hyperparameters)
  - [Early Stopping](#early-stopping)
- [Evaluation Metrics](#evaluation-metrics)
  - [Metric Definitions](#metric-definitions)
  - [Evaluation Pipeline](#evaluation-pipeline)
  - [Interpreting Results](#interpreting-results)
- [Model Rollback](#model-rollback)
  - [API-Driven Rollback](#api-driven-rollback)
  - [Manual Rollback](#manual-rollback)
- [Inference Statistics](#inference-statistics)
- [Cold-Start Fallback Strategy](#cold-start-fallback-strategy)
- [Model Comparison Dashboard](#model-comparison-dashboard)
- [Monitoring & Alerts](#monitoring--alerts)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    JourneyIQ ML Pipeline                        │
│                                                                 │
│  ┌──────────────┐    ┌───────────────┐    ┌──────────────────┐ │
│  │  Scheduler    │───▶│  NCF Trainer  │───▶│  Model Registry  │ │
│  │  (Daily)      │    │  (PyTorch)    │    │  (Versioned .pt) │ │
│  └──────┬───────┘    └───────────────┘    └────────┬─────────┘ │
│         │                                          │           │
│         │            ┌───────────────┐             │           │
│         └───────────▶│  Evaluator    │◀────────────┘           │
│                      │  (P@K, NDCG)  │                         │
│                      └───────┬───────┘                         │
│                              │                                 │
│                     ┌────────▼────────┐                        │
│                     │  evaluation_    │                        │
│                     │  metrics.json   │                        │
│                     └─────────────────┘                        │
│                                                                 │
│  ┌──────────────┐    ┌───────────────┐                         │
│  │  API Request  │───▶│  NCFPredictor │    ┌────────────────┐  │
│  │  /recommend   │    │  (Inference)  │───▶│ Inference Stats │  │
│  └──────────────┘    └───────────────┘    │ (Telemetry)     │  │
│                                           └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Model Registry

### NCFModelRegistry Class

The model registry is implemented in `backend/app/services/deep_learning/registry.py` as the `NCFModelRegistry` class. It provides:

| Method | Purpose |
|---|---|
| `list_checkpoints()` | Scans `backend/models/` for versioned `.pt` files and returns metadata |
| `get_active_model()` | Reads `model_metadata.json` and `evaluation_metrics.json` for the current model |
| `rollback_to_version(version_id)` | Restores a versioned checkpoint as `latest.pt` and updates metadata |
| `track_inference(duration_seconds)` | Thread-safe accumulator for inference call count and latency |
| `get_inference_telemetry()` | Returns total inference calls, average latency, and total latency |

### File Structure

All model artifacts are stored in `backend/models/`:

```
backend/models/
├── latest.pt                          # Active model checkpoint (always current)
├── ncf_model_v1752220800.pt           # Versioned checkpoint (Unix timestamp)
├── ncf_model_v1752134400.pt           # Previous version
├── ncf_model_v1752048000.pt           # Older version
├── model_metadata.json                # Training metadata for active model
└── evaluation_metrics.json            # Evaluation scores for active model
```

### Model Versioning

Each training run produces a unique version using a Unix timestamp identifier:

| File | Naming Convention | Description |
|---|---|---|
| **Active checkpoint** | `latest.pt` | Always points to the current production model |
| **Versioned checkpoint** | `ncf_model_v{timestamp}.pt` | Immutable snapshot for rollback capability |
| **Training metadata** | `model_metadata.json` | Version, training time, best epoch, loss history |
| **Evaluation metrics** | `evaluation_metrics.json` | Precision, recall, F1, hit rate, NDCG, coverage |

#### model_metadata.json Schema

```json
{
  "version": "v1752220800",
  "active_filename": "ncf_model_v1752220800.pt",
  "trained_at": "2026-07-11T03:00:00Z",
  "training_time_seconds": 142.37,
  "best_epoch": 23,
  "best_val_loss": 0.01847,
  "history": {
    "epochs": [1, 2, 3, "..."],
    "train_losses": [0.15234, 0.09871, 0.07452, "..."],
    "val_losses": [0.14102, 0.09234, 0.07001, "..."]
  }
}
```

#### evaluation_metrics.json Schema

```json
{
  "precision_at_10": 0.3421,
  "recall_at_10": 0.2187,
  "f1_at_10": 0.2667,
  "hit_rate": 0.7845,
  "ndcg": 0.4123,
  "coverage": 0.6534
}
```

#### Checkpoint (.pt) Contents

Each `.pt` file is a PyTorch `torch.save()` checkpoint containing:

```python
{
    "state_dict": model.state_dict(),        # Neural network weights
    "num_users": 1500,                        # User embedding table size
    "num_products": 3200,                     # Product embedding table size
    "embedding_dim": 32,                      # Embedding dimension
    "layers": [64, 32, 16],                   # MLP hidden layer sizes
    "user_to_idx": {1: 0, 2: 1, ...},        # User ID → index mapping
    "product_to_idx": {10: 0, 11: 1, ...},   # Product ID → index mapping
    "idx_to_user": {0: 1, 1: 2, ...},        # Index → User ID mapping
    "idx_to_product": {0: 10, 1: 11, ...},   # Index → Product ID mapping
    "version_id": 1752220800                  # Timestamp version
}
```

---

## Training Pipeline

### Scheduler Architecture

The training scheduler is implemented in `backend/app/services/ml/scheduler.py` and starts automatically via the FastAPI lifespan event.

```
Application Startup (lifespan)
         │
         ▼
    start_scheduler()
         │
    ┌────┴────────────────────┐
    ▼                         ▼
run_daily_pipeline()    run_hourly_metrics_logger()
(asyncio background)    (asyncio background)
    │                         │
    │ Every 24 hours:         │ Every 1 hour:
    │ 1. Hybrid Recommender   │ 1. Reload latest.pt
    │ 2. NCF Training         │ 2. Refresh predictor
    │ 3. NCF Evaluation       │    weights
    │                         │
    │ Retry: 4 attempts       │
    │ Backoff: 5s → 10s →     │
    │          20s → 40s      │
    └─────────────────────────┘
```

### NCF Training Process

The training pipeline (`backend/app/services/deep_learning/train.py`) executes the following steps:

1. **Data Loading** — Builds user-product interaction matrix from database events
2. **Dataset Split** — Creates train/test DataLoaders via `get_ncf_dataloaders()`
3. **Model Initialization** — Creates `NCFModel` with user/product embeddings + MLP layers
4. **Device Placement** — Auto-detects GPU (CUDA/MPS) or falls back to CPU
5. **Training Loop** — MSE loss with Adam optimizer, per-epoch validation
6. **Early Stopping** — Halts training if validation loss doesn't improve for `patience` epochs
7. **Checkpoint Saving** — Saves both `latest.pt` and `ncf_model_v{timestamp}.pt`
8. **Metadata Serialization** — Writes `model_metadata.json` with training history

### Hyperparameters

| Parameter | Default | Description |
|---|---|---|
| `epochs` | `50` | Maximum training epochs |
| `batch_size` | `64` | Samples per training batch |
| `embedding_dim` | `32` | Dimension of user/product embedding vectors |
| `layers` | `[64, 32, 16]` | MLP hidden layer sizes (decreasing) |
| `learning_rate` | `0.005` | Adam optimizer learning rate |
| `patience` | `5` | Early stopping patience (epochs without improvement) |

### Early Stopping

The training loop implements early stopping to prevent overfitting:

```
Epoch 1:  val_loss=0.142  ← best (patience=0)
Epoch 5:  val_loss=0.089  ← best (patience=0)
Epoch 10: val_loss=0.071  ← best (patience=0)
Epoch 11: val_loss=0.073  ↑ worse (patience=1)
Epoch 12: val_loss=0.075  ↑ worse (patience=2)
Epoch 13: val_loss=0.072  ↑ worse (patience=3)
Epoch 14: val_loss=0.074  ↑ worse (patience=4)
Epoch 15: val_loss=0.076  ↑ worse (patience=5 = limit)
→ EARLY STOP: Restore weights from Epoch 10
```

---

## Evaluation Metrics

### Metric Definitions

The `DeepLearningEvaluator` class (`backend/app/services/deep_learning/evaluate.py`) computes these metrics:

| Metric | Formula | Description |
|---|---|---|
| **Precision@K** | `|relevant ∩ recommended| / K` | Fraction of recommended items that are relevant |
| **Recall@K** | `|relevant ∩ recommended| / |relevant|` | Fraction of relevant items that are recommended |
| **F1@K** | `2 × (P@K × R@K) / (P@K + R@K)` | Harmonic mean of precision and recall |
| **Hit Rate** | `users_with_hits / total_users` | Fraction of users who received at least one relevant recommendation |
| **NDCG** | Normalized DCG | Measures ranking quality — higher-ranked relevant items score more |
| **Coverage** | `|unique_recommended| / |all_products|` | Fraction of the catalog represented in recommendations |

### Evaluation Pipeline

The evaluation runs automatically after each training cycle:

```python
# Triggered by scheduler after training
async def run_ncf_evaluation_pipeline(db):
    # 1. Load all users and products
    # 2. Build ground truth from interaction matrix
    # 3. Generate top-10 recommendations per user via NCFPredictor
    # 4. Calculate metrics and save to evaluation_metrics.json
    DeepLearningEvaluator.evaluate_and_save(
        recommendations,   # {user_id: [product_ids]}
        ground_truth,       # {user_id: [actual_product_ids]}
        all_product_ids,
        k=10
    )
```

### Interpreting Results

| Metric | Poor | Acceptable | Good | Excellent |
|---|---|---|---|---|
| Precision@10 | < 0.10 | 0.10–0.25 | 0.25–0.40 | > 0.40 |
| Recall@10 | < 0.05 | 0.05–0.15 | 0.15–0.30 | > 0.30 |
| Hit Rate | < 0.30 | 0.30–0.60 | 0.60–0.80 | > 0.80 |
| NDCG | < 0.15 | 0.15–0.30 | 0.30–0.50 | > 0.50 |
| Coverage | < 0.20 | 0.20–0.40 | 0.40–0.70 | > 0.70 |

> [!NOTE]
> Low coverage with high precision may indicate a popularity bias — the model recommends the same popular items to everyone. Monitor coverage to ensure catalog diversity.

---

## Model Rollback

### API-Driven Rollback

Roll back to any previously trained model version via the system API:

```bash
# List available checkpoints
curl -s http://localhost:8000/api/v1/system/models | jq '.data.checkpoints_registry'
```

Response:
```json
[
  {
    "version": "v1752220800",
    "filename": "ncf_model_v1752220800.pt",
    "file_size_bytes": 2458624,
    "created_at": "2026-07-11T03:00:00Z",
    "framework": "pytorch"
  },
  {
    "version": "v1752134400",
    "filename": "ncf_model_v1752134400.pt",
    "file_size_bytes": 2451200,
    "created_at": "2026-07-10T03:00:00Z",
    "framework": "pytorch"
  }
]
```

```bash
# Rollback to a specific version
curl -X POST http://localhost:8000/api/v1/system/models/rollback/v1752134400

# Response:
# {"success": true, "message": "Model registry rolled back to version v1752134400."}
```

#### What the Rollback Does

1. Locates `ncf_model_v{version}.pt` in `backend/models/`
2. Copies it to `latest.pt` (overwrites current active model)
3. Updates `model_metadata.json` with:
   - `version`: The rollback target version
   - `active_filename`: The restored checkpoint filename
   - `rolled_back_at`: UTC timestamp of the rollback
4. Logs the event via structlog

> [!WARNING]
> Rollback does **not** automatically reload the model into memory. The hourly metrics logger will refresh the in-memory weights within 1 hour, or restart the backend container for immediate effect:
> ```bash
> docker restart journeyiq_backend_prod
> ```

### Manual Rollback

If the API is unavailable, perform a manual rollback:

```bash
# SSH into backend container
docker exec -it journeyiq_backend_prod /bin/bash

# Navigate to models directory
cd /app/models/

# List checkpoints
ls -la ncf_model_v*.pt

# Copy desired version to latest.pt
cp ncf_model_v1752134400.pt latest.pt

# Update metadata (optional but recommended)
python -c "
import json, time
with open('model_metadata.json', 'r+') as f:
    m = json.load(f)
    m['version'] = 'v1752134400'
    m['active_filename'] = 'ncf_model_v1752134400.pt'
    m['rolled_back_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    f.seek(0)
    json.dump(m, f, indent=2)
    f.truncate()
"
```

---

## Inference Statistics

The `NCFModelRegistry` tracks inference telemetry in a thread-safe manner:

```python
# Automatically called during each prediction
NCFModelRegistry.track_inference(duration_seconds=0.0123)

# Query current stats
telemetry = NCFModelRegistry.get_inference_telemetry()
# Returns:
# {
#     "total_inference_calls": 1247,
#     "average_latency_ms": 12.34,
#     "total_latency_seconds": 15.3898
# }
```

### Monitoring Inference via API

```bash
curl -s http://localhost:8000/api/v1/system/models | jq '.data.inference_statistics'
```

### Prometheus Metrics

Inference metrics are exposed at `/api/v1/system/prometheus`:

```
journeyiq_ml_inferences_total 1247
journeyiq_ml_inference_latency_avg_ms 12.3400
journeyiq_ml_model_val_loss 0.01847
```

> [!TIP]
> Set Prometheus alerts for:
> - `journeyiq_ml_inference_latency_avg_ms > 100` — Model may need optimization
> - `journeyiq_ml_inferences_total` not increasing — Inference endpoint may be broken
> - `journeyiq_ml_model_val_loss > 0.5` — Model quality degradation

---

## Cold-Start Fallback Strategy

JourneyIQ handles the cold-start problem (new users/products with no interaction history) through a multi-tier fallback strategy:

```
┌─────────────────────────────────────────────────────────┐
│                  Recommendation Request                  │
│                  for User X, Product Y                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
               ┌─────────────────────┐
               │ NCF Deep Learning   │ ← Primary: Neural Collaborative
               │ Personalized Recs   │   Filtering with PyTorch
               └────────┬────────────┘
                         │
              User/Product in training data?
                    │           │
                   Yes          No
                    │           │
                    ▼           ▼
           ┌──────────┐  ┌──────────────────┐
           │ NCF Top-K│  │ Hybrid Recommender│ ← Fallback Tier 1
           │ Results  │  │ (Content + Collab │
           └──────────┘  │  + Popularity)    │
                         └────────┬─────────┘
                                  │
                        Enough interaction data?
                              │         │
                             Yes        No
                              │         │
                              ▼         ▼
                     ┌──────────┐ ┌───────────────┐
                     │ Hybrid   │ │ Trending /    │ ← Fallback Tier 2
                     │ Ranked   │ │ Popular       │   Popularity-based
                     │ Results  │ │ Products      │   recommendations
                     └──────────┘ └───────────────┘
```

### Strategy Details

| Tier | Strategy | When Used | Source |
|---|---|---|---|
| **Primary** | NCF Deep Learning | User + products exist in training data | `NCFPredictor.recommend_for_user()` |
| **Fallback 1** | Hybrid Recommender | New user or product not in NCF index | `HybridRanker.rank_for_user()` combines content similarity, collaborative filtering, and popularity |
| **Fallback 2** | Trending Products | No interaction data at all | Popularity metrics from `SimilarityEngine.compute_popularity_metrics()` |

### How the Hybrid Ranker Works

The `HybridRanker` (`backend/app/services/ml/hybrid_ranker.py`) combines three signals:

1. **Content Similarity** — TF-IDF or attribute-based similarity between products
2. **Collaborative Filtering** — User-user similarity from interaction patterns
3. **Popularity Score** — Global purchase/view counts

Each signal is weighted and combined into a final ranking score with human-readable explanations stored in the `Recommendation.explanation` field.

---

## Model Comparison Dashboard

The JourneyIQ frontend includes a model comparison dashboard accessible from the admin panel that visualizes:

### Available Views

| View | Description | Data Source |
|---|---|---|
| **Active Model Card** | Current version, training time, best epoch, validation loss | `GET /api/v1/system/models` → `active_model` |
| **Evaluation Metrics** | Precision@K, Recall@K, Hit Rate, NDCG, Coverage gauges | `evaluation_metrics` in active model response |
| **Training History Chart** | Epoch vs. train/val loss curves | `training_history.epochs`, `train_losses`, `val_losses` |
| **Checkpoint Registry** | Table of all available model versions with file sizes and dates | `checkpoints_registry` array |
| **Inference Telemetry** | Total calls, average latency, throughput | `inference_statistics` |
| **Rollback Controls** | Button to rollback to any previous version | `POST /api/v1/system/models/rollback/{version_id}` |

### API Endpoint for Dashboard Data

```bash
curl -s http://localhost:8000/api/v1/system/models | jq '.'
```

```json
{
  "success": true,
  "message": "MLOps model metadata stats read.",
  "data": {
    "active_model": {
      "active_version": "v1752220800",
      "active_filename": "ncf_model_v1752220800.pt",
      "trained_at": "2026-07-11T03:00:00Z",
      "training_time_seconds": 142.37,
      "framework": "pytorch",
      "best_epoch": 23,
      "best_val_loss": 0.01847,
      "evaluation_metrics": {
        "precision_at_10": 0.3421,
        "recall_at_10": 0.2187,
        "f1_at_10": 0.2667,
        "hit_rate": 0.7845,
        "ndcg": 0.4123,
        "coverage": 0.6534
      },
      "training_history": {
        "epochs": [1, 2, 3],
        "train_losses": [0.152, 0.098, 0.074],
        "val_losses": [0.141, 0.092, 0.070]
      }
    },
    "inference_statistics": {
      "total_inference_calls": 1247,
      "average_latency_ms": 12.34,
      "total_latency_seconds": 15.39
    },
    "checkpoints_registry": [
      {
        "version": "v1752220800",
        "filename": "ncf_model_v1752220800.pt",
        "file_size_bytes": 2458624,
        "created_at": "2026-07-11T03:00:00Z",
        "framework": "pytorch"
      }
    ]
  }
}
```

---

## Monitoring & Alerts

### Recommended Alert Thresholds

| Metric | Condition | Severity | Action |
|---|---|---|---|
| Model val_loss | > 0.50 | 🔴 Critical | Investigate training data quality, consider rollback |
| Inference latency | > 100ms avg | 🟡 Warning | Check model complexity, server resources |
| Inference calls | 0 for 1 hour | 🔴 Critical | Model may not be loaded; check logs |
| Hit rate | < 0.30 | 🟡 Warning | Model may need retraining with more data |
| Coverage | < 0.20 | 🟡 Warning | Popularity bias detected; tune hybrid weights |
| Scheduler status | `degraded` | 🔴 Critical | Training pipeline failed; check `SCHEDULER_HEALTH` |
| Checkpoint count | > 30 | 🟢 Info | Clean up old checkpoints to free disk space |

### Checkpoint Cleanup

```bash
# Keep only the last 7 checkpoints
cd backend/models/
ls -t ncf_model_v*.pt | tail -n +8 | xargs rm -f
```

> [!CAUTION]
> Always verify the active model's checkpoint is not in the deletion list. Check `model_metadata.json → active_filename` before cleanup.

---

*For backup and disaster recovery procedures, see [BACKUP.md](BACKUP.md). For production monitoring runbook, see [RUNBOOK.md](RUNBOOK.md).*

import json
import os
import shutil
import threading
import time
from typing import Any

import structlog

logger = structlog.get_logger()
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))

# Thread-safe global store for live inference statistics
_stats_lock = threading.Lock()
_INFERENCE_COUNT = 0
_TOTAL_INFERENCE_TIME = 0.0

class NCFModelRegistry:
    """Manages Deep Learning PyTorch NCF Model versioning, rollbacks, metadata, and telemetry."""

    @staticmethod
    def track_inference(duration_seconds: float) -> None:
        """Accumulates inference count and latency telemetry."""
        global _INFERENCE_COUNT, _TOTAL_INFERENCE_TIME
        with _stats_lock:
            _INFERENCE_COUNT += 1
            _TOTAL_INFERENCE_TIME += duration_seconds

    @staticmethod
    def get_inference_telemetry() -> dict[str, Any]:
        """Returns live inference counts and average execution latencies."""
        global _INFERENCE_COUNT, _TOTAL_INFERENCE_TIME
        with _stats_lock:
            count = _INFERENCE_COUNT
            total_time = _TOTAL_INFERENCE_TIME

        avg_ms = (total_time / count) * 1000 if count > 0 else 0.0
        return {
            "total_inference_calls": count,
            "average_latency_ms": round(avg_ms, 2),
            "total_latency_seconds": round(total_time, 4)
        }

    @staticmethod
    def list_checkpoints() -> list[dict[str, Any]]:
        """Scans models directory for PyTorch checkpoints and parses version metadata."""
        checkpoints = []
        if not os.path.exists(MODEL_DIR):
            return []

        for filename in os.listdir(MODEL_DIR):
            if filename.startswith("ncf_model_v") and filename.endswith(".pt"):
                file_path = os.path.join(MODEL_DIR, filename)
                try:
                    # Extract timestamp version from file name
                    version_raw = filename.replace("ncf_model_v", "").replace(".pt", "")
                    mtime = os.path.getmtime(file_path)

                    checkpoints.append({
                        "version": f"v{version_raw}",
                        "filename": filename,
                        "file_size_bytes": os.path.getsize(file_path),
                        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(mtime)),
                        "framework": "pytorch"
                    })
                except Exception as e:
                    logger.warning("Error reading model checkpoint file", filename=filename, error=str(e))

        # Sort by creation time descending
        checkpoints.sort(key=lambda x: x["version"], reverse=True)
        return checkpoints

    @staticmethod
    def get_active_model() -> dict[str, Any]:
        """Fetches metadata, metrics, and state of the currently loaded model."""
        metadata = {}
        metrics = {}

        metadata_path = os.path.join(MODEL_DIR, "model_metadata.json")
        metrics_path = os.path.join(MODEL_DIR, "evaluation_metrics.json")

        if os.path.exists(metadata_path):
            try:
                with open(metadata_path) as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.error("Failed to read model_metadata.json", error=str(e))

        if os.path.exists(metrics_path):
            try:
                with open(metrics_path) as f:
                    metrics = json.load(f)
            except Exception as e:
                logger.error("Failed to read evaluation_metrics.json", error=str(e))

        return {
            "active_version": metadata.get("version", "v0.0"),
            "active_filename": metadata.get("active_filename", "latest.pt"),
            "trained_at": metadata.get("trained_at", "N/A"),
            "training_time_seconds": metadata.get("training_time_seconds", 0.0),
            "framework": "pytorch",
            "best_epoch": metadata.get("best_epoch", 0),
            "best_val_loss": metadata.get("best_val_loss", 0.0),
            "evaluation_metrics": metrics,
            "training_history": metadata.get("history", {})
        }

    @staticmethod
    def rollback_to_version(version_id: str) -> bool:
        """
        Restores a versioned model checkpoint by copying it to latest.pt.
        Updates model_metadata.json configuration settings.
        """
        # Strip leading 'v' if provided
        version_num = version_id.lstrip('v')
        target_filename = f"ncf_model_v{version_num}.pt"
        target_path = os.path.join(MODEL_DIR, target_filename)
        latest_path = os.path.join(MODEL_DIR, "latest.pt")
        metadata_json_path = os.path.join(MODEL_DIR, "model_metadata.json")

        if not os.path.exists(target_path):
            logger.error("Rollback failed. Versioned checkpoint file not found", filename=target_filename)
            return False

        try:
            # Overwrite latest.pt
            shutil.copy2(target_path, latest_path)

            # Read existing metadata and update active version
            metadata = {}
            if os.path.exists(metadata_json_path):
                try:
                    with open(metadata_json_path) as f:
                        metadata = json.load(f)
                except Exception:
                    pass

            metadata["version"] = f"v{version_num}"
            metadata["active_filename"] = target_filename
            metadata["rolled_back_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            with open(metadata_json_path, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info("Successfully rolled back active model version", version=f"v{version_num}")
            return True
        except Exception as e:
            logger.error("Failed to perform model registry rollback", error=str(e))
            return False

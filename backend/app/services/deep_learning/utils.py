import os

import torch


def get_device() -> torch.device:
    """Returns CUDA GPU device if available, otherwise CPU."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def ensure_dir_exists(path: str) -> None:
    """Ensures parent directory for the given path exists."""
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

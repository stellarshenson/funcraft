"""The Hugging Face model caches the service knows: their folders under `HF_HOME` and their sizes."""

import os
import shutil
from pathlib import Path

HF_HOME = os.environ.get("HF_HOME") or str(Path.home() / ".cache/huggingface")

MODELS = {
    "s2pro": "fishaudio/s2-pro",
    "nemotron": "nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B",
}


def cache_dir(name: str) -> Path:
    """The hub's cache directory for `name`: `hub/models--<org>--<model>` under `HF_HOME`.

    Args:
        name: a key of `MODELS`.

    Returns:
        The directory the hub writes the model's blobs and snapshots into.
    """
    return Path(HF_HOME) / "hub" / ("models--" + MODELS[name].replace("/", "--"))


def real_files(path: Path) -> set[Path]:
    """Every real file `path` holds or links to, each stored file once.

    The hub keeps each blob in a shared store and links it from `snapshots/<rev>/`, so a link is
    resolved: the blob counts once however many links reach it, a blob outside the model directory
    counts too, and a broken link counts nothing.

    Args:
        path: the model's cache directory.

    Returns:
        The resolved paths of the files; empty when `path` is absent or holds none.
    """
    files: set[Path] = set()
    for root, _, names in os.walk(path, followlinks=False):
        for name in names:
            target = Path(root, name).resolve()
            if target.is_file():
                files.add(target)
    return files


def tree_bytes(path: Path) -> int:
    """The total size of the real files under `path` or linked from it, each stored file once.

    Args:
        path: the model's cache directory.

    Returns:
        The summed sizes in bytes; 0 when the path is absent or not a directory.
    """
    return sum(target.stat().st_size for target in real_files(path))


def delete(name: str) -> int:
    """Remove a model's cache and the shared blobs no other known model links to.

    Args:
        name: a key of `MODELS`.

    Returns:
        The bytes freed: the files of the model directory plus the shared blobs unlinked; a blob
        another model still links to stays and adds nothing; 0 when the cache is absent.
    """
    path = cache_dir(name)
    if not path.is_dir():
        return 0
    root = path.resolve()
    own = real_files(path)
    referenced = {target for other in MODELS if other != name
                  for target in real_files(cache_dir(other))}
    freed = sum(target.stat().st_size for target in own if target.is_relative_to(root))
    shutil.rmtree(path)
    for target in own:
        if target.is_relative_to(root) or target in referenced:
            continue
        freed += target.stat().st_size
        target.unlink()
    return freed


def describe(name: str, loaded: bool) -> dict:
    """One model's cache entry for `GET /models`.

    Args:
        name: a key of `MODELS`.
        loaded: whether the model is in memory now.

    Returns:
        `{"name", "model", "path", "cached", "bytes", "loaded"}`.
    """
    path = cache_dir(name)
    return {"name": name, "model": MODELS[name], "path": str(path), "cached": path.is_dir(),
            "bytes": tree_bytes(path), "loaded": loaded}

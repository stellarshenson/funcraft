"""Download one Hugging Face model at a fixed revision into the local cache and print its path.

Usage: fetch_model.py <repo_id> <revision>
"""
import sys

from huggingface_hub import snapshot_download

repo_id, revision = sys.argv[1], sys.argv[2]
print(snapshot_download(repo_id=repo_id, revision=revision))

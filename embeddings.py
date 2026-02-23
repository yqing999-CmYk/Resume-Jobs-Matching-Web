"""
OpenAI embedding generation with disk caching.

Cache layout  (backend/cache/):
  <sha256_of_text>.npy   — the embedding vector
"""
import hashlib
from pathlib import Path

import numpy as np
from openai import OpenAI

from backend.config import CACHE_DIR, EMBEDDING_MODEL, OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY)


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def get_embedding(text: str, use_cache: bool = True) -> np.ndarray:
    """
    Return a 1-D numpy float32 array for the given text.
    Results are cached to disk by content hash.
    """
    h = _text_hash(text)
    cache_file = CACHE_DIR / f"{h}.npy"

    if use_cache and cache_file.exists():
        return np.load(str(cache_file))

    response = _client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    vector = np.array(response.data[0].embedding, dtype=np.float32)

    if use_cache:
        np.save(str(cache_file), vector)

    return vector


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors. Returns float in [-1, 1]."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

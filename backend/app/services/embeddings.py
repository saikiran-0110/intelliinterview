"""OpenAI embeddings for semantic skill retrieval. Deterministic given a key: the
same text through the same pinned embedding model always returns the same vector,
so (unlike chat completions) this is safe to let feed the match score."""

from __future__ import annotations

import logging

import httpx
import numpy as np

from app.config import settings
from app.services.skill_catalog import chunk_document

logger = logging.getLogger(__name__)

# Canonical skill-phrase vectors are embedded once per server run, not once per
# analysis - there are only ~40 of them and they never change within a process.
_skill_phrase_cache: dict[str, list[float]] = {}


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Embed a batch of texts in a single request. Returns None (never raises) when
    no API key is configured or the request fails for any reason - callers must
    treat that as "semantic layer unavailable" and fall back to lexical-only behaviour."""
    if not settings.openai_api_key:
        logger.info("embeddings: no OpenAI API key configured, semantic retrieval skipped")
        return None
    if not texts:
        return []

    try:
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.openai_embedding_model, "input": texts},
            timeout=45.0,
        )
        response.raise_for_status()
        payload = response.json()
        return [item["embedding"] for item in payload["data"]]
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "embeddings: OpenAI returned status %s: %s",
            exc.response.status_code,
            exc.response.text[:300],
        )
        return None
    except httpx.HTTPError as exc:
        logger.warning("embeddings: OpenAI request failed: %s", exc)
        return None
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning("embeddings: could not parse OpenAI response: %s", exc)
        return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    vec_a = np.asarray(a, dtype=float)
    vec_b = np.asarray(b, dtype=float)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def get_skill_phrase_embedding(skill: str, phrase: str) -> list[float] | None:
    """Cached per canonical skill for the lifetime of the process."""
    if skill in _skill_phrase_cache:
        return _skill_phrase_cache[skill]
    vectors = embed_texts([phrase])
    if not vectors:
        return None
    vector = vectors[0]
    _skill_phrase_cache[skill] = vector
    return vector


def clear_skill_phrase_cache() -> None:
    """Test-only: let tests observe a cold cache instead of leaking state between them."""
    _skill_phrase_cache.clear()


def build_embedded_chunks(text: str) -> list[dict[str, object]] | None:
    """Chunk a CV/document body and embed every chunk in one batched call. Returns
    None when there is nothing to store (no key, embedding failure, or no text) -
    callers must treat that as "store nothing and carry on", never fail the caller."""
    chunks = chunk_document(text)
    if not chunks:
        return None
    vectors = embed_texts(chunks)
    if not vectors:
        return None
    return [{"text": chunk, "vector": vector} for chunk, vector in zip(chunks, vectors)]

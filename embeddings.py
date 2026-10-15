"""Shared helper: turn text into a vector (Gemini embeddings, free tier has real
quota for this) and rank stored vectors by relevance. No vector DB needed at
this scale — cosine similarity in-process over a few hundred/thousand rows is
instant.
"""
import logging

import numpy as np

import config

log = logging.getLogger("embeddings")

EMBED_MODEL = "gemini-embedding-001"


def embed(text: str) -> bytes | None:
    """Return a fact/memory's embedding as raw bytes (for storing in SQLite),
    or None if the embeddings call failed (caller should still save the text)."""
    try:
        from google import genai

        client = genai.Client(api_key=config.GEMINI_API_KEY)
        resp = client.models.embed_content(model=EMBED_MODEL, contents=text)
        vector = np.array(resp.embeddings[0].values, dtype=np.float32)
        return vector.tobytes()
    except Exception as e:
        log.warning("embed() failed, will store without a vector: %s", str(e)[:200])
        return None


def _to_array(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def rank_by_similarity(query_text: str, rows: list[tuple[int, bytes | None]], top_k: int = 8) -> list[int]:
    """rows: list of (row_id, embedding_blob_or_None). Returns row_ids of the
    top_k most relevant, most similar first. Rows without an embedding are
    ranked last (in original order) rather than dropped."""
    query_vec = embed(query_text)
    if query_vec is None:
        return [rid for rid, _ in rows][:top_k]
    q = _to_array(query_vec)
    q_norm = np.linalg.norm(q) or 1.0

    scored, unscored = [], []
    for rid, blob in rows:
        if blob is None:
            unscored.append(rid)
            continue
        v = _to_array(blob)
        sim = float(np.dot(q, v) / (q_norm * (np.linalg.norm(v) or 1.0)))
        scored.append((sim, rid))
    scored.sort(key=lambda x: x[0], reverse=True)
    ordered = [rid for _, rid in scored] + unscored
    return ordered[:top_k]

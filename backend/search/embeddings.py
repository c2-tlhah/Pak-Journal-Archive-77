"""
Video Embedding Manager — LaBSE + FAISS
========================================
Generates dense 768-dim embeddings from video metadata (summary + topics + entities)
using the LaBSE model already in the tagging pipeline.

Maintains a FAISS IndexFlatIP (inner-product on L2-normalised vectors = cosine sim)
that is rebuilt from the PostgreSQL `video_embeddings` table at startup and updated
incrementally when new videos are processed.
"""

import os
import logging
import threading
from typing import List, Dict, Optional, Tuple

import numpy as np
import faiss
import psycopg2

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton LaBSE loader (lazy, thread-safe)
# ---------------------------------------------------------------------------
_labse_lock = threading.Lock()
_labse_model = None


def _get_labse():
    """Load LaBSE once and cache it. Thread-safe."""
    global _labse_model
    if _labse_model is not None:
        return _labse_model
    with _labse_lock:
        if _labse_model is not None:
            return _labse_model
        import torch
        from sentence_transformers import SentenceTransformer
        logger.info("[Embeddings] Loading LaBSE model …")
        model = SentenceTransformer("sentence-transformers/LaBSE")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.half()
        model.to(device)
        _labse_model = model
        logger.info(f"[Embeddings] LaBSE loaded on {device}")
        return _labse_model


def unload_labse():
    """Free LaBSE from memory (e.g. after batch indexing)."""
    global _labse_model
    if _labse_model is not None:
        import torch, gc
        del _labse_model
        _labse_model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("[Embeddings] LaBSE unloaded")


# ---------------------------------------------------------------------------
# Embedding generation
# ---------------------------------------------------------------------------
def build_embedding_input(summaries: List[str],
                          topics: List[str],
                          entities: List[str],
                          category: str = "") -> str:
    """Concatenate video metadata into a single text for embedding.

    Target ~400 tokens so LaBSE's 512-token window isn't wasted.
    Structure:  [summaries] [category] [topics] [entities]
    """
    parts = []

    # Summaries — most informative, take the bulk
    summary_text = " ".join(s.strip() for s in summaries if s.strip())
    if summary_text:
        # Rough limit: ~250 tokens ≈ 800 chars for Urdu
        parts.append(summary_text[:800])

    if category and category != "unknown":
        parts.append(category)

    # Topics — top keywords
    if topics:
        parts.append(" ".join(topics[:15]))

    # Entities — person/org/location names
    if entities:
        parts.append(" ".join(entities[:15]))

    return " ".join(parts).strip()


def generate_embedding(text: str) -> np.ndarray:
    """Encode a single text into a 768-dim L2-normalised float32 vector."""
    model = _get_labse()
    vec = model.encode([text], batch_size=1, show_progress_bar=False,
                       convert_to_numpy=True, normalize_embeddings=True)
    return vec[0].astype(np.float32)


def generate_embeddings_batch(texts: List[str],
                              batch_size: int = 32) -> np.ndarray:
    """Encode multiple texts. Returns (N, 768) float32 matrix."""
    model = _get_labse()
    vecs = model.encode(texts, batch_size=batch_size, show_progress_bar=True,
                        convert_to_numpy=True, normalize_embeddings=True)
    return vecs.astype(np.float32)


# ---------------------------------------------------------------------------
# PostgreSQL helpers (one-off connections, same pattern as tagging.py)
# ---------------------------------------------------------------------------
def _get_pg_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "pak_journal_archive"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def save_embedding(video_id: str, embedding: np.ndarray,
                   embedding_input: str = "") -> bool:
    """Upsert a video embedding into PostgreSQL."""
    conn = None
    try:
        conn = _get_pg_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO video_embeddings (video_id, embedding, embedding_input,
                                          model_name, dimensions)
            VALUES (%s, %s, %s, 'LaBSE', 768)
            ON CONFLICT (video_id) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                embedding_input = EXCLUDED.embedding_input,
                updated_at = CURRENT_TIMESTAMP
        """, (video_id, embedding.tobytes(), embedding_input))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        logger.error(f"[Embeddings] save_embedding failed: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def load_all_embeddings() -> Tuple[List[str], np.ndarray]:
    """Load every video embedding from DB.
    Returns (video_ids: List[str], matrix: np.ndarray[N,768]).
    """
    conn = None
    try:
        conn = _get_pg_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT video_id::text, embedding, dimensions
            FROM video_embeddings
            ORDER BY created_at
        """)
        rows = cur.fetchall()
        cur.close()

        if not rows:
            return [], np.empty((0, 768), dtype=np.float32)

        video_ids = []
        vectors = []
        for vid, emb_bytes, dims in rows:
            vec = np.frombuffer(emb_bytes, dtype=np.float32)
            if vec.shape[0] == dims:
                video_ids.append(vid)
                vectors.append(vec)
            else:
                logger.warning(f"[Embeddings] Skipping {vid}: bad shape {vec.shape}")

        matrix = np.vstack(vectors) if vectors else np.empty((0, 768), dtype=np.float32)
        logger.info(f"[Embeddings] Loaded {len(video_ids)} embeddings from DB")
        return video_ids, matrix

    except Exception as e:
        logger.error(f"[Embeddings] load_all_embeddings failed: {e}")
        return [], np.empty((0, 768), dtype=np.float32)
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# FAISS Index Manager
# ---------------------------------------------------------------------------
class FAISSIndex:
    """In-memory FAISS index with video_id mapping.

    Uses IndexFlatIP (inner product) on L2-normalised vectors,
    which is equivalent to cosine similarity.
    """

    def __init__(self, dim: int = 768):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.video_ids: List[str] = []          # positional mapping
        self._lock = threading.Lock()
        logger.info(f"[FAISS] Empty index created (dim={dim})")

    # -- build from DB --
    def rebuild(self) -> int:
        """Reload all embeddings from PostgreSQL and rebuild the index."""
        video_ids, matrix = load_all_embeddings()
        with self._lock:
            self.index = faiss.IndexFlatIP(self.dim)
            self.video_ids = video_ids
            if len(video_ids) > 0:
                self.index.add(matrix)
        logger.info(f"[FAISS] Index rebuilt with {self.index.ntotal} vectors")
        return self.index.ntotal

    # -- incremental add --
    def add(self, video_id: str, embedding: np.ndarray):
        """Add a single vector. If video_id already present, rebuild to avoid dupes."""
        with self._lock:
            if video_id in self.video_ids:
                # Easiest path: just rebuild (rare — only on re-process)
                pass
            else:
                vec = embedding.reshape(1, -1).astype(np.float32)
                self.index.add(vec)
                self.video_ids.append(video_id)
                return
        # Rebuild if dupe detected (outside lock to avoid recursion)
        self.rebuild()

    # -- search --
    def search(self, query_embedding: np.ndarray,
               top_k: int = 50) -> List[Tuple[str, float]]:
        """Return up to top_k (video_id, cosine_score) pairs, descending."""
        if self.index.ntotal == 0:
            return []
        with self._lock:
            k = min(top_k, self.index.ntotal)
            query = query_embedding.reshape(1, -1).astype(np.float32)
            scores, indices = self.index.search(query, k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:
                    continue
                results.append((self.video_ids[idx], float(score)))
        return results

    @property
    def count(self) -> int:
        return self.index.ntotal


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_faiss_index: Optional[FAISSIndex] = None


def get_faiss_index() -> FAISSIndex:
    """Return the global FAISS index (creates + rebuilds on first call)."""
    global _faiss_index
    if _faiss_index is None:
        _faiss_index = FAISSIndex(dim=768)
        _faiss_index.rebuild()
    return _faiss_index


def init_faiss_index() -> int:
    """Explicitly initialise / rebuild the FAISS index. Returns vector count."""
    idx = get_faiss_index()
    return idx.rebuild()

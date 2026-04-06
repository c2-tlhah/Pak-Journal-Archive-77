"""
Query Processor — Two-Stage Entity Matching
=============================================
Stage 1 : Fuzzy-match query tokens against existing entities in PostgreSQL (fast)
Stage 2 : If no confident match → run NER on the query (smarter, heavier)

Also extracts keywords and generates the query embedding.
"""

import os
import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Urdu normalisation (copied from tagging.py to avoid circular imports)
# ---------------------------------------------------------------------------
_ALEF_VARIANTS  = re.compile(r"[\u0622\u0623\u0625\u0672\u0673\u0675]")
_YEH_VARIANTS   = re.compile(r"[\u0649\u06CC\u06CD\u06D0\u06D2]")
_HAMZA_VARIANTS = re.compile(r"[\u0654\u0655]")
_DIACRITICS     = re.compile(r"[\u064B-\u065F\u0670]")

URDU_STOPWORDS = frozenset([
    "میں", "ہم", "تم", "آپ", "وہ", "یہ", "اس", "ان", "جو", "کوئی", "کچھ",
    "سب", "کا", "کی", "کے", "نے", "کو", "سے", "پر", "تک", "لیے", "ساتھ",
    "اور", "یا", "لیکن", "مگر", "اگر", "تو", "کہ", "جب", "پھر", "اب",
    "ہے", "ہیں", "تھا", "تھی", "تھے", "ہوں", "ہو", "ہوا", "ہوئی", "ہوئے",
    "گیا", "گئی", "گئے", "رہا", "رہی", "رہے", "والے", "والا", "والی",
    "بھی", "ہی", "نہیں", "نہ", "مت", "بہت", "بعد", "پہلے", "دوران",
    "the", "a", "an", "is", "was", "were", "are", "of", "in", "on", "for",
    "to", "with", "and", "or", "but", "not", "from", "by", "at", "about",
])


def normalize_urdu(text: str) -> str:
    """Minimal Urdu normalization — Alef/Yeh/Hamza/diacritics."""
    if not text:
        return ""
    text = _ALEF_VARIANTS.sub("\u0627", text)
    text = _YEH_VARIANTS.sub("\u06CC", text)
    text = _HAMZA_VARIANTS.sub("", text)
    text = _DIACRITICS.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class QueryResult:
    """Processed output of a user query."""
    raw_query: str
    normalized_query: str
    embedding: np.ndarray
    matched_entities: List[Dict] = field(default_factory=list)
    # e.g. [{"text": "عمران خان", "type": "PER", "score": 95.0}]
    keywords: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def _get_pg_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "pak_journal_archive"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def _load_all_entities() -> List[Dict]:
    """Fetch distinct (entity_text, entity_type) from all videos."""
    conn = None
    try:
        conn = _get_pg_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT DISTINCT entity_text, entity_type
            FROM entities
            ORDER BY entity_text
        """)
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"[QueryProcessor] load entities failed: {e}")
        return []
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Stage 1: Fuzzy entity matching against DB
# ---------------------------------------------------------------------------
def _fuzzy_match_entities(query_text: str,
                          all_entities: List[Dict],
                          threshold: int = 75) -> List[Dict]:
    """Match query tokens and n-grams against known entities.

    Returns matches with fuzzy score >= threshold.
    """
    norm_query = normalize_urdu(query_text)
    tokens = norm_query.split()
    if not tokens:
        return []

    # Build n-grams (1, 2, 3 tokens) from the query
    ngrams = set()
    for n in range(1, min(4, len(tokens) + 1)):
        for i in range(len(tokens) - n + 1):
            ngrams.add(" ".join(tokens[i:i + n]))

    matches = []
    seen = set()
    for ent in all_entities:
        ent_text = ent["entity_text"]
        ent_norm = normalize_urdu(ent_text)
        if not ent_norm:
            continue

        best_score = 0
        for ng in ngrams:
            score = fuzz.ratio(ng, ent_norm)
            best_score = max(best_score, score)
            if score >= threshold:
                break

        if best_score >= threshold and ent_text not in seen:
            matches.append({
                "text": ent_text,
                "type": ent["entity_type"],
                "score": best_score,
            })
            seen.add(ent_text)

    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches


# ---------------------------------------------------------------------------
# Stage 2: NER fallback (only fires if Stage 1 finds nothing)
# ---------------------------------------------------------------------------
_ner_pipeline = None


def _run_ner_on_query(query_text: str) -> List[Dict]:
    """Run the WikiANN NER model on the query text.
    Returns list of {"text", "type", "score"}.
    """
    global _ner_pipeline

    if _ner_pipeline is None:
        try:
            from transformers import pipeline as hf_pipeline
            import torch
            device = 0 if torch.cuda.is_available() else -1
            _ner_pipeline = hf_pipeline(
                "ner",
                model="Davlan/xlm-roberta-base-wikiann-ner",
                aggregation_strategy="simple",
                device=device,
            )
            logger.info("[QueryProcessor] NER pipeline loaded for query processing")
        except Exception as e:
            logger.error(f"[QueryProcessor] NER load failed: {e}")
            return []

    try:
        ner_results = _ner_pipeline(query_text)
    except Exception as e:
        logger.warning(f"[QueryProcessor] NER inference failed: {e}")
        return []

    # Map labels: B-PER/I-PER → PER, etc.
    _type_map = {"PER": "PER", "ORG": "ORG", "LOC": "LOC"}
    entities = []
    seen = set()
    for ent in ner_results:
        text = ent.get("word", "").replace("▁", " ").strip()
        raw_label = ent.get("entity_group", "")
        etype = _type_map.get(raw_label, raw_label)
        if etype not in ("PER", "ORG", "LOC"):
            continue
        score = float(ent.get("score", 0))
        if text and text not in seen and len(text) >= 2 and score >= 0.50:
            entities.append({"text": text, "type": etype, "score": score * 100})
            seen.add(text)
    return entities


# ---------------------------------------------------------------------------
# Keyword extraction (lightweight — just tokenize + filter)
# ---------------------------------------------------------------------------
def _extract_keywords(query_text: str) -> List[str]:
    """Simple keyword extraction: tokens that aren't stopwords, ≥ 2 chars."""
    norm = normalize_urdu(query_text)
    tokens = norm.split()
    keywords = []
    for tok in tokens:
        if tok not in URDU_STOPWORDS and len(tok) >= 2:
            keywords.append(tok)
    return keywords


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def process_query(query_text: str,
                  ner_fallback: bool = True) -> QueryResult:
    """Process a search query:
    1. Normalize text
    2. Generate LaBSE embedding
    3. Two-stage entity matching (fuzzy → NER)
    4. Keyword extraction

    Parameters
    ----------
    query_text : str
        Raw user query (Urdu, English, or mixed).
    ner_fallback : bool
        If True, run NER when fuzzy matching yields no results.

    Returns
    -------
    QueryResult
    """
    from search.embeddings import generate_embedding

    normalized = normalize_urdu(query_text)
    logger.info(f"[QueryProcessor] Processing query: '{normalized}'")

    # 1. Generate embedding
    embedding = generate_embedding(normalized if normalized else query_text)

    # 2. Two-stage entity matching
    all_entities = _load_all_entities()
    matched = _fuzzy_match_entities(query_text, all_entities, threshold=75)

    if not matched and ner_fallback:
        logger.info("[QueryProcessor] Stage 1 no match → running NER fallback")
        ner_entities = _run_ner_on_query(query_text)
        # Cross-check NER results against DB entities for better matching
        if ner_entities and all_entities:
            for ne in ner_entities:
                sub_matches = _fuzzy_match_entities(ne["text"], all_entities, threshold=70)
                for sm in sub_matches:
                    if sm["text"] not in {m["text"] for m in matched}:
                        matched.append(sm)
        # If still nothing, keep raw NER results (novel entity in query)
        if not matched:
            matched = ner_entities

    # 3. Keywords
    keywords = _extract_keywords(query_text)

    logger.info(f"[QueryProcessor] Entities={len(matched)}, Keywords={len(keywords)}")
    return QueryResult(
        raw_query=query_text,
        normalized_query=normalized,
        embedding=embedding,
        matched_entities=matched,
        keywords=keywords,
    )

"""
Hybrid Search Engine — DB Queries + FAISS Semantic + Cross-Language
====================================================================
Leg 1-6 : Direct SQL on speaker, category, entities, tags, title, transcript
Leg 7   : FAISS semantic search (cosine via LaBSE) — bonus when embeddings exist

Entity quality filter strips garbage NER output before display.
"""

import os
import re
import logging
from typing import Dict, List

import numpy as np

from database.db_config import get_db_cursor
from database.video_models import Entity

logger = logging.getLogger(__name__)

# ── English ↔ Urdu category map ──────────────────────────────────────────
EN_TO_UR_CATEGORIES = {
    'politics': 'سیاست', 'political': 'سیاست', 'government': 'سیاست',
    'economy': 'معیشت', 'economic': 'معیشت', 'finance': 'معیشت', 'imf': 'معیشت',
    'security': 'سلامتی', 'defense': 'سلامتی', 'defence': 'سلامتی', 'military': 'سلامتی',
    'science': 'سائنس', 'technology': 'سائنس', 'tech': 'سائنس',
    'education': 'تعلیم', 'sports': 'کھیل', 'health': 'صحت',
    'religion': 'مذہب', 'culture': 'ثقافت', 'law': 'قانون',
}
UR_CATEGORIES = set(EN_TO_UR_CATEGORIES.values()) | {
    'سیاست', 'معیشت', 'سلامتی', 'سائنس', 'تعلیم', 'کھیل', 'صحت', 'مذہب', 'ثقافت', 'قانون',
}

# ── Speaker aliases (English variants → canonical name) ──────────────────
SPEAKER_ALIASES = {
    'nawaz': 'Nawaz Sharif', 'nawaz sharif': 'Nawaz Sharif', 'pmln': 'Nawaz Sharif',
    'shahbaz': 'Shahbaz Sharif', 'shahbaz sharif': 'Shahbaz Sharif',
    'imran': 'Imran Khan', 'imran khan': 'Imran Khan', 'pti': 'Imran Khan', 'ik': 'Imran Khan',
    'asim': 'Asim Munir', 'asim munir': 'Asim Munir',
    'نواز': 'Nawaz Sharif', 'شہباز': 'Shahbaz Sharif', 'عمران': 'Imran Khan',
}

# ── Common English ↔ Urdu keyword/entity map for cross-language search ───
EN_TO_UR_KEYWORDS = {
    'pakistan': 'پاکستان', 'india': 'ہندوستان', 'china': 'چین',
    'lahore': 'لاہور', 'karachi': 'کراچی', 'islamabad': 'اسلام آباد',
    'peshawar': 'پشاور', 'quetta': 'کوئٹہ',
    'army': 'فوج', 'media': 'میڈیا', 'court': 'عدالت',
    'election': 'الیکشن', 'corruption': 'کرپشن', 'terrorism': 'دہشتگردی',
    'flood': 'سیلاب', 'cricket': 'کرکٹ',
}


# ── Entity quality filter ────────────────────────────────────────────────
# Urdu speech openers / address phrases that NER mis-tags as entities
_GARBAGE_PREFIXES = (
    'میری ', 'ہماری ', 'عزیز ', 'بسم اللہ',
    'اپ کی اپ', 'اپ کی اپنی',
)
# Common Urdu particles / fragments that aren't real entities
_GARBAGE_EXACT = {
    'یں', 'جن', 'فت', 'ڈی', 'وں', 'اس', 'پی', 'کر', 'نی', 'اپ',
    'دل', 'نا', 'سپ', 'جی', 'سی', 'کی', 'کا', 'ہی', 'تو', 'بی',
}
# Patterns that signal sentence fragments rather than entity names
_FRAGMENT_PATTERN = re.compile(
    r'(سی نمٹنی|سی دہشتگردی|نی ریاست|نی دشمن|کی راہ بی|نوجوانوں السلام)',
)


def is_quality_entity(entity_text: str) -> bool:
    """Return True if entity_text looks like a real named entity."""
    text = entity_text.strip()
    # Too short (single Urdu char / particle)
    if len(text) < 3:
        return False
    # Too long — sentence fragment
    if len(text) > 30:
        return False
    # Too many words — likely a sentence fragment
    if len(text.split()) > 5:
        return False
    # Exact garbage match
    if text in _GARBAGE_EXACT:
        return False
    # Speech opener prefix
    for prefix in _GARBAGE_PREFIXES:
        if text.startswith(prefix):
            return False
    # Known fragment patterns
    if _FRAGMENT_PATTERN.search(text):
        return False
    return True


def filter_entities(entities: list) -> list:
    """Filter a list of entity dicts, keeping only quality entries."""
    return [e for e in entities if is_quality_entity(e.get('entity_text', ''))]


def _expand_query(query: str) -> dict:
    """Analyse query and produce cross-language expansions."""
    q_lower = query.lower().strip()
    terms = [t for t in q_lower.split() if len(t) >= 2]
    # Build bigrams too  ("nawaz sharif" from "nawaz sharif economy")
    bigrams = [f"{terms[i]} {terms[i+1]}" for i in range(len(terms) - 1)] if len(terms) >= 2 else []

    # Category expansion
    category_matches = set()
    for en, ur in EN_TO_UR_CATEGORIES.items():
        if en in q_lower:
            category_matches.add(ur)
    for ur_cat in UR_CATEGORIES:
        if ur_cat in query:
            category_matches.add(ur_cat)

    # Speaker expansion
    speaker_matches = set()
    for alias, full_name in SPEAKER_ALIASES.items():
        if alias in q_lower or alias in query:
            speaker_matches.add(full_name)

    # Keyword/entity cross-language expansion
    urdu_expansions = set()
    for en, ur in EN_TO_UR_KEYWORDS.items():
        if en in q_lower:
            urdu_expansions.add(ur)

    return {
        'original': query,
        'lower': q_lower,
        'terms': terms,
        'bigrams': bigrams,
        'category_matches': list(category_matches),
        'speaker_matches': list(speaker_matches),
        'urdu_expansions': list(urdu_expansions),
    }


def _add_score(scores: dict, vid: str, points: float, reason: str):
    """Accumulate score for a video, avoiding duplicate reason bonuses."""
    entry = scores.setdefault(vid, {'total': 0.0, 'reasons': []})
    if reason not in entry['reasons']:
        entry['total'] += points
        entry['reasons'].append(reason)


# ---------------------------------------------------------------------------
# Main search
# ---------------------------------------------------------------------------
def hybrid_search(query_text: str, top_k: int = 20) -> List[Dict]:
    """Search videos via direct DB queries.

    Returns a list of video dicts (same shape as /api/videos) sorted
    by relevance score descending, with extra `search_score` and
    `match_reasons` fields.
    """
    if not query_text or not query_text.strip():
        return []

    logger.info(f"[Search] Query: '{query_text}'")
    exp = _expand_query(query_text)
    q = exp['original']
    scores: Dict[str, dict] = {}

    try:
        with get_db_cursor(commit=False) as cur:

            # ── 1. Speaker search ─────────────────────────────────────
            speaker_conds = ["v.speaker ILIKE %s"]
            speaker_params = [f"%{q}%"]
            for name in exp['speaker_matches']:
                speaker_conds.append("v.speaker ILIKE %s")
                speaker_params.append(f"%{name}%")
            # Also try individual terms
            for term in exp['terms']:
                if len(term) >= 3:
                    speaker_conds.append("v.speaker ILIKE %s")
                    speaker_params.append(f"%{term}%")

            cur.execute(f"""
                SELECT DISTINCT v.id::text AS vid
                FROM videos v
                WHERE v.status = 'completed'
                  AND ({' OR '.join(speaker_conds)})
            """, speaker_params)
            for row in cur.fetchall():
                _add_score(scores, row['vid'], 0.40, 'speaker')

            # ── 2. Category search ────────────────────────────────────
            cat_conds = ["v.category ILIKE %s"]
            cat_params = [f"%{q}%"]
            for cat in exp['category_matches']:
                cat_conds.append("v.category ILIKE %s")
                cat_params.append(f"%{cat}%")
            for term in exp['terms']:
                # Map individual English terms too
                mapped = EN_TO_UR_CATEGORIES.get(term)
                if mapped:
                    cat_conds.append("v.category ILIKE %s")
                    cat_params.append(f"%{mapped}%")

            cur.execute(f"""
                SELECT DISTINCT v.id::text AS vid
                FROM videos v
                WHERE v.status = 'completed'
                  AND v.category IS NOT NULL
                  AND ({' OR '.join(cat_conds)})
            """, cat_params)
            for row in cur.fetchall():
                _add_score(scores, row['vid'], 0.35, 'category')

            # ── 3. Entity search (full query + Urdu expansions) ─────
            ent_conds = ["e.entity_text ILIKE %s"]
            ent_params = [f"%{q}%"]
            for ur in exp['urdu_expansions']:
                ent_conds.append("e.entity_text ILIKE %s")
                ent_params.append(f"%{ur}%")

            cur.execute(f"""
                SELECT DISTINCT e.video_id::text AS vid
                FROM entities e
                JOIN videos v ON v.id = e.video_id
                WHERE v.status = 'completed'
                  AND ({' OR '.join(ent_conds)})
            """, ent_params)
            for row in cur.fetchall():
                _add_score(scores, row['vid'], 0.30, 'entity')

            # Entity search per term (3+ chars)
            for term in exp['terms']:
                if len(term) >= 3:
                    ent_term_conds = ["e.entity_text ILIKE %s"]
                    ent_term_params = [f"%{term}%"]
                    mapped_ur = EN_TO_UR_KEYWORDS.get(term)
                    if mapped_ur:
                        ent_term_conds.append("e.entity_text ILIKE %s")
                        ent_term_params.append(f"%{mapped_ur}%")
                    cur.execute(f"""
                        SELECT DISTINCT e.video_id::text AS vid
                        FROM entities e
                        JOIN videos v ON v.id = e.video_id
                        WHERE v.status = 'completed'
                          AND ({' OR '.join(ent_term_conds)})
                    """, ent_term_params)
                    for row in cur.fetchall():
                        _add_score(scores, row['vid'], 0.15, 'entity_term')

            # ── 4. Tag search ─────────────────────────────────────────
            tag_conds = ["v.tags::text ILIKE %s"]
            tag_params = [f"%{q}%"]
            for term in exp['terms']:
                if len(term) >= 3:
                    tag_conds.append("v.tags::text ILIKE %s")
                    tag_params.append(f"%{term}%")
            # Cross-language: Urdu categories + keyword expansions in tags
            for cat in exp['category_matches']:
                tag_conds.append("v.tags::text ILIKE %s")
                tag_params.append(f"%{cat}%")
            for ur in exp['urdu_expansions']:
                tag_conds.append("v.tags::text ILIKE %s")
                tag_params.append(f"%{ur}%")

            cur.execute(f"""
                SELECT DISTINCT v.id::text AS vid
                FROM videos v
                WHERE v.status = 'completed'
                  AND v.tags IS NOT NULL
                  AND ({' OR '.join(tag_conds)})
            """, tag_params)
            for row in cur.fetchall():
                _add_score(scores, row['vid'], 0.20, 'tag')

            # ── 5. Title search ───────────────────────────────────────
            title_conds = ["v.original_filename ILIKE %s"]
            title_params = [f"%{q}%"]
            for term in exp['terms']:
                if len(term) >= 3:
                    title_conds.append("v.original_filename ILIKE %s")
                    title_params.append(f"%{term}%")

            cur.execute(f"""
                SELECT DISTINCT v.id::text AS vid
                FROM videos v
                WHERE v.status = 'completed'
                  AND ({' OR '.join(title_conds)})
            """, title_params)
            for row in cur.fetchall():
                _add_score(scores, row['vid'], 0.20, 'title')

            # ── 6. Transcript full-text ───────────────────────────────
            tx_conds = [
                "(to_tsvector('simple', t.transcript_text) @@ plainto_tsquery('simple', %s))",
                "t.transcript_text ILIKE %s",
            ]
            tx_params = [q, f"%{q}%"]
            for ur in exp['urdu_expansions']:
                tx_conds.append("t.transcript_text ILIKE %s")
                tx_params.append(f"%{ur}%")

            cur.execute(f"""
                SELECT DISTINCT t.video_id::text AS vid
                FROM transcriptions t
                JOIN videos v ON v.id = t.video_id
                WHERE v.status = 'completed'
                  AND ({' OR '.join(tx_conds)})
            """, tx_params)
            for row in cur.fetchall():
                _add_score(scores, row['vid'], 0.15, 'transcript')

            # Transcript per term
            for term in exp['terms']:
                if len(term) >= 3:
                    cur.execute("""
                        SELECT DISTINCT t.video_id::text AS vid
                        FROM transcriptions t
                        JOIN videos v ON v.id = t.video_id
                        WHERE v.status = 'completed'
                          AND t.transcript_text ILIKE %s
                    """, (f"%{term}%",))
                    for row in cur.fetchall():
                        _add_score(scores, row['vid'], 0.10, 'transcript_term')

    except Exception as e:
        logger.error(f"[Search] Query phase failed: {e}", exc_info=True)
        return []

    # ── 7. FAISS semantic search (bonus leg) ──────────────────────
    try:
        from search.embeddings import get_faiss_index, generate_embedding
        faiss_idx = get_faiss_index()
        if faiss_idx.count > 0:
            query_vec = generate_embedding(query_text)
            hits = faiss_idx.search(query_vec, top_k=50)
            for vid, cos_score in hits:
                boost = max(cos_score, 0.0) * 0.35  # scale cosine [0,1] → [0,0.35]
                _add_score(scores, vid, boost, 'semantic')
            logger.info(f"[Search] FAISS returned {len(hits)} hits "
                        f"(index has {faiss_idx.count} vectors)")
        else:
            logger.debug("[Search] FAISS index empty — skipping semantic leg")
    except Exception as e:
        logger.warning(f"[Search] FAISS semantic leg failed (non-fatal): {e}")

    if not scores:
        logger.info("[Search] No results found")
        return []

    # Rank and take top_k
    ranked = sorted(scores.items(), key=lambda x: x[1]['total'], reverse=True)[:top_k]
    video_ids = [vid for vid, _ in ranked]
    score_map = {vid: data for vid, data in ranked}

    return _enrich_results(video_ids, score_map)


# ---------------------------------------------------------------------------
# Enrich results — same shape as /api/videos
# ---------------------------------------------------------------------------
def _enrich_results(video_ids: List[str], score_data: Dict) -> List[Dict]:
    """Load full video data for search results (mirrors /api/videos shape)."""
    if not video_ids:
        return []

    results = []
    try:
        with get_db_cursor(commit=False) as cur:
            ph = ','.join(['%s'] * len(video_ids))

            # Videos
            cur.execute(f"""
                SELECT v.*,
                       (SELECT COUNT(*) FROM transcriptions WHERE video_id = v.id) AS transcription_count
                FROM videos v
                WHERE v.id::text IN ({ph})
            """, video_ids)
            videos = {str(r['id']): dict(r) for r in cur.fetchall()}

            # Latest transcription per video
            cur.execute(f"""
                SELECT DISTINCT ON (video_id)
                       video_id::text AS vid, id, transcript_text, language
                FROM transcriptions
                WHERE video_id::text IN ({ph})
                ORDER BY video_id, created_at DESC
            """, video_ids)
            transcriptions = {r['vid']: dict(r) for r in cur.fetchall()}

        # Build output in rank order
        for vid in video_ids:
            video = videos.get(vid)
            if not video:
                continue

            duration = video.get('duration')
            if duration is not None:
                duration = float(duration)

            storage_path = video.get('storage_path', '')
            video_url = None
            if storage_path:
                video_url = f"/uploads/{os.path.basename(storage_path)}"

            transcription = transcriptions.get(vid)
            entities = filter_entities(Entity.get_by_video_id(vid))
            sd = score_data.get(vid, {'total': 0, 'reasons': []})

            video_data = {
                'id': vid,
                'filename': video.get('original_filename', 'Unknown'),
                'original_filename': video.get('original_filename', 'Unknown'),
                'file_size': int(video.get('file_size', 0)),
                'duration': duration,
                'status': video.get('status', 'uploaded'),
                'upload_date': str(video['upload_date']) if video.get('upload_date') else None,
                'processed_date': str(video['processed_date']) if video.get('processed_date') else None,
                'storage_path': storage_path,
                'video_url': video_url,
                'has_transcription': transcription is not None,
                'transcription_count': int(video.get('transcription_count', 0)),
                'speaker': video.get('speaker', 'Unknown Speaker'),
                'category': video.get('category'),
                'tags': video.get('tags') or [],
                'entities': entities,
                'frontend_payload': video.get('frontend_payload') or {},
                # Search-specific
                'search_score': round(sd['total'], 4),
                'match_reasons': sd['reasons'],
            }

            if transcription:
                text = transcription.get('transcript_text', '')
                video_data['transcript_preview'] = (text[:200] + '...') if len(text) > 200 else text
                video_data['transcript_language'] = transcription.get('language', 'ur')
                video_data['transcript_word_count'] = len(text.split()) if text else 0
                video_data['transcription_id'] = str(transcription['id'])

            results.append(video_data)

        logger.info(f"[Search] Returning {len(results)} enriched results")
        return results

    except Exception as e:
        logger.error(f"[Search] Enrich failed: {e}", exc_info=True)
        return []

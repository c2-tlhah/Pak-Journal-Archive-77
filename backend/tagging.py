"""
Urdu Broadcast Media Tagging Pipeline
======================================
Standalone module that takes transcript segments (from Whisper) and an optional
speaker label (from the CNN politician classifier) and produces:

    FUSION_TAGS, ENTITIES, SUMMARIES, TOPICS

All intermediate artefacts are also returned.

Entry point
-----------
    run_tagging_pipeline(transcript_segments, speaker_name, video_id, user_id)

Hardware target: NVIDIA RTX 3070 Ti 8 GB — every model runs in float16 on CUDA
and VRAM is freed immediately after use.
"""

import os
import re
import gc
import json
import uuid
import logging
import warnings
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import numpy as np
import torch
import psycopg2
from psycopg2.extras import Json

from vocabulary import VOCABULARY

 
# Logger
 
logger = logging.getLogger(__name__)

 
# Urdu helpers
 

# Try urduhack; fall back to manual regex normalisation
try:
    import urduhack
    urduhack.download()                       # idempotent
    from urduhack.normalization import normalize as _urduhack_normalize
    _HAS_URDUHACK = True
    logger.info("urduhack available — using urduhack normalisation")
except Exception:
    _HAS_URDUHACK = False
    logger.warning("urduhack not available — falling back to regex normalisation")


# Manual Urdu normalisation (Alef / Yeh / Hamza unification + diacritics removal)
_ALEF_VARIANTS  = re.compile("[\u0622\u0623\u0625\u0672\u0673\u0675]")   # → ا
_YEH_VARIANTS   = re.compile("[\u0649\u06CC\u06CD\u06D0\u06D2]")          # → ی
_HAMZA_VARIANTS = re.compile("[\u0654\u0655]")                             # remove
_DIACRITICS     = re.compile("[\u064B-\u065F\u0670]")                      # remove

URDU_STOPWORDS = frozenset([
    # Pronouns & demonstratives
    "میں","ہم","تم","آپ","وہ","یہ","اس","ان","جو","کوئی","کچھ","سب",
    "اپنا","اپنی","اپنے","خود","مجھے","ہمیں","تمہیں","انہوں","انھوں","جس","جن",
    "جنہوں","جسے","جنھوں","اسے","اسی","انہیں","انھیں","ہماری","ہمارا","ہمارے",
    "تمہارا","تمہاری","تمہارے","آپکا","آپکی","آپکے","ان کا","ان کی","ان کے",
    "اُس","اِس","اُن","اِن","کسی","سبھی","دونوں","تینوں",
    # Postpositions & case markers
    "کا","کی","کے","نے","کو","سے","پر","میں","تک","لیے","لئے","واسطے",
    "ساتھ","بعد","پہلے","دوران","بارے","بغیر","ذریعے","مطابق","خلاف",
    "نیچے","اوپر","اندر","باہر","آگے","پیچھے","بیچ","درمیان","قریب","پاس",
    # Conjunctions & discourse markers
    "اور","یا","لیکن","مگر","بلکہ","اگر","تو","کہ","جب","تب","جبکہ",
    "پھر","اب","ابھی","البتہ","حالانکہ","تاکہ","کیونکہ","چونکہ","پس",
    "ورنہ","نیز","علاوہ","چنانچہ","خواہ","یعنی","گویا","شاید",
    # Auxiliaries & copulas
    "ہے","ہیں","تھا","تھی","تھے","ہوں","ہو","ہوا","ہوئی","ہوئے",
    "گیا","گئی","گئے","رہا","رہی","رہے","سکتا","سکتی","سکتے",
    "چاہیے","جائے","جاتا","جاتی","آتا","آتی","دیا","دی","دیے",
    "چُکا","چکا","چکی","چکے","رکھا","رکھی","رکھے",
    # Common verbs (light/support)
    "کیا","کیے","کرنا","کرتا","کرتی","کرتے","کریں","کرے","کرنے","کرو",
    "ہونا","ہوتا","ہوتی","ہوتے","ہونے","آنا","جانا","دینا","لینا","رکھنا",
    "ملنا","بنانا","لگنا","لگا","لگی","لگے","چلا","چلی",
    "کہنا","کہا","کہی","کہتا","کہتی","کہتے","بتانا","بتایا","بولا","بولی",
    "سمجھنا","سمجھا","سوچنا","سوچا","دیکھنا","دیکھا","سنا","سنی",
    "آیا","آئی","آئے","گیا","آ","جا","لے","دے","کر","ہو",
    "پڑا","پڑی","پڑے","ڈالا","ڈالی","اٹھا","اٹھایا","بیٹھا","بیٹھی",
    "ملا","ملی","ملے","بنا","بنی","بنے","رہنا",
    # Adverbs & particles
    "بہت","زیادہ","کم","ہی","بھی","صرف","سیر","نہیں","نہ","مت","ہاں","جی",
    "ابھی","کبھی","ہمیشہ","پھر","اب","آج","کل","وہاں","یہاں","کہاں",
    "کیسے","کیوں","کیا","کب","کدھر","ادھر","اِدھر","اُدھر","ذرا","بس",
    "واقعی","اصل","سچ","بالکل","قریباً","تقریباً","اکثر","عموماً","فوری",
    # Determiners, quantifiers & adjectives (generic)
    "ایک","دو","تین","بڑا","بڑی","بڑے","چھوٹا","چھوٹی","اچھا","اچھی",
    "نیا","نئی","نئے","پرانا","پرانی","اتنا","اتنی","کتنا","کتنی",
    "چار","پانچ","چھ","سات","آٹھ","نو","دس","پہلا","پہلی","دوسرا","دوسری",
    "تیسرا","تیسری","آخری","پچھلا","پچھلی","اگلا","اگلی","کئی","تمام","ہر",
    "پورا","پوری","پورے","کافی","سارا","ساری","سارے",
    # High-frequency generic nouns (non-informative)
    "بات","لوگ","لوگوں","طرح","طرف","وقت","کام","حال","جگہ","دن","سال",
    "بار","مرتبہ","معاملہ","صورت","حالات","چیز","شخص",
    "ملک","دنیا","بچے","بچوں","آدمی","عورت","گھر","نام","حکومت",
    "ضرورت","سوال","جواب","مسئلہ","فیصلہ","عمل","نتیجہ","مقصد",
    "اطلاع","خبر","رپورٹ","پروگرام","نشریات","بریکنگ","خبریں",
    # Honorifics & filler
    "صاحب","جناب","محترم","محترمہ","حضرات","بھائی","بہنوں","بھائیوں",
    "والے","والی","والا","والوں",
    "دیکھیے","سنیے","بتائیے","جانیے","آئیے","چلیے",
    # Common greetings & Islamic phrases (non-informative for tagging)
    "السلام","علیکم","وعلیکم","بسم","اللہ","الرحمن","الرحیم",
    "ماشاءاللہ","انشاءاللہ","الحمدللہ","سبحان","جزاک",
    # Urdu informal / filler / address terms / short fragments
    "اپ","نی","سی","ائی","پی","ی","وں","اج","عزیز","میری","دل","سپ","عظیم",
    "الم","ایاکن",
    # English stopwords that leak into Urdu transcripts
    "the","is","of","and","in","to","a","that","it","for","was","on","are",
    "this","with","you","we","he","she","they","but","or","an","be","has",
    "had","have","do","does","did","will","would","could","should","may",
    "can","so","very","just","also","not","no","yes","ok","okay","well",
    "like","about","from","been","were","being","what","which","who","how",
    "people","fool","thing","things","way","time","said","say","know","get",
    "think","want","need","make","take","come","see","look","give","go",
])
# Also keep a normalised copy so BERTopic's vectorizer (which receives
# normalised tokens from _urdu_tokenizer) can filter them correctly.
_URDU_STOPWORDS_NORMALISED: list  # populated after normalize_urdu is defined


def normalize_urdu(text: str) -> str:
    """Normalise a single Urdu string (urduhack if available, else regex)."""
    if not text or not isinstance(text, str):
        return ""
    if _HAS_URDUHACK:
        text = _urduhack_normalize(text)
    text = _ALEF_VARIANTS.sub("\u0627", text)
    text = _YEH_VARIANTS.sub("\u06CC", text)
    text = _HAMZA_VARIANTS.sub("", text)
    text = _DIACRITICS.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Build normalised copy of stopwords now that normalize_urdu is defined
_URDU_STOPWORDS_NORMALISED = list({normalize_urdu(w) for w in URDU_STOPWORDS if normalize_urdu(w)})

def _free_vram():
    """Delete references and release CUDA cache."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


 
# STEP 1 — Urdu Text Normalisation
 
def step1_normalise(segments: List[Dict]) -> List[Dict]:
    """Add *normalized_text* to each segment; drop segments < 5 tokens."""
    logger.info("[Step 1] Normalising Urdu text …")
    out = []
    for seg in segments:
        norm = normalize_urdu(seg.get("text", ""))
        if len(norm.split()) < 5:
            continue
        seg["normalized_text"] = norm
        out.append(seg)
    logger.info(f"[Step 1] {len(segments)} → {len(out)} segments after normalisation + filtering")
    return out


 
# STEP 2 — Chunked Summarisation  (mT5 XLSum)
 
def step2_summarise(segments: List[Dict]) -> Tuple[List[Dict], List[Dict], str]:
    """
    Returns (TRANSCRIPT_CHUNKS, CHUNK_SUMMARIES_LIST, VIDEO_TITLE).

    CHUNK_SUMMARIES_LIST  — list of dicts with chunk_id, chunk_summary, vocab_match_count.
    VIDEO_TITLE           — chunk summary with highest vocabulary match count (min 6 words),
                            fallback to first chunk summary if no vocabulary matches.

    No meta-summarisation is performed.  SUMMARY_LIST (kept for reference in the
    caller) is identical to CHUNK_SUMMARIES_LIST.
    """
    logger.info("[Step 2] Loading mT5 XLSum for summarisation …")
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    model_name = "csebuetnlp/mT5_multilingual_XLSum"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name, dtype=torch.float16
    ).to(_device()).eval()

    MAX_TOKENS = 400

    def _build_chunks(texts: List[str]) -> List[List[str]]:
        chunks, current, current_len = [], [], 0
        for t in texts:
            tlen = len(tokenizer.encode(t, add_special_tokens=False))
            if current and current_len + tlen > MAX_TOKENS:
                chunks.append(current)
                current, current_len = [], 0
            current.append(t)
            current_len += tlen
        if current:
            chunks.append(current)
        return chunks

    def _summarise_text(text: str, max_new: int = 80) -> str:
        inp = tokenizer("summarize: " + text, return_tensors="pt",
                        max_length=512, truncation=True).to(_device())
        with torch.no_grad():
            ids = model.generate(**inp, max_new_tokens=max_new, num_beams=4,
                                 early_stopping=True)
        return tokenizer.decode(ids[0], skip_special_tokens=True)

    texts = [s["normalized_text"] for s in segments]
    raw_chunks = _build_chunks(texts)

    transcript_chunks: List[Dict] = []
    chunk_summaries: List[Dict] = []

    for idx, chunk_texts in enumerate(raw_chunks):
        full = " ".join(chunk_texts)
        tok_count = len(tokenizer.encode(full, add_special_tokens=False))
        transcript_chunks.append({
            "chunk_id": idx,
            "segments_included": list(range(
                sum(len(c) for c in raw_chunks[:idx]),
                sum(len(c) for c in raw_chunks[:idx]) + len(chunk_texts)
            )),
            "text": full,
            "token_count": tok_count,
        })
        summary = _summarise_text(full, max_new=80)
        chunk_summaries.append({"chunk_id": idx, "chunk_summary": summary})

    logger.info(f"[Step 2] Produced {len(chunk_summaries)} chunk summaries")

    # --- Vocabulary match scoring per chunk summary (exact + fuzzy) ---
    from rapidfuzz import fuzz, process as rfprocess

    all_vocab_terms: List[str] = []
    for terms in VOCABULARY.values():
        all_vocab_terms.extend(terms)

    for cs in chunk_summaries:
        words = cs["chunk_summary"].split()
        match_count = 0
        for word in words:
            if len(word) < 2:
                continue
            # Exact match
            if word in all_vocab_terms:
                match_count += 1
                continue
            # Fuzzy match (threshold 80)
            result = rfprocess.extractOne(
                word, all_vocab_terms, scorer=fuzz.ratio, score_cutoff=80
            )
            if result:
                match_count += 1
        cs["vocab_match_count"] = match_count

    # --- Select VIDEO_TITLE: highest vocab_match_count, min 6 words ---
    candidates = sorted(chunk_summaries, key=lambda x: x["vocab_match_count"], reverse=True)
    video_title = ""
    for c in candidates:
        if c["vocab_match_count"] > 0 and len(c["chunk_summary"].split()) >= 6:
            video_title = c["chunk_summary"]
            break
    # Fallback: first chunk summary
    if not video_title and chunk_summaries:
        video_title = chunk_summaries[0]["chunk_summary"]

    logger.info(f"[Step 2] VIDEO_TITLE selected (vocab_matches={candidates[0]['vocab_match_count'] if candidates else 0}): "
                f"{video_title[:80]}…" if len(video_title) > 80 else f"[Step 2] VIDEO_TITLE: {video_title}")

    # Free VRAM
    del model, tokenizer
    _free_vram()

    return transcript_chunks, chunk_summaries, video_title


# ===================================================================
# STEP 3 — Embeddings  (LaBSE)
# ===================================================================
def step3_embeddings(segments: List[Dict]):
    """Return (embeddings: np.ndarray, labse) — caller must free labse after step 6."""
    logger.info("[Step 3] Loading LaBSE for embeddings …")
    from sentence_transformers import SentenceTransformer

    labse = SentenceTransformer("sentence-transformers/LaBSE")
    labse.half()                       # fp16
    labse.to(_device())

    texts = [s["normalized_text"] for s in segments]
    embeddings = labse.encode(texts, batch_size=32, show_progress_bar=False,
                              convert_to_numpy=True, normalize_embeddings=True)

    logger.info(f"[Step 3] Embeddings shape: {embeddings.shape}")
    # LaBSE kept alive — reused in step 6 for KeyBERT, freed there
    return embeddings.astype(np.float32), labse


 
# STEP 4 — Similarity Analysis
 
def step4_similarity(segments: List[Dict], embeddings: np.ndarray
                     ) -> Tuple[List[Dict], List[Dict]]:
    """Top-30 similar and top-30 dissimilar pairs."""
    logger.info("[Step 4] Computing cosine similarity matrix …")
    # embeddings already L2-normalised → dot = cosine
    sim_matrix = embeddings @ embeddings.T
    n = len(segments)

    # Extract upper triangle (no self-pairs)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((i, j, float(sim_matrix[i, j])))

    pairs.sort(key=lambda x: x[2], reverse=True)

    def _pair_dict(rank, i, j, score):
        return {
            "rank": rank,
            "segment_1": segments[i].get("normalized_text", ""),
            "segment_2": segments[j].get("normalized_text", ""),
            "speaker_1": segments[i].get("speaker_id", "unknown"),
            "speaker_2": segments[j].get("speaker_id", "unknown"),
            "similarity_score": round(score, 4),
        }

    similar   = [_pair_dict(r+1, i, j, s) for r, (i, j, s) in enumerate(pairs[:30])]
    dissimilar = [_pair_dict(r+1, i, j, s) for r, (i, j, s) in enumerate(pairs[-30:])]

    logger.info(f"[Step 4] Top similar: {similar[0]['similarity_score'] if similar else 'N/A'}, "
                f"Top dissimilar: {dissimilar[0]['similarity_score'] if dissimilar else 'N/A'}")
    return similar, dissimilar

 
# STEP 5 — Topic Modelling  (BERTopic)

# BERTopic's _preprocess_text strips [^A-Za-z0-9 ] ONLY when language="english".
# Passing language="multilingual" skips that stripping entirely, preserving Urdu.
try:
    from bertopic import BERTopic as _BERTopicCls  # noqa: F401 — import test only
    _BERTOPIC_AVAILABLE = True
    logger.info("BERTopic available — using BERTopic topic modelling (multilingual)")
except ImportError:
    _BERTOPIC_AVAILABLE = False
    logger.warning("BERTopic not available — will fall back to KMeans")


def _urdu_tokenizer(text: str) -> List[str]:
    """Whitespace tokenizer that keeps Urdu tokens (len >= 2)."""
    text = normalize_urdu(text)
    return [tok for tok in text.split() if len(tok) > 1]


def step5_topics(segments: List[Dict], embeddings: np.ndarray
                 ) -> Tuple[List[Dict], List[Dict]]:
    """Returns (TOPICS_LIST, TOPIC_ASSIGNMENTS_LIST).

    Uses BERTopic with language='multilingual' (skips Latin-only stripping)
    and a custom Urdu tokenizer / CountVectorizer.
    Falls back to KMeans if BERTopic is unavailable or returns no topics.
    """
    n = len(segments)
    docs = [seg["normalized_text"] for seg in segments]

    if _BERTOPIC_AVAILABLE:
        logger.info("[Step 5] Running BERTopic (Urdu-safe) …")
        from bertopic import BERTopic
        from sklearn.feature_extraction.text import CountVectorizer

        vectorizer_model = CountVectorizer(
            tokenizer=_urdu_tokenizer,
            preprocessor=None,
            token_pattern=None,
            lowercase=False,
            stop_words=_URDU_STOPWORDS_NORMALISED,
            ngram_range=(1, 2),
            min_df=1,
        )

        # min_topic_size: clamp to max(2, n//4) so very short transcripts still cluster
        min_topic_size = max(2, n // 4)

        # UMAP's spectral initialisation crashes with scipy.linalg.eigh when
        # n_samples is small.  Clamp n_neighbors and use 'random' init to avoid it.
        from umap import UMAP
        umap_neighbors = max(2, min(n - 1, 15))
        umap_model = UMAP(
            n_neighbors=umap_neighbors,
            n_components=min(5, n - 1),    # can't reduce to more dims than samples
            min_dist=0.0,
            metric="cosine",
            random_state=42,
            init="random",                 # avoid spectral init eigen-decomposition crash
        )

        topic_model = BERTopic(
            embedding_model=None,          # we supply pre-computed embeddings
            language="multilingual",       # skips the [^A-Za-z0-9] stripping in _preprocess_text
            umap_model=umap_model,
            vectorizer_model=vectorizer_model,
            min_topic_size=min_topic_size,
            calculate_probabilities=False,
            verbose=False,
        )

        topic_ids, _ = topic_model.fit_transform(docs, embeddings=embeddings)
        topic_info = topic_model.get_topic_info()

        topics_list: List[Dict] = []
        topic_kw_map: Dict[int, List[str]] = {}
        for _, row in topic_info.iterrows():
            tid = int(row["Topic"])
            if tid == -1:
                continue
            raw_terms = topic_model.get_topic(tid) or []
            kw = [normalize_urdu(w) for w, _ in raw_terms[:10] if normalize_urdu(w)]
            member_idxs = [i for i, t in enumerate(topic_ids) if int(t) == tid]
            rep_sents = [docs[i] for i in member_idxs[:3]]
            topics_list.append({
                "topic_id": tid,
                "topic_keywords": kw,
                "num_documents": int(row["Count"]),
                "representative_sentences": rep_sents,
            })
            topic_kw_map[tid] = kw

        topic_assignments: List[Dict] = []
        for idx, (seg, tid) in enumerate(zip(segments, topic_ids)):
            topic_assignments.append({
                "segment_id": seg.get("segment_id", idx),
                "text": seg.get("normalized_text", ""),
                "assigned_topic_id": int(tid),
                "topic_keywords": topic_kw_map.get(int(tid), []),
            })

        logger.info(f"[Step 5] BERTopic found {len(topics_list)} topics across {n} segments")
        del topic_model
        _free_vram()

        # If BERTopic assigned everything to outliers (-1), fall through to KMeans
        if not topics_list:
            logger.warning("[Step 5] BERTopic returned no topics (all outliers) — falling back to KMeans")
            _BERTOPIC_AVAILABLE_LOCAL = False
        else:
            _BERTOPIC_AVAILABLE_LOCAL = True

    else:
        _BERTOPIC_AVAILABLE_LOCAL = False

    if not _BERTOPIC_AVAILABLE_LOCAL:
        from sklearn.cluster import KMeans
        from collections import Counter

        n_clusters = max(2, min(n // 3, 8))
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        raw_labels = km.fit_predict(embeddings).tolist()

        cluster_texts: Dict[int, List[str]] = {i: [] for i in range(n_clusters)}
        for seg, lbl in zip(segments, raw_labels):
            cluster_texts[lbl].extend(seg["normalized_text"].split())

        topics_list = []
        topic_kw_map = {}
        for tid, words in cluster_texts.items():
            filtered = [w for w in words if w not in URDU_STOPWORDS and len(w) >= 3]
            kw = [w for w, _ in Counter(filtered).most_common(20)]
            count = sum(1 for l in raw_labels if l == tid)
            member_idxs = [i for i, l in enumerate(raw_labels) if l == tid]
            centre = km.cluster_centers_[tid]
            closest = min(member_idxs, key=lambda i: float(np.linalg.norm(embeddings[i] - centre)))
            topics_list.append({
                "topic_id": tid,
                "topic_keywords": kw,
                "num_documents": count,
                "representative_sentences": [segments[closest]["normalized_text"]],
            })
            topic_kw_map[tid] = kw

        topic_assignments = []
        for idx, (seg, lbl) in enumerate(zip(segments, raw_labels)):
            topic_assignments.append({
                "segment_id": seg.get("segment_id", idx),
                "text": seg.get("normalized_text", ""),
                "assigned_topic_id": lbl,
                "topic_keywords": topic_kw_map.get(lbl, []),
            })

        del km
        _free_vram()
        topic_ids = raw_labels  # used by no further code, but keeps variable consistent

    return topics_list, topic_assignments


 
# STEP 6 — Keyword Extraction  (YAKE + KeyBERT)
 
def step6_keywords(segments: List[Dict], speaker_role: str = "anchor",
                   labse=None) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Returns (YAKE_LIST, KEYBERT_LIST, COMPARISON_LIST)."""
    logger.info("[Step 6] Extracting keywords (YAKE + KeyBERT) …")

    ROLE_WEIGHTS = {
        "guest_expert": 1.5, "politician": 1.3,
        "reporter": 1.2, "anchor": 1.0, "unknown": 1.0,
    }
    role_w = ROLE_WEIGHTS.get(speaker_role, 1.0)

    # ---- YAKE (statistical — no GPU) --------------------------------
    import yake
    yake_ext = yake.KeywordExtractor(lan="ur", n=2, top=10, dedupLim=0.7,
                                      windowsSize=2)

    yake_list: List[Dict] = []
    for seg in segments:
        raw_kw = yake_ext.extract_keywords(seg["normalized_text"])
        filtered = [(w, s) for w, s in raw_kw
                     if not all(tok in URDU_STOPWORDS for tok in w.split())][:10]
        yake_list.append({
            "segment_id": seg.get("segment_id"),
            "text": seg["normalized_text"],
            "speaker_id": seg.get("speaker_id", "unknown"),
            "keywords": [{"word": w, "score": round(s, 4)} for w, s in filtered],
        })

    # ---- KeyBERT (LaBSE backbone — fp16 GPU) ------------------------
    logger.info("[Step 6] Attaching LaBSE to KeyBERT …")
    from keybert import KeyBERT
    if labse is None:
        from sentence_transformers import SentenceTransformer
        labse = SentenceTransformer("sentence-transformers/LaBSE")
        labse.half()
        labse.to(_device())
    kw_model = KeyBERT(model=labse)

    keybert_list: List[Dict] = []
    for seg in segments:
        raw_kw = kw_model.extract_keywords(
            seg["normalized_text"], keyphrase_ngram_range=(1, 2),
            top_n=10, use_mmr=True, diversity=0.5,
        )
        filtered = [(w, s) for w, s in raw_kw
                     if not all(tok in URDU_STOPWORDS for tok in w.split())][:10]
        weighted = [{"word": w, "score": round(s * role_w, 4)} for w, s in filtered]
        keybert_list.append({
            "segment_id": seg.get("segment_id"),
            "text": seg["normalized_text"],
            "speaker_id": seg.get("speaker_id", "unknown"),
            "keywords": weighted,
        })

    del kw_model
    # labse freed by caller (run_tagging_pipeline) after this step
    _free_vram()

    # ---- Comparison --------------------------------------------------
    comparison: List[Dict] = []
    for yk, kb in zip(yake_list, keybert_list):
        y_words = {k["word"] for k in yk["keywords"]}
        k_words = {k["word"] for k in kb["keywords"]}
        comparison.append({
            "segment_id": yk["segment_id"],
            "yake_keywords": yk["keywords"],
            "keybert_keywords": kb["keywords"],
            "overlap": list(y_words & k_words),
        })

    logger.info(f"[Step 6] Keywords extracted for {len(segments)} segments")
    return yake_list, keybert_list, comparison


# ===================================================================
# STEP 7 — Vocabulary Fuzzy Matching
# ===================================================================
def step7_vocab_match(segments: List[Dict]
                      ) -> Tuple[List[Dict], List[Dict]]:
    """Returns (VOCAB_MATCHES_LIST, VOCAB_METRICS_LIST)."""
    logger.info("[Step 7] Vocabulary fuzzy matching …")

    # Guard: skip entirely if vocabulary is empty or failed to load
    if not VOCABULARY or not any(VOCABULARY.values()):
        logger.warning("[Step 7] VOCABULARY is empty — skipping fuzzy match, returning unknowns")
        empty_matches = [
            {"segment_id": seg.get("segment_id"), "text": seg["normalized_text"],
             "matched_terms": [], "predicted_category": "unknown",
             "match_count": 0, "confidence_score": 0.0, "low_confidence": True}
            for seg in segments
        ]
        return empty_matches, []

    from rapidfuzz import fuzz, process

    THRESHOLD = 85          # raised from 80 to reduce false positives
    MIN_WORD_LEN = 4        # skip very short words (e.g. اور -> اوور)
    LOW_CONF = 0.45

    # Build flat term list per category once, outside the segment loop
    # Shape: [(cat, term), ...] — used with rapidfuzz process.extractOne for speed
    cat_terms: Dict[str, List[str]] = {cat: terms for cat, terms in VOCABULARY.items() if terms}
    # Flat list of (term, cat) for bulk matching
    all_terms: List[tuple] = [(term, cat) for cat, terms in cat_terms.items() for term in terms]
    term_strings: List[str] = [t[0] for t in all_terms]

    matches_list: List[Dict] = []
    cat_counts: Dict[str, List[float]] = {c: [] for c in cat_terms}

    for seg in segments:
        words = seg["normalized_text"].split()
        matched: List[Dict] = []
        cat_hits: Dict[str, int] = {c: 0 for c in cat_terms}

        for word in words:
            if len(word) < MIN_WORD_LEN:
                continue  # skip very short tokens — too noisy for fuzzy match
            if word in URDU_STOPWORDS:
                continue  # skip common stopwords like اور، لیکن, etc.
            # extractOne finds best match across all terms in one pass (O(n) not O(n*m))
            result = process.extractOne(word, term_strings, scorer=fuzz.ratio, score_cutoff=THRESHOLD)
            if result:
                matched_term, score, idx = result
                cat = all_terms[idx][1]
                matched.append({"word": word, "matched_term": matched_term, "category": cat})
                cat_hits[cat] += 1

        best_cat = max(cat_hits, key=cat_hits.get) if any(cat_hits.values()) else "unknown"
        total_words = max(len(words), 1)
        best_count = cat_hits.get(best_cat, 0)
        conf = best_count / total_words

        matches_list.append({
            "segment_id": seg.get("segment_id"),
            "text": seg["normalized_text"],
            "matched_terms": matched,
            "predicted_category": best_cat,
            "match_count": best_count,
            "confidence_score": round(conf, 4),
            "low_confidence": conf < LOW_CONF,
        })

        if best_cat != "unknown":
            cat_counts[best_cat].append(conf)

    metrics: List[Dict] = []
    for cat, scores in cat_counts.items():
        if scores:
            metrics.append({
                "category": cat,
                "match_count": len(scores),
                "avg_confidence": round(sum(scores) / len(scores), 4),
            })

    logger.info(f"[Step 7] Vocab match complete — {sum(m['match_count'] for m in metrics)} hits across {len(metrics)} cats")
    return matches_list, metrics


# ===================================================================
# STEP 8 — Named Entity Recognition  (WikiANN Urdu)
# ===================================================================
def step8_ner(segments: List[Dict]) -> List[Dict]:
    """Returns ENTITIES_LIST.

    Uses XLM-RoBERTa NER with aggressive post-processing:
    1. Drop entities in NER_JUNK set (common false positives)
    2. Drop entities that are pure stopwords
    3. Fuzzy-match against KNOWN_PER/ORG/LOC — if close, use canonical form
    4. Require minimum NER confidence score (0.55)
    5. Require minimum entity length (3 chars / 2 chars if known)
    """
    logger.info("[Step 8] Loading Urdu NER model …")
    from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline as hf_pipeline
    from rapidfuzz import fuzz, process as rfprocess

    # Import NER vocabulary
    try:
        from ner_vocabulary import (ALL_KNOWN_ENTITIES, NER_JUNK,
                                    KNOWN_PER, KNOWN_ORG, KNOWN_LOC,
                                    COUNTRY_NAMES)
    except ImportError:
        logger.warning("[Step 8] ner_vocabulary.py not found — running without NER vocab")
        ALL_KNOWN_ENTITIES = {"PER": frozenset(), "ORG": frozenset(), "LOC": frozenset()}
        NER_JUNK = frozenset()
        KNOWN_PER, KNOWN_ORG, KNOWN_LOC = frozenset(), frozenset(), frozenset()
        COUNTRY_NAMES = frozenset()

    model_name = "Davlan/xlm-roberta-base-wikiann-ner"
    fallback = "Davlan/bert-base-multilingual-cased-ner-hrl"

    try:
        tok = AutoTokenizer.from_pretrained(model_name)
        mdl = AutoModelForTokenClassification.from_pretrained(
            model_name, dtype=torch.float16
        ).to(_device()).eval()
        logger.info(f"[Step 8] Loaded {model_name}")
    except Exception as e:
        logger.warning(f"[Step 8] Primary NER model failed ({e}), trying fallback …")
        tok = AutoTokenizer.from_pretrained(fallback)
        mdl = AutoModelForTokenClassification.from_pretrained(
            fallback, dtype=torch.float16
        ).to(_device()).eval()
        logger.info(f"[Step 8] Loaded fallback: {fallback}")

    ner_pipe = hf_pipeline("ner", model=mdl, tokenizer=tok, device=_device(),
                           aggregation_strategy="simple")

    MIN_SCORE = 0.55          # minimum NER confidence
    MIN_LEN = 3               # minimum entity char length (relaxed to 2 for known)
    FUZZY_THRESHOLD = 82      # for matching against known vocabulary

    ALLOWED = {"PER", "LOC", "ORG"}
    entity_map: Dict[str, Dict] = {}  # key = (text, type)

    # Pre-build normalised stopword set for fast NER filtering
    norm_stops = {normalize_urdu(w) for w in URDU_STOPWORDS if normalize_urdu(w)}
    norm_junk = {normalize_urdu(w) for w in NER_JUNK if normalize_urdu(w)}

    # Pre-build normalised sets for type correction (avoid recomputing in loop)
    _norm_countries = {normalize_urdu(c) for c in COUNTRY_NAMES if normalize_urdu(c)}
    _norm_per = {normalize_urdu(p) for p in KNOWN_PER if normalize_urdu(p)}
    _norm_org = {normalize_urdu(o) for o in KNOWN_ORG if normalize_urdu(o)}
    _norm_loc = {normalize_urdu(l) for l in KNOWN_LOC if normalize_urdu(l)}

    def _is_junk_entity(text: str) -> bool:
        """Return True if entity should be discarded."""
        nt = normalize_urdu(text)
        if not nt or nt in norm_junk:
            return True
        tokens = nt.split()
        # All tokens are stopwords
        if all(t in norm_stops for t in tokens):
            return True
        # Single token that is a stopword or < MIN_LEN
        if len(tokens) == 1 and (tokens[0] in norm_stops or len(tokens[0]) < MIN_LEN):
            return True
        # Any token is a known junk pattern (substring match)
        for tok in tokens:
            if tok in norm_junk:
                # If multi-word and the junk is just one token, don't kill the whole entity
                # — but if over half the tokens are junk, discard
                pass
        junk_count = sum(1 for tok in tokens if tok in norm_junk or tok in norm_stops)
        if len(tokens) >= 2 and junk_count > len(tokens) // 2:
            return True
        return False

    def _trim_entity(text: str) -> str:
        """Strip leading/trailing stopwords from entity text.
        'مریم نواز کی پریس کانفرنس' -> 'مریم نواز'"""
        tokens = text.split()
        # Trim from right
        while len(tokens) > 1:
            nt = normalize_urdu(tokens[-1])
            if nt in norm_stops or nt in norm_junk or tokens[-1] in URDU_STOPWORDS:
                tokens.pop()
            else:
                break
        # Trim from left
        while len(tokens) > 1:
            nt = normalize_urdu(tokens[0])
            if nt in norm_stops or nt in norm_junk or tokens[0] in URDU_STOPWORDS:
                tokens.pop(0)
            else:
                break
        return " ".join(tokens)

    def _try_canonical(text: str, etype: str):
        """Fuzzy-match against known vocabulary; return (canonical_text, corrected_type).
        Searches the predicted type first, then all other types for cross-type rescue."""
        nt = normalize_urdu(text)
        # Pass 1: search within predicted type
        known_set = ALL_KNOWN_ENTITIES.get(etype, frozenset())
        if known_set:
            if nt in known_set or text in known_set:
                return text, etype
            match = rfprocess.extractOne(nt, known_set, scorer=fuzz.ratio)
            if match and match[1] >= FUZZY_THRESHOLD:
                return match[0], etype
        # Pass 2: search OTHER types (cross-type rescue)
        for other_type, other_set in ALL_KNOWN_ENTITIES.items():
            if other_type == etype or not other_set:
                continue
            if nt in other_set or text in other_set:
                return text, other_type
            match = rfprocess.extractOne(nt, other_set, scorer=fuzz.ratio)
            if match and match[1] >= FUZZY_THRESHOLD:
                return match[0], other_type
        return text, etype

    for seg in segments:
        results = ner_pipe(seg["normalized_text"])
        speaker = seg.get("speaker_id", "unknown")
        for ent in results:
            etype = ent["entity_group"]
            if etype not in ALLOWED:
                continue
            score = ent.get("score", 0.0)
            etext = ent["word"].strip()

            # Strip sub-word markers
            etext = etext.replace("##", "").strip()

            # Length gate
            if len(etext) < 2:
                continue

            # Confidence gate
            if score < MIN_SCORE:
                continue

            # ── First try to match raw text against known entities ──
            canonical, corrected_type = _try_canonical(etext, etype)
            nt_check = normalize_urdu(etext)
            # Entity is "known" if it matches any vocabulary set (exact or fuzzy)
            is_known_entity = (
                etext in KNOWN_PER or etext in KNOWN_ORG or etext in KNOWN_LOC
                or etext in COUNTRY_NAMES
                or nt_check in _norm_per or nt_check in _norm_org or nt_check in _norm_loc
                or nt_check in _norm_countries
                or (canonical != etext and len(canonical) >= len(etext))
            )
            if is_known_entity:
                if len(canonical) >= len(etext):
                    etext = canonical
                etype = corrected_type
            else:
                etype = corrected_type
                # ── Only trim unknown entities ──
                trimmed = _trim_entity(etext)
                if trimmed != etext:
                    etext = trimmed
                    # Try canonical again on trimmed text
                    canonical2, corrected_type2 = _try_canonical(etext, etype)
                    if len(canonical2) >= len(etext):
                        etext = canonical2
                        etype = corrected_type2

            # Junk filter (after trimming)
            if _is_junk_entity(etext):
                continue

            # ── Type correction ──
            nt = normalize_urdu(etext)
            if etext in COUNTRY_NAMES or nt in _norm_countries:
                etype = "LOC"
            elif etext in KNOWN_PER or nt in _norm_per:
                etype = "PER"
            elif etext in KNOWN_ORG or nt in _norm_org:
                etype = "ORG"
            elif etext in KNOWN_LOC or nt in _norm_loc:
                etype = "LOC"

            # Final length gate (stricter for unknown entities)
            _norm_sets = {"PER": _norm_per, "ORG": _norm_org, "LOC": _norm_loc}
            known_set = ALL_KNOWN_ENTITIES.get(etype, frozenset())
            norm_known = _norm_sets.get(etype, set())
            is_known = etext in known_set or nt in norm_known
            if not is_known and len(etext) < MIN_LEN:
                continue

            key = (etext, etype)
            if key not in entity_map:
                entity_map[key] = {
                    "entity_text": etext,
                    "entity_type": etype,
                    "mention_count": 0,
                    "mentioned_by_speakers": set(),
                    "max_score": 0.0,
                    "is_known": is_known,
                }
            entity_map[key]["mention_count"] += 1
            entity_map[key]["max_score"] = max(entity_map[key]["max_score"], score)
            entity_map[key]["mentioned_by_speakers"].add(speaker)

    entities = []
    for v in entity_map.values():
        v["mentioned_by_speakers"] = list(v["mentioned_by_speakers"])
        # Final cleanup: remove max_score from output (internal only)
        v.pop("max_score", None)
        v.pop("is_known", None)
        entities.append(v)

    entities.sort(key=lambda x: x["mention_count"], reverse=True)
    logger.info(f"[Step 8] Found {len(entities)} unique entities (after filtering)")

    del mdl, tok, ner_pipe
    _free_vram()

    return entities


# ===================================================================
# STEP 9 — Low-Confidence Gate
# ===================================================================
def step9_confidence_gate(vocab_matches: List[Dict],
                          topic_assignments: List[Dict]) -> List[Dict]:
    """Returns LOW_CONFIDENCE_FLAGS."""
    logger.info("[Step 9] Low-confidence gate …")
    topic_map = {ta["segment_id"]: ta for ta in topic_assignments}
    flags: List[Dict] = []
    for vm in vocab_matches:
        sid = vm["segment_id"]
        ta = topic_map.get(sid, {})
        needs = vm["confidence_score"] < 0.45 or ta.get("assigned_topic_id", -1) == -1
        flags.append({
            "segment_id": sid,
            "text": vm["text"],
            "vocab_confidence": vm["confidence_score"],
            "topic_id": ta.get("assigned_topic_id", -1),
            "needs_review": needs,
        })
    flagged = sum(1 for f in flags if f["needs_review"])
    logger.info(f"[Step 9] {flagged}/{len(flags)} segments flagged for review")
    return flags


# ===================================================================
# STEP 10 — Fusion Layer
# ===================================================================
WEIGHT_CONFIGS = [
    {"config_id": "F1", "label": "keyword_dominant",  "bertopic": 1.0, "keywords": 1.5, "vocab": 1.2},
    {"config_id": "F2", "label": "bertopic_dominant",  "bertopic": 1.5, "keywords": 1.0, "vocab": 1.2},
    {"config_id": "F3", "label": "vocab_dominant",     "bertopic": 1.2, "keywords": 1.2, "vocab": 1.5},
    {"config_id": "F4", "label": "equal_baseline",     "bertopic": 1.0, "keywords": 1.0, "vocab": 1.0},
    {"config_id": "F5", "label": "neural_dominant",    "bertopic": 2.0, "keywords": 1.5, "vocab": 0.8},
    {"config_id": "F6", "label": "keyword_heavy",      "bertopic": 0.8, "keywords": 2.0, "vocab": 0.8},
]


def _keyword_to_category(keywords: List[Dict]) -> str:
    """Map KeyBERT keywords against VOCABULARY to find single best category.

    For each keyword, first try matching the full phrase against vocabulary
    terms.  If that fails (score < 85), split into individual words and try
    each word separately.  Credit only the single best-matching category per
    keyword to prevent inflation across multiple categories.
    """
    from rapidfuzz import fuzz
    cat_scores: Dict[str, float] = {c: 0.0 for c in VOCABULARY}
    for kw_item in keywords:
        phrase = kw_item["word"]
        kw_score = kw_item.get("score", 0.5)

        best_cat = None
        best_score = 0

        # First: try the full phrase against all vocab terms
        for cat, terms in VOCABULARY.items():
            for term in terms:
                score = fuzz.ratio(phrase, term)
                if score > best_score:
                    best_score = score
                    best_cat = cat

        # If full-phrase match failed, try individual words
        if best_score < 85:
            for word in phrase.split():
                if len(word) < 4 or word in URDU_STOPWORDS:
                    continue
                for cat, terms in VOCABULARY.items():
                    for term in terms:
                        score = fuzz.ratio(word, term)
                        if score > best_score:
                            best_score = score
                            best_cat = cat

        if best_cat and best_score >= 85:
            cat_scores[best_cat] += kw_score
    best = max(cat_scores, key=cat_scores.get)
    return best if cat_scores[best] > 0 else "unknown"


def step10_fusion(segments: List[Dict],
                  topic_assignments: List[Dict],
                  keybert_list: List[Dict],
                  vocab_matches: List[Dict],
                  low_conf_flags: List[Dict],
                  speaker_role: str = "anchor"
                  ) -> Tuple[List[Dict], List[Dict], Dict]:
    """Returns (FUSION_TAGS_LIST, FUSION_METRICS_LIST, BEST_FUSION_CONFIG)."""
    logger.info("[Step 10] Running fusion across 6 weight configs …")

    ROLE_WEIGHTS = {
        "guest_expert": 1.5, "politician": 1.3,
        "reporter": 1.2, "anchor": 1.0, "unknown": 1.0,
    }
    role_w = ROLE_WEIGHTS.get(speaker_role, 1.0)

    # Index helpers
    ta_map = {ta["segment_id"]: ta for ta in topic_assignments}
    kb_map = {kb["segment_id"]: kb for kb in keybert_list}
    vm_map = {vm["segment_id"]: vm for vm in vocab_matches}
    lc_map = {lc["segment_id"]: lc for lc in low_conf_flags}

    all_categories = list(VOCABULARY.keys()) + ["unknown"]

    best_config = None
    best_avg = -1.0
    best_tags: List[Dict] = []
    metrics: List[Dict] = []

    for cfg in WEIGHT_CONFIGS:
        w_bt = cfg["bertopic"] * role_w
        w_kw = cfg["keywords"] * role_w
        w_vc = cfg["vocab"] * role_w

        config_tags: List[Dict] = []
        config_confs: List[float] = []

        for seg in segments:
            sid = seg.get("segment_id")
            ta = ta_map.get(sid, {})
            kb = kb_map.get(sid, {})
            vm = vm_map.get(sid, {})
            lc = lc_map.get(sid, {})

            # --- Three signals ---
            # BERTopic tag: map topic keywords → vocabulary category
            bt_kws = ta.get("topic_keywords", [])
            bt_tag = "unknown"
            if bt_kws:
                bt_tag = _keyword_to_category(
                    [{"word": w, "score": 1.0} for w in bt_kws]
                )

            # Keyword tag from KeyBERT
            kw_tag = _keyword_to_category(kb.get("keywords", []))

            # Vocab tag
            vc_tag = vm.get("predicted_category", "unknown")

            # Weighted voting
            scores: Dict[str, float] = {c: 0.0 for c in all_categories}
            scores[bt_tag] += w_bt
            scores[kw_tag] += w_kw
            scores[vc_tag] += w_vc

            # Consensus: keep labels with >= 2 module support
            # Deprioritize "unknown" — it means "no signal", not a real category
            module_support: Dict[str, int] = {c: 0 for c in all_categories}
            for tag in [bt_tag, kw_tag, vc_tag]:
                module_support[tag] += 1

            consensus_cats = [c for c in all_categories
                              if module_support[c] >= 2 and c != "unknown"]
            if consensus_cats:
                winner = max(consensus_cats, key=lambda c: scores[c])
            else:
                # No consensus among real categories — pick highest-scored non-unknown
                non_unknown = {c: s for c, s in scores.items() if c != "unknown" and s > 0}
                if non_unknown:
                    winner = max(non_unknown, key=non_unknown.get)
                else:
                    winner = "unknown"

            total_score = sum(scores.values())
            confidence = scores[winner] / total_score if total_score > 0 else 0.0

            # Build final tags (top categories by score)
            sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            final_tags = [{"tag": c, "confidence": round(s / total_score, 4) if total_score > 0 else 0.0}
                          for c, s in sorted_cats if s > 0]

            config_tags.append({
                "segment_id": sid,
                "text": seg.get("normalized_text", ""),
                "speaker_id": seg.get("speaker_id", "unknown"),
                "speaker_role": speaker_role,
                "bertopic_tag": bt_tag,
                "keyword_tag": kw_tag,
                "vocab_tag": vc_tag,
                "modules_agreed": module_support[winner],
                "final_tags": final_tags,
                "low_confidence": lc.get("needs_review", False),
            })
            config_confs.append(confidence)

        avg_conf = sum(config_confs) / max(len(config_confs), 1)
        metrics.append({
            "config_id": cfg["config_id"],
            "label": cfg["label"],
            "weights": {"bertopic": cfg["bertopic"], "keywords": cfg["keywords"], "vocab": cfg["vocab"]},
            "avg_confidence": round(avg_conf, 4),
        })

        if avg_conf > best_avg:
            best_avg = avg_conf
            best_config = {
                "config_id": cfg["config_id"],
                "label": cfg["label"],
                "avg_confidence": round(avg_conf, 4),
                "weights": {"bertopic": cfg["bertopic"], "keywords": cfg["keywords"], "vocab": cfg["vocab"]},
            }
            best_tags = config_tags

    logger.info(f"[Step 10] Best config: {best_config['config_id']} ({best_config['label']}) "
                f"avg_confidence={best_config['avg_confidence']:.4f}")
    return best_tags, metrics, best_config


# ===================================================================
# STEP 11 — Export (JSON + PostgreSQL)
# ===================================================================
def _get_pg_conn():
    """Open a one-off psycopg2 connection from env vars."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "pak_journal_archive"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def step11_export(all_outputs: Dict[str, Any],
                  video_id: str, user_id: str) -> None:
    """Save JSON file and upsert to PostgreSQL."""
    logger.info("[Step 11] Exporting results …")

    # --- JSON --------------------------------------------------------
    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    json_path = out_dir / "all_outputs.json"

    # numpy arrays aren't JSON-serialisable — convert embeddings
    serialisable = {}
    for k, v in all_outputs.items():
        if isinstance(v, np.ndarray):
            serialisable[k] = {"__type__": "ndarray", "shape": list(v.shape),
                               "dtype": str(v.dtype)}
        else:
            serialisable[k] = v

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(serialisable, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"[Step 11] JSON saved → {json_path}")

    # --- PostgreSQL ---------------------------------------------------
    conn = None
    try:
        conn = _get_pg_conn()
        cur = conn.cursor()

        # ---- fusion_tags ----
        for tag in all_outputs.get("FUSION_TAGS_LIST", []):
            cur.execute("""
                INSERT INTO fusion_tags (video_id, user_id, segment_id, segment_text,
                    speaker_id, speaker_role, bertopic_tag, keyword_tag, vocab_tag,
                    modules_agreed, final_tags, low_confidence)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (video_id, segment_id) DO UPDATE SET
                    segment_text=EXCLUDED.segment_text,
                    speaker_id=EXCLUDED.speaker_id,
                    speaker_role=EXCLUDED.speaker_role,
                    bertopic_tag=EXCLUDED.bertopic_tag,
                    keyword_tag=EXCLUDED.keyword_tag,
                    vocab_tag=EXCLUDED.vocab_tag,
                    modules_agreed=EXCLUDED.modules_agreed,
                    final_tags=EXCLUDED.final_tags,
                    low_confidence=EXCLUDED.low_confidence,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                video_id, user_id, tag["segment_id"], tag["text"],
                tag.get("speaker_id", "unknown"), tag.get("speaker_role", "anchor"),
                tag["bertopic_tag"], tag["keyword_tag"], tag["vocab_tag"],
                tag["modules_agreed"], Json(tag["final_tags"]),
                tag.get("low_confidence", False),
            ))
        conn.commit()
        logger.info(f"[Step 11] fusion_tags: {len(all_outputs.get('FUSION_TAGS_LIST', []))} rows upserted")

        # ---- entities ----
        for ent in all_outputs.get("ENTITIES_LIST", []):
            cur.execute("""
                INSERT INTO entities (video_id, user_id, entity_text, entity_type,
                    mention_count, mentioned_by_speakers)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (video_id, entity_text, entity_type) DO UPDATE SET
                    mention_count=EXCLUDED.mention_count,
                    mentioned_by_speakers=EXCLUDED.mentioned_by_speakers,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                video_id, user_id, ent["entity_text"], ent["entity_type"],
                ent["mention_count"], Json(ent["mentioned_by_speakers"]),
            ))
        conn.commit()
        logger.info(f"[Step 11] entities: {len(all_outputs.get('ENTITIES_LIST', []))} rows upserted")

        # ---- summaries ----
        for s in all_outputs.get("SUMMARY_LIST", []):
            cur.execute("""
                INSERT INTO summaries (video_id, user_id, summary_id, summary_text)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (video_id, summary_id) DO UPDATE SET
                    summary_text=EXCLUDED.summary_text,
                    updated_at=CURRENT_TIMESTAMP
            """, (video_id, user_id, s["summary_id"], s["text"]))
        conn.commit()
        logger.info(f"[Step 11] summaries: {len(all_outputs.get('SUMMARY_LIST', []))} rows upserted")

        # ---- topics ----
        for t in all_outputs.get("TOPICS_LIST", []):
            cur.execute("""
                INSERT INTO topics (video_id, user_id, topic_id, topic_keywords,
                    num_documents, representative_sentences)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (video_id, topic_id) DO UPDATE SET
                    topic_keywords=EXCLUDED.topic_keywords,
                    num_documents=EXCLUDED.num_documents,
                    representative_sentences=EXCLUDED.representative_sentences,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                video_id, user_id, t["topic_id"], Json(t["topic_keywords"]),
                t["num_documents"], Json(t["representative_sentences"]),
            ))
        conn.commit()
        logger.info(f"[Step 11] topics: {len(all_outputs.get('TOPICS_LIST', []))} rows upserted")

        cur.close()
    except Exception as e:
        logger.error(f"[Step 11] PostgreSQL export failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    # Summary
    for key, val in all_outputs.items():
        if isinstance(val, list):
            logger.info(f"  {key}: {len(val)} items")
        elif isinstance(val, dict):
            logger.info(f"  {key}: dict")
        elif isinstance(val, np.ndarray):
            logger.info(f"  {key}: ndarray {val.shape}")
        else:
            logger.info(f"  {key}: {type(val).__name__}")


# ===================================================================
# MAIN ENTRY POINT
# ===================================================================
def run_tagging_pipeline(
    transcript_segments: List[Dict],
    speaker_name: str = "Unknown Speaker",
    video_id: str = None,
    user_id: str = None,
    video_path: str = None,
) -> Dict[str, Any]:
    """
    Run the full 11-step tagging pipeline.

    Parameters
    ----------
    transcript_segments : list[dict]
        Whisper segments — each dict must have at least ``text``, ``start``, ``end``.
        A ``segment_id`` and ``speaker_id`` will be added if missing.
    speaker_name : str
        Video-level speaker from the politician classifier (e.g. "Imran Khan").
    video_id : str
        UUID of the video record in the database.
    user_id : str
        UUID of the owning user.
    video_path : str
        Path to the video file on disk (used for OCR frame extraction).

    Returns
    -------
    dict  —  ALL_PIPELINE_OUTPUTS
    """
    logger.info("=" * 70)
    logger.info(f"TAGGING PIPELINE START — video={video_id}")
    logger.info("=" * 70)

    # --- Normalise input structure ---
    for idx, seg in enumerate(transcript_segments):
        if "segment_id" not in seg:
            seg["segment_id"] = idx
        if "speaker_id" not in seg:
            seg["speaker_id"] = speaker_name
        if "start_time" not in seg and "start" in seg:
            seg["start_time"] = seg["start"]
        if "end_time" not in seg and "end" in seg:
            seg["end_time"] = seg["end"]

    # Infer a rough speaker role from the politician classifier output
    known_politicians = {
        "Ahmed Sharif", "Asif Zardari", "Asim Munir", "Benazir Bhutto",
        "Bilawal Bhutto", "Imran Khan", "Nawaz Sharif", "Shah Mehmood",
        "Shahbaz Sharif",
    }
    speaker_role = "politician" if speaker_name in known_politicians else "anchor"

    # Step 1
    segments = step1_normalise(transcript_segments)
    if not segments:
        logger.error("No segments survived normalisation — aborting pipeline")
        return {}

    # Step 2
    transcript_chunks, chunk_summaries, video_title = step2_summarise(segments)
    # SUMMARY_LIST is all chunk summaries kept for reference
    summary_list = chunk_summaries

    # Step 3 — load LaBSE once, keep it alive for step 6
    embeddings, labse = step3_embeddings(segments)

    # Step 4
    similar_pairs, dissimilar_pairs = step4_similarity(segments, embeddings)

    # Step 5
    topics_list, topic_assignments = step5_topics(segments, embeddings)

    # Step 6 — reuses the LaBSE instance from step 3
    yake_list, keybert_list, kw_comparison = step6_keywords(segments, speaker_role, labse=labse)
    del labse
    _free_vram()

    # Step 7
    vocab_matches, vocab_metrics = step7_vocab_match(segments)

    # Step 8
    entities_list = step8_ner(segments)

    # Step 9
    low_conf_flags = step9_confidence_gate(vocab_matches, topic_assignments)

    # Step 10
    fusion_tags, fusion_metrics, best_config = step10_fusion(
        segments, topic_assignments, keybert_list,
        vocab_matches, low_conf_flags, speaker_role,
    )

    # Step 10b — OCR Frame Extraction (visual text from video frames)
    ocr_tags: List[Dict] = []
    if video_path and os.path.exists(video_path):
        try:
            logger.info("[Step 10b] Running OCR extraction on video frames …")
            from ocr_extraction import extract_ocr_tags, unload_ocr
            ocr_tags = extract_ocr_tags(video_path, interval_sec=10, confidence_threshold=0.60)
            unload_ocr()
            _free_vram()
            logger.info(f"[Step 10b] OCR extracted {len(ocr_tags)} tags")

            # Run NER on OCR text to find names/orgs/locations in on-screen text
            if ocr_tags:
                ocr_segments = [{"normalized_text": t["text"],
                                 "speaker_id": "ocr"} for t in ocr_tags]
                try:
                    ocr_entities = step8_ner(ocr_segments)
                    # Merge OCR entities into main entities list (deduplicate)
                    existing_keys = {(e["entity_text"], e["entity_type"]) for e in entities_list}
                    for oe in ocr_entities:
                        key = (oe["entity_text"], oe["entity_type"])
                        if key not in existing_keys:
                            entities_list.append(oe)
                            existing_keys.add(key)
                    logger.info(f"[Step 10b] NER on OCR found {len(ocr_entities)} entities")
                except Exception as ner_ocr_err:
                    logger.warning(f"[Step 10b] NER on OCR text failed: {ner_ocr_err}")

        except Exception as ocr_err:
            logger.warning(f"[Step 10b] OCR extraction failed: {ocr_err}")
            ocr_tags = []
    else:
        logger.info("[Step 10b] Skipping OCR — no video_path provided")

    # Collect all outputs
    ALL_PIPELINE_OUTPUTS: Dict[str, Any] = {
        "TRANSCRIPT_CHUNKS": transcript_chunks,
        "CHUNK_SUMMARIES_LIST": chunk_summaries,
        "SUMMARY_LIST": summary_list,
        "VIDEO_TITLE": video_title,
        "EMBEDDINGS_TRANSCRIPT": embeddings,
        "SIMILAR_PAIRS_LIST": similar_pairs,
        "DISSIMILAR_PAIRS_LIST": dissimilar_pairs,
        "TOPICS_LIST": topics_list,
        "TOPIC_ASSIGNMENTS_LIST": topic_assignments,
        "KEYWORDS_YAKE_LIST": yake_list,
        "KEYWORDS_KEYBERT_LIST": keybert_list,
        "KEYWORDS_COMPARISON_LIST": kw_comparison,
        "VOCAB_MATCHES_LIST": vocab_matches,
        "VOCAB_METRICS_LIST": vocab_metrics,
        "ENTITIES_LIST": entities_list,
        "LOW_CONFIDENCE_FLAGS": low_conf_flags,
        "FUSION_TAGS_LIST": fusion_tags,
        "FUSION_METRICS_LIST": fusion_metrics,
        "BEST_FUSION_CONFIG": best_config,
        "OCR_TAGS": ocr_tags,
    }

    # Derive FINAL_CATEGORY and FINAL_TAGS_FLAT
    from collections import Counter
    if fusion_tags:
        # Use weighted multi-signal voting for category:
        # bertopic_tag (2x) + vocab_tag (1x) + keyword_tag (1.5x)
        # This prevents falsely-inflated vocab matches from dominating.
        cat_score: Dict[str, float] = {}
        for t in fusion_tags:
            bt = t.get("bertopic_tag", "unknown")
            vt = t.get("vocab_tag", "unknown")
            kt = t.get("keyword_tag", "unknown")
            for tag, weight in [(bt, 2.0), (kt, 1.5), (vt, 1.0)]:
                if tag and tag != "unknown":
                    cat_score[tag] = cat_score.get(tag, 0) + weight

        if cat_score:
            final_category = max(cat_score, key=cat_score.get)
        else:
            # All signals are unknown — truly unknown
            final_category = "unknown"

        # Build normalised stopword set for _is_junk_tag
        _norm_stop_set = frozenset(_URDU_STOPWORDS_NORMALISED)

        seen: set = set()
        final_tags_flat = []

        def _is_junk_tag(text):
            """Return True if text should NOT be a tag.
            Filters: stopwords, very short tokens, majority-stopword phrases.
            Uses BOTH original and normalised stopword sets for coverage."""
            text = text.strip()
            if not text or len(text) < 2:
                return True
            norm_text = normalize_urdu(text)
            tokens = text.split()
            norm_tokens = norm_text.split() if norm_text else tokens
            # Single token: must not be a stopword and must be 2+ chars
            if len(tokens) == 1:
                return (tokens[0] in URDU_STOPWORDS
                        or (norm_tokens and norm_tokens[0] in _norm_stop_set)
                        or len(tokens[0]) < 2)
            # Multi-word: discard if ALL tokens are stopwords
            if all(tok in URDU_STOPWORDS or tok in _norm_stop_set for tok in tokens):
                return True
            if all(tok in URDU_STOPWORDS or tok in _norm_stop_set for tok in norm_tokens):
                return True
            # 2-word phrase: discard if either word is a stopword
            if len(tokens) == 2:
                stop_count = sum(1 for tok in norm_tokens
                                 if tok in URDU_STOPWORDS or tok in _norm_stop_set)
                if stop_count >= 1:
                    return True
            # 3+ words: discard if >50% of tokens are stopwords
            if len(tokens) >= 3:
                stop_count = sum(1 for tok in norm_tokens
                                 if tok in URDU_STOPWORDS or tok in _norm_stop_set)
                if stop_count / len(norm_tokens) > 0.5:
                    return True
            # Discard if any single-char token exists (fragment artifact)
            if any(len(tok) < 2 for tok in tokens):
                return True
            return False

        # 1. Add actual keywords from KeyBERT (top descriptive words)
        for kb in keybert_list:
            for kw_item in kb.get("keywords", []):
                word = kw_item.get("word", "").strip()
                if word and word != "unknown" and not _is_junk_tag(word) and word not in seen:
                    final_tags_flat.append({
                        "tag": word,
                        "confidence": kw_item.get("score", 0.0),
                        "source": "keybert",
                    })
                    seen.add(word)

        # 2. Add matched vocabulary terms (actual terms, not category names)
        for vm in vocab_matches:
            for mt in vm.get("matched_terms", []):
                term = mt.get("matched_term", "").strip()
                if term and term not in seen and not _is_junk_tag(term):
                    final_tags_flat.append({
                        "tag": term,
                        "confidence": 0.8,
                        "source": "vocab",
                    })
                    seen.add(term)

        # 3. Add named entities (PER, ORG, LOC)
        for ent in entities_list:
            etext = ent.get("entity_text", "").strip()
            if etext and etext not in seen and not _is_junk_tag(etext):
                final_tags_flat.append({
                    "tag": etext,
                    "confidence": min(ent.get("mention_count", 1) / 5.0, 1.0),
                    "source": "entity",
                    "entity_type": ent.get("entity_type", ""),
                })
                seen.add(etext)

        # 4. Add the final category itself as a tag
        if final_category and final_category != "unknown" and final_category not in seen:
            final_tags_flat.append({
                "tag": final_category,
                "confidence": 1.0,
                "source": "category",
            })
            seen.add(final_category)

        # Sort by confidence descending, limit to top 30
        final_tags_flat.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        final_tags_flat = final_tags_flat[:30]

        # Append OCR-derived tags (filter stopwords)
        for ocr_tag in ocr_tags:
            tag_text = ocr_tag.get("text", "").strip()
            if tag_text and tag_text not in seen and not _is_junk_tag(tag_text):
                final_tags_flat.append({
                    "tag": tag_text,
                    "confidence": ocr_tag.get("confidence", 0.0),
                    "source": "ocr",
                })
                seen.add(tag_text)
    else:
        final_category = "unknown"
        final_tags_flat = []
        # Even without fusion tags, include OCR tags
        seen_ocr: set = set()
        for ocr_tag in ocr_tags:
            tag_text = ocr_tag.get("text", "").strip()
            if tag_text and tag_text not in seen_ocr:
                final_tags_flat.append({
                    "tag": tag_text,
                    "confidence": ocr_tag.get("confidence", 0.0),
                    "source": "ocr",
                })
                seen_ocr.add(tag_text)

    ALL_PIPELINE_OUTPUTS["FINAL_CATEGORY"] = final_category
    ALL_PIPELINE_OUTPUTS["FINAL_TAGS_FLAT"] = final_tags_flat

    # Step 11
    if video_id and user_id:
        step11_export(ALL_PIPELINE_OUTPUTS, video_id, user_id)
    else:
        logger.warning("[Step 11] Skipping DB export — no video_id/user_id provided")
        out_dir = Path("outputs")
        out_dir.mkdir(exist_ok=True)
        serialisable = {}
        for k, v in ALL_PIPELINE_OUTPUTS.items():
            if isinstance(v, np.ndarray):
                serialisable[k] = {"__type__": "ndarray", "shape": list(v.shape)}
            else:
                serialisable[k] = v
        with open(out_dir / "all_outputs.json", "w", encoding="utf-8") as f:
            json.dump(serialisable, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"[Step 11] JSON-only export saved")

    logger.info("=" * 70)
    logger.info("TAGGING PIPELINE COMPLETE")
    logger.info("=" * 70)

    return ALL_PIPELINE_OUTPUTS

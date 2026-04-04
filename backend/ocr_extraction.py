"""
OCR Frame Extraction Module
============================
Captures video frames (1 per 10 seconds) and uses PaddleOCR to extract
on-screen text (Urdu + English). Extracted text is cleaned, deduplicated,
and filtered to produce meaningful OCR tags for Pakistani news broadcasts.

Usage
-----
    from ocr_extraction import extract_ocr_tags
    ocr_tags = extract_ocr_tags(video_path)
"""

import os
import re
import logging
import tempfile
from typing import List, Dict, Any, Optional

import cv2

logger = logging.getLogger(__name__)

# Lazy-loaded PaddleOCR instance
_ocr_instance = None

# ── Channel branding / noise patterns to strip ──────────────────────
_CHANNEL_NOISE = re.compile(
    r"\b(?:"
    r"geo|ary|dunya|express|samaa|bol|hum|ptv|neo|92|dawn|aaj|gnn|"
    r"capital|such|roze|waqt|kay2|jaag|public|ab\s*tak|city\s*42|"
    r"news|live|hd|tv|urmedia|channel|exclusive|breaking|alert|update|"
    r"نیوز|لائیو|بریکنگ|الرٹ|تازہ\s*ترین|اہم\s*خبر|خصوصی"
    r")\b",
    re.IGNORECASE | re.UNICODE,
)

# Timestamps / dates
_TIMESTAMP_RE = re.compile(
    r"\b\d{1,2}[:/]\d{2}(?:[:/]\d{2})?\s*(?:am|pm|AM|PM)?\b"
    r"|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"
)

# Pure numbers / very short noise
_NOISE_RE = re.compile(r"^[\d\s\W]+$", re.UNICODE)


def _get_ocr():
    """Lazy-load PaddleOCR (heavy import)."""
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR
        import paddle
        use_gpu = paddle.device.is_compiled_with_cuda()
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang="ur",          # Urdu — also picks up English/digits
            use_gpu=use_gpu,
            show_log=False,
        )
        logger.info(f"PaddleOCR initialised (lang=ur, GPU={use_gpu})")
    return _ocr_instance


def _capture_frames(video_path: str, interval_sec: int = 10) -> List[Dict]:
    """
    Capture one frame every *interval_sec* seconds.

    Returns list of {"frame_idx": int, "timestamp": float, "image": np.ndarray}.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    frame_interval = int(fps * interval_sec)

    logger.info(f"[OCR] Video {os.path.basename(video_path)}: "
                f"{duration:.1f}s, {fps:.1f} fps, capturing every {interval_sec}s")

    frames = []
    frame_idx = 0
    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
        timestamp = frame_idx / fps
        frames.append({
            "frame_idx": frame_idx,
            "timestamp": round(timestamp, 2),
            "image": frame,
        })
        frame_idx += frame_interval

    cap.release()
    logger.info(f"[OCR] Captured {len(frames)} frames")
    return frames


def _clean_ocr_text(text: str) -> str:
    """Strip noise: channel branding, timestamps, collapse whitespace."""
    text = text.strip()
    text = _TIMESTAMP_RE.sub("", text)
    text = _CHANNEL_NOISE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Strip leading/trailing punctuation
    text = re.sub(r"^[\s\-:.|,،؟!]+|[\s\-:.|,،؟!]+$", "", text)
    return text


def _is_meaningful(text: str, min_len: int = 3) -> bool:
    """Filter out noise — short strings, pure numbers/punctuation."""
    if not text or len(text) < min_len:
        return False
    if _NOISE_RE.match(text):
        return False
    # Must have at least some word characters
    cleaned = re.sub(r"[^\w]", "", text, flags=re.UNICODE)
    return len(cleaned) >= min_len


def _split_ticker_line(text: str) -> List[str]:
    """Split long OCR lines (news tickers) into tag-sized phrases.
    Splits on common Urdu/English delimiters used in tickers."""
    # Common ticker delimiters
    parts = re.split(r"[|/\\,،۔\-]{1,3}|\s{3,}", text)
    result = []
    for p in parts:
        p = p.strip()
        if p and _is_meaningful(p):
            result.append(p)
    return result if result else ([text] if _is_meaningful(text) else [])


def extract_ocr_tags(
    video_path: str,
    interval_sec: int = 10,
    confidence_threshold: float = 0.60,
) -> List[Dict[str, Any]]:
    """
    Main entry: extract OCR text from video frames, clean and split into tags.

    Returns
    -------
    list[dict]  — each dict: {"text": str, "timestamp": float, "confidence": float, "source": "ocr"}
    """
    if not os.path.exists(video_path):
        logger.error(f"[OCR] Video file not found: {video_path}")
        return []

    frames = _capture_frames(video_path, interval_sec)
    if not frames:
        return []

    ocr = _get_ocr()
    all_tags: List[Dict[str, Any]] = []
    seen_texts: set = set()

    for fdata in frames:
        try:
            result = ocr.ocr(fdata["image"], cls=True)
            if not result or not result[0]:
                continue

            for line in result[0]:
                # line = [bbox, (text, confidence)]
                text_conf = line[1]
                raw_text = text_conf[0]
                conf = float(text_conf[1])

                if conf < confidence_threshold:
                    continue

                cleaned = _clean_ocr_text(raw_text)
                if not cleaned:
                    continue

                # Split long ticker lines into individual phrases
                phrases = _split_ticker_line(cleaned)

                for phrase in phrases:
                    # Deduplicate across frames (normalised key)
                    norm_key = re.sub(r"\s+", " ", phrase.lower().strip())
                    if norm_key in seen_texts or len(norm_key) < 3:
                        continue
                    seen_texts.add(norm_key)

                    all_tags.append({
                        "text": phrase,
                        "timestamp": fdata["timestamp"],
                        "confidence": round(conf, 4),
                        "source": "ocr",
                    })

        except Exception as e:
            logger.warning(f"[OCR] Frame {fdata['frame_idx']} failed: {e}")
            continue

    logger.info(f"[OCR] Extracted {len(all_tags)} unique OCR tags from {len(frames)} frames")
    return all_tags


def unload_ocr():
    """Release the PaddleOCR instance to free memory."""
    global _ocr_instance
    if _ocr_instance is not None:
        del _ocr_instance
        _ocr_instance = None
        logger.info("[OCR] PaddleOCR unloaded")

"""
Search API Routes
==================
Blueprint: /api/search
"""

import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

search_bp = Blueprint("search", __name__)


@search_bp.route("/api/search", methods=["GET"])
def search_videos():
    """Search across all videos.

    Query params:
        q       (required) — search query text
        limit   (optional) — max results, default 20, max 50

    Returns results in same shape as /api/videos with extra
    search_score and match_reasons fields.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    try:
        limit = int(request.args.get("limit", 20))
        limit = max(1, min(limit, 50))
    except (ValueError, TypeError):
        limit = 20

    try:
        from search.search_engine import hybrid_search
        results = hybrid_search(query_text=query, top_k=limit)

        return jsonify({
            "query": query,
            "count": len(results),
            "results": results,
        })

    except Exception as e:
        logger.error(f"[Search API] Search failed: {e}", exc_info=True)
        return jsonify({"error": "Search failed", "details": str(e)}), 500


@search_bp.route("/api/search/stats", methods=["GET"])
def search_stats():
    """Return FAISS index status."""
    try:
        from search.embeddings import get_faiss_index
        idx = get_faiss_index()
        return jsonify({
            "indexed_videos": idx.count,
            "embedding_dim": idx.dim,
        })
    except Exception as e:
        logger.error(f"[Search API] Stats failed: {e}")
        return jsonify({"error": str(e)}), 500


@search_bp.route("/api/search/reindex", methods=["POST"])
def reindex():
    """Force rebuild the FAISS index from DB embeddings."""
    try:
        from search.embeddings import init_faiss_index
        count = init_faiss_index()
        return jsonify({"message": "Reindex complete", "indexed_videos": count})
    except Exception as e:
        logger.error(f"[Search API] Reindex failed: {e}")
        return jsonify({"error": str(e)}), 500

"""Quick search engine test."""
from database.db_config import init_db_pool
init_db_pool()

from search.search_engine import hybrid_search

def test(label, query):
    results = hybrid_search(query)
    print(f"\n[{label}] '{query}' → {len(results)} results")
    for v in results[:3]:
        sp = v.get('speaker', '?')
        cat = v.get('category', '?')
        reasons = v.get('match_reasons', [])
        sc = v.get('search_score', 0)
        tags = [t.get('tag', t) if isinstance(t, dict) else t for t in (v.get('tags') or [])[:3]]
        ents = [e.get('entity_text', '') for e in (v.get('entities') or [])[:3]]
        has_url = bool(v.get('video_url'))
        has_trans = bool(v.get('transcript_preview'))
        print(f"  speaker={sp} | cat={cat} | reasons={reasons} | score={sc}")
        print(f"    tags={tags} | entities={ents} | video_url={has_url} | transcript={has_trans}")

test("Speaker", "Nawaz Sharif")
test("English category", "economy")
test("Urdu category", "سیاست")
test("Entity", "Pakistan")
test("Speaker2", "Imran Khan")
test("Mixed", "Shahbaz Sharif economy")

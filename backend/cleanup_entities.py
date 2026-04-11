"""
One-time cleanup: delete garbage entities from the DB.
Run from backend/:  python cleanup_entities.py
"""
from database.db_config import init_db_pool, get_db_cursor
from search.search_engine import is_quality_entity

init_db_pool()

deleted = 0
kept = 0

with get_db_cursor(commit=True) as cur:
    cur.execute("SELECT id, entity_text, entity_type, video_id FROM entities")
    rows = cur.fetchall()

    for r in rows:
        if not is_quality_entity(r['entity_text']):
            cur.execute("DELETE FROM entities WHERE id = %s", (r['id'],))
            print(f"  DEL  {r['entity_type']:4}  {repr(r['entity_text'])}")
            deleted += 1
        else:
            kept += 1

print(f"\nDone.  Deleted {deleted} garbage entities, kept {kept}.")

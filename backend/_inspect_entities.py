"""Inspect entity quality."""
from database.db_config import init_db_pool, get_db_cursor
init_db_pool()

with get_db_cursor(commit=False) as cur:
    cur.execute("""
        SELECT entity_text, entity_type, mention_count
        FROM entities
        ORDER BY length(entity_text) DESC
        LIMIT 40
    """)
    print("=== Longest entities (likely garbage) ===")
    for r in cur.fetchall():
        et = r['entity_text']
        print(f"  {r['entity_type']:4} | mc={r['mention_count']:2} | len={len(et):2} | {repr(et)}")

    cur.execute("""
        SELECT entity_text, entity_type, mention_count
        FROM entities
        ORDER BY length(entity_text) ASC
        LIMIT 20
    """)
    print("\n=== Shortest entities ===")
    for r in cur.fetchall():
        et = r['entity_text']
        print(f"  {r['entity_type']:4} | mc={r['mention_count']:2} | len={len(et):2} | {repr(et)}")

    cur.execute("SELECT COUNT(*) AS total FROM entities")
    total = cur.fetchone()['total']

    # Count entities with >5 words (sentence fragments)
    cur.execute("""
        SELECT COUNT(*) AS cnt FROM entities
        WHERE array_length(string_to_array(entity_text, ' '), 1) > 4
    """)
    long_word = cur.fetchone()['cnt']

    # Count entities shorter than 2 chars
    cur.execute("""
        SELECT COUNT(*) AS cnt FROM entities
        WHERE length(trim(entity_text)) < 2
    """)
    short = cur.fetchone()['cnt']

    print(f"\nTotal entities: {total}")
    print(f"  >4 words (sentence fragments): {long_word}")
    print(f"  <2 chars: {short}")

import re

def normalize(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()

def extract_place_query(user_text: str) -> str | None:
    patterns = [
        r"zoom sur (.+)",
        r"montre (.+)",
        r"où est (.+)",
        r"localise (.+)"
    ]
    for p in patterns:
        m = re.search(p, user_text.lower())
        if m:
            return m.group(1)
    return None

def resolve_place(cursor, user_text: str):
    q = extract_place_query(user_text)
    if not q:
        return None

    nq = normalize(q)

    cursor.execute(
        """
        SELECT p.place_id, p.canonical_name, p.place_type,
               p.latitude, p.longitude, p.default_zoom,
               p.source_table, p.source_id
        FROM solarx_place_aliases a
        JOIN solarx_places p ON p.place_id = a.place_id
        WHERE a.normalized_alias = %s
        LIMIT 1
        """,
        (nq,)
    )
    row = cursor.fetchone()
    if not row:
        return None

    return {
        "lat": row["latitude"],
        "lon": row["longitude"],
        "zoom": row["default_zoom"],
        "highlight": {
            "source_table": row["source_table"],
            "source_id": row["source_id"]
        }
    }

import os
import json
import mysql.connector
from shapely.geometry import shape

DB_HOST = os.environ.get("DB_HOST", "db")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "rootpassword")
DB_NAME = os.environ.get("DB_NAME", "projet_solarx")

def _connect():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

def _pick_name(props: dict):
    for k in ("name", "nom", "NAME", "Name", "COMMUNE", "commune", "Ville", "ville"):
        v = props.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None

def ensure_geo_boundaries_table(geojson_path: str, table_name: str = "solarx_geo_boundaries"):
    conn = _connect()
    created = False
    inserted = 0
    skipped = 0

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """,
            (DB_NAME, table_name),
        )
        exists = (cur.fetchone() or (0,))[0] > 0

        if not exists:
            created = True
            cur.execute(
                f"""
                CREATE TABLE `{table_name}` (
                  `id` INT NOT NULL AUTO_INCREMENT,
                  `name` VARCHAR(255) NOT NULL,
                  `centroid_lat` DOUBLE NOT NULL,
                  `centroid_lon` DOUBLE NOT NULL,
                  `properties` JSON NULL,
                  `geometry` JSON NOT NULL,
                  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`id`),
                  UNIQUE KEY `uniq_name` (`name`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
                """
            )
            conn.commit()

        # Ne recharge pas si déjà rempli
        cur.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        nrows = (cur.fetchone() or (0,))[0]
        if nrows > 0:
            return {"created": created, "inserted": 0, "skipped": 0, "table": table_name, "already_filled": True}

        if not os.path.exists(geojson_path):
            raise FileNotFoundError(f"GeoJSON not found at: {geojson_path}")

        with open(geojson_path, "r", encoding="utf-8") as f:
            geo = json.load(f)

        for feat in geo.get("features", []):
            props = feat.get("properties") or {}
            geom = feat.get("geometry")
            if not geom:
                skipped += 1
                continue

            name = _pick_name(props)
            if not name:
                skipped += 1
                continue

            try:
                g = shape(geom)
                c = g.centroid
                lat = float(c.y)
                lon = float(c.x)
            except Exception:
                skipped += 1
                continue

            cur.execute(
                f"""
                INSERT IGNORE INTO `{table_name}`
                  (name, centroid_lat, centroid_lon, properties, geometry)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, lat, lon, json.dumps(props, ensure_ascii=False), json.dumps(geom, ensure_ascii=False)),
            )
            if cur.rowcount == 1:
                inserted += 1
            else:
                skipped += 1

        conn.commit()
        return {"created": created, "inserted": inserted, "skipped": skipped, "table": table_name, "already_filled": False}

    finally:
        try:
            conn.close()
        except Exception:
            pass

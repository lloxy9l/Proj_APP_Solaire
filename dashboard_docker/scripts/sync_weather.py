import time
import requests
import mysql.connector
from datetime import datetime, timedelta, date
from typing import Optional, Any, Iterator, Tuple

DB_CONFIG = {
    "host": "mysql_db",
    "user": "dev",
    "password": "password",
    "database": "projet_solarx"
}

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARS = "temperature_2m_mean,precipitation_sum,shortwave_radiation_sum,sunshine_duration"
TIMEZONE = "Europe/Paris"


def date_chunks(start: date, end: date, chunk_days: int = 90) -> Iterator[Tuple[date, date]]:
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=chunk_days - 1), end)
        yield cur, chunk_end
        cur = chunk_end + timedelta(days=1)


def parse_mysql_date(x: Any) -> Optional[date]:
    if x is None:
        return None
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    if isinstance(x, str):
        s = x.strip()
        if " " in s:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").date()
        return datetime.strptime(s, "%Y-%m-%d").date()
    return None


def get_last_date(cursor, idpoint: int) -> Optional[date]:
    cursor.execute(
        "SELECT MAX(date_collecte) FROM 2026_solarx_mesures WHERE idpoint=%s",
        (idpoint,)
    )
    r = cursor.fetchone()
    return parse_mysql_date(r[0] if r else None)


def fetch_open_meteo(lat: float, lon: float, start_date: str, end_date: str, max_retries: int = 8) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": DAILY_VARS,
        "timezone": TIMEZONE
    }

    for attempt in range(1, max_retries + 1):
        r = requests.get(OPEN_METEO_URL, params=params, timeout=60)

        if r.status_code == 429:
            # backoff exponentiel + respect Retry-After si présent
            retry_after = r.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = float(retry_after)
                except Exception:
                    wait = 2 ** (attempt - 1)
            else:
                wait = 2 ** (attempt - 1)

            wait = min(wait, 180)  # limite 3 minutes
            print(f"[429] Rate limit. Pause {wait:.1f}s puis retry ({attempt}/{max_retries})...")
            time.sleep(wait)
            continue

        r.raise_for_status()
        return r.json()

    raise RuntimeError("Open-Meteo rate limit persistant (429). Réessaie plus tard.")


def upsert_daily(cursor, idpoint: int, d: str, tavg, prcp, irr, sun):
    cursor.execute("""
        INSERT INTO 2026_solarx_mesures
        (idpoint, date_collecte, temperature, precipitation, irradiance, ensoleillement)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            temperature=VALUES(temperature),
            precipitation=VALUES(precipitation),
            irradiance=VALUES(irradiance),
            ensoleillement=VALUES(ensoleillement)
    """, (idpoint, d, tavg, prcp, irr, sun))


def sync():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT idpoint, latitude, longitude FROM 2026_solarx_pointsgps")
    points = cur.fetchall()
    points = points[0:100]

    today = date.today()

    for idpoint, lat, lon in points:
        idpoint = int(idpoint)
        lat = float(lat)
        lon = float(lon)

        last = get_last_date(cur, idpoint)

        if last is None:
            start = date(2024, 1, 1)
        else:
            start = last + timedelta(days=1)

        if start > today:
            print(f"[OK] idpoint={idpoint} déjà à jour (last={last})")
            continue

        print(f"[SYNC] idpoint={idpoint} {start} -> {today}")

        for c_start, c_end in date_chunks(start, today, chunk_days=90):
            print(f"   -> chunk {c_start} -> {c_end}")

            data = fetch_open_meteo(lat, lon, c_start.isoformat(), c_end.isoformat())

            daily = data.get("daily") or {}
            days = daily.get("time") or []
            tavg = daily.get("temperature_2m_mean") or []
            prcp = daily.get("precipitation_sum") or []
            irr = daily.get("shortwave_radiation_sum") or []
            sun = daily.get("sunshine_duration") or []

            for i, day in enumerate(days):
                upsert_daily(
                    cur, idpoint, day,
                    tavg[i] if i < len(tavg) else None,
                    prcp[i] if i < len(prcp) else None,
                    irr[i] if i < len(irr) else None,
                    sun[i] if i < len(sun) else None
                )

            conn.commit()

            # pause entre chunks pour éviter 429
            time.sleep(1.2)

        # pause entre points
        time.sleep(1.2)

    cur.close()
    conn.close()
    print("[DONE] Sync completed.")


if __name__ == "__main__":
    sync()

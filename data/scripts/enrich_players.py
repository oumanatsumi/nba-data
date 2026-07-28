import sys, os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

db = "postgresql://postgres:postgres@localhost:5432/nba_data"
engine = create_engine(db, echo=False)
conn = engine.connect()

df = pd.read_csv("archive/csv/common_player_info.csv")

updated = 0
for _, row in df.iterrows():
    pid = int(row["person_id"])
    bd = None
    if pd.notna(row.get("birthdate")):
        try: bd = datetime.strptime(str(row["birthdate"])[:10], "%Y-%m-%d").date()
        except: pass
    h = None
    if pd.notna(row.get("height")):
        try:
            parts = str(row["height"]).split("-")
            h = int(round(int(parts[0]) * 30.48 + int(parts[1]) * 2.54))
        except: pass
    w = None
    if pd.notna(row.get("weight")):
        try: w = int(round(float(row["weight"]) * 0.453592))
        except: pass

    dy = None; dr = None; dn = None
    if pd.notna(row.get("draft_year")):
        try: dy = int(float(row["draft_year"]))
        except: pass
    if pd.notna(row.get("draft_round")):
        try: dr = int(float(row["draft_round"]))
        except: pass
    if pd.notna(row.get("draft_number")):
        try: dn = int(float(row["draft_number"]))
        except: pass

    ny = None
    if pd.notna(row.get("season_exp")):
        try: ny = int(float(row["season_exp"]))
        except: pass

    pos = str(row.get("position", ""))[:20] if pd.notna(row.get("position")) else None
    country = str(row.get("country", ""))[:100] if pd.notna(row.get("country")) else None

    r = conn.execute(text(
        "UPDATE players SET birth_date = :bd, height_cm = :h, weight_kg = :w,"
        " position = COALESCE(position, :pos), country = COALESCE(country, :country),"
        " draft_year = COALESCE(draft_year, :dy), draft_round = COALESCE(draft_round, :dr),"
        " draft_number = COALESCE(draft_number, :dn), nba_years = COALESCE(nba_years, :ny)"
        " WHERE player_id = :pid"
    ), {"pid": pid, "bd": bd, "h": h, "w": w, "pos": pos, "country": country,
        "dy": dy, "dr": dr, "dn": dn, "ny": ny})
    updated += r.rowcount

    if pid == 2544:
        r2 = conn.execute(text("SELECT birth_date, height_cm, weight_kg, position, country, draft_year, draft_round, draft_number, nba_years FROM players WHERE player_id=2544")).fetchone()
        print(f"LeBron: birth={r2[0]}, {r2[1]}cm, {r2[2]}kg, pos={r2[3]}, {r2[4]}, draft={r2[5]} R{r2[6]} P{r2[7]}, yrs={r2[8]}")

conn.commit()
conn.close()
print(f"Updated {updated} players")
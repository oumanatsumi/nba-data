"""Analyze nba.sqlite database structure"""
import sqlite3
import os

db_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "archive", "nba.sqlite"
)
conn = sqlite3.connect(db_path)

# List all tables
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()

print("=== Tables in nba.sqlite ===")
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
    print(f"  {t[0]:40s} {count:>10,} rows")

print("\n=== Table Details ===")
for t in tables:
    name = t[0]
    info = conn.execute(f"PRAGMA table_info([{name}])").fetchall()
    cols = [(c[1], c[2]) for c in info]
    print(f"\n[{name}] ({len(cols)} columns)")
    for col_name, col_type in cols[:12]:
        print(f"  - {col_name:40s} {col_type}")

conn.close()

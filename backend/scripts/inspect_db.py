"""Quick inspection of fines.db and rules.json"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fines.db")
RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rules.json")

# ── fines.db ──
print("=" * 60)
print("FINES DATABASE (fines.db)")
print("=" * 60)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("SELECT sql FROM sqlite_master WHERE type='table'")
for r in c.fetchall():
    print(f"\nSCHEMA: {r[0]}")

c.execute("SELECT COUNT(*) FROM fines")
print(f"\nTotal rows: {c.fetchone()[0]}")

c.execute("SELECT DISTINCT offence_code FROM fines ORDER BY offence_code")
print("\nOffence codes:")
for r in c.fetchall():
    print(f"  - {r[0]}")

c.execute("SELECT DISTINCT state FROM fines ORDER BY state")
print("\nStates:")
for r in c.fetchall():
    print(f"  - {r[0]}")

c.execute("SELECT DISTINCT vehicle_class FROM fines ORDER BY vehicle_class")
print("\nVehicle classes:")
for r in c.fetchall():
    print(f"  - {r[0]}")

c.execute("SELECT * FROM fines LIMIT 5")
cols = [d[0] for d in c.description]
print(f"\nColumns: {cols}")
print("\nSample rows:")
for row in c.fetchall():
    print(f"  {dict(zip(cols, row))}")

conn.close()

# ── rules.json ──
print("\n" + "=" * 60)
print("RULES DATABASE (rules.json)")
print("=" * 60)
with open(RULES_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

rules = data.get("rules", [])
print(f"Total rules: {len(rules)}")

# Sample
if rules:
    print(f"\nSample rule:")
    r = rules[0]
    for k, v in r.items():
        if isinstance(v, str) and len(v) > 200:
            v = v[:200] + "..."
        print(f"  {k}: {v}")

# Count tags
all_tags = set()
for r in rules:
    all_tags.update(r.get("tags", []))
print(f"\nUnique tags ({len(all_tags)}): {sorted(all_tags)[:20]}...")

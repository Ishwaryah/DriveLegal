"""Fix fines database — add missing entries and fix incorrect data."""
import sqlite3
import sys
import codecs
from datetime import datetime

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

conn = sqlite3.connect('backend/data/fines.db')
cursor = conn.cursor()

now = datetime.now().isoformat()

# ── 1. Add MINOR_DRIVING / UNDERAGE_DRIVING for India ──
# Section 199A: ₹25,000 fine, guardian/owner liable, 3 years imprisonment
inserts = [
    # Minor/underage driving - India (all states)
    ("MINOR_DRIVING", "ALL", "ALL", 25000, 25000, "Section 199A — Guardian/owner liable. ₹25,000 fine + 3 years imprisonment + cancellation of registration of vehicle", "https://parivahan.gov.in", now, "IN", "INR"),
    
    # Disabled parking - Saudi Arabia
    ("DISABLED_PARKING", "ALL", "ALL", 500, 900, "Moroor — SAR 500-900 for parking in disabled spots without authorization", "https://www.moi.gov.sa", now, "SA", "SAR"),
    
    # No license plate / number plate violation - add more aliases
    # (NUMBER_PLATE_VIOLATION already exists with ₹5000, but add NO_LICENSE_PLATE alias)
    ("NO_LICENSE_PLATE", "ALL", "ALL", 5000, 10000, "Section 192 — ₹5,000 first offence, ₹10,000 repeat. Driving without valid registration/number plate", "https://parivahan.gov.in", now, "IN", "INR"),

    # California specific no insurance
    ("NO_INSURANCE", "ALL", "CALIFORNIA", 100, 500, "CA Vehicle Code §16029 — $100-$200 base fine (with surcharges totals $400-$900). License suspension possible.", "https://leginfo.legislature.ca.gov", now, "US", "USD"),

    # New York DUI specific
    ("DRUNK_DRIVING", "ALL", "NEW_YORK", 500, 5000, "NY VTL §1192 — $500-$1,000 fine, license revoked 6+ months, possible jail. Misdemeanor.", "https://dmv.ny.gov", now, "US", "USD"),
]

for row in inserts:
    # Check if already exists
    cursor.execute(
        "SELECT id FROM fines WHERE offence_code=? AND vehicle_class=? AND state=? AND country=?",
        (row[0], row[1], row[2], row[8])
    )
    existing = cursor.fetchone()
    if existing:
        print(f"SKIP (exists): {row[0]} / {row[2]} / {row[8]}")
    else:
        import hashlib
        vhash = hashlib.sha256(f"{row[0]}{row[1]}{row[2]}{row[3]}{row[8]}".encode()).hexdigest()
        cursor.execute(
            """INSERT INTO fines (offence_code, vehicle_class, state, amount_inr, repeat_amount_inr, 
               section_ref, source_url, fetched_at, country, currency, version_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            row + (vhash,)
        )
        print(f"ADDED: {row[0]} / {row[2]} / {row[8]} — amount={row[3]}")

conn.commit()
conn.close()
print("\nDatabase fixes applied successfully!")

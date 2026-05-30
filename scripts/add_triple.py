import sqlite3
from datetime import datetime

conn = sqlite3.connect('backend/data/fines.db')
c = conn.cursor()
now = datetime.now().isoformat()

# Section 128 / 194C of Motor Vehicles Act: 
# Riding more than two persons on a two-wheeler
# Fine: Rs. 1000 and disqualification of license for 3 months
row = ("TRIPLE_RIDING", "TWO_WHEELER", "ALL", 1000, 1000, "Section 194C — ₹1,000 fine + disqualification of license for 3 months", "https://parivahan.gov.in", now, "IN", "INR")

import hashlib
vhash = hashlib.sha256(f"{row[0]}{row[1]}{row[2]}{row[3]}{row[8]}".encode()).hexdigest()

c.execute("SELECT id FROM fines WHERE offence_code=? AND vehicle_class=? AND state=? AND country=?", (row[0], row[1], row[2], row[8]))
if not c.fetchone():
    c.execute(
        """INSERT INTO fines (offence_code, vehicle_class, state, amount_inr, repeat_amount_inr, 
           section_ref, source_url, fetched_at, country, currency, version_hash)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        row + (vhash,)
    )
    print("Added TRIPLE_RIDING to database")
else:
    print("TRIPLE_RIDING already exists")

conn.commit()
conn.close()

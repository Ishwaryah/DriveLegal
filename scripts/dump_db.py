import sqlite3, json, sys, codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

conn = sqlite3.connect('backend/data/fines.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check specific offences that failed
checks = [
    ("NO_INSURANCE", "ALL", "IN"),
    ("NO_INSURANCE", "UP", "IN"),
    ("NO_SEATBELT", "ALL", "IN"),
    ("NO_LICENSE_PLATE", "ALL", "IN"),
    ("NO_NUMBER_PLATE", "ALL", "IN"),
    ("NO_REG_PLATE", "ALL", "IN"),
    ("MINOR_DRIVING", "ALL", "IN"),
    ("UNDERAGE_DRIVING", "ALL", "IN"),
    ("DISABLED_PARKING", "ALL", "SA"),
]

for code, state, country in checks:
    cursor.execute(
        "SELECT offence_code, vehicle_class, state, amount_inr, repeat_amount_inr, section_ref FROM fines WHERE offence_code=? AND state=? AND country=?",
        (code, state, country)
    )
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"FOUND: {dict(row)}")
    else:
        print(f"NOT FOUND: {code} / {state} / {country}")

# Search for anything with "insurance" in India
print("\n=== ALL INSURANCE IN INDIA ===")
cursor.execute("SELECT offence_code, vehicle_class, state, amount_inr, repeat_amount_inr, section_ref FROM fines WHERE offence_code LIKE '%INSURANCE%' AND country='IN'")
for row in cursor.fetchall():
    print(dict(row))

# Search for anything with "plate" or "number" or "registration"
print("\n=== ALL PLATE/NUMBER IN INDIA ===")
cursor.execute("SELECT offence_code, vehicle_class, state, amount_inr, repeat_amount_inr, section_ref FROM fines WHERE (offence_code LIKE '%PLATE%' OR offence_code LIKE '%NUMBER%' OR offence_code LIKE '%REG%') AND country='IN'")
for row in cursor.fetchall():
    print(dict(row))

# Search for anything with "minor" or "underage"
print("\n=== ALL MINOR/UNDERAGE IN INDIA ===")
cursor.execute("SELECT offence_code, vehicle_class, state, amount_inr, repeat_amount_inr, section_ref FROM fines WHERE (offence_code LIKE '%MINOR%' OR offence_code LIKE '%UNDER%' OR offence_code LIKE '%JUVENILE%') AND country='IN'")
for row in cursor.fetchall():
    print(dict(row))

conn.close()

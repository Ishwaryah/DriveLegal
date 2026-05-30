import sqlite3

conn = sqlite3.connect('backend/data/fines.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT offence_code, vehicle_class, state, amount_inr, section_ref FROM fines WHERE offence_code='TRIPLE_RIDING'")
print("TRIPLE_RIDING:")
for row in c.fetchall():
    print(dict(row))

c.execute("SELECT offence_code, vehicle_class, state, amount_inr, section_ref FROM fines WHERE offence_code='NO_HELMET'")
print("NO_HELMET:")
for row in c.fetchall():
    print(dict(row))

c.execute("SELECT offence_code, vehicle_class, state, amount_inr, section_ref FROM fines WHERE offence_code='SPEED_EXCESS'")
print("SPEED_EXCESS:")
for row in c.fetchall():
    print(dict(row))

conn.close()

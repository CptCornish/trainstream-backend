import sqlite3

conn = sqlite3.connect("trainstream.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("PRAGMA table_info(participants);")
rows = cur.fetchall()

for row in rows:
    print(dict(row))

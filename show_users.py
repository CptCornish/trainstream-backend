import sqlite3

db_path = "trainstream.db"

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("COLUMNS:")
cur.execute("PRAGMA table_info(users);")
for row in cur.fetchall():
    print(dict(row))

print("\nDATA (first 10 rows):")
cur.execute("SELECT * FROM users LIMIT 10;")
for row in cur.fetchall():
    print(dict(row))

conn.close()

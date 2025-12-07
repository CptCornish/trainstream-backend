import sqlite3

conn = sqlite3.connect("trainstream.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("PRAGMA table_info(course_templates);")
print("COLUMNS:")
for row in cur.fetchall():
    print(row["name"], row["type"])

print("\nDATA:")
cur.execute("SELECT * FROM course_templates")
for row in cur.fetchall():
    print(dict(row))

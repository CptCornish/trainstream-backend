import sqlite3

db_path = "trainstream.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

def has_column(table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table});")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols

changed = False

if not has_column("course_templates", "validity_months"):
    print("Adding column validity_months INTEGER...")
    cur.execute("ALTER TABLE course_templates ADD COLUMN validity_months INTEGER")
    changed = True
else:
    print("validity_months already exists")

if not has_column("course_templates", "cpd_hours"):
    print("Adding column cpd_hours REAL...")
    cur.execute("ALTER TABLE course_templates ADD COLUMN cpd_hours REAL")
    changed = True
else:
    print("cpd_hours already exists")

if changed:
    conn.commit()
    print("Upgrade complete.")
else:
    print("No changes needed.")

conn.close()

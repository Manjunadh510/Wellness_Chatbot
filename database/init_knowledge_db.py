import sqlite3

conn = sqlite3.connect("knowledge_base.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition TEXT UNIQUE NOT NULL,
    explanation TEXT NOT NULL,
    symptoms TEXT NOT NULL,
    first_aid TEXT NOT NULL,
    prevention TEXT NOT NULL
);
""")

conn.commit()
conn.close()
print("✅ Knowledge base table created.")

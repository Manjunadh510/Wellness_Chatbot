import sqlite3, json

with open("./health_knowledge_base_expanded.json") as f:
    data = json.load(f)

conn = sqlite3.connect("knowledge_base.db")
cursor = conn.cursor()

for entry in data:
    cursor.execute("""
        INSERT OR IGNORE INTO knowledge_base (condition, explanation, symptoms, first_aid, prevention)
        VALUES (?, ?, ?, ?, ?)
    """, (
        entry["condition"],
        entry["explanation"],
        json.dumps(entry["symptoms"]),
        entry["first_aid"],
        entry["prevention"]
    ))

conn.commit()
conn.close()

print("✅ Health knowledge data imported.")

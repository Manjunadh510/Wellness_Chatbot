import sqlite3
import bcrypt

conn = sqlite3.connect("admins.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);
""")

admin_email = "admin@gmail.com"
admin_username = "Admin"
adminpwd = "Admin@123"

hashed_password = bcrypt.hashpw(adminpwd.encode(), bcrypt.gensalt()).decode()

cursor.execute("INSERT OR IGNORE INTO admin_users (email, username, password) VALUES (?, ?, ?)",
               (admin_email, admin_username, hashed_password))

conn.commit()
conn.close()

print("✅ Admin user added.")

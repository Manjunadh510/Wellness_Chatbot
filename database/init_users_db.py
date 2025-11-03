import sqlite3

def initialize_db():
    database = 'users.db'

    create_users = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        age INTEGER,
        language TEXT
    );
    """

    create_chats = """
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """

    create_chat_messages = """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        role TEXT,
        message TEXT,
        entity TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES chats(id)
    );
    """

    create_feedback = """
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        user_email TEXT NOT NULL,
        rating INTEGER,
        comment TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES chats(id)
    );
    """

    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        cursor.execute(create_users)
        cursor.execute(create_chats)
        cursor.execute(create_chat_messages)
        cursor.execute(create_feedback)
        conn.commit()

if __name__ == "__main__":
    initialize_db()
    print("✅ Users, chats, chat_messages & feedback tables created.")

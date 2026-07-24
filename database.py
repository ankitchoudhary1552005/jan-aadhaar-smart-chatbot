import sqlite3

def create_database():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        user_message TEXT,
        bot_reply TEXT,
        chat_time TEXT
    )
    """)

    conn.commit()
    conn.close()

    print("Database created successfully!")

create_database()
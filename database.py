import sqlite3

conn = sqlite3.connect("chatbot.db")
cursor = conn.cursor()

# Chat table
cursor.execute("""
CREATE TABLE IF NOT EXISTS chats(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    user_message TEXT NOT NULL,
    bot_reply TEXT NOT NULL,
    chat_time TEXT NOT NULL
)
""")

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("Database created successfully!")
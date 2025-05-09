from g4f.models import default
from g4f.client import Client
import argparse
import sqlite3
from datetime import datetime
from datetime import timedelta

# Define the parser
parser = argparse.ArgumentParser(description='Short sample app')
parser.add_argument('--text', action="store", dest='text', default="")
parser.add_argument('--uid', action="store", dest='uid', default="")
args = parser.parse_args()

conn = sqlite3.connect("chats.sqlite")
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS gpt_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    role TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL
)
""")
conn.commit()

def store_message(user_id, role, message):
    cursor.execute("""
        INSERT INTO messages (user_id, role, message, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, role, message, datetime.utcnow()))
    conn.commit()

def get_user_messages(user_id):
    cursor.execute("""
        SELECT role, message, created_at FROM gpt_messages
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    return cursor.fetchall()

def delete_expired_messages():
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    cursor.execute("""
        DELETE FROM gpt_messages WHERE created_at < ?
    """, (one_year_ago,))
    conn.commit()

def main():
    client = Client()

    messages = get_user_messages(args.uid)
    print(messages, flush=True, end="")

    # response = client.chat.completions.create(
    #     model=default,
    #     messages=[{"role": "user", "content": args.text}],
    # )
    #
    # print(response.choices[0].message.content, flush=True, end="")

if __name__ == "__main__":
    main()
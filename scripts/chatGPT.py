from g4f.models import default
from g4f.client import Client
import argparse
import sqlite3
from datetime import datetime, timedelta

# Define the parser
parser = argparse.ArgumentParser(description='Short sample app')
parser.add_argument('--user', action=argparse.BooleanOptionalAction)
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
        INSERT INTO gpt_messages (user_id, role, message, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, role, message, datetime.utcnow()))
    conn.commit()

def get_user_messages(user_id):
    cursor.execute("""
        SELECT role, message, created_at FROM gpt_messages
        WHERE user_id = ?
        ORDER BY created_at
    """, (user_id,))
    data = cursor.fetchall()
    formatted = [{"role": role, "content": content} for role, content, _ in data]
    return formatted


def delete_expired_messages():
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    cursor.execute("""
        DELETE FROM gpt_messages WHERE created_at < ?
    """, (one_year_ago,))
    conn.commit()

def main():
    client = Client()

    # messages = get_user_messages(args.uid)
    messages = list()
    messages.append({"role": "user", "content": args.text})

    response = client.chat.completions.create(
        model=default,
        messages=messages,
    )

    answer = response.choices[0].message.content

    if answer[:16] == "New g4f version:":
        try:
            answer = answer.split("pip install -U g4f")[1]
        except IndexError:
            answer = None


    if answer:
        # store_message(args.uid, "user", args.text)
        # store_message(args.uid, "assistant", answer)
        if args.user:
            print(f"<@{args.uid}>,\n{answer}", flush=True, end="")
        else:
            print(f"{answer}", flush=True, end="")
    else:
        print("I dont received answer from server. Try again.")

if __name__ == "__main__":
    main()
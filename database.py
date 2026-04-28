import sqlite3

conn = sqlite3.connect("resume.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    score REAL,
    summary TEXT
)
""")
conn.commit()

def save_result(username, score, summary):
    c.execute(
        "INSERT INTO history (username, score, summary) VALUES (?, ?, ?)",
        (username, score, summary)
    )
    conn.commit()

def get_history(username):
    c.execute(
        "SELECT score, summary FROM history WHERE username = ? ORDER BY id DESC",
        (username,)
    )
    return c.fetchall()

def clear_history(username):
    c.execute(
        "DELETE FROM history WHERE username = ?",
        (username,)
    )
    conn.commit()
import sqlite3
import os

DB_PATH = "scores.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  score INTEGER,
                  wave INTEGER,
                  kills INTEGER,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_score(score, wave, kills):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO scores (score, wave, kills) VALUES (?, ?, ?)", (score, wave, kills))
    conn.commit()
    conn.close()

def get_highscore():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT MAX(score) FROM scores")
    result = c.fetchone()
    conn.close()
    return result[0] if result and result[0] is not None else 0

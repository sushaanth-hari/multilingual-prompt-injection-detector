import sqlite3
import hashlib
import os
from datetime import datetime

AUTH_DB = "data/users.db"

def init_auth_db():
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, email: str, password: str) -> dict:
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password, created_at)
            VALUES (?, ?, ?, ?)
        ''', (username, email, hash_password(password),
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return {"success": True, "message": "Registration successful!"}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username or email already exists!"}
    finally:
        conn.close()

def login_user(username: str, password: str) -> dict:
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, email FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"success": True, "user": {"id": user[0], "username": user[1], "email": user[2]}}
    return {"success": False, "message": "Invalid username or password!"}
import sqlite3
import os
from datetime import datetime

DB_FILE = "data/detections.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            detected_language TEXT,
            translated_text TEXT,
            is_injection INTEGER,
            risk_level TEXT,
            threat_types TEXT,
            confidence REAL,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_detection(result: dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO detections
        (original_text, detected_language, translated_text,
         is_injection, risk_level, threat_types, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        result.get("original_text"),
        result.get("detected_language"),
        result.get("translated_text"),
        1 if result.get("is_injection") else 0,
        result.get("risk_level"),
        ", ".join(result.get("threat_types", [])),
        result.get("confidence", 0),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def get_all_detections():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detections ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "original_text": r[1],
            "detected_language": r[2],
            "translated_text": r[3],
            "is_injection": bool(r[4]),
            "risk_level": r[5],
            "threat_types": r[6],
            "confidence": r[7],
            "timestamp": r[8]
        }
        for r in rows
    ]

def get_db_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM detections")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM detections WHERE is_injection=1")
    injections = cursor.fetchone()[0]
    cursor.execute(
        "SELECT detected_language, COUNT(*) FROM detections GROUP BY detected_language"
    )
    languages = dict(cursor.fetchall())
    cursor.execute(
        "SELECT risk_level, COUNT(*) FROM detections GROUP BY risk_level"
    )
    risk_counts = dict(cursor.fetchall())
    conn.close()
    return {
        "total_checked": total,
        "injections_found": injections,
        "safe_prompts": total - injections,
        "languages_detected": languages,
        "risk_breakdown": risk_counts
    }
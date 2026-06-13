import json
import os
from datetime import datetime

LOG_FILE = "data/logs.json"

def load_logs() -> list:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def save_log(entry: dict):
    logs = load_logs()
    entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def get_stats() -> dict:
    logs = load_logs()
    total = len(logs)
    injections = sum(1 for l in logs if l.get("is_injection"))
    safe = total - injections
    languages = {}
    for l in logs:
        lang = l.get("detected_language", "unknown")
        languages[lang] = languages.get(lang, 0) + 1
    return {
        "total_checked": total,
        "injections_found": injections,
        "safe_prompts": safe,
        "languages_detected": languages
    }

def format_response(result: dict) -> dict:
    return {
        "status": "success",
        "data": result,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
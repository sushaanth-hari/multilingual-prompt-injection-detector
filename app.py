from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.detector import detect_injection
from src.utils import format_response
from src.database import init_db, save_detection, get_all_detections, get_db_stats
from src.auth import init_auth_db, register_user, login_user
from src.report import generate_pdf_report
from src.chat import get_ai_response
import sqlite3
import os

app = FastAPI(title="InjectionGuard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
init_auth_db()

class PromptRequest(BaseModel):
    text: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/")
def home():
    return {"message": "InjectionGuard is running!"}

@app.post("/register")
def register(req: RegisterRequest):
    result = register_user(req.username, req.email, req.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/login")
def login(req: LoginRequest):
    result = login_user(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result

@app.post("/chat")
def chat(request: PromptRequest):
    detection = detect_injection(request.text)
    save_detection(detection)
    ai_response = get_ai_response(request.text)
    return {
        "blocked": False,
        "is_injection": detection["is_injection"],
        "has_warning": detection["is_injection"],
        "risk_level": detection["risk_level"],
        "threat_types": detection["threat_types"],
        "confidence": detection["confidence"],
        "detected_language": detection["detected_language"],
        "message": ai_response
    }

@app.post("/detect")
def detect(request: PromptRequest):
    result = detect_injection(request.text)
    save_detection(result)
    return format_response(result)

@app.get("/stats")
def stats():
    return get_db_stats()

@app.get("/chart-data")
def chart_data():
    conn = sqlite3.connect("data/detections.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id,confidence,is_injection,timestamp FROM detections ORDER BY id DESC LIMIT 10")
    recent = cursor.fetchall()
    cursor.execute("SELECT risk_level,COUNT(*) FROM detections GROUP BY risk_level")
    risk = dict(cursor.fetchall())
    cursor.execute("SELECT detected_language,COUNT(*) FROM detections GROUP BY detected_language")
    languages = dict(cursor.fetchall())
    cursor.execute("SELECT DATE(timestamp),COUNT(*) FROM detections WHERE timestamp>=DATE('now','-7 days') GROUP BY DATE(timestamp) ORDER BY DATE(timestamp)")
    daily = dict(cursor.fetchall())
    conn.close()
    return {
        "confidence_data": [
            {"id":r[0],"confidence":r[1],"is_injection":bool(r[2]),"timestamp":r[3]}
            for r in reversed(recent)
        ],
        "risk_breakdown": risk,
        "language_breakdown": languages,
        "daily_detections": daily
    }

@app.get("/history")
def history():
    return get_all_detections()

@app.delete("/clear")
def clear_history():
    conn = sqlite3.connect("data/detections.db")
    conn.execute("DELETE FROM detections")
    conn.commit()
    conn.close()
    return {"message": "Cleared!"}

@app.get("/report")
def download_report():
    detections = get_all_detections()
    stats_data = get_db_stats()
    filename = generate_pdf_report(detections, stats_data)
    return FileResponse(
        path=os.path.abspath(filename),
        media_type="application/pdf",
        filename="InjectionGuard_Report.pdf"
    )
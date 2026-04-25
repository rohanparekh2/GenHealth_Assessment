import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import models
from db import Base, SessionLocal, engine
from routes.orders import router as orders_router
from services.upload_service import process_upload


app = FastAPI(title="Orders API")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://genhealth-assessment-1.onrender.com"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logger_middleware(request, call_next):
    response = await call_next(request)

    db = SessionLocal()
    try:
        db.add(
            models.RequestLog(
                endpoint_path=request.url.path,
                http_method=request.method,
            )
        )
        db.commit()
    finally:
        db.close()

    return response


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(orders_router)
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


@app.post("/upload", tags=["upload"])
def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = file.file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(pdf_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20MB limit")

    try:
        return process_upload(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc


@app.get("/logs", tags=["logs"])
def get_logs():
    db = SessionLocal()
    try:
        logs = db.query(models.SystemLog).order_by(models.SystemLog.timestamp.desc()).limit(200).all()
        return [
            {
                "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                "action": log.action,
                "entity_id": log.entity_id,
                "message": log.message,
            }
            for log in logs
        ]
    finally:
        db.close()

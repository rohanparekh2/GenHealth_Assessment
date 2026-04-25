from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

import models
from db import Base, SessionLocal, engine
from routes.orders import router as orders_router
from services.pdf_parser import extract_patient_fields, extract_text_from_pdf


app = FastAPI(title="Orders API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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

    try:
        extracted_text = extract_text_from_pdf(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc

    parsed_fields = extract_patient_fields(extracted_text)
    response = {
        "first_name": parsed_fields.get("first_name"),
        "last_name": parsed_fields.get("last_name"),
        "date_of_birth": parsed_fields.get("date_of_birth"),
    }
    if not all([response["first_name"], response["last_name"], response["date_of_birth"]]):
        response["raw_text_preview"] = parsed_fields.get("raw_text_preview")
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Could not extract all required patient fields from PDF.",
                "parsed": response,
            },
        )

    dob_raw = str(response["date_of_birth"])
    dob_value = None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y"):
        try:
            dob_value = datetime.strptime(dob_raw, fmt).date()
            break
        except ValueError:
            continue

    if dob_value is None:
        raise HTTPException(
            status_code=400,
            detail=f"Extracted date_of_birth '{dob_raw}' is not in a supported format.",
        )

    db = SessionLocal()
    patient_id = None
    try:
        patient = models.Order(
            patient_first_name=str(response["first_name"]),
            patient_last_name=str(response["last_name"]),
            date_of_birth=dob_value,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        db.add(
            models.SystemLog(
                action="UPLOAD_PDF",
                entity_id=patient.id,
                message=f"Imported patient {patient.patient_first_name} {patient.patient_last_name} from PDF",
            )
        )
        db.commit()
        patient_id = patient.id
    finally:
        db.close()

    return {**response, "id": patient_id}


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

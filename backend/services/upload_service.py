from datetime import datetime

import models
from db import SessionLocal
from services.pdf_parser import extract_patient_fields, extract_text_from_pdf


def process_upload(pdf_bytes: bytes) -> dict:
    extracted_text = extract_text_from_pdf(pdf_bytes)
    parsed_fields = extract_patient_fields(extracted_text)

    response = {
        "first_name": parsed_fields.get("first_name"),
        "last_name": parsed_fields.get("last_name"),
        "date_of_birth": parsed_fields.get("date_of_birth"),
    }
    if not all([response["first_name"], response["last_name"], response["date_of_birth"]]):
        response["raw_text_preview"] = parsed_fields.get("raw_text_preview")
        response["created"] = False
        response["reason"] = "Could not extract all required patient fields from PDF."
        return response

    dob_raw = str(response["date_of_birth"])
    dob_value = None
    for fmt in (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%m/%d/%y",
        "%d/%m/%y",
        "%m-%d-%y",
        "%d-%m-%y",
    ):
        try:
            dob_value = datetime.strptime(dob_raw, fmt).date()
            break
        except ValueError:
            continue

    if dob_value is None:
        response["created"] = False
        response["reason"] = f"Extracted date_of_birth '{dob_raw}' is not in a supported format."
        return response

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

    return {**response, "id": patient_id, "created": True}

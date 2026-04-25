import io
import os
import re

import fitz
import pytesseract
from PIL import Image


def _is_valid_extracted_text(text: str) -> bool:
    cleaned = (text or "").strip()
    return len(cleaned) > 30 and any(char.isalpha() for char in cleaned)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        extracted_text = "\n".join(page.get_text() for page in doc)
        if _is_valid_extracted_text(extracted_text):
            return extracted_text

        ocr_dpi = int(os.getenv("OCR_DPI", "150"))
        max_ocr_pages = int(os.getenv("MAX_OCR_PAGES", "4"))
        ocr_text_chunks = []
        try:
            for page_index, page in enumerate(doc):
                if page_index >= max_ocr_pages:
                    break
                pix = page.get_pixmap(dpi=ocr_dpi)
                with Image.open(io.BytesIO(pix.tobytes("png"))) as image:
                    ocr_text_chunks.append(pytesseract.image_to_string(image))
        except Exception:
            return extracted_text
        return "\n".join(ocr_text_chunks)


def _normalize_text(raw_text: str) -> tuple[str, str]:
    original = raw_text or ""
    collapsed = re.sub(r"\s+", " ", original).strip()
    normalized = collapsed.lower()
    return collapsed, normalized


def _split_name(full_name: str) -> tuple[str | None, str | None]:
    parts = [p for p in full_name.strip().split() if p]
    if len(parts) < 2:
        return None, None
    return parts[0], parts[-1]


def extract_patient_fields(raw_text: str) -> dict:
    collapsed_text, normalized_text = _normalize_text(raw_text)
    raw_lines = [line.strip() for line in (raw_text or "").splitlines() if line.strip()]

    first_name = None
    last_name = None
    date_of_birth = None

    dob_patterns = [
        r"\b(?:patient date of birth|dob|date of birth|birth date|d\.o\.b\.)\b\s*[:\-]?\s*([0-3]?\d[\/\-][0-3]?\d[\/\-]\d{4})",
        r"\b(?:patient date of birth|dob|date of birth|birth date|d\.o\.b\.)\b\s*[:\-]?\s*(\d{4}[\/\-][0-1]?\d[\/\-][0-3]?\d)",
        r"\b(?:patient date of birth|dob|date of birth|birth date|d\.o\.b\.)\b\s*[:\-]?\s*([a-z]{3,9}\s+\d{1,2},?\s+\d{4})",
    ]
    for pattern in dob_patterns:
        match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
        if match:
            date_of_birth = match.group(1).strip()
            break

    if not date_of_birth:
        fallback_dob_patterns = [
            r"\b([0-3]?\d[\/\-][0-3]?\d[\/\-]\d{4})\b",
            r"\b(\d{4}[\/\-][0-1]?\d[\/\-][0-3]?\d)\b",
            r"\b([a-z]{3,9}\s+\d{1,2},?\s+\d{4})\b",
        ]
        for pattern in fallback_dob_patterns:
            fallback_dob = re.search(
                pattern,
                normalized_text,
                flags=re.IGNORECASE,
            )
            if fallback_dob:
                date_of_birth = fallback_dob.group(1).strip()
                break

    for line in raw_lines:
        match = re.search(
            r"(?i)\b(?:patient name|full name|name)\b\s*[:\-]\s*([a-z'`\-]+(?:\s+[a-z'`\-]+){1,2})\b",
            line,
        )
        if match:
            first_name, last_name = _split_name(match.group(1))
            if first_name and last_name:
                break

    labeled_name_patterns = [
        r"\b(?:patient name|full name|name)\b\s*[:\-]\s*([a-z'`\-]+(?:\s+[a-z'`\-]+){1,2})\b",
    ]
    for pattern in labeled_name_patterns:
        if first_name and last_name:
            break
        match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
        if match:
            first_name, last_name = _split_name(match.group(1))
            if first_name and last_name:
                break

    if not first_name or not last_name:
        nearby_patient_name = re.search(
            r"\bpatient(?:\s+name)?\b.{0,40}\b([a-z'`\-]{2,})\s+([a-z'`\-]{2,})\b",
            normalized_text,
            flags=re.IGNORECASE,
        )
        if nearby_patient_name:
            candidate_first = nearby_patient_name.group(1).strip()
            candidate_last = nearby_patient_name.group(2).strip()
            blocked_terms = {"number", "phone", "dob", "date", "birth", "member", "id"}
            if candidate_first not in blocked_terms and candidate_last not in blocked_terms:
                first_name = first_name or candidate_first
                last_name = last_name or candidate_last

    if first_name:
        first_name = first_name.title()
    if last_name:
        last_name = last_name.title()

    return {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": date_of_birth,
        "raw_text_preview": collapsed_text[:300],
    }

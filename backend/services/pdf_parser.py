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
    blocked_name_terms = {
        "number",
        "phone",
        "dob",
        "date",
        "birth",
        "member",
        "id",
        "source",
        "facility",
        "record",
        "information",
        "medical",
        "history",
    }

    dob_patterns = [
        r"\b(?:patient date of birth|dob|date of birth|birth date|d\.o\.b\.)\b\s*[:\-]?\s*([0-3]?\d[\/\-][0-3]?\d[\/\-]\d{4})",
        r"\b(?:patient date of birth|dob|date of birth|birth date|d\.o\.b\.)\b\s*[:\-]?\s*([0-3]?\d[\/\-][0-3]?\d[\/\-]\d{2})",
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
            r"\b([0-3]?\d[\/\-][0-3]?\d[\/\-]\d{2})\b",
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

    if not date_of_birth:
        # Some documents use "Date: mm/dd/yy" near patient demographics.
        contextual_date_match = re.search(
            r"(?i)\b(?:patient name|date of birth|birth date).{0,120}\bdate\b\s*[:\-]\s*([0-3]?\d[\/\-][0-3]?\d[\/\-](?:\d{2}|\d{4}))",
            normalized_text,
        )
        if contextual_date_match:
            date_of_birth = contextual_date_match.group(1).strip()

    global_comma_name_match = re.search(
        r"(?i)\b(?:patient name|patient information|patient info)\b\s*[:\-]?\s*([a-z'`\-]{2,})\s*,\s*([a-z'`\-]{2,})\b",
        normalized_text,
    )
    if global_comma_name_match:
        candidate_last = global_comma_name_match.group(1).strip()
        candidate_first = global_comma_name_match.group(2).strip()
        if candidate_first not in blocked_name_terms and candidate_last not in blocked_name_terms:
            last_name = candidate_last
            first_name = candidate_first

    for line in raw_lines:
        if first_name and last_name:
            break
        # Prefer explicit "Patient Name: Last, First" format.
        comma_name_match = re.search(
            r"(?i)\b(?:patient name|patient information|patient info)\b\s*[:\-]\s*([a-z'`\-]+)\s*,\s*([a-z'`\-]+)\b",
            line,
        )
        if comma_name_match:
            candidate_last = comma_name_match.group(1).strip()
            candidate_first = comma_name_match.group(2).strip()
            if candidate_first not in blocked_name_terms and candidate_last not in blocked_name_terms:
                last_name = candidate_last
                first_name = candidate_first
                break

        # Fallback to "Patient Name: First Last" format and stop before extra labels.
        direct_name_match = re.search(
            r"(?i)\b(?:patient name|patient information|patient info|full name|name)\b\s*[:\-]?\s*([a-z'`\-]+\s+[a-z'`\-]+)(?:\s+(?:birth date|date of birth|date|dob|phone|address|id)\b|$)",
            line,
        )
        if direct_name_match:
            candidate_first, candidate_last = _split_name(direct_name_match.group(1))
            if (
                candidate_first
                and candidate_last
                and candidate_first.lower() not in blocked_name_terms
                and candidate_last.lower() not in blocked_name_terms
            ):
                first_name, last_name = candidate_first, candidate_last
                break

    if not first_name or not last_name:
        # Support common pattern: "Patient Information John Doe Birth Date ..."
        info_name_match = re.search(
            r"(?i)\bpatient information\b\s*[:\-]?\s*([a-z'`\-]{2,})\s+([a-z'`\-]{2,})(?:\s+\b(?:birth date|date of birth|dob|date)\b)",
            normalized_text,
        )
        if info_name_match:
            candidate_first = info_name_match.group(1).strip()
            candidate_last = info_name_match.group(2).strip()
            if candidate_first not in blocked_name_terms and candidate_last not in blocked_name_terms:
                first_name = first_name or candidate_first
                last_name = last_name or candidate_last

    if not first_name or not last_name:
        # Support "Patient Details:" followed by a name line.
        details_name_match = re.search(
            r"(?i)\bpatient details\b\s*[:\-]?\s*(?:\n|\s)+([a-z'`\-]{2,})\s+([a-z'`\-]{2,})(?:\s+\b(?:birth date|date of birth|dob|date)\b|$)",
            raw_text or "",
        )
        if details_name_match:
            candidate_first = details_name_match.group(1).strip().lower()
            candidate_last = details_name_match.group(2).strip().lower()
            if candidate_first not in blocked_name_terms and candidate_last not in blocked_name_terms:
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

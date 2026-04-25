# GenHealth Assessment

Minimal full-stack patient management app with:

- FastAPI + SQLAlchemy backend
- React + TypeScript + Vite frontend
- PDF upload parsing (PyMuPDF + OCR fallback via Tesseract)

## Deployed URLs

- Backend: `https://genhealth-assessment-backend.onrender.com`
- Frontend: `https://genhealth-assessment-1.onrender.com`

## Features

- Create, list, update, and delete patient records
- Upload PDF and extract patient fields (first name, last name, DOB)
- Persist records and system logs in database
- System logs endpoint + dashboard table

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic
- Frontend: React, TypeScript, Vite, Tailwind CSS
- OCR: PyMuPDF + pytesseract + Tesseract binary

## Local Setup

### 1) Install backend dependencies

```bash
pip install -r requirements.txt
```

Install Tesseract (needed for scanned/image PDFs):

```bash
brew install tesseract
```

### 2) Run backend

```bash
cd backend
uvicorn main:app --reload
```

Backend runs on `http://127.0.0.1:8000`.

### 3) Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

## API Endpoints

### Health

- `GET /health`

### Patients (`/orders`)

- `POST /orders` - create patient
- `GET /orders` - list patients
- `GET /orders/{id}` - get single patient
- `PUT /orders/{id}` - update patient
- `DELETE /orders/{id}` - delete patient

### PDF Upload

- `POST /upload`
  - Multipart field: `file` (PDF)
  - Returns extracted fields and creation status:
    - `created: true` with `id` when insertion succeeds
    - `created: false` with `reason` when required fields are missing/invalid

### Logs

- `GET /logs` - recent system logs

## Environment Variables

Backend:

- `DATABASE_URL` (optional)
  - default fallback: `sqlite:///./orders.db`
- `CORS_ORIGINS` (optional, comma-separated)
  - default includes local frontend + deployed frontend placeholder
- `OCR_DPI` (optional)
  - default: `150`
- `MAX_OCR_PAGES` (optional)
  - default: `4`

Frontend:

- `VITE_API_BASE_URL`
  - default fallback in code: `http://127.0.0.1:8000`

## Basic Security Notes

- CORS restricted to configured allowed origins (via `CORS_ORIGINS`)
- No auth included (assessment scope)
- No stack traces intentionally returned in API responses
- Upload endpoint enforces PDF content type and empty-file checks

## Deployment (Render + Docker)

This repo includes:

- `Dockerfile` for backend (includes Tesseract install)
- `render.yaml` for service scaffolding
- `RENDER_DEPLOY.md` with deployment steps

Recommended flow:

1. Deploy backend web service (Docker)
2. Deploy frontend static site
3. Set frontend `VITE_API_BASE_URL` to backend URL
4. (Optional hardening) move from SQLite fallback to Render Postgres via `DATABASE_URL`
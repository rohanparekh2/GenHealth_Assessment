# Render Deployment Guide (Fast Path)

This repo is configured for a speed-first Render deploy with Docker + Tesseract.

## Phase 1: Go Live Quickly (SQLite fallback)

1. Push this repo to GitHub.
2. In Render, create services using `render.yaml` (Blueprint) or create them manually:
   - `genhealth-backend` as Docker web service.
   - `genhealth-frontend` as static site from `frontend`.
3. Set frontend env var:
   - `VITE_API_BASE_URL=https://<your-backend>.onrender.com`
4. Deploy both services.
5. Verify:
   - Backend health: `https://<your-backend>.onrender.com/health`
   - Frontend loads and can call backend.

Notes:
- Backend defaults to SQLite if `DATABASE_URL` is not set.
- OCR works because Docker installs `tesseract-ocr`.

## Phase 2: Harden with Postgres (recommended)

1. Create a Render PostgreSQL instance.
2. Copy the Internal/External connection string.
3. Set backend env var:
   - `DATABASE_URL=<render postgres url>`
4. Redeploy backend.

`backend/db.py` already supports:
- `DATABASE_URL` from environment
- fallback to SQLite when missing
- `postgres://` URL normalization

## CORS note for this assessment

Backend currently uses wildcard CORS (`allow_origins=["*"]`) to avoid deploy URL mismatch issues during time-constrained testing.

For production hardening, replace with your real frontend domain list.

## Smoke Test Checklist

1. `GET /health` returns 200.
2. `POST /orders` creates patient.
3. `GET /orders` lists records.
4. `PUT /orders/{id}` updates record.
5. `DELETE /orders/{id}` removes record.
6. `POST /upload` extracts and inserts patient from PDF.
7. `GET /logs` returns action logs.

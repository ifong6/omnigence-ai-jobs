# Omnigence.ai Job Post + Minimal Backend (FastAPI)

This bundle includes:
- `index.html` + `logo.svg` (static job posting + application form)
- `api/app.py` + `api/index.py` (FastAPI backend to receive applications and email them to you)
- `requirements.txt` and `vercel.json`

## 1) Configure email sending (required)
The backend sends you an email with the applicant data + resume attachment.

Set these environment variables:

- `TO_EMAIL` (default: omnigence.ai@gmail.com)
- `SMTP_HOST` (e.g., smtp.gmail.com)
- `SMTP_PORT` (default: 587)
- `SMTP_USERNAME` (your SMTP login email)
- `SMTP_PASSWORD` (for Gmail: use an *App Password*)
- `SMTP_FROM` (optional; defaults to SMTP_USERNAME)

Optional:
- `MAX_RESUME_BYTES` (default 5MB)

## 2) Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn api.app:app --reload --port 8000
```

Open: http://localhost:8000 (serves `index.html` via your static hosting if you serve it separately)
API health: http://localhost:8000/api/health

> If you host the HTML separately (e.g., Vercel static), ensure it submits to the same domain `/api/apply`.

## 3) Deploy on Vercel
- Push these files to a repo
- Import into Vercel
- Add the environment variables in Vercel Project Settings

Routes are configured so:
- `/api/*` -> FastAPI
- everything else -> `index.html`

## Notes
- The form includes a hidden honeypot field (`website`) to deter bots.
- File types allowed: PDF/DOC/DOCX

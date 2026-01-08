from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

APP_NAME = "Omnigence.ai Application Backend"

# Email routing
TO_EMAIL = os.getenv("TO_EMAIL", "omnigence.ai@gmail.com")

# SMTP (set these in your hosting environment)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # use an app password for Gmail
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME or TO_EMAIL)

# Limits
MAX_RESUME_BYTES = int(os.getenv("MAX_RESUME_BYTES", str(5 * 1024 * 1024)))  # 5MB default

app = FastAPI(title=APP_NAME)

# If you host frontend+backend on same domain, CORS not needed.
# This is helpful for local dev if you serve frontend elsewhere.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _send_email_with_attachment(
    *,
    subject: str,
    body: str,
    attachment_filename: str,
    attachment_bytes: bytes,
    attachment_content_type: str = "application/octet-stream",
) -> None:
    # If SMTP isn't configured, fail with a clear message.
    if not (SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD):
        raise RuntimeError(
            "Email not configured. Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD (and optionally SMTP_PORT/SMTP_FROM/TO_EMAIL)."
        )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = TO_EMAIL
    msg.set_content(body)

    maintype, subtype = ("application", "octet-stream")
    try:
        if "/" in attachment_content_type:
            maintype, subtype = attachment_content_type.split("/", 1)
    except Exception:
        pass

    msg.add_attachment(
        attachment_bytes,
        maintype=maintype,
        subtype=subtype,
        filename=attachment_filename,
    )

    # SMTP STARTTLS
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


@app.get("/api/health")
def health():
    return {"ok": True, "service": APP_NAME}


@app.post("/api/apply")
async def apply(
    # Honeypot
    website: str = Form(default=""),
    # Applicant fields
    name: str = Form(...),
    email: str = Form(...),
    hours_per_week: str = Form(...),
    linkedin: Optional[str] = Form(default=None),
    github: Optional[str] = Form(default=None),
    portfolio: Optional[str] = Form(default=None),
    note: Optional[str] = Form(default=None),
    # Resume
    resume: UploadFile = File(...),
):
    # Basic spam check
    if website.strip():
        # silently accept to avoid giving signal to bots
        return JSONResponse({"ok": True, "message": "Submitted."})

    # Validate resume size
    content = await resume.read()
    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail=f"Resume too large. Max {MAX_RESUME_BYTES // (1024*1024)}MB.")

    filename = resume.filename or "resume"
    ctype = resume.content_type or "application/octet-stream"

    # Basic allowlist
    allowed = {".pdf", ".doc", ".docx"}
    lower = filename.lower()
    if not any(lower.endswith(ext) for ext in allowed):
        raise HTTPException(status_code=400, detail="Unsupported resume format. Please upload PDF/DOC/DOCX.")

    subject = f"[Omnigence.ai] Internship application — {name}"
    lines = [
        "New application received:",
        "",
        f"Name: {name}",
        f"Email: {email}",
        f"Hours/week: {hours_per_week}",
        f"LinkedIn: {linkedin or ''}",
        f"GitHub: {github or ''}",
        f"Portfolio: {portfolio or ''}",
        "",
        "Note:",
        note or "",
        "",
        f"Attachment: {filename} ({ctype}, {len(content)} bytes)",
    ]
    body = "\n".join(lines)

    try:
        _send_email_with_attachment(
            subject=subject,
            body=body,
            attachment_filename=filename,
            attachment_bytes=content,
            attachment_content_type=ctype,
        )
    except RuntimeError as e:
        # Configuration issue
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return {"ok": True, "message": "Application submitted."}

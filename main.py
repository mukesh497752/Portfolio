import logging
import os
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field

logger = logging.getLogger("portfolio")


def allowed_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000")
    origins = [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]
    if "*" in origins:
        raise RuntimeError("CORS_ORIGINS must list explicit origins; wildcard CORS is not allowed.")
    for origin in origins:
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError(f"Invalid origin in CORS_ORIGINS: {origin!r}")
    return origins


app = FastAPI(title="Portfolio Contact API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class ContactMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    message: str = Field(min_length=10, max_length=5000)
    website: str = Field(default="", max_length=200)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/contact", status_code=202)
async def send_contact_message(contact: ContactMessage, request: Request) -> dict[str, str]:
    # The hidden form field is a low-friction spam trap; discard bot submissions without forwarding them.
    if contact.website:
        return {"message": "Message received"}

    api_key = os.getenv("RESEND_API_KEY")
    sender = os.getenv("RESEND_FROM_EMAIL")
    recipient = os.getenv("CONTACT_TO_EMAIL")
    if not api_key or not sender or not recipient:
        logger.error("Contact email is not configured; required Resend settings are missing.")
        raise HTTPException(status_code=503, detail="The contact form is temporarily unavailable.")

    payload = {
        "from": sender,
        "to": [recipient],
        "subject": "New portfolio contact form message",
        "reply_to": str(contact.email),
        "text": f"From: {contact.name}\nEmail: {contact.email}\n\n{contact.message}",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error("Resend rejected a contact message with status %s.", exc.response.status_code)
        raise HTTPException(status_code=502, detail="The message could not be delivered. Please try again later.") from exc
    except httpx.RequestError as exc:
        logger.error("Unable to reach Resend while sending a contact message: %s", exc)
        raise HTTPException(status_code=502, detail="The message could not be delivered. Please try again later.") from exc

    logger.info("Contact message accepted from %s.", request.client.host if request.client else "unknown client")
    return {"message": "Message sent"}

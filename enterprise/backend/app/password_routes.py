from __future__ import annotations

import hashlib
import json
import os
import smtplib
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .main import JWT_ALGORITHM, JWT_SECRET, normalized_email, password_hash
from .models import UserModel

router = APIRouter(prefix="/api/auth", tags=["Password recovery"])

RESET_TOKEN_MINUTES = int(os.getenv("RESET_TOKEN_MINUTES", "30"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8170").rstrip("/")
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME or "no-reply@ucan.local").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes"}
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM = os.getenv("RESEND_FROM", SMTP_FROM).strip()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    email_delivery_configured: bool
    delivery_provider: str


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=4000)
    new_password: str = Field(min_length=10, max_length=128)


class PasswordRecoveryStatus(BaseModel):
    configured: bool
    provider: str
    frontend_url: str
    token_minutes: int


def _password_fingerprint(user: UserModel) -> str:
    return hashlib.sha256(user.password_hash.encode("utf-8")).hexdigest()[:24]


def _create_reset_token(user: UserModel) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user.id,
            "purpose": "password-reset",
            "pwd": _password_fingerprint(user),
            "iat": now,
            "exp": now + timedelta(minutes=RESET_TOKEN_MINUTES),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def _provider() -> str:
    if RESEND_API_KEY and RESEND_FROM:
        return "resend"
    if SMTP_HOST and SMTP_FROM:
        return "smtp"
    return "not-configured"


def _send_with_resend(recipient: str, reset_url: str) -> bool:
    if not RESEND_API_KEY or not RESEND_FROM:
        return False
    payload = {
        "from": RESEND_FROM,
        "to": [recipient],
        "subject": "Restablecer contraseña — UCAN Reality Lab",
        "html": (
            "<h2>Restablecer contraseña</h2>"
            "<p>Recibimos una solicitud para restablecer su contraseña de UCAN Reality Lab.</p>"
            f'<p><a href="{reset_url}">Crear una contraseña nueva</a></p>'
            f"<p>El enlace expira en {RESET_TOKEN_MINUTES} minutos.</p>"
            "<p>Si usted no solicitó este cambio, ignore este mensaje.</p>"
        ),
    }
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return False


def _send_with_smtp(recipient: str, reset_url: str) -> bool:
    if not SMTP_HOST or not SMTP_FROM:
        return False
    message = EmailMessage()
    message["Subject"] = "Restablecer contraseña — UCAN Reality Lab"
    message["From"] = SMTP_FROM
    message["To"] = recipient
    message.set_content(
        "Recibimos una solicitud para restablecer su contraseña de UCAN Reality Lab.\n\n"
        f"Abra este enlace dentro de los próximos {RESET_TOKEN_MINUTES} minutos:\n{reset_url}\n\n"
        "Si usted no solicitó este cambio, ignore este mensaje."
    )
    try:
        context = ssl.create_default_context()
        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=25, context=context) as server:
                if SMTP_USERNAME:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(message)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=25) as server:
                server.ehlo()
                if SMTP_USE_TLS:
                    server.starttls(context=context)
                    server.ehlo()
                if SMTP_USERNAME:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException):
        return False


def _send_reset_email(recipient: str, reset_url: str) -> bool:
    if _provider() == "resend":
        return _send_with_resend(recipient, reset_url)
    if _provider() == "smtp":
        return _send_with_smtp(recipient, reset_url)
    return False


@router.get("/password-recovery-status", response_model=PasswordRecoveryStatus)
def password_recovery_status() -> PasswordRecoveryStatus:
    provider = _provider()
    return PasswordRecoveryStatus(
        configured=provider != "not-configured",
        provider=provider,
        frontend_url=FRONTEND_URL,
        token_minutes=RESET_TOKEN_MINUTES,
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> ForgotPasswordResponse:
    # Respuesta uniforme: nunca confirma si una cuenta existe.
    user = db.scalar(select(UserModel).where(UserModel.email == normalized_email(str(payload.email))))
    if user and user.is_active:
        token = _create_reset_token(user)
        reset_url = f"{FRONTEND_URL}/reset-password.html?token={token}"
        _send_reset_email(user.email, reset_url)
    provider = _provider()
    return ForgotPasswordResponse(
        message=(
            "Si el correo está registrado, recibirá un enlace para crear una contraseña nueva. "
            "Revise también la carpeta de correo no deseado."
        ),
        email_delivery_configured=provider != "not-configured",
        delivery_provider=provider,
    )


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    error = HTTPException(status_code=400, detail="El enlace es inválido, expiró o ya fue utilizado")
    try:
        claims = jwt.decode(payload.token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if claims.get("purpose") != "password-reset" or not claims.get("sub"):
            raise error
    except jwt.PyJWTError as exc:
        raise error from exc
    user = db.get(UserModel, claims["sub"])
    if not user or not user.is_active or claims.get("pwd") != _password_fingerprint(user):
        raise error
    user.password_hash = password_hash.hash(payload.new_password)
    db.commit()
    return {"message": "Contraseña actualizada correctamente. Regrese al inicio e inicie sesión con la contraseña nueva."}

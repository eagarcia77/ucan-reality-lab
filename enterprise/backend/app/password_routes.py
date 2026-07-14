from __future__ import annotations

import hashlib
import os
import smtplib
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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    email_delivery_configured: bool


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=4000)
    new_password: str = Field(min_length=10, max_length=128)


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


def _send_reset_email(recipient: str, reset_url: str) -> bool:
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
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException):
        return False


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> ForgotPasswordResponse:
    # Respuesta uniforme para evitar revelar si una cuenta existe.
    user = db.scalar(select(UserModel).where(UserModel.email == normalized_email(str(payload.email))))
    delivered = False
    if user and user.is_active:
        token = _create_reset_token(user)
        reset_url = f"{FRONTEND_URL}/reset-password.html?token={token}"
        delivered = _send_reset_email(user.email, reset_url)
    return ForgotPasswordResponse(
        message="Si el correo está registrado, recibirá instrucciones para restablecer la contraseña.",
        email_delivery_configured=bool(SMTP_HOST and SMTP_FROM),
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
    return {"message": "Contraseña actualizada correctamente. Ya puede iniciar sesión."}

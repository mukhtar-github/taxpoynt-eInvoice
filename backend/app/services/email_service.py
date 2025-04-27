import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional # type: ignore

import emails # type: ignore
from emails.template import JinjaTemplate # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.core.config import settings
from app.models.user import User # type: ignore


def _generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def _create_email(
    email_to: str,
    subject_template: str,
    html_template: str,
    environment: Dict[str, Any],
) -> emails.Message:
    """Create an email message."""
    subject = JinjaTemplate(subject_template).render(**environment)
    html = JinjaTemplate(html_template).render(**environment)
    message = emails.Message(
        subject=subject,
        html=html,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    return message.address(email_to)


def send_email(
    email_to: str,
    subject_template: str,
    html_template: str,
    environment: Dict[str, Any],
) -> None:
    """Send an email."""
    message = _create_email(email_to, subject_template, html_template, environment)
    smtp_options = {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
    }
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    if settings.SMTP_TLS:
        smtp_options["tls"] = settings.SMTP_TLS

    response = message.send(smtp=smtp_options)
    logging.info(f"Email sent to {email_to}, status: {response.status_code}")


def generate_email_verification_token(db: Session, user: User) -> str:
    """Generate email verification token and store it in the database."""
    token = _generate_token()
    user.email_verification_token = token
    user.email_verification_sent_at = datetime.now()
    db.add(user)
    db.commit()
    return token


def verify_email_token(db: Session, token: str) -> Optional[User]:
    """Verify email token and update user verification status."""
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        return None
    
    # Mark email as verified
    user.is_email_verified = True
    user.email_verification_token = None
    db.add(user)
    db.commit()
    return user


def generate_password_reset_token(db: Session, user: User) -> str:
    """Generate password reset token and store it in the database."""
    token = _generate_token()
    user.password_reset_token = token
    user.password_reset_at = datetime.now()
    # Token expires in 24 hours
    user.password_reset_expires_at = datetime.now() + timedelta(hours=24)
    db.add(user)
    db.commit()
    return token


def verify_password_reset_token(db: Session, token: str) -> Optional[User]:
    """Verify password reset token."""
    user = db.query(User).filter(User.password_reset_token == token).first()
    if not user:
        return None
    
    # Check if token is expired
    if user.password_reset_expires_at < datetime.now():
        return None
    
    return user


def send_email_verification(db: Session, user: User, base_url: str) -> None:
    """Send email verification email."""
    token = generate_email_verification_token(db, user)
    verification_url = f"{base_url}/auth/verify/{token}"
    
    subject = "TaxPoynt - Verify your email address"
    html_template = """
    <p>Hi {{ user.full_name }},</p>
    <p>Please verify your email address by clicking the link below:</p>
    <p><a href="{{ verification_url }}">{{ verification_url }}</a></p>
    <p>This link will expire in 48 hours.</p>
    <p>Best regards,<br>The TaxPoynt Team</p>
    """
    
    send_email(
        email_to=user.email,
        subject_template=subject,
        html_template=html_template,
        environment={
            "user": user,
            "verification_url": verification_url,
        },
    )


def send_password_reset(db: Session, user: User, base_url: str) -> None:
    """Send password reset email."""
    token = generate_password_reset_token(db, user)
    reset_url = f"{base_url}/auth/reset-password/{token}"
    
    subject = "TaxPoynt - Reset your password"
    html_template = """
    <p>Hi {{ user.full_name }},</p>
    <p>To reset your password, please click the link below:</p>
    <p><a href="{{ reset_url }}">{{ reset_url }}</a></p>
    <p>This link will expire in 24 hours.</p>
    <p>If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
    <p>Best regards,<br>The TaxPoynt Team</p>
    """
    
    send_email(
        email_to=user.email,
        subject_template=subject,
        html_template=html_template,
        environment={
            "user": user,
            "reset_url": reset_url,
        },
    ) 
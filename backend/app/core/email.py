from __future__ import annotations

"""Outgoing email over SMTP. Dev points this at Mailpit; production needs real SMTP settings."""

import smtplib
from email.message import EmailMessage

import structlog

from app.config import get_settings

logger = structlog.get_logger()


def send_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Returns False (and logs) when SMTP is not configured."""
    settings = get_settings()
    if not settings.SMTP_HOST:
        logger.warning("smtp_not_configured", to=to, subject=subject)
        return False
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_USER:
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)
    return True

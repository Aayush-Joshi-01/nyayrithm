from __future__ import annotations

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.notification_tasks.send_webhook")
def send_webhook(url: str, payload: dict) -> None:
    import httpx
    try:
        httpx.post(url, json=payload, timeout=10)
    except Exception as exc:
        logger.warning("webhook_failed", url=url, error=str(exc))


@celery_app.task(
    name="app.tasks.notification_tasks.send_invite_email", bind=True, max_retries=3,
    default_retry_delay=30,
)
def send_invite_email(self, to: str, org_name: str, role: str, inviter: str, url: str) -> None:
    """Email a firm invitation. The link is also returned to the inviter, so a failed
    delivery never blocks onboarding."""
    from app.core.email import send_email

    body = (
        f"{inviter} has invited you to join {org_name} on Nyayrithm as {role}.\n\n"
        f"Accept the invitation (sign in or register with this email address):\n{url}\n\n"
        "The link works once and expires in 7 days. If you were not expecting this, ignore "
        "this message.\n\n"
        "Nyayrithm is a simulation tool for training and preparation. It is not legal advice."
    )
    try:
        send_email(to, f"You're invited to {org_name} on Nyayrithm", body)
    except Exception as exc:  # noqa: BLE001
        logger.warning("invite_email_failed", to=to, error=str(exc))
        raise self.retry(exc=exc) from exc

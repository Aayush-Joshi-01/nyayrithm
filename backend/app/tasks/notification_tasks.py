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

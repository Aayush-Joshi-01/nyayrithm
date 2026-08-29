from __future__ import annotations

from celery import Celery

from app.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
    app = Celery(
        "nyayrithm",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            "app.tasks.evidence_tasks",
            "app.tasks.simulation_tasks",
            "app.tasks.notification_tasks",
        ],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_routes={
            "app.tasks.evidence_tasks.*": {"queue": "evidence"},
            "app.tasks.simulation_tasks.*": {"queue": "simulation"},
            "app.tasks.notification_tasks.*": {"queue": "default"},
        },
        worker_prefetch_multiplier=1,  # fair dispatch for long-running tasks
        task_acks_late=True,
        # A crashed simulation must not be redelivered forever (poison message).
        task_reject_on_worker_lost=False,
        task_default_retry_delay=30,
    )
    return app


celery_app = create_celery_app()

from celery import Celery

from app.core.config import settings
from app.services.email import send_email

celery_app = Celery(
    "job_portal",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)


@celery_app.task(name="send_email")
def send_email_task(to_email: str, subject: str, body: str) -> None:
    send_email(to_email, subject, body)

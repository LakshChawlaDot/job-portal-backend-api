from app.core.config import settings


def send_email(to_email: str, subject: str, body: str) -> None:
    if not settings.emails_enabled:
        print(f"[email disabled] to={to_email} subject={subject} body={body}")
        return
    print(f"Send email to {to_email}: {subject}\n{body}")


def send_application_submitted(to_email: str, job_title: str) -> None:
    send_email(to_email, "Application submitted", f"Your application for {job_title} was submitted.")


def send_application_status(to_email: str, job_title: str, status: str) -> None:
    send_email(to_email, f"Application {status}", f"Your application for {job_title} was {status}.")

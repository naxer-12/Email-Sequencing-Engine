import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings
from database import SessionLocal
from kafka.producer import produce_event
from models import Enrollment, Recipient, SequenceStep
from routers.tracking import create_tracking_token
from tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_sequence_email(self, enrollment_id: int, step_id: int):
    """
    Send an email step to a recipient.

    Args:
        enrollment_id: Which enrollment to send to
        step_id: Which sequence step to send

    Raises:
        Exception: If send fails (will be retried with exponential backoff)
    """
    db = SessionLocal()
    try:
        # 1. Fetch enrollment and check status
        enrollment = db.query(Enrollment).filter_by(id=enrollment_id).first()
        if not enrollment:
            raise ValueError(f"Enrollment {enrollment_id} not found")

        if enrollment.status in ("unsubscribed", "replied"):
            # Check-before-execute pattern: don't send if unsubscribed
            return {"status": "skipped", "reason": enrollment.status}

        # 2. Fetch step and recipient
        step = db.query(SequenceStep).filter_by(id=step_id).first()
        recipient = db.query(Recipient).filter_by(id=enrollment.recipient_id).first()

        if not step or not recipient:
            raise ValueError(f"Step {step_id} or recipient not found")

        # 3. Personalize email body
        body = step.body.replace("{{first_name}}", recipient.first_name or "there")

        # 4. Inject tracking pixel (you'll implement this in Phase 4)
        body = inject_tracking_pixel(body, enrollment_id, step_id)

        body = rewrite_links(body, enrollment_id, step_id)

        # 5. Send via SMTP
        subject = step.subject
        _send_email(recipient.email, subject, body)

        # 6. Emit Kafka event (Phase 4)
        produce_event("email.sent", enrollment_id, step_id)

        return {"status": "sent", "recipient": recipient.email}

    except Exception as exc:
        # Retry with exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=2**self.request.retries * 60)

    finally:
        db.close()


def _send_email(to: str, subject: str, body: str):
    """Send email via SMTP (using Mailtrap for testing)"""
    msg = MIMEMultipart("alternative")
    msg["From"] = "Alice@example.com"
    msg["To"] = to
    msg["Subject"] = subject

    part = MIMEText(body, "html")
    msg.attach(part)

    print("Inside Send email")

    print(f"This is smtp host {settings.smtp_host}")
    print(f"This is smtp host {settings.smtp_port}")
    print(f"This is smtp host {settings.smtp_user}")
    print(f"This is smtp host {settings.smtp_password}")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.set_debuglevel(1)
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_user, [to], msg.as_string())


def inject_tracking_pixel(body: str, enrollment_id: int, step_id: int) -> str:
    """Add a 1x1 pixel that fires when the email is opened"""
    token = create_tracking_token(enrollment_id, step_id)
    pixel_html = f'<img src="http://localhost:8080/t/open/{token}" width="1" height="1" alt="" style="display:none;">'
    return body + pixel_html


def rewrite_links(body: str, enrollment_id: int, step_id: int) -> str:
    """Rewrite all links to go through our redirect endpoint"""
    import re
    from urllib.parse import urlencode

    token = create_tracking_token(enrollment_id, step_id)

    def replace_link(match):
        original_url = match.group(1)
        params = urlencode({"token": token, "url": original_url})
        return f'href="http://localhost:8000/t/click?{params}"'

    # Match <a href="...">
    pattern = r'href="([^"]+)"'
    return re.sub(pattern, replace_link, body)

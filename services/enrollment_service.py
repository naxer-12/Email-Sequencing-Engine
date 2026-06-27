from sqlalchemy.orm import Session

from models import Enrollment, SequenceStep
from tasks.email_tasks import send_sequence_email


def enroll_recipient(db: Session, sequence_id: int, recipient_id: int) -> Enrollment:
    """Enroll a recipient in a sequence and schedule all email steps"""

    # 1. Create enrollment record
    enrollment = Enrollment(
        sequence_id=sequence_id, recipient_id=recipient_id, status="active"
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    # 2. Get all steps in order
    steps = (
        db.query(SequenceStep)
        .filter_by(sequence_id=sequence_id)
        .order_by(SequenceStep.step_order)
        .all()
    )

    # 3. Schedule a task for each step
    for step in steps:
        delay_seconds = step.delay_days * 86_400
        send_sequence_email.apply_async(
            kwargs={"enrollment_id": enrollment.id, "step_id": step.id},
            countdown=delay_seconds,
        )

    return enrollment

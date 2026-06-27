from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.enrollment import Enrollment
from models.recipient import Recipient
from models.sequence import Sequence, SequenceStep

router = APIRouter(prefix="/sequences", tags=["enrollments"])


class EnrollmentCreate(BaseModel):
    recipient_id: int


@router.post("/{sequence_id}/enrollments/")
def enroll_recipient(
    sequence_id: int, enrollment: EnrollmentCreate, db: Session = Depends(get_db)
):
    # Check sequence exists
    sequence = db.query(Sequence).filter(Sequence.id == sequence_id).first()
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")

    # Check recipient exists
    recipient = (
        db.query(Recipient).filter(Recipient.id == enrollment.recipient_id).first()
    )
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Check not already enrolled
    existing = (
        db.query(Enrollment)
        .filter(
            Enrollment.sequence_id == sequence_id,
            Enrollment.recipient_id == enrollment.recipient_id,
        )
        .first()
    )
    if existing:
        return existing

    # Create enrollment
    db_enrollment = Enrollment(
        sequence_id=sequence_id, recipient_id=enrollment.recipient_id, status="active"
    )
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)

    # Schedule email tasks
    steps = (
        db.query(SequenceStep)
        .filter(SequenceStep.sequence_id == sequence_id)
        .order_by(SequenceStep.step_order)
        .all()
    )

    for step in steps:
        delay_seconds = step.delay_days * 86400
        try:
            from tasks.email_tasks import send_sequence_email

            send_sequence_email.apply_async(
                kwargs={"enrollment_id": db_enrollment.id, "step_id": step.id},
                countdown=delay_seconds,
            )
            print(f"Scheduled step {step.step_order} with delay {delay_seconds}s")
        except Exception as e:
            print(f"Failed to schedule step {step.step_order}: {e}")

    return {
        "id": db_enrollment.id,
        "sequence_id": sequence_id,
        "recipient_id": enrollment.recipient_id,
        "status": db_enrollment.status,
        "message": f"Enrolled successfully. {len(steps)} email(s) scheduled.",
    }


@router.get("/{sequence_id}/enrollments/")
def list_enrollments(sequence_id: int, db: Session = Depends(get_db)):
    enrollments = (
        db.query(Enrollment).filter(Enrollment.sequence_id == sequence_id).all()
    )
    return enrollments

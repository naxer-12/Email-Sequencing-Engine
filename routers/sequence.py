from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.sequence import Sequence, SequenceStep

router = APIRouter(prefix="/sequences", tags=["sequences"])


class SequenceCreate(BaseModel):
    user_id: int
    name: str


class StepCreate(BaseModel):
    step_order: int
    subject: str
    body: str
    delay_days: int = 0


@router.post("/")
def create_sequence(sequence: SequenceCreate, db: Session = Depends(get_db)):
    db_sequence = Sequence(user_id=sequence.user_id, name=sequence.name)
    db.add(db_sequence)
    db.commit()
    db.refresh(db_sequence)
    return db_sequence


@router.get("/{sequence_id}")
def get_sequence(sequence_id: int, db: Session = Depends(get_db)):
    sequence = db.query(Sequence).filter(Sequence.id == sequence_id).first()
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return sequence


@router.post("/{sequence_id}/steps")  # ← THIS IS WHAT WAS MISSING
def add_step(sequence_id: int, step: StepCreate, db: Session = Depends(get_db)):
    # Check sequence exists
    sequence = db.query(Sequence).filter(Sequence.id == sequence_id).first()
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")

    db_step = SequenceStep(
        sequence_id=sequence_id,
        step_order=step.step_order,
        subject=step.subject,
        body=step.body,
        delay_days=step.delay_days,
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


@router.get("/{sequence_id}/steps")
def get_steps(sequence_id: int, db: Session = Depends(get_db)):
    steps = (
        db.query(SequenceStep)
        .filter(SequenceStep.sequence_id == sequence_id)
        .order_by(SequenceStep.step_order)
        .all()
    )
    return steps

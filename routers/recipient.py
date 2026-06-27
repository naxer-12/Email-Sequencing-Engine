from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.recipient import Recipient

router = APIRouter(prefix="/recipients", tags=["recipients"])


class RecipientCreate(BaseModel):
    email: str
    first_name: str
    company: str = ""


@router.post("/")
def create_recipient(recipient: RecipientCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(Recipient).filter(Recipient.email == recipient.email).first()

    if existing:
        return existing  # return existing instead of error

    db_recipient = Recipient(
        email=recipient.email,
        first_name=recipient.first_name,
        company=recipient.company,
    )
    db.add(db_recipient)
    db.commit()
    db.refresh(db_recipient)
    return db_recipient


@router.get("/{recipient_id}")
def get_recipient(recipient_id: int, db: Session = Depends(get_db)):
    recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()

    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    return recipient


@router.get("/")
def list_recipients(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Recipient).offset(skip).limit(limit).all()

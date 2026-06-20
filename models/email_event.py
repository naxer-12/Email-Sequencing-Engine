from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base  # or from app.database import Base


class EmailEvent(Base):
    __tablename__ = "email_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("enrollments.id"), nullable=False
    )
    step_id: Mapped[int] = mapped_column(
        ForeignKey("sequence_steps.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Use string reference instead of importing Enrollment
    enrollment: Mapped["Enrollment"] = relationship(back_populates="events")

    __table_args__ = (Index("ix_enrollment_event_type", "enrollment_id", "event_type"),)

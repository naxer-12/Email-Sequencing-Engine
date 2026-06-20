from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    sequence_id: Mapped[int] = mapped_column(ForeignKey("sequences.id"), nullable=False)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("recipients.id"), nullable=False
    )
    current_step: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(50), default="active")
    enrolled_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # String references - no direct imports needed
    sequence: Mapped["Sequence"] = relationship(back_populates="enrollments")
    recipient: Mapped["Recipient"] = relationship()
    events: Mapped[list["EmailEvent"]] = relationship(back_populates="enrollment")

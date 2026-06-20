from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Recipient(Base):
    __tablename__ = "recipients"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100))
    company: Mapped[str] = mapped_column(String(255))

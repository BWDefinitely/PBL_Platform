from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    milestone: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    sent_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class DocContribution(Base):
    __tablename__ = "doc_contributions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    milestone: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PresentationRecord(Base):
    __tablename__ = "presentation_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    milestone: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    words: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    milestone: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    happened_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

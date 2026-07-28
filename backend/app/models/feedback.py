from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime, timezone
from app.database import Base


class ContentFeedback(Base):
    __tablename__ = "content_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_type = Column(String, nullable=False)
    content_id = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

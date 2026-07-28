from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    curricula = relationship("Curriculum", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    topic_masteries = relationship("TopicMastery", back_populates="user")
    learning_events = relationship("LearningEvent", back_populates="user")
    learner_profile = relationship("LearnerProfile", back_populates="user", uselist=False)

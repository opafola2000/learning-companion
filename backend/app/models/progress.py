from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Float, nullable=False)
    taken_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")
    answers = relationship("UserAnswer", back_populates="attempt", cascade="all, delete-orphan")


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_option_id = Column(Integer, ForeignKey("answer_options.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)

    attempt = relationship("QuizAttempt", back_populates="answers")


class TopicMastery(Base):
    __tablename__ = "topic_masteries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    mastery_score = Column(Float, default=0.0)
    attempts_count = Column(Integer, default=0)
    last_assessed = Column(DateTime)
    next_review_at = Column(DateTime, nullable=True)
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=1)

    user = relationship("User", back_populates="topic_masteries")
    topic = relationship("Topic", back_populates="masteries")

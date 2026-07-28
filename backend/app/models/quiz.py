from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    quiz_type = Column(String, default="practice")
    num_questions = Column(Integer, nullable=False)
    blueprint_version = Column(String, nullable=True)
    exam_code = Column(String, nullable=True)
    validation_status = Column(String, default="pending")
    is_stale = Column(String, default="false")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    topic = relationship("Topic", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    explanation = Column(Text)
    difficulty = Column(String, default="intermediate")
    objective_id = Column(String, nullable=True)
    source_reference = Column(String, nullable=True)
    citation_snippet = Column(Text, nullable=True)

    quiz = relationship("Quiz", back_populates="questions")
    options = relationship("AnswerOption", back_populates="question", cascade="all, delete-orphan")


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)

    question = relationship("Question", back_populates="options")

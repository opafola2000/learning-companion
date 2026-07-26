from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Curriculum(Base):
    __tablename__ = "curricula"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    description = Column(Text)
    overall_structure = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="curricula")
    modules = relationship("Module", back_populates="curriculum", cascade="all, delete-orphan", order_by="Module.order_index")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    curriculum_id = Column(Integer, ForeignKey("curricula.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False)
    status = Column(String, default="not_started")

    curriculum = relationship("Curriculum", back_populates="modules")
    topics = relationship("Topic", back_populates="module", cascade="all, delete-orphan", order_by="Topic.order_index")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False)
    difficulty = Column(String, default="beginner")
    status = Column(String, default="not_started")

    module = relationship("Module", back_populates="topics")
    resources = relationship("Resource", back_populates="topic", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="topic", cascade="all, delete-orphan")
    masteries = relationship("TopicMastery", back_populates="topic", cascade="all, delete-orphan")

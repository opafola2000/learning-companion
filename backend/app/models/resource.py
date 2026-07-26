from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    type = Column(String, default="article")
    summary = Column(Text)

    topic = relationship("Topic", back_populates="resources")

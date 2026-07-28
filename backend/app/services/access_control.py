from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.curriculum import Topic, Curriculum


def verify_topic_access(db: Session, topic_id: int, user_id: int) -> Topic:
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic or not topic.module or not topic.module.curriculum:
        raise HTTPException(status_code=404, detail="Topic not found")
    if topic.module.curriculum.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return topic

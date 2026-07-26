from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.curriculum import Topic
from app.models.resource import Resource
from app.routers.auth import get_current_user
from app.schemas.progress import ResourceResponse
from app.services.resource_service import search_and_save_resources

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.post("/search/{topic_id}", response_model=list[ResourceResponse])
def search_resources(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    skill_name = topic.module.curriculum.skill_name

    try:
        resources = search_and_save_resources(db, topic_id, skill_name)
        return resources
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resource search failed: {str(e)}")


@router.get("/{topic_id}", response_model=list[ResourceResponse])
def get_resources(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resources = db.query(Resource).filter(Resource.topic_id == topic_id).all()
    return resources

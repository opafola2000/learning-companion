from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.resource import Resource
from app.routers.auth import get_current_user
from app.schemas.progress import ResourceResponse
from app.services.resource_service import search_and_save_resources
from app.services.access_control import verify_topic_access
from app.limiter import limiter

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.post("/search/{topic_id}", response_model=list[ResourceResponse])
@limiter.limit("5/minute")
def search_resources(
    request: Request,
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic = verify_topic_access(db, topic_id, current_user.id)
    skill_name = topic.module.curriculum.skill_name

    try:
        resources = search_and_save_resources(
            db, topic_id, skill_name, user_id=current_user.id
        )
        return resources
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resource search failed: {str(e)}")


@router.get("/{topic_id}", response_model=list[ResourceResponse])
def get_resources(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_topic_access(db, topic_id, current_user.id)
    resources = db.query(Resource).filter(Resource.topic_id == topic_id).all()
    return resources

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.curriculum import Curriculum
from app.routers.auth import get_current_user
from app.schemas.progress import CurriculumProgressResponse, RecommendationResponse
from app.services.mastery_service import get_curriculum_progress, get_recommendations

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/recommendations", response_model=list[RecommendationResponse])
def recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_recommendations(db, current_user.id)


@router.get("/{curriculum_id}", response_model=CurriculumProgressResponse)
def curriculum_progress(
    curriculum_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    curriculum = db.query(Curriculum).filter(
        Curriculum.id == curriculum_id,
        Curriculum.user_id == current_user.id,
    ).first()
    if not curriculum:
        raise HTTPException(status_code=404, detail="Curriculum not found")

    try:
        return get_curriculum_progress(db, current_user.id, curriculum_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

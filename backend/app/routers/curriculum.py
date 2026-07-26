from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.curriculum import Curriculum
from app.models.progress import TopicMastery
from app.routers.auth import get_current_user
from app.schemas.curriculum import (
    GenerateCurriculumRequest,
    CurriculumResponse,
    CurriculumListItem,
    ModuleResponse,
    TopicResponse,
)
from app.services.curriculum_service import generate_curriculum

router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])


@router.get("", response_model=list[CurriculumListItem])
def list_curricula(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    curricula = db.query(Curriculum).filter(
        Curriculum.user_id == current_user.id
    ).order_by(Curriculum.created_at.desc()).all()

    result = []
    for c in curricula:
        topic_count = sum(len(m.topics) for m in c.modules)
        masteries = db.query(TopicMastery).filter(
            TopicMastery.user_id == current_user.id,
        ).all()
        topic_ids = {t.id for m in c.modules for t in m.topics}
        relevant = [m for m in masteries if m.topic_id in topic_ids]
        overall = (
            sum(m.mastery_score for m in relevant) / len(relevant)
            if relevant else 0.0
        )

        result.append(CurriculumListItem(
            id=c.id,
            skill_name=c.skill_name,
            description=c.description,
            created_at=c.created_at,
            module_count=len(c.modules),
            topic_count=topic_count,
            overall_mastery=overall,
        ))
    return result


@router.post("/generate", response_model=CurriculumResponse)
def create_curriculum(
    data: GenerateCurriculumRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        curriculum = generate_curriculum(db, current_user.id, data.skill_name)
        return _build_curriculum_response(db, curriculum, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate curriculum: {str(e)}")


@router.get("/{curriculum_id}", response_model=CurriculumResponse)
def get_curriculum(
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

    return _build_curriculum_response(db, curriculum, current_user.id)


def _build_curriculum_response(
    db: Session, curriculum: Curriculum, user_id: int
) -> CurriculumResponse:
    modules = []
    for module in curriculum.modules:
        topics = []
        for topic in module.topics:
            mastery = db.query(TopicMastery).filter(
                TopicMastery.user_id == user_id,
                TopicMastery.topic_id == topic.id,
            ).first()
            topics.append(TopicResponse(
                id=topic.id,
                title=topic.title,
                description=topic.description,
                order_index=topic.order_index,
                difficulty=topic.difficulty,
                status=topic.status,
                mastery_score=mastery.mastery_score if mastery else None,
            ))
        modules.append(ModuleResponse(
            id=module.id,
            title=module.title,
            description=module.description,
            order_index=module.order_index,
            status=module.status,
            topics=topics,
        ))

    return CurriculumResponse(
        id=curriculum.id,
        skill_name=curriculum.skill_name,
        description=curriculum.description,
        created_at=curriculum.created_at,
        modules=modules,
    )

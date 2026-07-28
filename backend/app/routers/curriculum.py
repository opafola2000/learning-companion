from fastapi import APIRouter, Depends, HTTPException, Request
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
    SourceCitation,
)
from app.services.curriculum_service import generate_curriculum
from app.services.audit_service import log_action
from app.limiter import limiter

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
            exam_code=c.exam_code,
            blueprint_version=c.blueprint_version,
            validation_status=c.validation_status,
            module_count=len(c.modules),
            topic_count=topic_count,
            overall_mastery=overall,
        ))
    return result


@router.post("/generate", response_model=CurriculumResponse)
@limiter.limit("3/minute")
def create_curriculum(
    request: Request,
    data: GenerateCurriculumRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        curriculum = generate_curriculum(db, current_user.id, data.skill_name)
        log_action(
            db,
            "curriculum_generated",
            user_id=current_user.id,
            resource_type="curriculum",
            resource_id=curriculum.id,
            ip_address=request.client.host if request.client else None,
            details={"skill_name": data.skill_name},
        )
        db.commit()
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
                objective_ids=topic.objective_ids or [],
                source_urls=topic.source_urls or [],
                validation_status=topic.validation_status,
            ))
        modules.append(ModuleResponse(
            id=module.id,
            title=module.title,
            description=module.description,
            order_index=module.order_index,
            status=module.status,
            topics=topics,
        ))

    sources = [
        SourceCitation(**s) if isinstance(s, dict) else s
        for s in (curriculum.sources or [])
    ]

    return CurriculumResponse(
        id=curriculum.id,
        skill_name=curriculum.skill_name,
        description=curriculum.description,
        created_at=curriculum.created_at,
        exam_code=curriculum.exam_code,
        blueprint_version=curriculum.blueprint_version,
        validation_status=curriculum.validation_status,
        sources=sources,
        modules=modules,
    )

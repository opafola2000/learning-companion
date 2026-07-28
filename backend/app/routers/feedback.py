from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.feedback import ContentFeedback
from app.routers.auth import get_current_user
from app.schemas.progress import ContentFeedbackCreate, ContentFeedbackResponse
from app.services.audit_service import log_action
from app.limiter import limiter

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=ContentFeedbackResponse)
@limiter.limit("10/minute")
def submit_feedback(
    request: Request,
    data: ContentFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feedback = ContentFeedback(
        user_id=current_user.id,
        content_type=data.content_type,
        content_id=data.content_id,
        reason=data.reason,
        comment=data.comment,
    )
    db.add(feedback)
    log_action(
        db,
        "content_feedback",
        user_id=current_user.id,
        resource_type=data.content_type,
        resource_id=data.content_id,
        ip_address=request.client.host if request.client else None,
        details={"reason": data.reason},
    )
    db.commit()
    db.refresh(feedback)
    return feedback

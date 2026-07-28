from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.quiz import Quiz
from app.models.progress import TopicMastery
from app.routers.auth import get_current_user
from app.schemas.quiz import (
    GenerateQuizRequest, QuizResponse, QuizSubmission, QuizResultResponse,
    QuestionResponse, AnswerOptionResponse,
)
from app.services.quiz_service import generate_quiz, submit_quiz
from app.services.access_control import verify_topic_access
from app.services.audit_service import log_action
from app.limiter import limiter

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/generate/{topic_id}", response_model=QuizResponse)
@limiter.limit("5/minute")
def create_quiz(
    request: Request,
    topic_id: int,
    data: GenerateQuizRequest = GenerateQuizRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_topic_access(db, topic_id, current_user.id)

    mastery = db.query(TopicMastery).filter(
        TopicMastery.user_id == current_user.id,
        TopicMastery.topic_id == topic_id,
    ).first()
    mastery_level = mastery.mastery_score / 100 if mastery else 0.0

    try:
        quiz = generate_quiz(
            db, topic_id, data.num_questions, data.quiz_type, mastery_level,
            user_id=current_user.id,
        )
        log_action(
            db,
            "quiz_generated",
            user_id=current_user.id,
            resource_type="quiz",
            resource_id=quiz.id,
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        return _build_quiz_response(quiz)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    verify_topic_access(db, quiz.topic_id, current_user.id)
    return _build_quiz_response(quiz)


@router.post("/{quiz_id}/submit", response_model=QuizResultResponse)
def submit_quiz_answers(
    quiz_id: int,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    verify_topic_access(db, quiz.topic_id, current_user.id)

    try:
        answers = [
            {"question_id": a.question_id, "selected_option_id": a.selected_option_id}
            for a in submission.answers
        ]
        result = submit_quiz(db, current_user.id, quiz_id, answers)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz submission failed: {str(e)}")


def _build_quiz_response(quiz: Quiz) -> QuizResponse:
    questions = []
    for q in quiz.questions:
        options = [
            AnswerOptionResponse(id=o.id, option_text=o.option_text)
            for o in q.options
        ]
        questions.append(QuestionResponse(
            id=q.id,
            question_text=q.question_text,
            difficulty=q.difficulty,
            objective_id=q.objective_id,
            options=options,
        ))
    return QuizResponse(
        id=quiz.id,
        topic_id=quiz.topic_id,
        quiz_type=quiz.quiz_type,
        num_questions=quiz.num_questions,
        created_at=quiz.created_at,
        exam_code=quiz.exam_code,
        blueprint_version=quiz.blueprint_version,
        validation_status=quiz.validation_status,
        questions=questions,
    )

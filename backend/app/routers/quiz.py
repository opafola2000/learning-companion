from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/generate/{topic_id}", response_model=QuizResponse)
def create_quiz(
    topic_id: int,
    data: GenerateQuizRequest = GenerateQuizRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mastery = db.query(TopicMastery).filter(
        TopicMastery.user_id == current_user.id,
        TopicMastery.topic_id == topic_id,
    ).first()
    mastery_level = mastery.mastery_score / 100 if mastery else 0.0

    try:
        quiz = generate_quiz(
            db, topic_id, data.num_questions, data.quiz_type, mastery_level
        )
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
    return _build_quiz_response(quiz)


@router.post("/{quiz_id}/submit", response_model=QuizResultResponse)
def submit_quiz_answers(
    quiz_id: int,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
            options=options,
        ))
    return QuizResponse(
        id=quiz.id,
        topic_id=quiz.topic_id,
        quiz_type=quiz.quiz_type,
        num_questions=quiz.num_questions,
        created_at=quiz.created_at,
        questions=questions,
    )

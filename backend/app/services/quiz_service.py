from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.quiz import Quiz, Question, AnswerOption
from app.models.progress import QuizAttempt, UserAnswer, TopicMastery
from app.models.curriculum import Topic
from app.services.bedrock_client import get_bedrock_client
from app.services.grounding_service import fetch_topic_context, get_profile_for_skill
from app.services.validation_service import validate_quiz_questions
from app.services.memory_service import (
    apply_spaced_repetition,
    record_event,
    update_profile_after_quiz,
)

QUIZ_SYSTEM_PROMPT = """You are an expert exam question writer for professional certification exams.
Generate practice questions grounded ONLY in the provided official source material.

Return a JSON object:
{
  "questions": [
    {
      "question_text": "Full question text with scenario if applicable",
      "difficulty": "beginner|intermediate|advanced",
      "objective_id": "OBJ-1 matching an exam objective",
      "source_reference": "URL or source title used",
      "citation_snippet": "Short quote supporting the correct answer",
      "explanation": "Why the correct answer is correct, citing the source",
      "options": [
        {"text": "Option A", "is_correct": false},
        {"text": "Option B", "is_correct": true},
        {"text": "Option C", "is_correct": false},
        {"text": "Option D", "is_correct": false}
      ]
    }
  ]
}

Guidelines:
- Each question must have exactly 4 options with exactly 1 correct answer
- Use ONLY facts from the provided source material — no invented services or deprecated features
- Match the exam question style described in the exam profile
- Include objective_id and source_reference for every question
- Mix factual recall, conceptual, and scenario-based questions"""


def generate_quiz(
    db: Session,
    topic_id: int,
    num_questions: int = 5,
    quiz_type: str = "practice",
    mastery_level: float = 0.0,
    user_id: int | None = None,
) -> Quiz:
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise ValueError(f"Topic {topic_id} not found")

    bedrock = get_bedrock_client()
    module = topic.module
    skill_name = module.curriculum.skill_name if module and module.curriculum else "the certification"
    profile = get_profile_for_skill(skill_name)
    source_context = fetch_topic_context(topic.title, skill_name, profile)

    difficulty_hint = "beginner to intermediate"
    if mastery_level > 0.6:
        difficulty_hint = "intermediate to advanced"
    elif mastery_level > 0.3:
        difficulty_hint = "intermediate"

    user_message = f"""Generate {num_questions} practice questions for:

Certification: {skill_name}
Exam code: {profile.exam_code}
Blueprint version: {profile.blueprint_version}
Question style: {profile.question_style}
Topic: {topic.title}
Description: {topic.description}
Objective IDs for this topic: {topic.objective_ids or []}
Target difficulty: {difficulty_hint}
Current mastery: {mastery_level:.0%}

Official source material (use ONLY these facts):
{source_context}

Generate exam-realistic questions grounded in this material."""

    result = bedrock.invoke_sonnet_json(QUIZ_SYSTEM_PROMPT, user_message)
    raw_questions = result.get("questions", [])[:num_questions]

    validation = validate_quiz_questions(
        skill_name, profile.exam_code, topic.title, raw_questions, source_context
    )
    validated_map = {
        v.get("question_text", ""): v
        for v in validation.get("questions", [])
    }

    valid_questions = []
    for q in raw_questions:
        v = validated_map.get(q.get("question_text", ""), {})
        if v.get("is_valid", True):
            q["objective_id"] = v.get("objective_id") or q.get("objective_id")
            q["source_reference"] = v.get("source_reference") or q.get("source_reference")
            q["citation_snippet"] = v.get("citation_snippet") or q.get("citation_snippet")
            valid_questions.append(q)

    if not valid_questions:
        valid_questions = raw_questions

    quiz = Quiz(
        topic_id=topic_id,
        quiz_type=quiz_type,
        num_questions=len(valid_questions),
        blueprint_version=profile.blueprint_version,
        exam_code=profile.exam_code,
        validation_status=validation.get("validation_status", "needs_review"),
        is_stale="false",
    )
    db.add(quiz)
    db.flush()

    for q_data in valid_questions:
        question = Question(
            quiz_id=quiz.id,
            question_text=q_data["question_text"],
            explanation=q_data.get("explanation", ""),
            difficulty=q_data.get("difficulty", "intermediate"),
            objective_id=q_data.get("objective_id"),
            source_reference=q_data.get("source_reference"),
            citation_snippet=q_data.get("citation_snippet"),
        )
        db.add(question)
        db.flush()

        for opt_data in q_data.get("options", []):
            db.add(AnswerOption(
                question_id=question.id,
                option_text=opt_data["text"],
                is_correct=opt_data.get("is_correct", False),
            ))

    if user_id:
        record_event(db, user_id, "quiz_generated", topic_id=topic_id, details={
            "quiz_id": quiz.id,
            "exam_code": profile.exam_code,
            "blueprint_version": profile.blueprint_version,
        })

    db.commit()
    db.refresh(quiz)
    return quiz


def submit_quiz(
    db: Session, user_id: int, quiz_id: int, answers: list[dict]
) -> dict:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise ValueError(f"Quiz {quiz_id} not found")

    correct_count = 0
    total = len(answers)
    user_answers = []
    wrong_objectives = []

    for ans in answers:
        question = db.query(Question).filter(Question.id == ans["question_id"]).first()
        if not question:
            continue

        selected_option = db.query(AnswerOption).filter(
            AnswerOption.id == ans["selected_option_id"]
        ).first()
        is_correct = selected_option.is_correct if selected_option else False
        if is_correct:
            correct_count += 1
        elif question.objective_id:
            wrong_objectives.append(question.objective_id)

        user_answers.append({
            "question_id": ans["question_id"],
            "selected_option_id": ans["selected_option_id"],
            "is_correct": is_correct,
        })

    score = (correct_count / total * 100) if total > 0 else 0

    attempt = QuizAttempt(
        user_id=user_id,
        quiz_id=quiz_id,
        score=score,
    )
    db.add(attempt)
    db.flush()

    for ua in user_answers:
        db.add(UserAnswer(
            attempt_id=attempt.id,
            question_id=ua["question_id"],
            selected_option_id=ua["selected_option_id"],
            is_correct=ua["is_correct"],
        ))

    mastery_score = _update_mastery(db, user_id, quiz.topic_id, score)
    update_profile_after_quiz(db, user_id, quiz.topic_id, score, wrong_objectives)
    record_event(db, user_id, "quiz_completed", topic_id=quiz.topic_id, details={
        "quiz_id": quiz_id,
        "score": score,
        "wrong_objectives": wrong_objectives,
    })

    db.commit()
    db.refresh(attempt)

    questions_detail = []
    for q in quiz.questions:
        ua_match = next((a for a in user_answers if a["question_id"] == q.id), None)
        questions_detail.append({
            "id": q.id,
            "question_text": q.question_text,
            "difficulty": q.difficulty,
            "explanation": q.explanation,
            "objective_id": q.objective_id,
            "source_reference": q.source_reference,
            "citation_snippet": q.citation_snippet,
            "options": [
                {"id": o.id, "option_text": o.option_text, "is_correct": o.is_correct}
                for o in q.options
            ],
            "user_selected_option_id": ua_match["selected_option_id"] if ua_match else None,
            "is_correct": ua_match["is_correct"] if ua_match else None,
        })

    return {
        "attempt_id": attempt.id,
        "score": score,
        "total_questions": total,
        "correct_count": correct_count,
        "questions": questions_detail,
        "mastery_update": mastery_score,
        "exam_code": quiz.exam_code,
        "blueprint_version": quiz.blueprint_version,
    }


def _update_mastery(db: Session, user_id: int, topic_id: int, new_score: float) -> float:
    mastery = db.query(TopicMastery).filter(
        TopicMastery.user_id == user_id,
        TopicMastery.topic_id == topic_id,
    ).first()

    if mastery is None:
        mastery = TopicMastery(
            user_id=user_id,
            topic_id=topic_id,
            mastery_score=new_score,
            attempts_count=1,
            last_assessed=datetime.now(timezone.utc),
            ease_factor=2.5,
            interval_days=1,
        )
        db.add(mastery)
        apply_spaced_repetition(mastery, new_score)
        return new_score

    weight_new = 0.6
    weight_old = 0.4
    mastery.mastery_score = (weight_new * new_score) + (weight_old * mastery.mastery_score)
    mastery.attempts_count += 1
    mastery.last_assessed = datetime.now(timezone.utc)
    apply_spaced_repetition(mastery, new_score)

    return mastery.mastery_score

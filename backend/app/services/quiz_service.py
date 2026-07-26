from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.quiz import Quiz, Question, AnswerOption
from app.models.progress import QuizAttempt, UserAnswer, TopicMastery
from app.models.curriculum import Topic
from app.services.bedrock_client import get_bedrock_client

QUIZ_SYSTEM_PROMPT = """You are an expert exam question writer for professional certification exams.
Generate practice questions that match real exam format and difficulty.

Return a JSON object:
{
  "questions": [
    {
      "question_text": "The full question text. For scenario-based questions, include the scenario.",
      "difficulty": "beginner|intermediate|advanced",
      "explanation": "Detailed explanation of why the correct answer is correct and why others are wrong.",
      "options": [
        {"text": "Option A text", "is_correct": false},
        {"text": "Option B text", "is_correct": true},
        {"text": "Option C text", "is_correct": false},
        {"text": "Option D text", "is_correct": false}
      ]
    }
  ]
}

Guidelines:
- Each question must have exactly 4 options with exactly 1 correct answer
- Mix question types: factual recall, conceptual understanding, scenario-based application
- Explanations should teach, not just state the answer
- Adjust difficulty based on the requested level
- Questions should be realistic and match actual certification exam style"""


def generate_quiz(
    db: Session,
    topic_id: int,
    num_questions: int = 5,
    quiz_type: str = "practice",
    mastery_level: float = 0.0,
) -> Quiz:
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise ValueError(f"Topic {topic_id} not found")

    bedrock = get_bedrock_client()

    difficulty_hint = "beginner to intermediate"
    if mastery_level > 0.6:
        difficulty_hint = "intermediate to advanced"
    elif mastery_level > 0.3:
        difficulty_hint = "intermediate"

    module = topic.module
    skill_name = module.curriculum.skill_name if module and module.curriculum else "the certification"

    user_message = f"""Generate {num_questions} practice questions for:

Topic: {topic.title}
Description: {topic.description}
Certification: {skill_name}
Target difficulty: {difficulty_hint}
Current mastery: {mastery_level:.0%}

Generate questions that will help assess and build knowledge on this topic."""

    result = bedrock.invoke_sonnet_json(QUIZ_SYSTEM_PROMPT, user_message)

    quiz = Quiz(
        topic_id=topic_id,
        quiz_type=quiz_type,
        num_questions=num_questions,
    )
    db.add(quiz)
    db.flush()

    for q_data in result.get("questions", [])[:num_questions]:
        question = Question(
            quiz_id=quiz.id,
            question_text=q_data["question_text"],
            explanation=q_data.get("explanation", ""),
            difficulty=q_data.get("difficulty", "intermediate"),
        )
        db.add(question)
        db.flush()

        for opt_data in q_data.get("options", []):
            option = AnswerOption(
                question_id=question.id,
                option_text=opt_data["text"],
                is_correct=opt_data.get("is_correct", False),
            )
            db.add(option)

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
        )
        db.add(mastery)
        return new_score

    # Weighted average with recency bias: new scores count more
    weight_new = 0.6
    weight_old = 0.4
    mastery.mastery_score = (weight_new * new_score) + (weight_old * mastery.mastery_score)
    mastery.attempts_count += 1
    mastery.last_assessed = datetime.now(timezone.utc)

    return mastery.mastery_score

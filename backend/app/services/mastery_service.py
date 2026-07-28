from sqlalchemy.orm import Session

from app.models.progress import TopicMastery
from app.models.curriculum import Curriculum
from app.services.memory_service import is_due_for_review


def get_curriculum_progress(db: Session, user_id: int, curriculum_id: int) -> dict:
    curriculum = db.query(Curriculum).filter(
        Curriculum.id == curriculum_id,
        Curriculum.user_id == user_id,
    ).first()
    if not curriculum:
        raise ValueError("Curriculum not found")

    topics_progress = []
    total_mastery = 0.0
    topic_count = 0

    for module in curriculum.modules:
        for topic in module.topics:
            mastery = db.query(TopicMastery).filter(
                TopicMastery.user_id == user_id,
                TopicMastery.topic_id == topic.id,
            ).first()

            score = mastery.mastery_score if mastery else 0.0
            total_mastery += score
            topic_count += 1

            status = _mastery_status(score, mastery)

            topics_progress.append({
                "topic_id": topic.id,
                "topic_title": topic.title,
                "module_title": module.title,
                "mastery_score": score,
                "attempts_count": mastery.attempts_count if mastery else 0,
                "last_assessed": mastery.last_assessed if mastery else None,
                "next_review_at": mastery.next_review_at if mastery else None,
                "status": status,
            })

    overall = (total_mastery / topic_count) if topic_count > 0 else 0.0

    return {
        "curriculum_id": curriculum_id,
        "skill_name": curriculum.skill_name,
        "exam_code": curriculum.exam_code,
        "blueprint_version": curriculum.blueprint_version,
        "validation_status": curriculum.validation_status,
        "overall_mastery": overall,
        "topics": topics_progress,
    }


def get_recommendations(db: Session, user_id: int) -> list[dict]:
    masteries = db.query(TopicMastery).filter(
        TopicMastery.user_id == user_id
    ).all()

    mastery_map = {m.topic_id: m for m in masteries}
    curricula = db.query(Curriculum).filter(Curriculum.user_id == user_id).all()

    recommendations = []
    priority = 0

    for curriculum in curricula:
        for module in curriculum.modules:
            for topic in module.topics:
                mastery = mastery_map.get(topic.id)
                score = mastery.mastery_score if mastery else 0.0
                due = is_due_for_review(mastery)

                if due and mastery and score >= 30:
                    priority += 1
                    recommendations.append({
                        "topic_id": topic.id,
                        "topic_title": topic.title,
                        "module_title": module.title,
                        "current_mastery": score,
                        "recommendation_type": "spaced_review",
                        "reason": (
                            f"Spaced repetition: '{topic.title}' is due for review "
                            f"(last score {score:.0f}%)."
                        ),
                        "priority": priority,
                    })
                elif mastery is None:
                    priority += 1
                    recommendations.append({
                        "topic_id": topic.id,
                        "topic_title": topic.title,
                        "module_title": module.title,
                        "current_mastery": 0.0,
                        "recommendation_type": "start",
                        "reason": f"You haven't studied '{topic.title}' yet. Start with the basics!",
                        "priority": priority,
                    })
                elif score < 30:
                    priority += 1
                    recommendations.append({
                        "topic_id": topic.id,
                        "topic_title": topic.title,
                        "module_title": module.title,
                        "current_mastery": score,
                        "recommendation_type": "review",
                        "reason": (
                            f"Your mastery of '{topic.title}' is low ({score:.0f}%). "
                            "Review the fundamentals and retake practice quizzes."
                        ),
                        "priority": priority,
                    })
                elif score < 60:
                    priority += 1
                    recommendations.append({
                        "topic_id": topic.id,
                        "topic_title": topic.title,
                        "module_title": module.title,
                        "current_mastery": score,
                        "recommendation_type": "practice",
                        "reason": (
                            f"You're making progress on '{topic.title}' ({score:.0f}%). "
                            "Take more practice quizzes to reinforce your knowledge."
                        ),
                        "priority": priority,
                    })
                elif score < 80:
                    recommendations.append({
                        "topic_id": topic.id,
                        "topic_title": topic.title,
                        "module_title": module.title,
                        "current_mastery": score,
                        "recommendation_type": "challenge",
                        "reason": (
                            f"You're proficient in '{topic.title}' ({score:.0f}%). "
                            "Try advanced-level questions to push for mastery."
                        ),
                        "priority": priority + 100,
                    })

    recommendations.sort(key=lambda r: r["priority"])
    return recommendations[:10]


def _mastery_status(score: float, mastery: TopicMastery | None) -> str:
    if mastery is None or mastery.attempts_count == 0:
        return "not_started"
    if is_due_for_review(mastery) and mastery.attempts_count > 0:
        return "due_for_review"
    if score >= 80:
        return "mastered"
    if score >= 60:
        return "proficient"
    if score >= 30:
        return "in_progress"
    return "needs_review"

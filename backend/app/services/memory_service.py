from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.memory import LearningEvent, LearnerProfile


def _as_utc(dt: datetime) -> datetime:
    """Normalize SQLite naive datetimes for safe comparisons."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def record_event(
    db: Session,
    user_id: int,
    event_type: str,
    topic_id: int | None = None,
    details: dict | None = None,
) -> None:
    db.add(LearningEvent(
        user_id=user_id,
        topic_id=topic_id,
        event_type=event_type,
        details=details or {},
    ))


def get_or_create_profile(db: Session, user_id: int) -> LearnerProfile:
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if profile is None:
        profile = LearnerProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


def update_profile_after_quiz(
    db: Session,
    user_id: int,
    topic_id: int,
    score: float,
    wrong_objectives: list[str] | None = None,
) -> None:
    profile = get_or_create_profile(db, user_id)
    profile.total_study_sessions += 1
    profile.avg_quiz_score = (
        (profile.avg_quiz_score * (profile.total_study_sessions - 1) + score)
        / profile.total_study_sessions
    )

    weak = list(profile.weak_objectives or [])
    for obj_id in wrong_objectives or []:
        if obj_id and obj_id not in weak:
            weak.append(obj_id)
    profile.weak_objectives = weak[-20:]
    profile.updated_at = datetime.now(timezone.utc)


def update_profile_after_resources(
    db: Session,
    user_id: int,
    resource_types: list[str],
) -> None:
    if not resource_types:
        return
    profile = get_or_create_profile(db, user_id)
    type_counts: dict[str, int] = dict(profile.learning_notes.get("resource_type_counts", {}))
    for rtype in resource_types:
        type_counts[rtype] = type_counts.get(rtype, 0) + 1
    profile.preferred_resource_type = max(type_counts, key=type_counts.get)
    notes = dict(profile.learning_notes or {})
    notes["resource_type_counts"] = type_counts
    profile.learning_notes = notes
    profile.updated_at = datetime.now(timezone.utc)


def apply_spaced_repetition(mastery, score: float) -> None:
    """SM-2 inspired scheduling for topic review."""
    now = datetime.now(timezone.utc)

    if score >= 80:
        mastery.interval_days = min(max(mastery.interval_days * 2, 1), 30)
        mastery.ease_factor = min(mastery.ease_factor + 0.1, 3.0)
    elif score >= 60:
        mastery.interval_days = max(mastery.interval_days, 3)
    else:
        mastery.interval_days = 1
        mastery.ease_factor = max(mastery.ease_factor - 0.2, 1.3)

    mastery.next_review_at = now + timedelta(days=mastery.interval_days)


def is_due_for_review(mastery) -> bool:
    if mastery is None or mastery.next_review_at is None:
        return mastery is None or mastery.attempts_count == 0
    return _as_utc(mastery.next_review_at) <= datetime.now(timezone.utc)

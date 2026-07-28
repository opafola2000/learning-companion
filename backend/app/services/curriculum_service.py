from sqlalchemy.orm import Session

from app.models.curriculum import Curriculum, Module, Topic
from app.services.bedrock_client import get_bedrock_client
from app.services.grounding_service import fetch_exam_context, get_profile_for_skill
from app.services.validation_service import validate_curriculum
from app.services.memory_service import record_event

CURRICULUM_SYSTEM_PROMPT = """You are an expert curriculum designer for professional certification exams.
Create a curriculum grounded ONLY in the provided official source material. Do not invent topics.

Return a JSON object with this exact structure:
{
  "description": "Brief description of the certification and what it covers",
  "modules": [
    {
      "title": "Module title aligned to an exam domain",
      "description": "What this module covers",
      "objective_ids": ["OBJ-1"],
      "topics": [
        {
          "title": "Topic title",
          "description": "What the learner will study",
          "difficulty": "beginner|intermediate|advanced",
          "objective_ids": ["OBJ-1"],
          "source_urls": ["https://official-source-url"]
        }
      ]
    }
  ]
}

Guidelines:
- Create 4-6 modules covering the full exam scope from the sources
- Each module should have 3-5 topics
- Every topic MUST map to exam objectives found in the source material
- Include source_urls from the provided sources for each topic
- Do not include topics absent from official objectives
- Order modules from foundational to advanced"""


def generate_curriculum(db: Session, user_id: int, skill_name: str) -> Curriculum:
    bedrock = get_bedrock_client()
    profile = get_profile_for_skill(skill_name)
    grounded = fetch_exam_context(skill_name, profile)

    user_message = f"""Create a learning curriculum for: {skill_name}
Exam code: {profile.exam_code}
Blueprint version: {profile.blueprint_version}
Effective date: {profile.effective_date}

Official source material (use ONLY these facts):
{grounded["context_text"]}

Create a structured curriculum that covers all exam objectives from these sources."""

    result = bedrock.invoke_sonnet_json(CURRICULUM_SYSTEM_PROMPT, user_message, max_tokens=8192)

    validation = validate_curriculum(
        skill_name,
        result,
        grounded["context_text"],
        profile.exam_code,
    )

    topic_mappings = {
        m.get("topic_title", ""): m
        for m in validation.get("topic_mappings", [])
    }

    curriculum = Curriculum(
        user_id=user_id,
        skill_name=skill_name,
        description=result.get("description", ""),
        overall_structure=result,
        blueprint_version=profile.blueprint_version,
        exam_code=profile.exam_code,
        validation_status=validation.get("validation_status", "needs_review"),
        sources=grounded["sources"],
        objectives=validation.get("objectives", []),
        is_stale="false",
    )
    db.add(curriculum)
    db.flush()

    for mod_idx, mod_data in enumerate(result.get("modules", [])):
        module = Module(
            curriculum_id=curriculum.id,
            title=mod_data["title"],
            description=mod_data.get("description", ""),
            order_index=mod_idx,
        )
        db.add(module)
        db.flush()

        for topic_idx, topic_data in enumerate(mod_data.get("topics", [])):
            mapping = topic_mappings.get(topic_data.get("title", ""), {})
            topic = Topic(
                module_id=module.id,
                title=topic_data["title"],
                description=topic_data.get("description", ""),
                order_index=topic_idx,
                difficulty=topic_data.get("difficulty", "intermediate"),
                objective_ids=topic_data.get("objective_ids") or mapping.get("objective_ids", []),
                source_urls=topic_data.get("source_urls", []),
                validation_status="verified" if mapping.get("grounded") else "needs_review",
            )
            db.add(topic)

    record_event(db, user_id, "curriculum_generated", details={
        "skill_name": skill_name,
        "exam_code": profile.exam_code,
        "validation_status": curriculum.validation_status,
    })

    db.commit()
    db.refresh(curriculum)
    return curriculum

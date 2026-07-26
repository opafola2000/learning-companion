import json
from sqlalchemy.orm import Session
from app.models.curriculum import Curriculum, Module, Topic
from app.services.bedrock_client import get_bedrock_client
from app.services.tavily_client import get_tavily_client

CURRICULUM_SYSTEM_PROMPT = """You are an expert curriculum designer for professional certification exams.
Given a certification or skill name and exam guide information, create a comprehensive, structured learning curriculum.

Return a JSON object with this exact structure:
{
  "description": "Brief description of the certification and what it covers",
  "modules": [
    {
      "title": "Module title",
      "description": "What this module covers",
      "topics": [
        {
          "title": "Topic title",
          "description": "What the learner will study",
          "difficulty": "beginner|intermediate|advanced"
        }
      ]
    }
  ]
}

Guidelines:
- Create 4-8 modules that cover the full exam scope
- Each module should have 3-6 topics
- Order modules from foundational to advanced
- Order topics within modules logically
- Tag difficulty accurately based on conceptual complexity
- Align topics with real exam objectives when exam guide info is provided
- Make topic descriptions actionable and specific"""


def generate_curriculum(db: Session, user_id: int, skill_name: str) -> Curriculum:
    bedrock = get_bedrock_client()
    tavily = get_tavily_client()

    exam_results = tavily.search_exam_guide(skill_name)
    exam_context = "\n\n".join(
        f"Source: {r.get('title', 'N/A')}\nURL: {r.get('url', 'N/A')}\nContent: {r.get('content', 'N/A')}"
        for r in exam_results[:5]
    )

    user_message = f"""Create a learning curriculum for: {skill_name}

Here is information about the exam/certification gathered from official sources:

{exam_context}

Based on this information, create a structured curriculum that covers all exam objectives."""

    result = bedrock.invoke_sonnet_json(CURRICULUM_SYSTEM_PROMPT, user_message)

    curriculum = Curriculum(
        user_id=user_id,
        skill_name=skill_name,
        description=result.get("description", ""),
        overall_structure=result,
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
            topic = Topic(
                module_id=module.id,
                title=topic_data["title"],
                description=topic_data.get("description", ""),
                order_index=topic_idx,
                difficulty=topic_data.get("difficulty", "intermediate"),
            )
            db.add(topic)

    db.commit()
    db.refresh(curriculum)
    return curriculum

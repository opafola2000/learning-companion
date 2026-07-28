from sqlalchemy.orm import Session

from app.models.resource import Resource
from app.models.curriculum import Topic
from app.services.bedrock_client import get_bedrock_client
from app.services.tavily_client import get_tavily_client
from app.services.grounding_service import (
    classify_trust_tier,
    extract_domain,
    get_profile_for_skill,
    is_trusted_resource,
)
from app.services.memory_service import record_event, update_profile_after_resources

SUMMARIZE_SYSTEM_PROMPT = """You are a learning resource evaluator. Given search results for a study topic,
evaluate and summarize each resource for a learner.

Return a JSON array of objects:
[
  {
    "title": "Resource title",
    "url": "Resource URL",
    "type": "article|video|documentation|lab|practice_exam",
    "summary": "2-3 sentence summary of what the learner will gain",
    "citation_snippet": "One sentence quoting or paraphrasing key fact from the source"
  }
]

Guidelines:
- Only include resources genuinely useful for the certification exam topic
- Prefer official documentation and recent content
- Filter out brain dumps, exam cheat sites, and irrelevant results
- Limit to the top 5-8 most useful resources"""


def search_and_save_resources(
    db: Session, topic_id: int, skill_context: str, user_id: int | None = None
) -> list[Resource]:
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise ValueError(f"Topic {topic_id} not found")

    profile = get_profile_for_skill(skill_context)
    tavily = get_tavily_client()
    bedrock = get_bedrock_client()

    search_results = [
        r for r in tavily.search_resources(topic.title, skill_context, profile)
        if is_trusted_resource(r.get("url", ""), profile)
    ]

    search_context = "\n\n".join(
        f"Title: {r.get('title', 'N/A')}\nURL: {r.get('url', 'N/A')}\nContent: {r.get('content', 'N/A')}"
        for r in search_results
    )

    user_message = f"""Topic: {topic.title}
Certification: {skill_context}
Exam code: {profile.exam_code}
Topic description: {topic.description}
Official topic sources: {topic.source_urls or []}

Search results:
{search_context}

Evaluate these resources and return the best ones for studying this exam topic."""

    evaluated = bedrock.invoke_haiku_json(SUMMARIZE_SYSTEM_PROMPT, user_message)
    if isinstance(evaluated, dict):
        evaluated = evaluated.get("resources", evaluated.get("items", []))
    if not isinstance(evaluated, list):
        evaluated = []

    db.query(Resource).filter(Resource.topic_id == topic_id).delete()

    resources = []
    resource_types = []
    for item in evaluated:
        url = item.get("url", "")
        if not url or not is_trusted_resource(url, profile):
            continue
        trust = classify_trust_tier(url, profile)
        resource = Resource(
            topic_id=topic_id,
            title=item["title"],
            url=url,
            type=item.get("type", "article"),
            summary=item.get("summary", ""),
            source_domain=extract_domain(url),
            trust_tier=trust,
            citation_snippet=item.get("citation_snippet"),
        )
        db.add(resource)
        resources.append(resource)
        resource_types.append(resource.type)

    if user_id:
        record_event(db, user_id, "resources_viewed", topic_id=topic_id, details={
            "count": len(resources),
            "types": resource_types,
        })
        update_profile_after_resources(db, user_id, resource_types)

    db.commit()
    for r in resources:
        db.refresh(r)
    return resources

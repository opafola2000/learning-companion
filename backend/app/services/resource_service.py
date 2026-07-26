from sqlalchemy.orm import Session
from app.models.resource import Resource
from app.models.curriculum import Topic
from app.services.bedrock_client import get_bedrock_client
from app.services.tavily_client import get_tavily_client

SUMMARIZE_SYSTEM_PROMPT = """You are a learning resource evaluator. Given search results for a study topic,
evaluate and summarize each resource for a learner.

Return a JSON array of objects:
[
  {
    "title": "Resource title",
    "url": "Resource URL",
    "type": "article|video|documentation|lab|practice_exam",
    "summary": "2-3 sentence summary of what the learner will gain from this resource"
  }
]

Guidelines:
- Only include resources that are genuinely useful for learning the topic
- Classify the type accurately
- Write summaries from the learner's perspective
- Filter out irrelevant or low-quality results
- Limit to the top 5-8 most useful resources"""


def search_and_save_resources(
    db: Session, topic_id: int, skill_context: str
) -> list[Resource]:
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise ValueError(f"Topic {topic_id} not found")

    tavily = get_tavily_client()
    bedrock = get_bedrock_client()

    search_results = tavily.search_resources(topic.title, skill_context)

    search_context = "\n\n".join(
        f"Title: {r.get('title', 'N/A')}\nURL: {r.get('url', 'N/A')}\nContent: {r.get('content', 'N/A')}"
        for r in search_results
    )

    user_message = f"""Topic: {topic.title}
Context: Learning for {skill_context}
Topic description: {topic.description}

Search results:
{search_context}

Evaluate these resources and return the best ones for studying this topic."""

    evaluated = bedrock.invoke_haiku_json(SUMMARIZE_SYSTEM_PROMPT, user_message)

    db.query(Resource).filter(Resource.topic_id == topic_id).delete()

    resources = []
    for item in evaluated:
        resource = Resource(
            topic_id=topic_id,
            title=item["title"],
            url=item["url"],
            type=item.get("type", "article"),
            summary=item.get("summary", ""),
        )
        db.add(resource)
        resources.append(resource)

    db.commit()
    for r in resources:
        db.refresh(r)
    return resources

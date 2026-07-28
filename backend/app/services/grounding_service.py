from datetime import datetime, timezone
from urllib.parse import urlparse

from app.data.exam_profiles import ExamProfile, BLOCKED_DOMAINS, match_exam_profile
from app.services.tavily_client import get_tavily_client


def get_profile_for_skill(skill_name: str) -> ExamProfile:
    return match_exam_profile(skill_name)


def fetch_exam_context(skill_name: str, profile: ExamProfile) -> dict:
    tavily = get_tavily_client()
    results = tavily.search_exam_guide(skill_name, profile)

    sources = []
    chunks = []
    for r in results:
        url = r.get("url", "")
        if _is_blocked(url):
            continue
        sources.append({
            "title": r.get("title", "N/A"),
            "url": url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        })
        chunks.append(
            f"Source: {r.get('title', 'N/A')}\n"
            f"URL: {url}\n"
            f"Content: {r.get('content', 'N/A')}"
        )

    return {
        "profile": profile,
        "sources": sources,
        "context_text": "\n\n---\n\n".join(chunks),
    }


def fetch_topic_context(topic_title: str, skill_name: str, profile: ExamProfile) -> str:
    tavily = get_tavily_client()
    results = tavily.search_topic_for_quiz(topic_title, skill_name, profile)
    chunks = []
    for r in results:
        url = r.get("url", "")
        if _is_blocked(url):
            continue
        chunks.append(
            f"Source: {r.get('title', 'N/A')}\n"
            f"URL: {url}\n"
            f"Content: {r.get('content', 'N/A')}"
        )
    return "\n\n---\n\n".join(chunks)


def extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def classify_trust_tier(url: str, profile: ExamProfile) -> str:
    domain = extract_domain(url)
    if not domain:
        return "unknown"
    if any(blocked in domain for blocked in BLOCKED_DOMAINS):
        return "blocked"
    if any(trusted in domain for trusted in profile.trusted_resource_domains):
        return "official"
    if any(allowed in domain for allowed in profile.allowed_domains):
        return "trusted"
    return "community"


def is_trusted_resource(url: str, profile: ExamProfile) -> bool:
    return classify_trust_tier(url, profile) != "blocked"


def _is_blocked(url: str) -> bool:
    domain = extract_domain(url)
    return any(blocked in domain for blocked in BLOCKED_DOMAINS)

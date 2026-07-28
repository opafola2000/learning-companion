from tavily import TavilyClient
from app.config import get_settings
from app.data.exam_profiles import ExamProfile, DEFAULT_PROFILE


class TavilySearchClient:
    def __init__(self):
        settings = get_settings()
        self.client = TavilyClient(api_key=settings.tavily_api_key)

    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: list[str] | None = None,
    ) -> list[dict]:
        kwargs = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }
        if include_domains:
            kwargs["include_domains"] = include_domains

        response = self.client.search(**kwargs)
        return response.get("results", [])

    def search_exam_guide(self, skill_name: str, profile: ExamProfile | None = None) -> list[dict]:
        profile = profile or DEFAULT_PROFILE
        year = profile.effective_date[:4]
        query = (
            f"{skill_name} {profile.exam_code} official exam guide objectives syllabus {year}"
        )
        domains = profile.allowed_domains or None
        return self.search(
            query=query,
            max_results=8,
            search_depth="advanced",
            include_domains=domains,
        )

    def search_exam_updates(self, skill_name: str, profile: ExamProfile) -> list[dict]:
        query = f"{skill_name} {profile.exam_code} exam changes updates {profile.blueprint_version}"
        return self.search(
            query=query,
            max_results=5,
            search_depth="advanced",
            include_domains=profile.allowed_domains or None,
        )

    def search_resources(self, topic: str, skill_context: str, profile: ExamProfile | None = None) -> list[dict]:
        profile = profile or DEFAULT_PROFILE
        query = f"{topic} official documentation tutorial for {skill_context}"
        domains = profile.trusted_resource_domains or profile.allowed_domains or None
        return self.search(
            query=query,
            max_results=10,
            search_depth="basic",
            include_domains=domains,
        )

    def search_topic_for_quiz(self, topic: str, skill_context: str, profile: ExamProfile) -> list[dict]:
        query = (
            f"{topic} {skill_context} {profile.exam_code} exam objectives "
            f"official documentation {profile.blueprint_version}"
        )
        return self.search(
            query=query,
            max_results=8,
            search_depth="advanced",
            include_domains=profile.allowed_domains or None,
        )


_tavily_client: TavilySearchClient | None = None


def get_tavily_client() -> TavilySearchClient:
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilySearchClient()
    return _tavily_client

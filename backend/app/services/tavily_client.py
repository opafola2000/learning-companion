from tavily import TavilyClient
from app.config import get_settings


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

    def search_exam_guide(self, skill_name: str) -> list[dict]:
        return self.search(
            query=f"{skill_name} official exam guide objectives syllabus",
            max_results=5,
            search_depth="advanced",
        )

    def search_resources(self, topic: str, skill_context: str) -> list[dict]:
        return self.search(
            query=f"{topic} tutorial guide learning resource for {skill_context}",
            max_results=10,
            search_depth="basic",
        )


_tavily_client: TavilySearchClient | None = None


def get_tavily_client() -> TavilySearchClient:
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilySearchClient()
    return _tavily_client

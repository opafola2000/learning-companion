from pydantic import BaseModel
from datetime import datetime


class TopicMasteryResponse(BaseModel):
    topic_id: int
    topic_title: str
    module_title: str
    mastery_score: float
    attempts_count: int
    last_assessed: datetime | None
    status: str

    model_config = {"from_attributes": True}


class CurriculumProgressResponse(BaseModel):
    curriculum_id: int
    skill_name: str
    overall_mastery: float
    topics: list[TopicMasteryResponse] = []


class RecommendationResponse(BaseModel):
    topic_id: int
    topic_title: str
    module_title: str
    current_mastery: float
    recommendation_type: str
    reason: str
    priority: int


class ResourceResponse(BaseModel):
    id: int
    title: str
    url: str
    type: str
    summary: str | None

    model_config = {"from_attributes": True}

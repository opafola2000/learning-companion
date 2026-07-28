from pydantic import BaseModel, Field
from datetime import datetime


class TopicMasteryResponse(BaseModel):
    topic_id: int
    topic_title: str
    module_title: str
    mastery_score: float
    attempts_count: int
    last_assessed: datetime | None
    next_review_at: datetime | None = None
    status: str

    model_config = {"from_attributes": True}


class CurriculumProgressResponse(BaseModel):
    curriculum_id: int
    skill_name: str
    exam_code: str | None = None
    blueprint_version: str | None = None
    validation_status: str | None = None
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
    source_domain: str | None = None
    trust_tier: str | None = None
    citation_snippet: str | None = None

    model_config = {"from_attributes": True}


class ContentFeedbackCreate(BaseModel):
    content_type: str = Field(pattern="^(topic|question|resource|curriculum)$")
    content_id: int
    reason: str = Field(min_length=3, max_length=100)
    comment: str | None = Field(default=None, max_length=1000)


class ContentFeedbackResponse(BaseModel):
    id: int
    content_type: str
    content_id: int
    reason: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

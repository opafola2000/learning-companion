from pydantic import BaseModel, Field
from datetime import datetime


class SourceCitation(BaseModel):
    title: str
    url: str
    retrieved_at: str | None = None


class GenerateCurriculumRequest(BaseModel):
    skill_name: str = Field(min_length=2, max_length=200)


class TopicResponse(BaseModel):
    id: int
    title: str
    description: str | None
    order_index: int
    difficulty: str
    status: str
    mastery_score: float | None = None
    objective_ids: list[str] = []
    source_urls: list[str] = []
    validation_status: str | None = None

    model_config = {"from_attributes": True}


class ModuleResponse(BaseModel):
    id: int
    title: str
    description: str | None
    order_index: int
    status: str
    topics: list[TopicResponse] = []

    model_config = {"from_attributes": True}


class CurriculumResponse(BaseModel):
    id: int
    skill_name: str
    description: str | None
    created_at: datetime
    exam_code: str | None = None
    blueprint_version: str | None = None
    validation_status: str | None = None
    sources: list[SourceCitation] = []
    modules: list[ModuleResponse] = []

    model_config = {"from_attributes": True}


class CurriculumListItem(BaseModel):
    id: int
    skill_name: str
    description: str | None
    created_at: datetime
    exam_code: str | None = None
    blueprint_version: str | None = None
    validation_status: str | None = None
    module_count: int = 0
    topic_count: int = 0
    overall_mastery: float = 0.0

    model_config = {"from_attributes": True}

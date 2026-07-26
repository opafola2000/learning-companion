from pydantic import BaseModel
from datetime import datetime


class GenerateCurriculumRequest(BaseModel):
    skill_name: str


class TopicResponse(BaseModel):
    id: int
    title: str
    description: str | None
    order_index: int
    difficulty: str
    status: str
    mastery_score: float | None = None

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
    modules: list[ModuleResponse] = []

    model_config = {"from_attributes": True}


class CurriculumListItem(BaseModel):
    id: int
    skill_name: str
    description: str | None
    created_at: datetime
    module_count: int = 0
    topic_count: int = 0
    overall_mastery: float = 0.0

    model_config = {"from_attributes": True}

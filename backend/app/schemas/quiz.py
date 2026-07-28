from pydantic import BaseModel, Field
from datetime import datetime


class GenerateQuizRequest(BaseModel):
    num_questions: int = Field(default=5, ge=1, le=20)
    quiz_type: str = "practice"


class AnswerOptionResponse(BaseModel):
    id: int
    option_text: str

    model_config = {"from_attributes": True}


class AnswerOptionWithCorrect(BaseModel):
    id: int
    option_text: str
    is_correct: bool

    model_config = {"from_attributes": True}


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    difficulty: str
    objective_id: str | None = None
    options: list[AnswerOptionResponse] = []

    model_config = {"from_attributes": True}


class QuestionWithExplanation(BaseModel):
    id: int
    question_text: str
    difficulty: str
    explanation: str | None
    objective_id: str | None = None
    source_reference: str | None = None
    citation_snippet: str | None = None
    options: list[AnswerOptionWithCorrect] = []
    user_selected_option_id: int | None = None
    is_correct: bool | None = None

    model_config = {"from_attributes": True}


class QuizResponse(BaseModel):
    id: int
    topic_id: int
    quiz_type: str
    num_questions: int
    created_at: datetime
    exam_code: str | None = None
    blueprint_version: str | None = None
    validation_status: str | None = None
    questions: list[QuestionResponse] = []

    model_config = {"from_attributes": True}


class AnswerSubmission(BaseModel):
    question_id: int
    selected_option_id: int


class QuizSubmission(BaseModel):
    answers: list[AnswerSubmission]


class QuizResultResponse(BaseModel):
    attempt_id: int
    score: float
    total_questions: int
    correct_count: int
    questions: list[QuestionWithExplanation] = []
    mastery_update: float | None = None
    exam_code: str | None = None
    blueprint_version: str | None = None

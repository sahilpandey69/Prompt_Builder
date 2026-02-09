from typing import Any

from pydantic import BaseModel, Field


class QuestionOption(BaseModel):
    id: str
    field: str
    question: str
    type: str  # single_choice | multiple_choice | text
    options: list[str] = Field(default_factory=list)
    required: bool = True
    answered: bool = False


class CreateInputMetadata(BaseModel):
    filename: str | None = None
    file_type: str | None = None


class CreateRequest(BaseModel):
    session_id: str | None = None
    input: dict[str, Any]  # type, content, metadata


class CreateResponse(BaseModel):
    session_id: str
    status: str  # parsed | needs_input | generating | complete
    questions: list[dict[str, Any]] = Field(default_factory=list)
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    completeness_score: int = 0


class AnswerRequest(BaseModel):
    session_id: str
    answers: dict[str, Any]


class AnswerResponse(BaseModel):
    session_id: str
    status: str  # generating | needs_input | complete
    questions: list[dict[str, Any]] = Field(default_factory=list)
    progress: int = 0


class ResultResponse(BaseModel):
    session_id: str
    final_prompt: str = ""
    quality_score: int = 0
    validation_results: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    deployed: bool = False
    rating: int = 0
    issues: str = ""
    manual_edits: str = ""


class TemplateItem(BaseModel):
    id: str
    name: str
    description: str
    use_count: int = 0
    avg_rating: float = 0.0
    language: str = "English"


class FromTemplateRequest(BaseModel):
    template_id: str
    customizations: dict[str, Any] = Field(default_factory=dict)

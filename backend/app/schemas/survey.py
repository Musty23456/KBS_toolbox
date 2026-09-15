from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.question import QuestionType
from app.models.survey import SurveyStatus


class ChoiceIn(BaseModel):
    value: str = Field(max_length=255)
    label: str = Field(max_length=500)
    order_index: int = 0
    cascade_parent_value: str | None = None


class ChoiceOut(ChoiceIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


class QuestionIn(BaseModel):
    code: str = Field(max_length=100)
    label: str
    hint: str | None = None
    type: QuestionType
    order_index: int = 0
    is_required: bool = False
    min_value: float | None = None
    max_value: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    regex_pattern: str | None = None
    relevance_expression: str | None = None
    calculation_expression: str | None = None
    default_value: str | None = None
    cascade_parent_question_id: str | None = None
    choices: list[ChoiceIn] = []


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    label: str
    hint: str | None
    type: QuestionType
    order_index: int
    is_required: bool
    min_value: float | None
    max_value: float | None
    min_length: int | None
    max_length: int | None
    regex_pattern: str | None
    relevance_expression: str | None
    calculation_expression: str | None
    default_value: str | None
    cascade_parent_question_id: str | None
    choices: list[ChoiceOut] = []


class SurveyCreate(BaseModel):
    title: str = Field(max_length=255)
    description: str | None = None
    questions: list[QuestionIn] = []


class SurveyUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    questions: list[QuestionIn] | None = None


class SurveySummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None
    status: SurveyStatus
    created_at: datetime
    current_version_number: int | None = None
    current_version_id: str | None = None


class SurveyDetailOut(SurveySummaryOut):
    questions: list[QuestionOut] = []

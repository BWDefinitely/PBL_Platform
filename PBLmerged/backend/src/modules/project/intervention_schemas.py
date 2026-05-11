from datetime import datetime

from pydantic import BaseModel, Field


class InterventionCreateRequest(BaseModel):
    student_id: str = Field(min_length=1, max_length=64)
    action_type: str = Field(min_length=1, max_length=64)
    milestone: str | None = Field(default=None, max_length=16)
    note: str | None = Field(default=None, max_length=1000)


class InterventionResponse(BaseModel):
    id: int
    student_id: str
    action_type: str
    milestone: str | None
    note: str | None
    status: str
    created_at: datetime


class InterventionStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=32)

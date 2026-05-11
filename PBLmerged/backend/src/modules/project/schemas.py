from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    term: str | None = None
    status: str = "active"


class ProjectResponse(BaseModel):
    id: int
    name: str
    term: str | None
    status: str

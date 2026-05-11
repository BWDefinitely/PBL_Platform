from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class UserState(BaseModel):
    energy: int = Field(5, ge=1, le=10)
    emotion: Literal['happy', 'neutral', 'sad', 'stressed'] = 'neutral'
    available_time: int = Field(60, ge=1)
    environment: Literal['home', 'office', 'cafe', 'travel'] = 'home'


class TaskItem(BaseModel):
    id: str
    name: str
    deadline: Optional[str] = None
    urgency: Literal['low', 'medium', 'high'] = 'medium'
    importance: int = Field(5, ge=1, le=10)
    estimated_time: int = Field(30, ge=1)


class PrioritizeRequest(BaseModel):
    user_state: UserState
    tasks: List[TaskItem]

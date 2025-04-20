from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserOut(BaseModel):
    id: int
    username: str

class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str = Field(..., max_length=255)
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    due_date: Optional[datetime] = None

class TaskOut(TaskBase):
    id: int
    owner: UserOut
    created_at: datetime
    updated_at: datetime

class TaskDetailOut(TaskOut):
    assignees: List[UserOut] = []

class TaskAssigneeCreate(BaseModel):
    user_ids: List[int]

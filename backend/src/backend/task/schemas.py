from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from ..consts import TaskStatus

class UserOut(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(
        from_attributes=True,
    )

class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str = Field(..., max_length=255)
    due_date: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus

class TaskOut(TaskBase):
    id: int
    owner: UserOut
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class TaskDetailOut(TaskOut):
    assignees: List[UserOut] = []

class TaskAssigneeCreate(BaseModel):
    user_ids: List[int]

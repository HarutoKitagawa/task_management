from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Session
from ..consts import TaskEventType
from ..models import Task, User, TaskEvent as TaskEventModel, Notification

class TaskEvent(ABC):
    def __init__(self, task: Task, actor: User):
        self.id: Optional[int] = None
        self.task = task
        self.actor = actor
    
    @abstractmethod
    def save(self, db: Session) -> bool:
        pass

    @abstractmethod
    def _create_message(self) -> str:
        pass
    
    def notificate(self, db: Session):
        participant_ids = {self.task.owner.id}
        if self.task.assignees:
            participant_ids.update([assignee.user_id for assignee in self.task.assignees])
        
        for participant_id in participant_ids:
            if participant_id != self.actor.id:  # Avoid notifying the actor
                if self.id is not None:
                    notification = Notification(
                        user_id=participant_id,
                        task_event_id=self.id,
                        message=self._create_message(),
                    )
                    db.add(notification)
        db.commit()

class TaskAssignmentEvent(TaskEvent):
    def __init__(self, task: Task, actor: User, assignee: User):
        super().__init__(task, actor)
        self.assignee = assignee

    def save(self, db: Session):
        event = TaskEventModel(
            task_id=self.task.id,
            actor_id=self.actor.id,
            event_type=TaskEventType.TASK_ASSIGNED,
            payload={"assignee_id": self.assignee.id},
            message=self._create_message(),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        self.id = event.id
        self.notificate(db)
    
    def _create_message(self) -> str:
        return f"Task '{self.task.title}' has been assigned to {self.assignee.username} by {self.actor.username}."

class TaskStatusUpdatedEvent(TaskEvent):
    def __init__(self, task: Task, actor: User, old_status: str, new_status: str):
        super().__init__(task, actor)
        self.old_status = old_status
        self.new_status = new_status

    def save(self, db: Session):
        event = TaskEventModel(
            task_id=self.task.id,
            actor_id=self.actor.id,
            event_type=TaskEventType.TASK_STATUS_UPDATED,
            payload={"old_status": self.old_status, "new_status": self.new_status},
            message=self._create_message(),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        self.id = event.id
        self.notificate(db)
    
    def _create_message(self) -> str:
        return f"Task '{self.task.title}' status changed from {self.old_status} to {self.new_status} by {self.actor.username}."
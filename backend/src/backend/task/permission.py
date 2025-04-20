from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Task, TaskAssignee, User
from ..auth.dependencies import get_current_user


def get_task_or_404(task_id: int, db: Session) -> Task:
    task = db.query(Task).filter(Task.id == task_id, Task.deleted_at.is_(None)).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


def verify_task_owner(task: Task, user: User):
    if task.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action"
        )


def verify_task_participant(task: Task, user: User, db: Session):
    if task.owner_id == user.id:
        return
    assignee = db.query(TaskAssignee).filter(
        TaskAssignee.task_id == task.id,
        TaskAssignee.user_id == user.id,
        TaskAssignee.deleted_at.is_(None)
    ).first()
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action"
        )


def get_task_with_perticipant_check(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    task = get_task_or_404(task_id, db)
    verify_task_participant(task, current_user, db)
    return task


def get_task_with_owner_check(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    task = get_task_or_404(task_id, db)
    verify_task_owner(task, current_user)
    return task

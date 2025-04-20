from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import User, Task, TaskAssignee
from .permission import get_task_with_perticipant_check, get_task_with_owner_check
from .event import TaskAssignmentEvent, TaskStatusUpdatedEvent
from .schemas import *

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task_create: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_task = Task(
        title=task_create.title,
        description=task_create.description,
        due_date=task_create.due_date,
        owner_id=current_user.id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return TaskOut.model_validate(new_task)

@router.get("", response_model=TasksGetOut)
def get_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get tasks where user is the owner
    owned_tasks = db.query(Task).filter(
        Task.owner_id == current_user.id,
        Task.deleted_at.is_(None)
    ).all()
    
    # Get tasks where user is assigned
    assigned_task_ids = db.query(TaskAssignee.task_id).filter(
        TaskAssignee.user_id == current_user.id,
        TaskAssignee.deleted_at.is_(None)
    ).all()
    
    assigned_task_ids = [task_id for (task_id,) in assigned_task_ids]
    
    assigned_tasks = []
    if assigned_task_ids:
        assigned_tasks = [TaskOut.model_validate(task) for task in db.query(Task).filter(
            Task.id.in_(assigned_task_ids),
            Task.deleted_at.is_(None)
        ).all()]
    
    return TasksGetOut(
        owned_tasks=[TaskOut.model_validate(task) for task in owned_tasks],
        assigned_tasks=assigned_tasks
    )
    

@router.get("/{task_id}", response_model=TaskDetailOut)
def get_task(
    task: Task = Depends(get_task_with_perticipant_check),
    db: Session = Depends(get_db),
):  
    # Get assignees
    assignees = db.query(User).join(
        TaskAssignee, User.id == TaskAssignee.user_id
    ).filter(
        TaskAssignee.task_id == task.id,
        TaskAssignee.deleted_at.is_(None)
    ).all()
    
    # Create response with assignees
    return TaskDetailOut(
        id=task.id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        status=task.status,
        owner=UserOut.model_validate(task.owner),
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignees=[UserOut.model_validate(user) for user in assignees]
    )

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_update: TaskUpdate,
    task: Task = Depends(get_task_with_owner_check),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Update fields if provided
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.due_date is not None:
        task.due_date = task_update.due_date
    task_status_updated = (
        task_update.status is not None and
        task.status != task_update.status
    )
    old_status = task.status
    if task_status_updated:
        task.status = task_update.status
    
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)

    # Create task status updated event
    if task_status_updated:
        TaskStatusUpdatedEvent(
            task,
            current_user,
            old_status,
            task.status
        ).save(db)
    
    return task

@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_status_update: TaskStatusUpdate,
    task: Task = Depends(get_task_with_perticipant_check),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):    
    old_status = task.status
    task_status_updated = old_status != task_status_update.status
    if not task_status_updated:
        return TaskOut.model_validate(task)
    # Update status
    task.status = task_status_update.status
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)

    # Create task status updated event
    TaskStatusUpdatedEvent(
        task,
        current_user,
        old_status,
        task.status
    ).save(db)
    
    return TaskOut.model_validate(task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task: Task = Depends(get_task_with_owner_check),
    db: Session = Depends(get_db),
):
    # Soft delete
    task.deleted_at = datetime.now(timezone.utc)
    db.commit()
    
    return None

@router.post("/{task_id}/assignees", response_model=TaskDetailOut)
def assign_users_to_task(
    assignee_data: TaskAssigneeCreate,
    task: Task = Depends(get_task_with_owner_check),
    db: Session = Depends(get_db),
):    
    # Verify all users exist
    user_ids = assignee_data.user_ids
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    found_user_ids = [user.id for user in users]
    
    if len(found_user_ids) != len(user_ids):
        missing_ids = set(user_ids) - set(found_user_ids)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Users with ids {missing_ids} not found"
        )
    
    # Get existing assignees to avoid duplicates
    existing_assignees = db.query(TaskAssignee).filter(
        TaskAssignee.task_id == task.id,
        TaskAssignee.deleted_at.is_(None)
    ).all()
    existing_user_ids = [assignee.user_id for assignee in existing_assignees]
    
    new_assignee_ids = set(user_ids) - set(existing_user_ids)
    # Add new assignees
    for user_id in new_assignee_ids:
        new_assignee = TaskAssignee(
            task_id=task.id,
            user_id=user_id
        )
        db.add(new_assignee)
    
    db.commit()

    new_assignees = db.query(User).filter(
        User.id.in_(new_assignee_ids)
    ).all()

    # Create task assignment event
    for assignee in new_assignees:
        TaskAssignmentEvent(
            task,
            task.owner,
            assignee
        ).save(db)
    
    # Get updated assignees for response
    existing_assignee_users = db.query(User).filter(
        User.id.in_(existing_user_ids)
    ).all()
    assignees = list(new_assignees) + list(existing_assignee_users)
    
    # Create response with assignees
    return TaskDetailOut(
        id=task.id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        status=task.status,
        owner=UserOut.model_validate(task.owner),
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignees=[UserOut.model_validate(user) for user in assignees]
    )

@router.delete("/{task_id}/assignees/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assignee_from_task(
    user_id: int,
    task: Task = Depends(get_task_with_owner_check),
    db: Session = Depends(get_db),
):
    # Find the assignee
    assignee = db.query(TaskAssignee).filter(
        TaskAssignee.task_id == task.id,
        TaskAssignee.user_id == user_id,
        TaskAssignee.deleted_at.is_(None)
    ).first()
    
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not assigned to this task"
        )
    
    # Soft delete the assignment
    assignee.deleted_at = datetime.now(timezone.utc)
    db.commit()
    
    return None

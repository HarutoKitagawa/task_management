from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import User, Task, TaskAssignee
from .schemas import *

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Helper function to check if user is the owner of a task
def check_task_owner(task: Task, user: User):
    if task.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action"
        )

# Helper function to check if user has access to a task (owner or assignee)
def check_task_access(task: Task, user: User, db: Session):
    # Check if user is the owner
    if task.owner_id == user.id:
        return True
    
    # Check if user is assigned to the task
    assignee = db.query(TaskAssignee).filter(
        TaskAssignee.task_id == task.id,
        TaskAssignee.user_id == user.id,
        TaskAssignee.deleted_at.is_(None)
    ).first()
    
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task"
        )
    return True

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
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has access to this task
    check_task_access(task, current_user, db)
    
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
        owner=UserOut.model_validate(task.owner),
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignees=[UserOut.model_validate(user) for user in assignees]
    )

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user is the owner
    check_task_owner(task, current_user)
    
    # Update fields if provided
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.due_date is not None:
        task.due_date = task_update.due_date
    if task_update.status is not None:
        task.status = task_update.status
    
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    
    return task

@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int,
    task_status_update: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user is the owner or assignee
    check_task_access(task, current_user, db)
    
    # Update status
    task.status = task_status_update.status
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return TaskOut.model_validate(task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user is the owner
    check_task_owner(task, current_user)
    
    # Soft delete
    task.deleted_at = datetime.now(timezone.utc)
    db.commit()
    
    return None

@router.post("/{task_id}/assignees", response_model=TaskDetailOut)
def assign_users_to_task(
    task_id: int,
    assignee_data: TaskAssigneeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user is the owner
    check_task_owner(task, current_user)
    
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
    
    # Add new assignees
    for user_id in user_ids:
        if user_id not in existing_user_ids:
            new_assignee = TaskAssignee(
                task_id=task.id,
                user_id=user_id
            )
            db.add(new_assignee)
    
    db.commit()
    
    # Get updated assignees for response
    assignees = db.query(User).join(
        TaskAssignee, User.id == TaskAssignee.user_id
    ).filter(
        TaskAssignee.task_id == task.id,
        TaskAssignee.deleted_at.is_(None)
    ).all()

    print(task.assignees)
    
    # Create response with assignees
    return TaskDetailOut(
        id=task.id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        owner=UserOut.model_validate(task.owner),
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignees=[UserOut.model_validate(user) for user in assignees]
    )

@router.delete("/{task_id}/assignees/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assignee_from_task(
    task_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user is the owner
    check_task_owner(task, current_user)
    
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

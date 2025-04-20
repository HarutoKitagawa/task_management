from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

from src.backend.consts import TaskStatus, TaskEventType

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    tasks = relationship("Task", back_populates="owner", foreign_keys="Task.owner_id")
    assigned_tasks = relationship("TaskAssignee", back_populates="user", foreign_keys="TaskAssignee.user_id")
    task_events = relationship("TaskEvent", back_populates="actor", foreign_keys="TaskEvent.actor_id")
    notifications = relationship("Notification", back_populates="user", foreign_keys="Notification.user_id")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="tasks", foreign_keys=[owner_id])
    assignees = relationship("TaskAssignee", back_populates="task", foreign_keys="TaskAssignee.task_id")
    events = relationship("TaskEvent", back_populates="task", foreign_keys="TaskEvent.task_id")

class TaskAssignee(Base):
    __tablename__ = "task_assignees"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    task = relationship("Task", back_populates="assignees", foreign_keys=[task_id])
    user = relationship("User", back_populates="assigned_tasks", foreign_keys=[user_id])

class TaskEvent(Base):
    __tablename__ = "task_events"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(Enum(TaskEventType), nullable=False)
    payload = Column(JSON, nullable=False)
    message = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    task = relationship("Task", back_populates="events", foreign_keys=[task_id])
    actor = relationship("User", back_populates="task_events", foreign_keys=[actor_id])
    notifications = relationship("Notification", back_populates="task_event", foreign_keys="Notification.task_event_id")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_event_id = Column(Integer, ForeignKey("task_events.id"), nullable=False)
    message = Column(String(255), nullable=False)
    is_read = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="notifications", foreign_keys=[user_id])
    task_event = relationship("TaskEvent", back_populates="notifications", foreign_keys=[task_event_id])
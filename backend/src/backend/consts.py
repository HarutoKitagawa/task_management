import enum

class TaskStatus(enum.StrEnum):
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'

class TaskEventType(enum.StrEnum):
    TASK_ASSIGNED = 'TASK_ASSIGNED'
    TASK_STATUS_UPDATED = 'TASK_STATUS_UPDATED'
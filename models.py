"""
Data models for the Task Scheduler application.
Defines the structure of Task objects and related data.
"""

from dataclasses import dataclass, field
from typing import List, Set
from enum import Enum
from datetime import datetime


class TaskStatus(Enum):
    """Enumeration for task execution status."""
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


@dataclass
class Task:
    """
    Represents a single task in the scheduler.
    
    Attributes:
        id: Unique identifier for the task
        name: Human-readable task name
        description: Optional task description
        dependencies: List of task IDs that must complete before this task
        priority: Priority level (1-10, higher = more important)
        status: Current execution status
        created_at: Timestamp of task creation
    """
    id: str
    name: str
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    priority: int = 5
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    
    def __hash__(self):
        """Make Task hashable for use in sets."""
        return hash(self.id)
    
    def __eq__(self, other):
        """Compare tasks by ID."""
        if isinstance(other, Task):
            return self.id == other.id
        return False
    
    def to_dict(self) -> dict:
        """Convert task to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'dependencies': self.dependencies,
            'priority': self.priority,
            'status': self.status.value,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ExecutionPlan:
    """
    Represents a generated execution plan.
    
    Attributes:
        execution_order: List of task IDs in execution order
        is_valid: Whether the plan is valid (no cycles)
        error_message: Error message if plan is invalid
        tasks: Dictionary of all tasks in the plan
    """
    execution_order: List[str] = field(default_factory=list)
    is_valid: bool = True
    error_message: str = ""
    tasks: dict = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def add_error(self, message: str):
        """Mark plan as invalid with error message."""
        self.is_valid = False
        self.error_message = message

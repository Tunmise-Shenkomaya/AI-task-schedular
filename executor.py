"""
Task execution simulation module.
Handles autonomous execution of tasks and status updates.
"""

import threading
import time
from typing import List, Optional
from models import Task, TaskStatus


class TaskExecutor:
    """
    Simulates autonomous task execution.
    Executes tasks in planned order and manages status updates.
    """
    
    def __init__(self, tasks: List[Task]):
        """
        Initialize the executor.
        
        Args:
            tasks: List of Task objects in execution order
        """
        self.tasks = tasks
        self.stop_flag = False
        self.pause_flag = False
        self.execution_thread: Optional[threading.Thread] = None
    
    def execute_task(self, task: Task):
        """
        Execute a single task with status simulation.
        
        Args:
            task: Task to execute
        """
        if self.stop_flag:
            return
        
        # Set to RUNNING
        task.status = TaskStatus.RUNNING
        
        # Simulate execution time (1.5 seconds per task)
        time.sleep(1.5)
        
        if not self.stop_flag:
            # Set to COMPLETED
            task.status = TaskStatus.COMPLETED
    
    def pause_execution(self):
        """Pause task execution."""
        self.pause_flag = True
    
    def resume_execution(self):
        """Resume paused task execution."""
        self.pause_flag = False
    
    def stop_execution(self):
        """Stop task execution."""
        self.stop_flag = True
        
        # Reset all running tasks to pending
        for task in self.tasks:
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.PENDING

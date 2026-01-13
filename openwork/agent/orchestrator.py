"""Task orchestrator for managing multiple agent tasks."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A task to be executed by the agent."""
    id: str
    description: str
    allowed_paths: list[str]
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TaskOrchestrator:
    """
    Manages task queue and execution.
    
    Features:
    - Task queue management
    - Concurrent task execution
    - Task history tracking
    """
    
    def __init__(self, max_concurrent_tasks: int = 1):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: dict[str, Task] = {}
        self.task_queue: asyncio.Queue[str] = asyncio.Queue()
        self._running = False
        self._worker_task: asyncio.Task | None = None
        self._agent_loop = None
    
    def set_agent_loop(self, agent_loop: Any) -> None:
        """Set the agent loop to use for task execution."""
        self._agent_loop = agent_loop
    
    def create_task(self, description: str, allowed_paths: list[str]) -> Task:
        """Create a new task and add it to the queue."""
        task_id = str(uuid4())
        task = Task(
            id=task_id,
            description=description,
            allowed_paths=allowed_paths,
        )
        self.tasks[task_id] = task
        return task
    
    async def submit_task(self, task: Task) -> None:
        """Submit a task for execution."""
        await self.task_queue.put(task.id)
    
    async def start(self) -> None:
        """Start the task worker."""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
    
    async def stop(self) -> None:
        """Stop the task worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
    
    async def _worker(self) -> None:
        """Worker that processes tasks from the queue."""
        while self._running:
            try:
                task_id = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                await self._execute_task(task_id)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
    
    async def _execute_task(self, task_id: str) -> None:
        """Execute a single task."""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            if self._agent_loop:
                result = await self._agent_loop.run(
                    task.description,
                    task.allowed_paths,
                )
                task.result = result
                task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                if not result.success:
                    task.error = result.error
            else:
                task.status = TaskStatus.FAILED
                task.error = "No agent loop configured"
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
        finally:
            task.completed_at = datetime.now()
    
    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> list[Task]:
        """Get all tasks."""
        return list(self.tasks.values())
    
    def get_pending_tasks(self) -> list[Task]:
        """Get all pending tasks."""
        return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            return True
        return False

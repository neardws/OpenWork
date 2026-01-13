"""
Subagent system for parallel task execution.

Subagents allow:
- Parallel execution of independent tasks
- Isolated context per subagent
- Result aggregation back to main agent
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from openwork.agent.loop import AgentLoop, AgentResult


class SubagentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SubagentTask:
    """A task for a subagent to execute."""
    id: str
    description: str
    allowed_paths: list[str]
    parent_context: dict[str, Any] = field(default_factory=dict)
    status: SubagentStatus = SubagentStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


@dataclass
class SubagentResult:
    """Result from subagent execution."""
    task_id: str
    success: bool
    output: Any
    summary: str
    error: str | None = None


class SubagentManager:
    """
    Manages subagent spawning and coordination.
    
    Features:
    - Spawn multiple subagents in parallel
    - Each subagent has isolated context
    - Results are summarized and returned to parent
    """
    
    def __init__(
        self,
        agent_loop: AgentLoop,
        max_concurrent: int = 5,
        max_subagent_iterations: int = 10,
    ):
        self.agent_loop = agent_loop
        self.max_concurrent = max_concurrent
        self.max_subagent_iterations = max_subagent_iterations
        self.tasks: dict[str, SubagentTask] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    def create_task(
        self,
        description: str,
        allowed_paths: list[str],
        parent_context: dict[str, Any] | None = None,
    ) -> SubagentTask:
        """Create a new subagent task."""
        task = SubagentTask(
            id=str(uuid4()),
            description=description,
            allowed_paths=allowed_paths,
            parent_context=parent_context or {},
        )
        self.tasks[task.id] = task
        return task
    
    async def execute_task(self, task: SubagentTask) -> SubagentResult:
        """Execute a single subagent task."""
        async with self._semaphore:
            task.status = SubagentStatus.RUNNING
            
            try:
                from openwork.agent.loop import AgentLoop
                
                subagent = AgentLoop(
                    llm=self.agent_loop.llm,
                    tools=list(self.agent_loop.tools.values()),
                    max_iterations=self.max_subagent_iterations,
                    verbose=self.agent_loop.verbose,
                )
                
                result = await subagent.run(
                    task=task.description,
                    allowed_paths=task.allowed_paths,
                )
                
                task.status = SubagentStatus.COMPLETED if result.success else SubagentStatus.FAILED
                task.result = result
                task.completed_at = datetime.now()
                task.error = result.error
                
                return SubagentResult(
                    task_id=task.id,
                    success=result.success,
                    output=result.output,
                    summary=self._summarize_result(result),
                    error=result.error,
                )
                
            except Exception as e:
                task.status = SubagentStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                
                return SubagentResult(
                    task_id=task.id,
                    success=False,
                    output=None,
                    summary=f"Subagent failed: {e}",
                    error=str(e),
                )
    
    async def execute_parallel(
        self,
        tasks: list[SubagentTask],
    ) -> list[SubagentResult]:
        """Execute multiple subagent tasks in parallel."""
        coroutines = [self.execute_task(task) for task in tasks]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(SubagentResult(
                    task_id=tasks[i].id,
                    success=False,
                    output=None,
                    summary=f"Exception: {result}",
                    error=str(result),
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def spawn_and_wait(
        self,
        subtasks: list[dict[str, Any]],
        allowed_paths: list[str],
    ) -> list[SubagentResult]:
        """
        Spawn subagents for a list of subtasks and wait for completion.
        
        Args:
            subtasks: List of dicts with 'description' key
            allowed_paths: Paths subagents can access
            
        Returns:
            List of SubagentResults
        """
        tasks = [
            self.create_task(
                description=st["description"],
                allowed_paths=allowed_paths,
                parent_context=st.get("context", {}),
            )
            for st in subtasks
        ]
        
        return await self.execute_parallel(tasks)
    
    def _summarize_result(self, result: AgentResult) -> str:
        """Create a brief summary of agent result."""
        if result.success:
            output = str(result.output)
            if len(output) > 500:
                output = output[:500] + "..."
            return f"Completed: {output}"
        else:
            return f"Failed: {result.error}"
    
    def get_task(self, task_id: str) -> SubagentTask | None:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> list[SubagentTask]:
        """Get all tasks."""
        return list(self.tasks.values())
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self.tasks.get(task_id)
        if task and task.status == SubagentStatus.PENDING:
            task.status = SubagentStatus.CANCELLED
            return True
        return False


class SubagentTool:
    """
    Tool that allows the agent to spawn subagents.
    
    This enables the agent to delegate subtasks to parallel workers.
    """
    
    name = "spawn_subagent"
    description = "Spawn subagents to work on subtasks in parallel. Use for independent tasks that can run concurrently."
    requires_path_check = False
    parameters = {
        "type": "object",
        "properties": {
            "subtasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Description of the subtask"
                        }
                    },
                    "required": ["description"]
                },
                "description": "List of subtasks to execute in parallel"
            }
        },
        "required": ["subtasks"]
    }
    
    def __init__(self, manager: SubagentManager, allowed_paths: list[str]):
        self.manager = manager
        self.allowed_paths = allowed_paths
    
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute subagent spawning."""
        from openwork.tools.base import ToolResult
        
        subtasks = kwargs.get("subtasks", [])
        
        if not subtasks:
            return ToolResult(
                success=False,
                output=None,
                error="No subtasks provided"
            )
        
        if len(subtasks) > 10:
            return ToolResult(
                success=False,
                output=None,
                error="Maximum 10 subtasks allowed"
            )
        
        results = await self.manager.spawn_and_wait(
            subtasks=subtasks,
            allowed_paths=self.allowed_paths,
        )
        
        success_count = sum(1 for r in results if r.success)
        
        return ToolResult(
            success=success_count > 0,
            output={
                "total": len(results),
                "successful": success_count,
                "failed": len(results) - success_count,
                "results": [
                    {
                        "task_id": r.task_id,
                        "success": r.success,
                        "summary": r.summary,
                    }
                    for r in results
                ]
            },
            metadata={"subtask_count": len(subtasks)}
        )
    
    def to_schema(self) -> dict[str, Any]:
        """Convert to LLM function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

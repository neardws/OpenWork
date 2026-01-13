"""
Agent Loop - Core execution loop for OpenWork.

Implements the agent loop pattern:
Gather Context -> Take Action -> Verify Work -> Repeat
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

from openwork.agent.context import Context, MessageRole, Observation

if TYPE_CHECKING:
    from openwork.llm.base import BaseLLM
    from openwork.tools.base import BaseTool, ToolResult


class AgentState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class AgentDecision:
    """Decision made by the LLM."""
    thought: str
    tool_name: str | None = None
    tool_params: dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False
    final_answer: str | None = None
    needs_verification: bool = False


@dataclass
class AgentResult:
    """Result of agent execution."""
    success: bool
    output: str
    observations: list[Observation] = field(default_factory=list)
    error: str | None = None
    iterations: int = 0


class AgentLoop:
    """
    Core agent loop implementation.
    
    The agent loop follows this pattern:
    1. Gather Context - Collect relevant information
    2. Take Action - Execute tool operations  
    3. Verify Work - Validate results
    4. Repeat or Complete
    """
    
    SYSTEM_PROMPT = """You are OpenWork, an AI assistant that helps users automate tasks with their local files.

You have access to tools for:
- Reading and writing files
- Executing bash commands
- Searching file contents
- Making web requests

When given a task:
1. Think about what information you need
2. Use appropriate tools to gather information and take action
3. Verify your work produces correct results
4. Report back to the user

Always operate only within the allowed directories the user has granted access to.
Be careful with file operations - verify paths before modifying files.

Available tools:
{tools}

Respond in this JSON format:
{{
    "thought": "your reasoning about what to do next",
    "tool": "tool_name" or null if no tool needed,
    "params": {{}},  // tool parameters if using a tool
    "is_complete": false,  // true when task is done
    "answer": "final answer to user" or null
}}
"""
    
    def __init__(
        self,
        llm: BaseLLM,
        tools: list[BaseTool],
        max_iterations: int = 20,
        verbose: bool = False,
    ):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.state = AgentState.IDLE
        self._callbacks: list[callable] = []
    
    def add_callback(self, callback: callable) -> None:
        """Add a callback for state changes."""
        self._callbacks.append(callback)
    
    async def _notify_callbacks(self, event: str, data: Any = None) -> None:
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event, data)
                else:
                    callback(event, data)
            except Exception:
                pass
    
    def _get_tools_description(self) -> str:
        """Get formatted description of available tools."""
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(f"- {name}: {tool.description}")
        return "\n".join(descriptions)
    
    async def run(self, task: str, allowed_paths: list[str] | None = None) -> AgentResult:
        """
        Run the agent loop for a given task.
        
        Args:
            task: The task description from the user
            allowed_paths: List of paths the agent is allowed to access
            
        Returns:
            AgentResult with the outcome of the task
        """
        from pathlib import Path
        
        context = Context(
            task=task,
            allowed_paths=[Path(p).resolve() for p in (allowed_paths or [])],
        )
        
        system_prompt = self.SYSTEM_PROMPT.format(tools=self._get_tools_description())
        context.add_message(MessageRole.SYSTEM, system_prompt)
        
        iterations = 0
        
        try:
            while iterations < self.max_iterations:
                iterations += 1
                self.state = AgentState.THINKING
                await self._notify_callbacks("thinking", {"iteration": iterations})
                
                decision = await self._get_decision(context)
                
                if self.verbose:
                    print(f"[Iteration {iterations}] Thought: {decision.thought}")
                
                if decision.is_complete:
                    self.state = AgentState.COMPLETE
                    await self._notify_callbacks("complete", {"answer": decision.final_answer})
                    return AgentResult(
                        success=True,
                        output=decision.final_answer or "Task completed.",
                        observations=context.observations,
                        iterations=iterations,
                    )
                
                if decision.tool_name:
                    self.state = AgentState.EXECUTING
                    await self._notify_callbacks("executing", {
                        "tool": decision.tool_name,
                        "params": decision.tool_params
                    })
                    
                    result = await self._execute_tool(
                        decision.tool_name,
                        decision.tool_params,
                        context,
                    )
                    
                    observation = Observation(
                        tool_name=decision.tool_name,
                        input_params=decision.tool_params,
                        output=result.output if result.success else None,
                        success=result.success,
                        error=result.error,
                    )
                    context.add_observation(observation)
                    
                    if self.verbose:
                        status = "Success" if result.success else f"Error: {result.error}"
                        print(f"[Tool: {decision.tool_name}] {status}")
            
            self.state = AgentState.ERROR
            return AgentResult(
                success=False,
                output="",
                observations=context.observations,
                error=f"Max iterations ({self.max_iterations}) reached",
                iterations=iterations,
            )
            
        except Exception as e:
            self.state = AgentState.ERROR
            await self._notify_callbacks("error", {"error": str(e)})
            return AgentResult(
                success=False,
                output="",
                observations=context.observations,
                error=str(e),
                iterations=iterations,
            )
    
    async def _get_decision(self, context: Context) -> AgentDecision:
        """Get the next decision from the LLM."""
        import json
        
        messages = context.get_messages_for_llm()
        response = await self.llm.generate(messages)
        
        try:
            data = json.loads(response)
            return AgentDecision(
                thought=data.get("thought", ""),
                tool_name=data.get("tool"),
                tool_params=data.get("params", {}),
                is_complete=data.get("is_complete", False),
                final_answer=data.get("answer"),
            )
        except json.JSONDecodeError:
            return AgentDecision(
                thought=response,
                is_complete=True,
                final_answer=response,
            )
    
    async def _execute_tool(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: Context,
    ) -> ToolResult:
        """Execute a tool with the given parameters."""
        from openwork.tools.base import ToolResult
        
        if tool_name not in self.tools:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unknown tool: {tool_name}",
            )
        
        tool = self.tools[tool_name]
        
        if hasattr(tool, 'requires_path_check') and tool.requires_path_check:
            path = params.get('path') or params.get('file_path')
            if path:
                from pathlib import Path
                if not context.is_path_allowed(Path(path)):
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Path not allowed: {path}",
                    )
        
        try:
            return await tool.execute(**params)
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
            )

"""Context management for agent execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from pathlib import Path


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A single message in the conversation history."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Observation:
    """An observation from tool execution."""
    tool_name: str
    input_params: dict[str, Any]
    output: Any
    success: bool
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Context:
    """
    Context for agent execution.
    
    Manages:
    - Conversation history
    - Tool observations
    - Allowed paths for file operations
    - Task state
    """
    task: str
    allowed_paths: list[Path] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    max_history_length: int = 50
    
    def __post_init__(self) -> None:
        if self.task:
            self.add_message(MessageRole.USER, self.task)
    
    def add_message(self, role: MessageRole, content: str, **metadata: Any) -> None:
        """Add a message to the conversation history."""
        self.messages.append(Message(
            role=role,
            content=content,
            metadata=metadata
        ))
        self._trim_history()
    
    def add_observation(self, observation: Observation) -> None:
        """Add a tool observation."""
        self.observations.append(observation)
        tool_message = f"Tool: {observation.tool_name}\n"
        if observation.success:
            tool_message += f"Output: {observation.output}"
        else:
            tool_message += f"Error: {observation.error}"
        self.add_message(MessageRole.TOOL, tool_message, tool_name=observation.tool_name)
    
    def is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed paths."""
        path = path.resolve()
        return any(
            path == allowed or allowed in path.parents
            for allowed in self.allowed_paths
        )
    
    def get_messages_for_llm(self) -> list[dict[str, str]]:
        """Get messages formatted for LLM API."""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ]
    
    def _trim_history(self) -> None:
        """Trim conversation history if it exceeds max length."""
        if len(self.messages) > self.max_history_length:
            system_messages = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            recent_messages = self.messages[-self.max_history_length + len(system_messages):]
            self.messages = system_messages + recent_messages
    
    def get_summary(self) -> str:
        """Get a summary of the current context state."""
        return (
            f"Task: {self.task}\n"
            f"Messages: {len(self.messages)}\n"
            f"Observations: {len(self.observations)}\n"
            f"Allowed paths: {[str(p) for p in self.allowed_paths]}"
        )

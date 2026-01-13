"""Base tool class and tool result."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    output: Any
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BaseTool(ABC):
    """
    Base class for all tools.
    
    Subclasses must implement:
    - name: Tool identifier
    - description: Human-readable description
    - parameters: JSON schema for parameters
    - execute: Async execution method
    """
    
    name: str
    description: str
    parameters: dict[str, Any]
    requires_path_check: bool = False
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with success status and output
        """
        pass
    
    def to_schema(self) -> dict[str, Any]:
        """Convert tool to LLM function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }
    
    def validate_params(self, **kwargs: Any) -> tuple[bool, str | None]:
        """
        Validate parameters against schema.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        required = self.parameters.get("required", [])
        for param in required:
            if param not in kwargs:
                return False, f"Missing required parameter: {param}"
        return True, None

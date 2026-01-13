"""Base LLM interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    usage: dict[str, int] | None = None
    raw_response: Any = None


class BaseLLM(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    async def generate_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        Generate a response with tool calling support.
        
        Args:
            messages: List of message dicts
            tools: List of tool schemas
            **kwargs: Additional parameters
            
        Returns:
            Dict with 'content' and optionally 'tool_calls'
        """
        pass

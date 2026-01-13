"""LLM provider using litellm for unified model access."""

from __future__ import annotations

import os
from typing import Any

from openwork.llm.base import BaseLLM


class LLMProvider(BaseLLM):
    """
    LLM provider using litellm for unified access to multiple models.
    
    Supports:
    - OpenAI (gpt-4, gpt-4-turbo, gpt-3.5-turbo)
    - Anthropic (claude-3-opus, claude-3-sonnet, claude-3-haiku)
    - Google (gemini-pro, gemini-pro-vision)
    - Local models via Ollama (ollama/llama2, ollama/mistral)
    - And many more through litellm
    """
    
    MODEL_ALIASES = {
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4-turbo-preview",
        "gpt-3.5": "gpt-3.5-turbo",
        "claude-opus": "claude-3-opus-20240229",
        "claude-sonnet": "claude-3-sonnet-20240229",
        "claude-haiku": "claude-3-haiku-20240307",
        "gemini": "gemini/gemini-pro",
        "llama2": "ollama/llama2",
        "mistral": "ollama/mistral",
        "codellama": "ollama/codellama",
    }
    
    def __init__(
        self,
        model: str = "gpt-4",
        api_key: str | None = None,
        api_base: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.model = self.MODEL_ALIASES.get(model, model)
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if api_key:
            if "claude" in model.lower() or "anthropic" in model.lower():
                os.environ["ANTHROPIC_API_KEY"] = api_key
            elif "gemini" in model.lower():
                os.environ["GEMINI_API_KEY"] = api_key
            else:
                os.environ["OPENAI_API_KEY"] = api_key
    
    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any
    ) -> str:
        """Generate response using litellm."""
        try:
            import litellm
            
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                api_base=self.api_base,
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            raise ImportError("litellm is required. Install with: pip install litellm")
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}")
    
    async def generate_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        **kwargs: Any
    ) -> dict[str, Any]:
        """Generate response with tool calling support."""
        try:
            import litellm
            
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                api_base=self.api_base,
            )
            
            message = response.choices[0].message
            
            result = {
                "content": message.content or "",
            }
            
            if hasattr(message, "tool_calls") and message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                    for tc in message.tool_calls
                ]
            
            return result
            
        except ImportError:
            raise ImportError("litellm is required. Install with: pip install litellm")
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}")


def create_llm(
    model: str = "gpt-4",
    api_key: str | None = None,
    **kwargs: Any
) -> LLMProvider:
    """
    Create an LLM provider instance.
    
    Args:
        model: Model name or alias
        api_key: API key for the provider
        **kwargs: Additional configuration
        
    Returns:
        Configured LLMProvider instance
    """
    return LLMProvider(model=model, api_key=api_key, **kwargs)

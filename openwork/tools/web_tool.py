"""Web request tool for HTTP operations."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

import httpx

from openwork.tools.base import BaseTool, ToolResult


class WebTool(BaseTool):
    """
    Tool for making HTTP requests.
    
    Supports:
    - GET, POST, PUT, DELETE methods
    - JSON and text responses
    - Custom headers
    - Timeout configuration
    """
    
    name = "web"
    description = "Make HTTP requests to fetch web content or interact with APIs"
    requires_path_check = False
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to request"
            },
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                "description": "HTTP method (default: GET)",
                "default": "GET"
            },
            "headers": {
                "type": "object",
                "description": "HTTP headers to include"
            },
            "body": {
                "type": "string",
                "description": "Request body (for POST/PUT/PATCH)"
            },
            "json_body": {
                "type": "object",
                "description": "JSON request body (for POST/PUT/PATCH)"
            },
            "timeout": {
                "type": "integer",
                "description": "Request timeout in seconds (default: 30)",
                "default": 30
            }
        },
        "required": ["url"]
    }
    
    BLOCKED_DOMAINS = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
    ]
    
    def __init__(
        self,
        default_timeout: int = 30,
        max_response_size: int = 10 * 1024 * 1024,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
    ):
        self.default_timeout = default_timeout
        self.max_response_size = max_response_size
        self.allowed_domains = allowed_domains
        self.blocked_domains = blocked_domains or self.BLOCKED_DOMAINS
    
    def _is_url_allowed(self, url: str) -> tuple[bool, str | None]:
        """Check if URL is allowed."""
        try:
            parsed = urlparse(url)
            domain = parsed.hostname or ""
            
            if not parsed.scheme or parsed.scheme not in ["http", "https"]:
                return False, f"Invalid scheme: {parsed.scheme}"
            
            for blocked in self.blocked_domains:
                if domain == blocked or domain.endswith(f".{blocked}"):
                    return False, f"Blocked domain: {domain}"
            
            if self.allowed_domains:
                allowed = any(
                    domain == d or domain.endswith(f".{d}")
                    for d in self.allowed_domains
                )
                if not allowed:
                    return False, f"Domain not in whitelist: {domain}"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid URL: {e}"
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute HTTP request."""
        url = kwargs.get("url")
        method = kwargs.get("method", "GET").upper()
        headers = kwargs.get("headers", {})
        body = kwargs.get("body")
        json_body = kwargs.get("json_body")
        timeout = kwargs.get("timeout", self.default_timeout)
        
        if not url:
            return ToolResult(
                success=False,
                output=None,
                error="url is required"
            )
        
        is_allowed, error = self._is_url_allowed(url)
        if not is_allowed:
            return ToolResult(
                success=False,
                output=None,
                error=error
            )
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                request_kwargs: dict[str, Any] = {
                    "method": method,
                    "url": url,
                    "headers": headers,
                }
                
                if json_body is not None:
                    request_kwargs["json"] = json_body
                elif body is not None:
                    request_kwargs["content"] = body
                
                response = await client.request(**request_kwargs)
                
                content_length = len(response.content)
                if content_length > self.max_response_size:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Response too large: {content_length} bytes"
                    )
                
                content_type = response.headers.get("content-type", "")
                
                if "application/json" in content_type:
                    try:
                        output = response.json()
                    except Exception:
                        output = response.text
                else:
                    output = response.text
                
                return ToolResult(
                    success=response.is_success,
                    output=output,
                    error=None if response.is_success else f"HTTP {response.status_code}",
                    metadata={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "content_type": content_type,
                        "content_length": content_length,
                    }
                )
                
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                output=None,
                error=f"Request timed out after {timeout} seconds"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )

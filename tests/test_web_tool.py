"""Tests for web tool."""

import pytest
from openwork.tools.web_tool import WebTool


class TestWebTool:
    """Tests for WebTool."""
    
    @pytest.mark.asyncio
    async def test_blocked_localhost(self):
        """Test that localhost requests are blocked."""
        tool = WebTool()
        
        result = await tool.execute(url="http://localhost:8080/test")
        assert not result.success
        assert "Blocked" in result.error
    
    @pytest.mark.asyncio
    async def test_blocked_internal_ip(self):
        """Test that internal IP requests are blocked."""
        tool = WebTool()
        
        result = await tool.execute(url="http://127.0.0.1/test")
        assert not result.success
        assert "Blocked" in result.error
    
    @pytest.mark.asyncio
    async def test_invalid_scheme(self):
        """Test that invalid URL schemes are rejected."""
        tool = WebTool()
        
        result = await tool.execute(url="ftp://example.com/file")
        assert not result.success
        assert "scheme" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_url_validation(self):
        """Test URL validation logic."""
        tool = WebTool()
        
        is_allowed, error = tool._is_url_allowed("https://api.example.com/data")
        assert is_allowed
        assert error is None
        
        is_allowed, error = tool._is_url_allowed("http://localhost/test")
        assert not is_allowed
        assert "Blocked" in error
    
    @pytest.mark.asyncio
    async def test_missing_url(self):
        """Test error when URL is missing."""
        tool = WebTool()
        
        result = await tool.execute(method="GET")
        assert not result.success
        assert "required" in result.error.lower()

"""Tests for code execution tool."""

import pytest
from openwork.tools.code_tool import CodeTool


class TestCodeTool:
    """Tests for CodeTool."""
    
    @pytest.mark.asyncio
    async def test_simple_code(self):
        """Test executing simple Python code."""
        tool = CodeTool()
        
        result = await tool.execute(code="print(2 + 2)")
        assert result.success
        assert "4" in result.output
    
    @pytest.mark.asyncio
    async def test_multiline_code(self):
        """Test executing multiline code."""
        tool = CodeTool()
        
        code = """
x = 10
y = 20
print(x + y)
"""
        result = await tool.execute(code=code)
        assert result.success
        assert "30" in result.output
    
    @pytest.mark.asyncio
    async def test_blocked_import_os(self):
        """Test that import os is blocked."""
        tool = CodeTool()
        
        result = await tool.execute(code="import os; print(os.getcwd())")
        assert not result.success
        assert "Blocked" in result.error
    
    @pytest.mark.asyncio
    async def test_blocked_subprocess(self):
        """Test that subprocess import is blocked."""
        tool = CodeTool()
        
        result = await tool.execute(code="import subprocess")
        assert not result.success
        assert "Blocked" in result.error
    
    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test code execution timeout."""
        tool = CodeTool()
        
        code = """
import time
time.sleep(10)
print("done")
"""
        result = await tool.execute(code=code, timeout=1)
        assert not result.success
        assert "timed out" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_syntax_error(self):
        """Test handling syntax errors."""
        tool = CodeTool()
        
        result = await tool.execute(code="print(")
        assert not result.success
    
    @pytest.mark.asyncio
    async def test_missing_code(self):
        """Test error when code is missing."""
        tool = CodeTool()
        
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower()

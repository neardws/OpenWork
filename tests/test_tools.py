"""Tests for tools module."""

import pytest
import tempfile
from pathlib import Path

from openwork.tools.file_tool import FileTool
from openwork.tools.bash_tool import BashTool
from openwork.tools.search_tool import SearchTool


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestFileTool:
    """Tests for FileTool."""
    
    @pytest.mark.asyncio
    async def test_write_and_read(self, temp_dir):
        """Test writing and reading a file."""
        tool = FileTool()
        file_path = temp_dir / "test.txt"
        content = "Hello, OpenWork!"
        
        write_result = await tool.execute(
            operation="write",
            path=str(file_path),
            content=content
        )
        assert write_result.success
        
        read_result = await tool.execute(
            operation="read",
            path=str(file_path)
        )
        assert read_result.success
        assert read_result.output == content
    
    @pytest.mark.asyncio
    async def test_list_directory(self, temp_dir):
        """Test listing directory contents."""
        tool = FileTool()
        
        (temp_dir / "file1.txt").write_text("test1")
        (temp_dir / "file2.txt").write_text("test2")
        (temp_dir / "subdir").mkdir()
        
        result = await tool.execute(
            operation="list",
            path=str(temp_dir)
        )
        assert result.success
        assert len(result.output) == 3
    
    @pytest.mark.asyncio
    async def test_exists(self, temp_dir):
        """Test checking if path exists."""
        tool = FileTool()
        
        result = await tool.execute(
            operation="exists",
            path=str(temp_dir)
        )
        assert result.success
        assert result.output["exists"] is True
        assert result.output["type"] == "directory"
        
        result = await tool.execute(
            operation="exists",
            path=str(temp_dir / "nonexistent")
        )
        assert result.success
        assert result.output["exists"] is False


class TestBashTool:
    """Tests for BashTool."""
    
    @pytest.mark.asyncio
    async def test_simple_command(self):
        """Test executing a simple command."""
        tool = BashTool()
        
        result = await tool.execute(command="echo 'Hello World'")
        assert result.success
        assert "Hello World" in result.output
    
    @pytest.mark.asyncio
    async def test_dangerous_command_blocked(self):
        """Test that dangerous commands are blocked."""
        tool = BashTool()
        
        result = await tool.execute(command="sudo rm -rf /")
        assert not result.success
        assert "Blocked" in result.error or "Dangerous" in result.error
    
    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test command timeout."""
        tool = BashTool()
        
        result = await tool.execute(
            command="sleep 10",
            timeout=1
        )
        assert not result.success
        assert "timed out" in result.error.lower()


class TestSearchTool:
    """Tests for SearchTool."""
    
    @pytest.mark.asyncio
    async def test_search_in_file(self, temp_dir):
        """Test searching for content in a file."""
        tool = SearchTool()
        
        file_path = temp_dir / "test.txt"
        file_path.write_text("line 1: hello\nline 2: world\nline 3: hello world")
        
        result = await tool.execute(
            pattern="hello",
            path=str(file_path)
        )
        assert result.success
        assert len(result.output) == 2
    
    @pytest.mark.asyncio
    async def test_search_recursive(self, temp_dir):
        """Test recursive directory search."""
        tool = SearchTool()
        
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        (temp_dir / "file1.txt").write_text("target text here")
        (subdir / "file2.txt").write_text("another target text")
        
        result = await tool.execute(
            pattern="target",
            path=str(temp_dir),
            recursive=True
        )
        assert result.success
        assert len(result.output) == 2

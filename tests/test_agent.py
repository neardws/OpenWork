"""Tests for agent module."""

import pytest
from pathlib import Path

from openwork.agent.context import Context, MessageRole, Observation
from openwork.sandbox.manager import SandboxManager, SandboxConfig


class TestContext:
    """Tests for Context class."""
    
    def test_create_context(self):
        """Test creating a context."""
        ctx = Context(task="Test task")
        assert ctx.task == "Test task"
        assert len(ctx.messages) == 1
        assert ctx.messages[0].role == MessageRole.USER
    
    def test_add_message(self):
        """Test adding messages to context."""
        ctx = Context(task="Test")
        ctx.add_message(MessageRole.ASSISTANT, "Response")
        
        assert len(ctx.messages) == 2
        assert ctx.messages[1].role == MessageRole.ASSISTANT
        assert ctx.messages[1].content == "Response"
    
    def test_add_observation(self):
        """Test adding observations."""
        ctx = Context(task="Test")
        obs = Observation(
            tool_name="test_tool",
            input_params={"key": "value"},
            output="result",
            success=True,
        )
        ctx.add_observation(obs)
        
        assert len(ctx.observations) == 1
        assert ctx.observations[0].tool_name == "test_tool"
    
    def test_path_allowed(self, tmp_path):
        """Test path validation."""
        ctx = Context(
            task="Test",
            allowed_paths=[tmp_path],
        )
        
        assert ctx.is_path_allowed(tmp_path)
        assert ctx.is_path_allowed(tmp_path / "subdir")
        assert not ctx.is_path_allowed(Path("/etc"))
    
    def test_get_messages_for_llm(self):
        """Test getting messages formatted for LLM."""
        ctx = Context(task="Test task")
        ctx.add_message(MessageRole.ASSISTANT, "Response")
        
        messages = ctx.get_messages_for_llm()
        
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
    
    def test_trim_history(self):
        """Test that history is trimmed when exceeding max length."""
        ctx = Context(task="Test", max_history_length=5)
        
        for i in range(10):
            ctx.add_message(MessageRole.ASSISTANT, f"Message {i}")
        
        assert len(ctx.messages) <= 5


class TestSandboxManager:
    """Tests for SandboxManager."""
    
    def test_add_allowed_path(self, tmp_path):
        """Test adding allowed paths."""
        manager = SandboxManager()
        manager.add_allowed_path(tmp_path)
        
        assert tmp_path.resolve() in manager.config.allowed_paths
    
    def test_is_path_allowed(self, tmp_path):
        """Test path checking."""
        manager = SandboxManager()
        manager.add_allowed_path(tmp_path)
        
        assert manager.is_path_allowed(tmp_path)
        assert manager.is_path_allowed(tmp_path / "subdir" / "file.txt")
        assert not manager.is_path_allowed(Path("/etc/passwd"))
    
    def test_extension_validation(self):
        """Test file extension validation."""
        manager = SandboxManager()
        
        assert manager.is_extension_allowed(Path("file.txt"))
        assert manager.is_extension_allowed(Path("script.py"))
        assert not manager.is_extension_allowed(Path("program.exe"))
    
    def test_validate_path(self, tmp_path):
        """Test full path validation."""
        manager = SandboxManager()
        manager.add_allowed_path(tmp_path)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        is_valid, error = manager.validate_path(test_file)
        assert is_valid
        assert error is None
        
        is_valid, error = manager.validate_path(Path("/etc/passwd"))
        assert not is_valid
        assert error is not None
    
    def test_get_status(self, tmp_path):
        """Test getting sandbox status."""
        manager = SandboxManager()
        manager.add_allowed_path(tmp_path)
        
        status = manager.get_status()
        
        assert "allowed_paths" in status
        assert str(tmp_path.resolve()) in status["allowed_paths"]
        assert "docker_available" in status

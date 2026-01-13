"""Bash command execution tool."""

from __future__ import annotations

import asyncio
import shlex
from typing import Any

from openwork.tools.base import BaseTool, ToolResult


class BashTool(BaseTool):
    """
    Tool for executing bash commands.
    
    Security features:
    - Command timeout
    - Working directory restriction
    - Configurable command whitelist/blacklist
    """
    
    name = "bash"
    description = "Execute bash commands. Use for file operations, searches, and system tasks."
    requires_path_check = True
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute"
            },
            "working_dir": {
                "type": "string",
                "description": "Working directory for the command (optional)"
            },
            "timeout": {
                "type": "integer",
                "description": "Command timeout in seconds (default: 60)",
                "default": 60
            }
        },
        "required": ["command"]
    }
    
    DANGEROUS_COMMANDS = [
        "rm -rf /",
        "rm -rf ~",
        "dd if=",
        "mkfs",
        ":(){ :|:& };:",
        "> /dev/sda",
        "chmod -R 777 /",
    ]
    
    BLOCKED_PATTERNS = [
        "sudo",
        "su ",
        "curl | bash",
        "wget | bash",
        "eval",
    ]
    
    def __init__(
        self,
        default_timeout: int = 60,
        max_output_length: int = 50000,
        allowed_commands: list[str] | None = None,
        blocked_commands: list[str] | None = None,
    ):
        self.default_timeout = default_timeout
        self.max_output_length = max_output_length
        self.allowed_commands = allowed_commands
        self.blocked_commands = blocked_commands or self.BLOCKED_PATTERNS
    
    def _is_command_safe(self, command: str) -> tuple[bool, str | None]:
        """Check if command is safe to execute."""
        command_lower = command.lower().strip()
        
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous in command_lower:
                return False, f"Dangerous command pattern detected: {dangerous}"
        
        for blocked in self.blocked_commands:
            if blocked.lower() in command_lower:
                return False, f"Blocked command pattern: {blocked}"
        
        if self.allowed_commands:
            cmd_parts = shlex.split(command)
            if cmd_parts and cmd_parts[0] not in self.allowed_commands:
                return False, f"Command not in whitelist: {cmd_parts[0]}"
        
        return True, None
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute bash command."""
        command = kwargs.get("command")
        working_dir = kwargs.get("working_dir")
        timeout = kwargs.get("timeout", self.default_timeout)
        
        if not command:
            return ToolResult(
                success=False,
                output=None,
                error="command is required"
            )
        
        is_safe, error = self._is_command_safe(command)
        if not is_safe:
            return ToolResult(
                success=False,
                output=None,
                error=error
            )
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Command timed out after {timeout} seconds"
                )
            
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            
            if len(stdout_str) > self.max_output_length:
                stdout_str = stdout_str[:self.max_output_length] + "\n... (truncated)"
            if len(stderr_str) > self.max_output_length:
                stderr_str = stderr_str[:self.max_output_length] + "\n... (truncated)"
            
            success = process.returncode == 0
            
            output = stdout_str
            if stderr_str and not success:
                output = f"stdout:\n{stdout_str}\nstderr:\n{stderr_str}"
            
            return ToolResult(
                success=success,
                output=output,
                error=stderr_str if not success else None,
                metadata={
                    "return_code": process.returncode,
                    "command": command,
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )

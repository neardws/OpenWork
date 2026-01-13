"""Code execution tool for running Python code safely."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any

from openwork.tools.base import BaseTool, ToolResult


class CodeTool(BaseTool):
    """
    Tool for executing Python code in an isolated environment.
    
    Features:
    - Isolated execution via subprocess
    - Timeout protection
    - Output capture
    - Optional working directory
    """
    
    name = "code"
    description = "Execute Python code to perform calculations, data processing, or generate outputs"
    requires_path_check = True
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute"
            },
            "working_dir": {
                "type": "string",
                "description": "Working directory for code execution"
            },
            "timeout": {
                "type": "integer",
                "description": "Execution timeout in seconds (default: 30)",
                "default": 30
            }
        },
        "required": ["code"]
    }
    
    BLOCKED_IMPORTS = [
        "os.system",
        "subprocess",
        "shutil.rmtree",
        "__import__",
        "exec",
        "eval",
        "compile",
        "open",  # restrict file access
    ]
    
    BLOCKED_PATTERNS = [
        "import os",
        "from os import",
        "import subprocess",
        "import shutil",
        "import sys",
        "__builtins__",
        "globals()",
        "locals()",
    ]
    
    def __init__(
        self,
        default_timeout: int = 30,
        max_output_length: int = 50000,
        allow_file_access: bool = False,
    ):
        self.default_timeout = default_timeout
        self.max_output_length = max_output_length
        self.allow_file_access = allow_file_access
    
    def _is_code_safe(self, code: str) -> tuple[bool, str | None]:
        """Check if code is safe to execute."""
        code_lower = code.lower()
        
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.lower() in code_lower:
                return False, f"Blocked pattern detected: {pattern}"
        
        return True, None
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute Python code."""
        code = kwargs.get("code")
        working_dir = kwargs.get("working_dir")
        timeout = kwargs.get("timeout", self.default_timeout)
        
        if not code:
            return ToolResult(
                success=False,
                output=None,
                error="code is required"
            )
        
        if not self.allow_file_access:
            is_safe, error = self._is_code_safe(code)
            if not is_safe:
                return ToolResult(
                    success=False,
                    output=None,
                    error=error
                )
        
        wrapper_code = f'''
import json
import sys
from io import StringIO

_stdout = StringIO()
_stderr = StringIO()
_old_stdout = sys.stdout
_old_stderr = sys.stderr
sys.stdout = _stdout
sys.stderr = _stderr

_result = None
_error = None

try:
{self._indent_code(code)}
except Exception as e:
    _error = str(e)

sys.stdout = _old_stdout
sys.stderr = _old_stderr

output = {{
    "stdout": _stdout.getvalue(),
    "stderr": _stderr.getvalue(),
    "error": _error,
}}
print(json.dumps(output))
'''
        
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                f.write(wrapper_code)
                temp_file = f.name
            
            try:
                process = await asyncio.create_subprocess_exec(
                    'python3', temp_file,
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
                        error=f"Code execution timed out after {timeout} seconds"
                    )
                
                if process.returncode != 0:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Process exited with code {process.returncode}: {stderr.decode()}"
                    )
                
                import json
                try:
                    result = json.loads(stdout.decode())
                except json.JSONDecodeError:
                    return ToolResult(
                        success=False,
                        output=stdout.decode()[:self.max_output_length],
                        error="Failed to parse execution result"
                    )
                
                if result.get("error"):
                    return ToolResult(
                        success=False,
                        output=result.get("stdout", ""),
                        error=result["error"]
                    )
                
                output = result.get("stdout", "")
                if len(output) > self.max_output_length:
                    output = output[:self.max_output_length] + "\n... (truncated)"
                
                return ToolResult(
                    success=True,
                    output=output,
                    metadata={
                        "stderr": result.get("stderr", ""),
                    }
                )
                
            finally:
                Path(temp_file).unlink(missing_ok=True)
                
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def _indent_code(self, code: str, spaces: int = 4) -> str:
        """Indent code for wrapper."""
        indent = " " * spaces
        lines = code.split("\n")
        return "\n".join(indent + line for line in lines)

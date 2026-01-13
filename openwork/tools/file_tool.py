"""File operations tool."""

from __future__ import annotations

import aiofiles
from pathlib import Path
from typing import Any

from openwork.tools.base import BaseTool, ToolResult


class FileTool(BaseTool):
    """
    Tool for file system operations.
    
    Supports:
    - read: Read file contents
    - write: Write content to file
    - list: List directory contents
    - exists: Check if path exists
    - mkdir: Create directory
    - delete: Delete file or directory
    """
    
    name = "file"
    description = "Perform file system operations: read, write, list, exists, mkdir, delete"
    requires_path_check = True
    parameters = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["read", "write", "list", "exists", "mkdir", "delete"],
                "description": "The file operation to perform"
            },
            "path": {
                "type": "string",
                "description": "The file or directory path"
            },
            "content": {
                "type": "string",
                "description": "Content to write (for write operation)"
            },
        },
        "required": ["operation", "path"]
    }
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute file operation."""
        operation = kwargs.get("operation")
        path_str = kwargs.get("path")
        content = kwargs.get("content")
        
        if not operation or not path_str:
            return ToolResult(
                success=False,
                output=None,
                error="operation and path are required"
            )
        
        path = Path(path_str).resolve()
        
        try:
            if operation == "read":
                return await self._read(path)
            elif operation == "write":
                return await self._write(path, content or "")
            elif operation == "list":
                return await self._list(path)
            elif operation == "exists":
                return await self._exists(path)
            elif operation == "mkdir":
                return await self._mkdir(path)
            elif operation == "delete":
                return await self._delete(path)
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Unknown operation: {operation}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    async def _read(self, path: Path) -> ToolResult:
        """Read file contents."""
        if not path.exists():
            return ToolResult(
                success=False,
                output=None,
                error=f"File not found: {path}"
            )
        
        if not path.is_file():
            return ToolResult(
                success=False,
                output=None,
                error=f"Not a file: {path}"
            )
        
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
        
        return ToolResult(
            success=True,
            output=content,
            metadata={"path": str(path), "size": len(content)}
        )
    
    async def _write(self, path: Path, content: str) -> ToolResult:
        """Write content to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)
        
        return ToolResult(
            success=True,
            output=f"Written {len(content)} bytes to {path}",
            metadata={"path": str(path), "size": len(content)}
        )
    
    async def _list(self, path: Path) -> ToolResult:
        """List directory contents."""
        if not path.exists():
            return ToolResult(
                success=False,
                output=None,
                error=f"Directory not found: {path}"
            )
        
        if not path.is_dir():
            return ToolResult(
                success=False,
                output=None,
                error=f"Not a directory: {path}"
            )
        
        entries = []
        for entry in path.iterdir():
            entry_type = "dir" if entry.is_dir() else "file"
            entries.append({
                "name": entry.name,
                "type": entry_type,
                "path": str(entry),
            })
        
        return ToolResult(
            success=True,
            output=entries,
            metadata={"path": str(path), "count": len(entries)}
        )
    
    async def _exists(self, path: Path) -> ToolResult:
        """Check if path exists."""
        exists = path.exists()
        path_type = None
        if exists:
            path_type = "directory" if path.is_dir() else "file"
        
        return ToolResult(
            success=True,
            output={"exists": exists, "type": path_type},
            metadata={"path": str(path)}
        )
    
    async def _mkdir(self, path: Path) -> ToolResult:
        """Create directory."""
        if path.exists():
            return ToolResult(
                success=True,
                output=f"Directory already exists: {path}",
                metadata={"path": str(path), "created": False}
            )
        
        path.mkdir(parents=True, exist_ok=True)
        
        return ToolResult(
            success=True,
            output=f"Created directory: {path}",
            metadata={"path": str(path), "created": True}
        )
    
    async def _delete(self, path: Path) -> ToolResult:
        """Delete file or directory."""
        if not path.exists():
            return ToolResult(
                success=False,
                output=None,
                error=f"Path not found: {path}"
            )
        
        if path.is_file():
            path.unlink()
            return ToolResult(
                success=True,
                output=f"Deleted file: {path}",
                metadata={"path": str(path), "type": "file"}
            )
        elif path.is_dir():
            import shutil
            shutil.rmtree(path)
            return ToolResult(
                success=True,
                output=f"Deleted directory: {path}",
                metadata={"path": str(path), "type": "directory"}
            )
        
        return ToolResult(
            success=False,
            output=None,
            error=f"Unknown path type: {path}"
        )

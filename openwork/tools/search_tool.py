"""Search tool for finding content in files."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from openwork.tools.base import BaseTool, ToolResult


class SearchTool(BaseTool):
    """
    Tool for searching file contents.
    
    Supports:
    - Text search with regex
    - Recursive directory search
    - File type filtering
    """
    
    name = "search"
    description = "Search for content in files. Supports regex patterns and file type filtering."
    requires_path_check = True
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Search pattern (supports regex)"
            },
            "path": {
                "type": "string",
                "description": "Directory or file to search in"
            },
            "recursive": {
                "type": "boolean",
                "description": "Search recursively in subdirectories",
                "default": True
            },
            "file_pattern": {
                "type": "string",
                "description": "File pattern to match (e.g., '*.py', '*.txt')",
                "default": "*"
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Case sensitive search",
                "default": False
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 100
            }
        },
        "required": ["pattern", "path"]
    }
    
    def __init__(self, max_file_size: int = 10 * 1024 * 1024):
        self.max_file_size = max_file_size
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute search operation."""
        pattern = kwargs.get("pattern")
        path_str = kwargs.get("path")
        recursive = kwargs.get("recursive", True)
        file_pattern = kwargs.get("file_pattern", "*")
        case_sensitive = kwargs.get("case_sensitive", False)
        max_results = kwargs.get("max_results", 100)
        
        if not pattern or not path_str:
            return ToolResult(
                success=False,
                output=None,
                error="pattern and path are required"
            )
        
        path = Path(path_str).resolve()
        
        if not path.exists():
            return ToolResult(
                success=False,
                output=None,
                error=f"Path not found: {path}"
            )
        
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
        except re.error as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid regex pattern: {e}"
            )
        
        results = []
        files_searched = 0
        
        try:
            if path.is_file():
                files_to_search = [path]
            else:
                if recursive:
                    files_to_search = list(path.rglob(file_pattern))
                else:
                    files_to_search = list(path.glob(file_pattern))
            
            for file_path in files_to_search:
                if len(results) >= max_results:
                    break
                
                if not file_path.is_file():
                    continue
                
                if file_path.stat().st_size > self.max_file_size:
                    continue
                
                files_searched += 1
                file_results = await self._search_file(file_path, regex, max_results - len(results))
                results.extend(file_results)
            
            return ToolResult(
                success=True,
                output=results,
                metadata={
                    "files_searched": files_searched,
                    "matches_found": len(results),
                    "truncated": len(results) >= max_results,
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    async def _search_file(
        self,
        file_path: Path,
        regex: re.Pattern,
        max_results: int
    ) -> list[dict[str, Any]]:
        """Search a single file for matches."""
        results = []
        
        try:
            content = await asyncio.to_thread(file_path.read_text, encoding="utf-8", errors="replace")
            
            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                if len(results) >= max_results:
                    break
                
                matches = list(regex.finditer(line))
                if matches:
                    results.append({
                        "file": str(file_path),
                        "line": line_num,
                        "content": line.strip()[:500],
                        "matches": len(matches),
                    })
        except Exception:
            pass
        
        return results

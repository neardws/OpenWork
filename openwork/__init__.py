"""
OpenWork - Open source AI agent for local file automation

Inspired by Claude Cowork, OpenWork provides:
- Multi-model support (Claude, OpenAI, Gemini, Ollama)
- Local file system automation
- Extensible tool system
- Friendly GUI interface
"""

__version__ = "0.1.0"

from openwork.agent.loop import AgentLoop
from openwork.agent.context import Context
from openwork.agent.subagent import SubagentManager
from openwork.tools.base import BaseTool, ToolResult
from openwork.tools.file_tool import FileTool
from openwork.tools.bash_tool import BashTool
from openwork.tools.search_tool import SearchTool
from openwork.tools.web_tool import WebTool
from openwork.tools.code_tool import CodeTool
from openwork.sandbox.manager import SandboxManager

__all__ = [
    "__version__",
    "AgentLoop",
    "Context",
    "SubagentManager",
    "BaseTool",
    "ToolResult",
    "FileTool",
    "BashTool",
    "SearchTool",
    "WebTool",
    "CodeTool",
    "SandboxManager",
]

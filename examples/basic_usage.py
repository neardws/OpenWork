"""
Basic usage example for OpenWork.

This example demonstrates:
1. Setting up the LLM provider
2. Creating an agent with tools
3. Running a simple task
"""

import asyncio
import os
from pathlib import Path

from openwork.llm.provider import LLMProvider
from openwork.agent.loop import AgentLoop
from openwork.tools.file_tool import FileTool
from openwork.tools.bash_tool import BashTool
from openwork.tools.search_tool import SearchTool


async def main():
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        return
    
    model = "gpt-4"  # or "claude-sonnet", "ollama/llama2", etc.
    llm = LLMProvider(model=model, api_key=api_key)
    
    tools = [
        FileTool(),
        BashTool(),
        SearchTool(),
    ]
    
    agent = AgentLoop(
        llm=llm,
        tools=tools,
        max_iterations=10,
        verbose=True
    )
    
    workspace = Path("./workspace")
    workspace.mkdir(exist_ok=True)
    
    task = "List all files in the workspace directory and create a summary.txt file"
    
    print(f"Running task: {task}")
    print(f"Allowed path: {workspace.resolve()}")
    print("-" * 50)
    
    result = await agent.run(
        task=task,
        allowed_paths=[str(workspace.resolve())]
    )
    
    print("-" * 50)
    if result.success:
        print(f"Success! Output:\n{result.output}")
    else:
        print(f"Failed: {result.error}")
    
    print(f"\nIterations: {result.iterations}")
    print(f"Observations: {len(result.observations)}")


if __name__ == "__main__":
    asyncio.run(main())

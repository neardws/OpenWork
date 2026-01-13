"""FastAPI application for OpenWork backend."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openwork.server.websocket import ConnectionManager


class TaskRequest(BaseModel):
    """Request model for creating a task."""
    task: str
    allowed_paths: list[str]
    model: str = "gpt-4"
    api_key: str | None = None


class TaskResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    status: str
    output: str | None = None
    error: str | None = None
    iterations: int = 0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


manager = ConnectionManager()
_agent_loop = None
_tasks: dict[str, dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="OpenWork API",
        description="Open source AI agent for local file automation",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        from openwork import __version__
        return HealthResponse(status="ok", version=__version__)
    
    @app.get("/models")
    async def list_models():
        """List available LLM models."""
        return {
            "models": [
                {"id": "gpt-4", "name": "GPT-4", "provider": "openai"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai"},
                {"id": "claude-sonnet", "name": "Claude Sonnet", "provider": "anthropic"},
                {"id": "claude-haiku", "name": "Claude Haiku", "provider": "anthropic"},
                {"id": "gemini", "name": "Gemini Pro", "provider": "google"},
                {"id": "ollama/llama2", "name": "Llama 2 (Local)", "provider": "ollama"},
                {"id": "ollama/mistral", "name": "Mistral (Local)", "provider": "ollama"},
            ]
        }
    
    @app.post("/tasks", response_model=TaskResponse)
    async def create_task(request: TaskRequest):
        """Create and execute a new task."""
        from uuid import uuid4
        from openwork.llm.provider import LLMProvider
        from openwork.agent.loop import AgentLoop
        from openwork.tools import FileTool, BashTool, SearchTool, WebTool, CodeTool
        
        if not request.api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        
        for path in request.allowed_paths:
            if not Path(path).exists():
                raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")
        
        task_id = str(uuid4())
        _tasks[task_id] = {
            "status": "running",
            "output": None,
            "error": None,
            "iterations": 0,
        }
        
        async def run_task():
            try:
                llm = LLMProvider(model=request.model, api_key=request.api_key)
                tools = [FileTool(), BashTool(), SearchTool(), WebTool(), CodeTool()]
                agent = AgentLoop(llm=llm, tools=tools, verbose=True)
                
                async def on_event(event: str, data: Any = None):
                    await manager.broadcast({
                        "task_id": task_id,
                        "event": event,
                        "data": data,
                    })
                
                agent.add_callback(on_event)
                
                result = await agent.run(
                    task=request.task,
                    allowed_paths=request.allowed_paths,
                )
                
                _tasks[task_id].update({
                    "status": "completed" if result.success else "failed",
                    "output": result.output,
                    "error": result.error,
                    "iterations": result.iterations,
                })
                
                await manager.broadcast({
                    "task_id": task_id,
                    "event": "finished",
                    "data": _tasks[task_id],
                })
                
            except Exception as e:
                _tasks[task_id].update({
                    "status": "failed",
                    "error": str(e),
                })
                await manager.broadcast({
                    "task_id": task_id,
                    "event": "error",
                    "data": {"error": str(e)},
                })
        
        asyncio.create_task(run_task())
        
        return TaskResponse(
            task_id=task_id,
            status="running",
        )
    
    @app.get("/tasks/{task_id}", response_model=TaskResponse)
    async def get_task(task_id: str):
        """Get task status by ID."""
        if task_id not in _tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = _tasks[task_id]
        return TaskResponse(
            task_id=task_id,
            status=task["status"],
            output=task.get("output"),
            error=task.get("error"),
            iterations=task.get("iterations", 0),
        )
    
    @app.get("/tasks")
    async def list_tasks():
        """List all tasks."""
        return {
            "tasks": [
                {
                    "task_id": tid,
                    "status": t["status"],
                }
                for tid, t in _tasks.items()
            ]
        }
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)
    
    return app


app = create_app()


def run_server(host: str = "127.0.0.1", port: int = 8765):
    """Run the FastAPI server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()

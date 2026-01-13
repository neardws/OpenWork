"""Command-line interface for OpenWork."""

import asyncio
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    raise ImportError("typer and rich are required. Install with: pip install typer rich")

app = typer.Typer(
    name="openwork",
    help="OpenWork - Open source AI agent for local file automation",
    add_completion=False,
)

console = Console()


@app.command()
def run(
    task: str = typer.Argument(..., help="Task to execute"),
    paths: list[str] = typer.Option(
        [],
        "--path",
        "-p",
        help="Allowed paths (can specify multiple)",
    ),
    model: str = typer.Option(
        "gpt-4",
        "--model",
        "-m",
        help="LLM model to use",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        envvar="OPENWORK_API_KEY",
        help="API key for LLM provider",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """Run an agent task."""
    from openwork.llm.provider import LLMProvider
    from openwork.agent.loop import AgentLoop
    from openwork.tools.file_tool import FileTool
    from openwork.tools.bash_tool import BashTool
    from openwork.tools.search_tool import SearchTool
    
    if not api_key:
        console.print("[red]Error: API key is required. Use --api-key or set OPENWORK_API_KEY[/red]")
        raise typer.Exit(1)
    
    if not paths:
        console.print("[yellow]Warning: No paths specified. Using current directory.[/yellow]")
        paths = [str(Path.cwd())]
    
    validated_paths = []
    for p in paths:
        path = Path(p).resolve()
        if not path.exists():
            console.print(f"[red]Error: Path does not exist: {path}[/red]")
            raise typer.Exit(1)
        validated_paths.append(str(path))
    
    console.print(Panel(f"[bold]Task:[/bold] {task}", title="OpenWork"))
    console.print(f"[dim]Model: {model}[/dim]")
    console.print(f"[dim]Allowed paths: {', '.join(validated_paths)}[/dim]")
    console.print()
    
    llm = LLMProvider(model=model, api_key=api_key)
    tools = [FileTool(), BashTool(), SearchTool()]
    agent = AgentLoop(llm=llm, tools=tools, verbose=verbose)
    
    async def execute():
        return await agent.run(task, validated_paths)
    
    with console.status("[bold green]Working on task..."):
        result = asyncio.run(execute())
    
    if result.success:
        console.print(Panel(result.output, title="[green]Success[/green]"))
    else:
        console.print(Panel(result.error or "Unknown error", title="[red]Failed[/red]"))
    
    if result.observations and verbose:
        console.print("\n[bold]Tool Executions:[/bold]")
        for obs in result.observations:
            status = "[green]✓[/green]" if obs.success else "[red]✗[/red]"
            console.print(f"  {status} {obs.tool_name}")


@app.command()
def ui():
    """Launch the Streamlit web interface."""
    import subprocess
    import sys
    
    ui_path = Path(__file__).parent / "ui" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(ui_path)])


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8765, "--port", "-p", help="Port to listen on"),
):
    """Start the API server for macOS app."""
    from openwork.server.app import run_server
    console.print(f"[green]Starting OpenWork API server on {host}:{port}[/green]")
    run_server(host=host, port=port)


@app.command()
def version():
    """Show version information."""
    from openwork import __version__
    console.print(f"OpenWork version {__version__}")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()

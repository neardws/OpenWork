# OpenWork

Open source AI agent for local file automation - inspired by Claude Cowork.

## Features

- **Multi-Model Support**: Works with OpenAI, Anthropic Claude, Google Gemini, and local models via Ollama
- **File Automation**: Read, write, organize, and manage files through natural language
- **Extensible Tools**: Built-in tools for file operations, bash commands, and content search
- **Safe Execution**: Path-based sandbox for secure file access
- **Friendly Interface**: CLI and Streamlit web UI

## Installation

```bash
pip install openwork
```

Or install from source:

```bash
git clone https://github.com/neardws/OpenWork.git
cd OpenWork
pip install -e ".[all]"
```

## Quick Start

### CLI Usage

```bash
# Set your API key
export OPENWORK_API_KEY="your-api-key"

# Run a task
openwork run "List all Python files and create a summary" -p ./my_project -m gpt-4
```

### Python API

```python
import asyncio
from openwork.llm.provider import LLMProvider
from openwork.agent.loop import AgentLoop
from openwork.tools import FileTool, BashTool, SearchTool

async def main():
    llm = LLMProvider(model="gpt-4", api_key="your-api-key")
    tools = [FileTool(), BashTool(), SearchTool()]
    agent = AgentLoop(llm=llm, tools=tools)
    
    result = await agent.run(
        task="Organize my downloads folder by file type",
        allowed_paths=["~/Downloads"]
    )
    print(result.output)

asyncio.run(main())
```

### Web UI

```bash
openwork ui
```

## Supported Models

| Provider  | Models                                         |
| --------- | ---------------------------------------------- |
| OpenAI    | gpt-4, gpt-4-turbo, gpt-3.5-turbo              |
| Anthropic | claude-3-opus, claude-3-sonnet, claude-3-haiku |
| Google    | gemini-pro                                     |
| Ollama    | llama2, mistral, codellama, etc.               |

## Architecture

OpenWork follows the Agent Loop pattern:

```
Gather Context → Take Action → Verify Work → Repeat
```

### Core Components

- **Agent Loop**: Orchestrates task execution with LLM decision making
- **Tools**: Modular actions (file, bash, search, web)
- **Sandbox**: Path-based access control for security
- **LLM Provider**: Unified interface via litellm

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check openwork/

# Type check
mypy openwork/
```

## Comparison with Claude Cowork

| Feature          | Claude Cowork  | OpenWork              |
| ---------------- | -------------- | --------------------- |
| Open Source      | No             | Yes                   |
| Model Support    | Claude only    | Multi-model           |
| Local Deployment | No             | Yes                   |
| Cost             | $100-200/month | Free (API costs only) |
| Extensibility    | Limited        | Plugin system         |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## Acknowledgments

Inspired by [Claude Cowork](https://claude.com/blog/cowork-research-preview) by Anthropic.

---

**Note**: This is an independent open source project and is not affiliated with Anthropic.

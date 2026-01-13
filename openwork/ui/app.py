"""
OpenWork Streamlit UI

Run with: streamlit run openwork/ui/app.py
"""

import asyncio
from pathlib import Path

try:
    import streamlit as st
except ImportError:
    raise ImportError("Streamlit is required for UI. Install with: pip install streamlit")


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "allowed_paths" not in st.session_state:
        st.session_state.allowed_paths = []
    if "task_history" not in st.session_state:
        st.session_state.task_history = []
    if "agent_loop" not in st.session_state:
        st.session_state.agent_loop = None
    if "llm_provider" not in st.session_state:
        st.session_state.llm_provider = None


def setup_sidebar():
    """Setup sidebar with configuration options."""
    st.sidebar.title("OpenWork Settings")
    
    st.sidebar.subheader("LLM Configuration")
    model = st.sidebar.selectbox(
        "Model",
        ["gpt-4", "gpt-3.5-turbo", "claude-sonnet", "claude-haiku", "ollama/llama2"],
        index=0
    )
    
    api_key = st.sidebar.text_input("API Key", type="password")
    
    st.sidebar.subheader("Allowed Folders")
    
    new_path = st.sidebar.text_input("Add folder path")
    if st.sidebar.button("Add Path") and new_path:
        path = Path(new_path).resolve()
        if path.exists() and path.is_dir():
            if str(path) not in st.session_state.allowed_paths:
                st.session_state.allowed_paths.append(str(path))
                st.sidebar.success(f"Added: {path}")
        else:
            st.sidebar.error("Invalid directory path")
    
    if st.session_state.allowed_paths:
        st.sidebar.write("Current paths:")
        for i, path in enumerate(st.session_state.allowed_paths):
            col1, col2 = st.sidebar.columns([3, 1])
            col1.text(path[:30] + "..." if len(path) > 30 else path)
            if col2.button("X", key=f"remove_{i}"):
                st.session_state.allowed_paths.pop(i)
                st.rerun()
    
    return model, api_key


def setup_agent(model: str, api_key: str):
    """Setup the agent with configuration."""
    if not api_key:
        return None
    
    from openwork.llm.provider import LLMProvider
    from openwork.agent.loop import AgentLoop
    from openwork.tools.file_tool import FileTool
    from openwork.tools.bash_tool import BashTool
    from openwork.tools.search_tool import SearchTool
    
    llm = LLMProvider(model=model, api_key=api_key)
    
    tools = [
        FileTool(),
        BashTool(),
        SearchTool(),
    ]
    
    agent = AgentLoop(llm=llm, tools=tools, verbose=True)
    
    return agent


async def run_agent_task(agent, task: str, allowed_paths: list[str]):
    """Run an agent task asynchronously."""
    result = await agent.run(task, allowed_paths)
    return result


def main():
    """Main UI entry point."""
    st.set_page_config(
        page_title="OpenWork - AI File Automation",
        page_icon="🤖",
        layout="wide"
    )
    
    init_session_state()
    model, api_key = setup_sidebar()
    
    st.title("OpenWork")
    st.caption("Open source AI agent for local file automation")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("What would you like me to do?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        if not api_key:
            with st.chat_message("assistant"):
                st.error("Please enter an API key in the sidebar.")
            return
        
        if not st.session_state.allowed_paths:
            with st.chat_message("assistant"):
                st.warning("Please add at least one allowed folder path in the sidebar.")
            return
        
        agent = setup_agent(model, api_key)
        
        with st.chat_message("assistant"):
            with st.spinner("Working on your task..."):
                try:
                    result = asyncio.run(
                        run_agent_task(
                            agent,
                            prompt,
                            st.session_state.allowed_paths
                        )
                    )
                    
                    if result.success:
                        st.success("Task completed!")
                        st.markdown(result.output)
                        response = result.output
                    else:
                        st.error(f"Task failed: {result.error}")
                        response = f"Error: {result.error}"
                    
                    if result.observations:
                        with st.expander("Tool Executions"):
                            for obs in result.observations:
                                status = "✅" if obs.success else "❌"
                                st.write(f"{status} **{obs.tool_name}**")
                                if obs.success:
                                    st.code(str(obs.output)[:500])
                                else:
                                    st.error(obs.error)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    response = f"Error: {str(e)}"
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })


if __name__ == "__main__":
    main()

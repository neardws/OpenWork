# OpenWork 实现计划

## 项目定位

OpenWork 是 Claude Cowork 的开源替代方案，提供:
- 多模型支持 (Claude, OpenAI, Gemini, 本地模型如 Ollama)
- 本地文件系统自动化
- 友好的 GUI 界面
- 可扩展的工具系统

## 技术栈选择

### 后端 (Python)
- **FastAPI** - Web API 框架
- **asyncio** - 异步执行
- **litellm** - 统一多模型接口
- **watchdog** - 文件系统监控

### 前端 (可选方案)
- **方案 A**: Streamlit (快速原型)
- **方案 B**: Gradio (AI 应用友好)
- **方案 C**: React + Electron (桌面应用)

### 核心依赖
- Python 3.10+
- Docker (沙箱隔离，可选)

## 架构设计

```
┌─────────────────────────────────────────────────────┐
│                   OpenWork GUI                       │
│  (Streamlit/Gradio/React)                           │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│               Agent Orchestrator                     │
│  - Task Queue                                        │
│  - Context Manager                                   │
│  - Agent Loop Controller                             │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│               Tool System                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  Bash   │ │  File   │ │  Web    │ │ Custom  │   │
│  │  Tool   │ │  Tool   │ │  Tool   │ │  Tools  │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              LLM Provider Layer                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Claude  │ │ OpenAI  │ │ Gemini  │ │ Ollama  │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
└─────────────────────────────────────────────────────┘
```

## 实现阶段

### Phase 1: 核心框架 (Week 1)
- [ ] 项目结构搭建
- [ ] Agent Loop 实现
- [ ] 基础 Tool 系统
- [ ] LLM 提供者抽象层

### Phase 2: 工具系统 (Week 2)
- [ ] File Tool (读/写/创建/删除)
- [ ] Bash Tool (命令执行)
- [ ] Search Tool (文件内容搜索)
- [ ] Web Tool (网络请求)

### Phase 3: GUI 界面 (Week 3)
- [ ] 任务输入界面
- [ ] 实时进度展示
- [ ] 文件夹授权管理
- [ ] 历史任务记录

### Phase 4: 高级功能 (Week 4)
- [ ] 子代理系统
- [ ] 上下文压缩
- [ ] 安全沙箱 (Docker)
- [ ] MCP 协议支持 (可选)

## 目录结构

```
openwork/
├── openwork/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── loop.py          # Agent Loop 核心
│   │   ├── context.py       # 上下文管理
│   │   └── orchestrator.py  # 任务编排
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py          # Tool 基类
│   │   ├── file_tool.py     # 文件操作
│   │   ├── bash_tool.py     # Bash 执行
│   │   ├── search_tool.py   # 搜索工具
│   │   └── web_tool.py      # Web 请求
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py          # LLM 基类
│   │   ├── provider.py      # 提供者管理
│   │   └── adapters/        # 各模型适配器
│   ├── sandbox/
│   │   ├── __init__.py
│   │   └── manager.py       # 沙箱管理
│   └── ui/
│       ├── __init__.py
│       └── app.py           # GUI 入口
├── tests/
├── examples/
├── pyproject.toml
├── README.md
└── LICENSE
```

## 核心 API 设计

### Agent Loop

```python
class AgentLoop:
    async def run(self, task: str, context: Context) -> Result:
        """
        Agent Loop 核心流程:
        1. Gather Context - 收集相关信息
        2. Take Action - 执行工具操作
        3. Verify Work - 验证结果
        4. Repeat or Complete
        """
        while not self.is_complete():
            # 1. 获取 LLM 决策
            decision = await self.llm.decide(task, context)
            
            # 2. 执行工具
            if decision.tool:
                result = await self.tools.execute(decision.tool)
                context.add_observation(result)
            
            # 3. 验证
            if decision.verify:
                verified = await self.verify(result)
                if not verified:
                    continue
            
            # 4. 检查完成
            if decision.complete:
                return self.finalize(context)
```

### Tool 基类

```python
class BaseTool(ABC):
    name: str
    description: str
    parameters: dict
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass
    
    def to_schema(self) -> dict:
        """转换为 LLM function calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
```

## 安全考量

1. **文件系统隔离**
   - 只允许访问用户明确授权的目录
   - 使用白名单机制

2. **命令执行限制**
   - Bash 命令白名单/黑名单
   - 超时机制
   - 资源限制

3. **Prompt Injection 防护**
   - 输入清理
   - 输出验证
   - 敏感操作确认

## 下一步行动

1. 创建项目基础结构
2. 实现 Agent Loop 核心
3. 实现基础 Tool 系统
4. 集成 litellm 多模型支持
5. 创建简单的 Streamlit UI

# Claude Cowork 调研发现

## 概述

Claude Cowork 是 Anthropic 于 2026 年 1 月 12 日发布的通用 AI Agent 工具，定位为 "Claude Code for the rest of your work"。它将 Claude Code 强大的代理能力从开发者扩展到普通用户。

## 核心功能

### 1. 文件系统操作
- 授予特定文件夹访问权限
- 读取、编辑、创建文件
- 智能文件管理和组织

### 2. 任务自动化
- 收据整理成报表
- 文件重命名和分类
- 文档生成和格式转换
- 媒体文件管理

### 3. Agent Loop (核心架构)
```
Gather Context → Take Action → Verify Work → Repeat
```

### 4. 安全沙箱
- 使用 Apple VZVirtualMachine 框架
- 文件系统容器化隔离
- 只能访问明确授权的文件夹

## 技术架构

### Agent SDK 核心组件
1. **Tools (工具)** - 主要操作原语
2. **Bash & Scripts** - 灵活的命令执行
3. **Code Generation** - 代码生成能力
4. **MCP (Model Context Protocol)** - 外部服务集成
5. **Subagents** - 子代理并行执行

### Context 管理
- Agentic Search (文件系统搜索)
- Semantic Search (语义搜索)
- Compaction (上下文压缩)

### 验证机制
- Rules-based feedback (规则验证)
- Visual feedback (视觉反馈)
- LLM as a judge (LLM 评判)

## 产品定位

| 特性 | Claude Code | Claude Cowork |
|------|-------------|---------------|
| 目标用户 | 开发者 | 所有用户 |
| 界面 | 终端 | GUI |
| 主要场景 | 编码 | 文件自动化 |
| 技术要求 | 需要编程知识 | 无需编程 |

## 竞品分析

1. **ChatGPT** - 对话为主，无本地执行能力
2. **Gemini** - 无本地文件系统访问
3. **Microsoft Copilot** - 不同范式，集成 Office
4. **OpenAI Codex/Agent** - 类似但功能有限

## 开源替代方案参考

### claude-flow (11.8k stars)
- 多代理编排平台
- 支持 swarm intelligence
- MCP 协议集成
- TypeScript/JavaScript 实现

### claude-agent-sdk-python (4.1k stars)
- Anthropic 官方 Python SDK
- 提供 Agent 基础能力
- 依赖 Claude Code CLI

## 关键洞察

1. **核心价值**: 给 AI 一台计算机，让它像人一样工作
2. **产品策略**: 观察用户行为 > 问用户意见
3. **技术基础**: 基于 Claude Code/Agent SDK
4. **安全考量**: 沙箱隔离 + prompt injection 防护

## OpenWork 实现方向

### 必须实现
- [ ] Agent Loop 核心循环
- [ ] 文件系统沙箱访问
- [ ] Tool 系统设计
- [ ] GUI 界面 (非终端)
- [ ] 多模型支持 (OpenAI, Claude, 本地模型)

### 可选增强
- [ ] 子代理系统
- [ ] MCP 协议支持
- [ ] 语义搜索
- [ ] 上下文压缩

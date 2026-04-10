# MyAgent 用户指南

## 概述

MyAgent 是一个基于 DeepAgents 框架的自动化代码生成系统，支持 workflow 驱动的多代理编排和人机协同。

## 快速开始

### 1. 安装

```bash
cd D:/python-projects/langchain/CASE-LangChain/Demo-01/myagent1
pip install -e .
```

### 2. 配置 LLM 提供者

MyAgent 支持三种 LLM 提供者：

#### Anthropic (默认)
```python
os.environ['MYAGENT_LLM_PROVIDER'] = 'anthropic'
os.environ['MYAGENT_LLM_MODEL'] = 'claude-sonnet-4-6'
os.environ['ANTHROPIC_API_KEY'] = 'your-api-key'
```

#### OpenAI
```python
os.environ['MYAGENT_LLM_PROVIDER'] = 'openai'
os.environ['MYAGENT_LLM_MODEL'] = 'gpt-4'
os.environ['OPENAI_API_KEY'] = 'your-api-key'
```

#### Ollama (本地模型)
```python
os.environ['MYAGENT_LLM_PROVIDER'] = 'ollama'
os.environ['MYAGENT_LLM_MODEL'] = 'llama2'
```

**启动 Ollama 服务：**
```bash
ollama serve
ollama pull llama2  # 或其他模型
```

### 3. 初始化项目

```bash
myagent init --name my-project
cd my-project
```

这会创建以下文件结构：
```
my-project/
├── workflow.md      # 工作流配置
├── agent.md         # 代理角色定义
├── PLANNING.md      # 规划文档 (待生成)
├── STATUS.md        # 项目状态
├── LOGS/            # 日志目录
└── src/             # 源码目录
```

## 工作流命令

### 生成规划

```bash
myagent run --phase plan
```

这会：
1. 解析 `workflow.md` 定义的工作流
2. 使用 LLM 生成 `PLANNING.md` 文档
3. 显示生成的规划内容

### 确认规划

```bash
myagent confirm --file PLANNING.md
```

在确认前，您可以编辑 `PLANNING.md` 修改规划内容。

### 执行规划

```bash
myagent run --phase execute
```

### 并行执行

```bash
myagent run --phase execute --parallel
```

### 恢复执行

```bash
myagent run --phase execute --resume
```

## 查看状态

### 项目状态

```bash
myagent status
```

### 实时监控

```bash
myagent status --live
```

### 查看日志

```bash
myagent logs --agent architect
myagent logs --agent backend-dev --follow
```

## 人机协同

### 跳过任务

```bash
myagent skip --task "Module Development"
```

### 回退任务

```bash
myagent rollback --task "Module Development"
```

### 批准危险操作

```bash
myagent approve --operation op-123
```

### 拒绝危险操作

```bash
myagent reject --operation op-123
```

## 配置文件

### workflow.md

定义项目的阶段、任务和依赖关系：

```markdown
## Phases

- [Phase 1] 需求分析 (depends: none)
  - Task: 架构设计 (owner: architect)

- [Phase 2] 开发 (depends: Phase 1)
  - Task: 后端开发 (parallel: true, owner: backend-dev)
  - Task: 前端开发 (parallel: true, owner: frontend-dev)

## Rules

- 每个阶段必须通过质量门禁 (Lint/Test)
```

### agent.md

定义代理角色和路由规则：

```markdown
## Roles

- architect: 架构设计、技术选型
- backend-dev: 后端开发、API 设计
- frontend-dev: 前端开发、UI 实现
- qa-engineer: 测试、质量保证

## Routing Rules

- 架构设计 -> architect (串行)
- 业务开发 -> backend-dev + frontend-dev (并行)
- 测试 -> qa-engineer (串行)
```

## 架构说明

```
workflow.md + agent.md
        ↓
   Main Agent (Supervisor)
        ↓
   PLANNING.md (人工确认)
        ↓
   Sub-Agent 调度 (并行/串行)
        ↓
   Quality Gates (Lint/Test)
        ↓
   STATUS.md + LOGS/
```

### 核心模块

| 模块 | 功能 |
|------|------|
| `workflow/` | 解析 workflow.md，构建 DAG |
| `planner/` | 生成 PLANNING.md |
| `agents/` | DeepAgents 多代理调度 |
| `executor/` | 任务执行、断点续跑 |
| `progress/` | 进度追踪、日志管理 |
| `hitl/` | 人机协同、确认门禁 |
| `quality/` | 质量门禁 (Lint/Test) |
| `vcs/` | Git 版本控制 |

## 故障排除

### Ollama 连接失败

1. 确保 Ollama 服务运行中：
   ```bash
   ollama serve
   ```

2. 检查模型已下载：
   ```bash
   ollama list
   ```

3. 测试连接：
   ```python
   from langchain_openai import ChatOpenAI
   llm = ChatOpenAI(
       model="llama2",
       openai_api_base="http://localhost:11434/v1",
       api_key="ollama",
   )
   ```

### API Key 未设置

如果环境变量未设置，MyAgent 会自动使用 mock 模式：
```
[Mock architect] Task completed
```

要使用真实 LLM，请设置相应的 API key 环境变量。

### 工作流解析错误

检查 `workflow.md` 格式：
- Phase 依赖必须使用正确的名称
- Task 必须指定 owner
- 避免循环依赖

## 开发指南

### 测试

```bash
pytest tests/ -v
```

### 代码检查

```bash
ruff check src/myagent/
```

### 运行示例

```bash
python test_flow.py
```
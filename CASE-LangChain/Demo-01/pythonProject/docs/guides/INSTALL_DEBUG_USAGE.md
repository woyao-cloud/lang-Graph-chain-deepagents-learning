# DeepAgents 安装与调试指南

**文档版本:** 1.0
**编制日期:** 2026-04-09

---

## 1. 安装

### 1.1 环境要求

| 要求 | 版本 |
|------|------|
| Python | >= 3.11 |
| pip | >= 21.0 |
| Git | 任意版本 |

### 1.2 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### 1.3 安装依赖

```bash
# 安装核心依赖
pip install click typer myagent langchain-openai langchain-core langgraph

# 安装开发依赖（用于测试）
pip install pytest pytest-cov

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 1.4 验证安装

```bash
# 检查 Python 版本
python --version
# 输出应类似: Python 3.11.x

# 验证 myagent 导入
python -c "from myagent import create_deep_agent; print('OK')"
```

---

## 2. 项目初始化

### 2.1 创建新项目

```bash
# 使用 myagent init 初始化项目
python -m myagent init --name my-project --dir ./my-project

# 或在当前目录初始化
python -m myagent init --name my-project
```

### 2.2 初始化的项目结构

```
my-project/
├── workflow.md      # 工作流配置
├── agent.md        # Agent 角色定义
├── PLANNING.md     # 规划文档（生成）
├── STATUS.md       # 状态报告（运行后生成）
├── LOGS/           # 日志目录
│   ├── workflow/
│   ├── agents/
│   └── quality/
└── src/            # 源代码目录
```

---

## 3. 使用方法

### 3.1 CLI 命令

```bash
# 查看帮助
python -m myagent --help

# 初始化项目
python -m myagent init --name <project-name>

# 运行工作流
python -m myagent run --phase plan       # 生成规划
python -m myagent run --phase execute     # 执行任务

# 确认规划
python -m myagent confirm --file PLANNING.md

# 查看状态
python -m myagent status                  # 查看状态
python -m myagent status --live           # 实时监控

# 查看日志
python -m myagent logs --agent architect  # 查看指定 Agent 日志
python -m myagent logs --agent backend-dev --follow

# 人工干预
python -m myagent skip --task <task-name>        # 跳过任务
python -m myagent rollback --task <task-name>    # 回退任务
python -m myagent approve --operation <op-id>    # 批准危险操作
python -m myagent reject --operation <op-id>     # 拒绝危险操作
```

### 3.2 工作流配置 (workflow.md)

```markdown
## Phases

- [Phase 1] 需求分析与架构设计 (depends: none)
  - Task: 架构设计 (owner: architect)

- [Phase 2] 核心模块开发 (depends: Phase 1)
  - Task: 模块A开发 (parallel: true, owner: backend-dev)
  - Task: 模块B开发 (parallel: true, owner: backend-dev, frontend-dev)

- [Phase 3] 联调与测试 (depends: Phase 2)
  - Task: 集成测试 (owner: qa-engineer)

## Rules

- 每阶段输出必须通过自动化校验
- 并行任务需使用独立命名空间
- 危险操作需人工二次确认
```

### 3.3 Agent 配置 (agent.md)

```markdown
## Roles

- architect:
    description: 负责架构设计、技术选型
    tools: [read_file, write_file, edit_file, glob, grep, execute]
    model: openai/gpt-4o

- backend-dev:
    description: 负责后端业务逻辑开发
    tools: [read_file, write_file, edit_file, glob, grep, execute]
    model: openai/gpt-4o

- frontend-dev:
    description: 负责前端 UI 开发
    tools: [read_file, write_file, glob, grep]
    model: openai/gpt-4o

- qa-engineer:
    description: 负责测试用例生成
    tools: [read_file, write_file, glob, run_tests]
    model: openai/gpt-4o
```

---

## 4. 调试

### 4.1 IDE 调试配置

#### VS Code (.vscode/launch.json)

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Module",
            "type": "python",
            "request": "launch",
            "module": "myagent",
            "args": ["run", "--phase", "plan"],
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal"
        },
        {
            "name": "Debug: Init Command",
            "type": "python",
            "request": "launch",
            "module": "myagent",
            "args": ["init", "--name", "test-project"],
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal"
        }
    ]
}
```

#### PyCharm

1. **Run > Edit Configurations**
2. **点击 + > Python**
3. **配置:**
   - Name: `myagent run`
   - Module name: `myagent`
   - Parameters: `run --phase plan`
   - Working directory: 项目根目录

### 4.2 断点调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 IDE 断点
# 建议在以下位置设置断点:
# - myagent/workflow/parser.py: parse() 方法
# - myagent/scheduler/dispatcher.py: route() 方法
# - myagent/agents/supervisor.py: generate_planning() 方法
```

### 4.3 日志调试

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 或设置特定模块的日志级别
logging.getLogger('myagent.workflow').setLevel(logging.DEBUG)
logging.getLogger('myagent.scheduler').setLevel(logging.DEBUG)
```

### 4.4 查看详细日志

```bash
# 运行后查看日志
cat LOGS/workflow/phase-1.log
cat LOGS/agents/architect/input-prompt.json
cat LOGS/agents/architect/output-response.json

# 实时跟踪
tail -f LOGS/agents/backend-dev/*.log
```

### 4.5 常见问题排查

| 问题 | 可能原因 | 解决方法 |
|------|----------|----------|
| `ModuleNotFoundError: No module named 'myagent'` | 未正确安装 | `pip install -e .` 或 `PYTHONPATH=.` |
| `workflow.md not found` | 工作流文件不存在 | 先运行 `myagent init` |
| `Agent initialization failed` | API Key 未设置 | 设置环境变量 `OPENAI_API_KEY` |
| `Permission denied` | 文件权限问题 | 检查项目目录权限 |
| `Circular dependency detected` | workflow.md 配置错误 | 检查 Phase depends 配置 |

---

## 5. API 调用示例

### 5.1 在 Python 代码中使用

```python
from myagent.workflow.parser import WorkflowParser
from myagent.workflow.dag import DAGBuilder

# 解析工作流
parser = WorkflowParser()
workflow = parser.parse_file("workflow.md")

# 构建 DAG
dag = DAGBuilder(workflow).build()

# 获取拓扑排序
sorted_nodes = dag.topological_sort()
for node in sorted_nodes:
    print(f"{node.id}: {node.name}")
```

### 5.2 使用 myagent 框架创建 Agent

```python
from myagent import create_deep_agent
from langchain_openai import ChatOpenAI

# 初始化 LLM
llm = ChatOpenAI(
    api_key="your-api-key",
    base_url="https://api.openai.com/v1",
    model="gpt-4o",
    temperature=0.2
)

# 创建 Agent
agent = create_deep_agent(
    model=llm,
    tools=[search_tool, read_file_tool],
    system_prompt="You are an expert developer..."
)

# 执行任务
result = agent.invoke({
    "messages": [{"role": "user", "content": "Write a hello world function"}]
})
```

### 5.3 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_workflow_parser.py -v

# 运行并生成覆盖率报告
pytest tests/ --cov=myagent --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

---

## 6. 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `OPENAI_API_KEY` | 是 | OpenAI API Key |
| `OPENAI_API_BASE` | 否 | API 代理地址 |
| `ANTHROPIC_API_KEY` | 否 | Anthropic API Key |
| `TAVILY_API_KEY` | 否 | Tavily 搜索 API Key |
| `DEEPAGENTS_LOG_LEVEL` | 否 | 日志级别 (DEBUG/INFO/WARNING) |

---

## 7. 快速参考

```bash
# 1. 初始化项目
python -m myagent init --name my-project

# 2. 进入项目目录
cd my-project

# 3. 编辑 workflow.md 和 agent.md

# 4. 生成规划
python -m myagent run --phase plan

# 5. 确认规划（可编辑 PLANNING.md）
python -m myagent confirm --file PLANNING.md

# 6. 执行
python -m myagent run --phase execute

# 7. 查看状态
python -m myagent status --live
```

---

**文档结束**

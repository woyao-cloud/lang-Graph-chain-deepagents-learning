# DeepAgents 快速入门

**文档版本:** 1.0
**编制日期:** 2026-04-09

---

## 5 分钟快速上手

### Step 1: 安装

```bash
pip install deepagents click typer
```

### Step 2: 初始化项目

```bash
python -m deepagents init --name my-code-agent
cd my-code-agent
```

### Step 3: 配置工作流

编辑 `workflow.md`:

```markdown
## Phases

- [Phase 1] 架构设计 (depends: none)
  - Task: 系统架构设计 (owner: architect)

- [Phase 2] 开发 (depends: Phase 1)
  - Task: 后端开发 (parallel: true, owner: backend-dev)
  - Task: 前端开发 (parallel: true, owner: frontend-dev)
```

### Step 4: 运行

```bash
# 生成规划
python -m deepagents run --phase plan

# 确认并执行
python -m deepagents confirm --file PLANNING.md
python -m deepagents run --phase execute
```

---

## 核心概念

### 1. 工作流 (workflow.md)

定义项目开发的**阶段**和**任务**:

```markdown
- [Phase N] 阶段名称 (depends: Phase K)
  - Task: 任务名 (parallel: true/false, owner: agent名)
```

### 2. Agent 角色 (agent.md)

定义可用的 **Sub-Agent**:

```markdown
- architect:   架构师 - 做技术选型和架构设计
- backend-dev: 后端开发 - 写业务逻辑
- frontend-dev: 前端开发 - 写 UI
- qa-engineer: 测试 - 写测试用例
```

### 3. 规划 (PLANNING.md)

系统自动生成，包含:
- 任务拆解树
- 技术栈建议
- 文件结构
- 接口契约

### 4. 人机协同

关键节点需要**人工确认**:
- PLANNING.md 生成后
- 质量校验失败后
- 危险操作执行前

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `deepagents init --name xxx` | 初始化项目 |
| `deepagents run --phase plan` | 生成规划 |
| `deepagents confirm` | 确认规划 |
| `deepagents run --phase execute` | 执行任务 |
| `deepagents status` | 查看状态 |
| `deepagents logs --agent xxx` | 查看日志 |
| `deepagents skip --task xxx` | 跳过任务 |

---

## 目录结构

```
.
├── workflow.md          # 工作流配置
├── agent.md           # Agent 定义
├── PLANNING.md        # 生成的规划
├── STATUS.md         # 运行状态
└── LOGS/             # 日志
    ├── workflow/     # 工作流日志
    ├── agents/       # Agent 日志
    └── quality/      # 质量报告
```

---

## 下一步

- 查看 [安装与调试指南](./INSTALL_DEBUG_USAGE.md) 了解完整文档
- 查看 [架构文档](../ARCHITECTURE.md) 了解系统设计
- 查看 [需求文档](../../requirments/SPEC.md) 了解功能规格

---

**文档结束**

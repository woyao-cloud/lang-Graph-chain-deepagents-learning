"""MyAgent - 全自动化、可解释、可干预的工程级代码生成系统.

基于 DeepAgents 的多代理代码生成系统，支持:
- Workflow 解析与 DAG 调度
- 多代理并行/串行执行
- 人机协同与确认门禁
- 质量门禁 (Lint/Test)
- 版本控制自动化
"""

from myagent.config import (
    HITLConfig,
    MyAgentConfig,
    QualityGateConfig,
    VCSConfig,
    load_config,
)
from myagent.models import (
    AgentRegistryModel,
    AgentRole,
    ExecutionResult,
    Phase,
    PhaseStatus,
    PlanningDocument,
    ProgressInfo,
    QualityGateResult,
    RoutingRule,
    SubTask,
    Task,
    TaskMode,
    TaskStatus,
    TaskTree,
    VCSCommit,
    WorkflowModel,
)
from myagent.agents import AgentRegistry, AgentRouter, AgentScheduler
from myagent.executor import Checkpoint, TaskRunner
from myagent.hitl import ConfirmationGate, DangerousOpGuard
from myagent.planner import PlanningGenerator, TaskDecomposer, RiskAnalyzer
from myagent.progress import LogManager, PhaseProgress, ProgressTracker
from myagent.quality import LintChecker, QualityGateRunner, TestRunner
from myagent.vcs import BranchManager, CommitGenerator, GitRunner, VCSManager
from myagent.workflow import DAG, DAGBuilder, DAGNode, WorkflowParser

__version__ = "0.1.0"

__all__ = [
    # Config
    "HITLConfig",
    "MyAgentConfig",
    "QualityGateConfig",
    "VCSConfig",
    "load_config",
    # Models
    "AgentRegistryModel",
    "AgentRole",
    "ExecutionResult",
    "Phase",
    "PhaseStatus",
    "PlanningDocument",
    "ProgressInfo",
    "QualityGateResult",
    "RoutingRule",
    "SubTask",
    "Task",
    "TaskMode",
    "TaskStatus",
    "TaskTree",
    "VCSCommit",
    "WorkflowModel",
    # Workflow
    "WorkflowParser",
    "DAGBuilder",
    "DAG",
    "DAGNode",
    # Planner
    "PlanningGenerator",
    "TaskDecomposer",
    "RiskAnalyzer",
    # Agents
    "AgentRegistry",
    "AgentRouter",
    "AgentScheduler",
    # Executor
    "TaskRunner",
    "Checkpoint",
    # HITL
    "ConfirmationGate",
    "DangerousOpGuard",
    # Progress
    "ProgressTracker",
    "PhaseProgress",
    "LogManager",
    # Quality
    "LintChecker",
    "TestRunner",
    "QualityGateRunner",
    # VCS
    "GitRunner",
    "BranchManager",
    "CommitGenerator",
    "VCSManager",
]

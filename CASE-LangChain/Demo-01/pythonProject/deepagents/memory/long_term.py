"""
Long-term Memory - 长期记忆（跨会话持久化）
FR-EXEC-001.3: 记忆管理
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class SkillEntry:
    """
    技能条目
    存储可用技能的定义和使用信息
    """
    skill_id: str
    name: str
    description: str
    source_path: str  # SKILL.md 路径
    content: str
    # embedding: List[float] = field(default_factory=list)  # 向量化表示
    usage_count: int = 0
    success_rate: float = 0.0
    last_used_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentNote:
    """
    Agent 笔记
    Agent 在工作中记录的笔记
    """
    note_id: str
    agent_type: str
    content: str
    project: str
    task_type: str
    created_at: str = ""
    updated_at: str = ""


@dataclass
class SuccessPattern:
    """
    成功模式
    存储可复用的成功经验
    """
    pattern_id: str
    name: str
    description: str
    context: str  # 使用场景
    example_code: str
    success_metrics: Dict[str, float] = field(default_factory=dict)
    applicable_projects: List[str] = field(default_factory=list)


@dataclass
class ProjectKnowledge:
    """
    项目知识
    存储项目特定的上下文信息
    """
    project_path: str
    project_name: str
    tech_stack: List[str] = field(default_factory=list)
    architecture: str = ""
    key_files: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)


class LongTermMemory:
    """
    长期记忆
    跨会话持久化，支持语义检索
    """

    def __init__(self, storage_dir: str = ".deepagents/memory"):
        self.storage_dir = Path(storage_dir)
        self.skills_file = self.storage_dir / "skills.json"
        self.notes_file = self.storage_dir / "notes.json"
        self.patterns_file = self.storage_dir / "patterns.json"
        self.projects_file = self.storage_dir / "projects.json"

        # 内存缓存
        self._skills: Dict[str, SkillEntry] = {}
        self._notes: Dict[str, AgentNote] = {}
        self._patterns: Dict[str, SuccessPattern] = {}
        self._projects: Dict[str, ProjectKnowledge] = {}

        # 确保存储目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 加载已有数据
        self._load_all()

    def _load_all(self):
        """加载所有持久化数据"""
        self._skills = self._load_json(self.skills_file, SkillEntry)
        self._notes = self._load_json(self.notes_file, AgentNote)
        self._patterns = self._load_json(self.patterns_file, SuccessPattern)
        self._projects = self._load_json(self.projects_file, ProjectKnowledge)

    def _load_json(self, file_path: Path, dataclass_type):
        """加载 JSON 文件"""
        result = {}
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if dataclass_type == SkillEntry:
                            result[k] = SkillEntry(**v)
                        elif dataclass_type == AgentNote:
                            result[k] = AgentNote(**v)
                        elif dataclass_type == SuccessPattern:
                            result[k] = SuccessPattern(**v)
                        elif dataclass_type == ProjectKnowledge:
                            result[k] = ProjectKnowledge(**v)
            except Exception:
                pass
        return result

    def _save_json(self, file_path: Path, data: Dict):
        """保存 JSON 文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                {k: v.__dict__ for k, v in data.items()},
                f,
                ensure_ascii=False,
                indent=2
            )

    # Skills 管理
    def add_skill(self, skill: SkillEntry):
        """添加技能"""
        self._skills[skill.skill_id] = skill
        self._save_json(self.skills_file, self._skills)

    def get_skill(self, skill_id: str) -> Optional[SkillEntry]:
        """获取技能"""
        return self._skills.get(skill_id)

    def find_skills(self, query: str, limit: int = 5) -> List[SkillEntry]:
        """搜索技能（简单关键词匹配）"""
        query_lower = query.lower()
        results = []
        for skill in self._skills.values():
            if (query_lower in skill.name.lower() or
                query_lower in skill.description.lower() or
                any(query_lower in tag.lower() for tag in skill.tags)):
                results.append(skill)
        return results[:limit]

    def record_skill_usage(self, skill_id: str, success: bool):
        """记录技能使用"""
        skill = self._skills.get(skill_id)
        if skill:
            skill.usage_count += 1
            if success:
                skill.success_rate = (skill.success_rate * (skill.usage_count - 1) + 1) / skill.usage_count
            else:
                skill.success_rate = skill.success_rate * (skill.usage_count - 1) / skill.usage_count
            skill.last_used_at = datetime.now().isoformat()

    # Notes 管理
    def add_note(self, note: AgentNote):
        """添加笔记"""
        self._notes[note.note_id] = note
        self._save_json(self.notes_file, self._notes)

    def get_notes_by_agent(self, agent_type: str) -> List[AgentNote]:
        """获取指定 Agent 类型的笔记"""
        return [n for n in self._notes.values() if n.agent_type == agent_type]

    def get_notes_by_project(self, project: str) -> List[AgentNote]:
        """获取指定项目的笔记"""
        return [n for n in self._notes.values() if n.project == project]

    # Patterns 管理
    def add_pattern(self, pattern: SuccessPattern):
        """添加成功模式"""
        self._patterns[pattern.pattern_id] = pattern
        self._save_json(self.patterns_file, self._patterns)

    def find_patterns(self, context: str) -> List[SuccessPattern]:
        """查找适用的成功模式"""
        context_lower = context.lower()
        results = []
        for pattern in self._patterns.values():
            if context_lower in pattern.context.lower():
                results.append(pattern)
        return results

    # Projects 管理
    def add_project(self, project: ProjectKnowledge):
        """添加项目知识"""
        self._projects[project.project_path] = project
        self._save_json(self.projects_file, self._projects)

    def get_project(self, project_path: str) -> Optional[ProjectKnowledge]:
        """获取项目知识"""
        return self._projects.get(project_path)

    def update_project(self, project_path: str, **kwargs):
        """更新项目知识"""
        project = self._projects.get(project_path)
        if project:
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            self._save_json(self.projects_file, self._projects)

    # 检索接口
    def semantic_search(
        self,
        query: str,
        memory_type: str = "all",  # "short", "long", "all"
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        语义检索
        （简化版：关键词匹配）
        """
        results = []

        # 搜索技能
        if memory_type in ["long", "all"]:
            skills = self.find_skills(query, limit)
            for skill in skills:
                results.append({
                    "type": "skill",
                    "content": skill.description,
                    "source": skill.source_path,
                    "relevance": 0.8
                })

        # 搜索模式
        if memory_type in ["long", "all"]:
            patterns = self.find_patterns(query)
            for pattern in patterns[:limit]:
                results.append({
                    "type": "pattern",
                    "content": pattern.description,
                    "example": pattern.example_code,
                    "context": pattern.context,
                    "relevance": 0.7
                })

        return results[:limit]

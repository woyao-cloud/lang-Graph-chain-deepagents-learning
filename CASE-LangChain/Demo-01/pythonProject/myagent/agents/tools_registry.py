"""
Tools Registry - 工具注册表
管理所有可用的 LangChain 工具
"""

from typing import List, Dict
from langchain.tools import tool

# Import standard tools
try:
    from langchain_community.tools import FileReadTool, FileWriteTool
except ImportError:
    FileReadTool = None
    FileWriteTool = None


class ToolsRegistry:
    """
    工具注册表
    提供预定义的工具集
    """

    # 预定义工具集
    TOOL_SETS = {
        "default": [
            "read_file",
            "write_file",
            "edit_file",
            "glob",
            "grep",
        ],
        "full": [
            "read_file",
            "write_file",
            "edit_file",
            "glob",
            "grep",
            "execute",
            "git_status",
            "git_commit",
        ],
        "backend": [
            "read_file",
            "write_file",
            "edit_file",
            "glob",
            "grep",
            "execute",
        ],
        "frontend": [
            "read_file",
            "write_file",
            "edit_file",
            "glob",
            "grep",
        ],
        "qa": [
            "read_file",
            "write_file",
            "glob",
            "grep",
            "run_tests",
        ],
    }

    @classmethod
    def get_tools(cls, tool_names: List[str]) -> List:
        """
        获取工具实例列表
        """
        tools = []
        for name in tool_names:
            tool_instance = cls._create_tool(name)
            if tool_instance:
                tools.append(tool_instance)
        return tools

    @classmethod
    def get_tool_set(cls, set_name: str) -> List:
        """
        获取预定义工具集
        """
        tool_names = cls.TOOL_SETS.get(set_name, cls.TOOL_SETS["default"])
        return cls.get_tools(tool_names)

    @classmethod
    def _create_tool(cls, name: str):
        """
        创建单个工具实例
        """
        # 文件操作工具
        if name == "read_file":
            return cls._create_read_file_tool()
        elif name == "write_file":
            return cls._create_write_file_tool()
        elif name == "edit_file":
            return cls._create_edit_file_tool()
        elif name == "glob":
            return cls._create_glob_tool()
        elif name == "grep":
            return cls._create_grep_tool()
        # Git 工具
        elif name == "git_status":
            return cls._create_git_status_tool()
        elif name == "git_commit":
            return cls._create_git_commit_tool()
        # 执行工具
        elif name == "execute":
            return cls._create_execute_tool()
        # 测试工具
        elif name == "run_tests":
            return cls._create_run_tests_tool()
        else:
            return None

    @classmethod
    def _create_read_file_tool(cls):
        """创建文件读取工具"""
        @tool
        def read_file(file_path: str) -> str:
            """Read the contents of a file.

            Args:
                file_path: The path to the file to read.
            """
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        return read_file

    @classmethod
    def _create_write_file_tool(cls):
        """创建文件写入工具"""
        @tool
        def write_file(file_path: str, content: str) -> str:
            """Write content to a file.

            Args:
                file_path: The path to the file to write.
                content: The content to write.
            """
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File written: {file_path}"

        return write_file

    @classmethod
    def _create_edit_file_tool(cls):
        """创建文件编辑工具"""
        @tool
        def edit_file(file_path: str, old_string: str, new_string: str) -> str:
            """Edit a file by replacing old_string with new_string.

            Args:
                file_path: The path to the file to edit.
                old_string: The string to replace.
                new_string: The replacement string.
            """
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if old_string not in content:
                return f"Error: old_string not found in file"

            new_content = content.replace(old_string, new_string)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return f"File edited: {file_path}"

        return edit_file

    @classmethod
    def _create_glob_tool(cls):
        """创建文件搜索工具"""
        @tool
        def glob(pattern: str) -> str:
            """Find files matching a glob pattern.

            Args:
                pattern: The glob pattern to match (e.g., "**/*.py").
            """
            import glob as g
            matches = g.glob(pattern, recursive=True)
            return "\n".join(matches) if matches else "No matches found"

        return glob

    @classmethod
    def _create_grep_tool(cls):
        """创建文本搜索工具"""
        @tool
        def grep(pattern: str, path: str = ".") -> str:
            """Search for a pattern in files.

            Args:
                pattern: The regex pattern to search for.
                path: The directory path to search in.
            """
            import re
            import glob

            matches = []
            for file in glob.glob(f"{path}/**/*", recursive=True):
                if file.is_file():
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            for i, line in enumerate(f, 1):
                                if re.search(pattern, line):
                                    matches.append(f"{file}:{i}: {line.rstrip()}")
                    except Exception:
                        pass

            return "\n".join(matches) if matches else "No matches found"

        return grep

    @classmethod
    def _create_git_status_tool(cls):
        """创建 Git 状态工具"""
        @tool
        def git_status() -> str:
            """Get the current git status."""
            import subprocess
            result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
            return result.stdout or "No changes"

        return git_status

    @classmethod
    def _create_git_commit_tool(cls):
        """创建 Git 提交工具"""
        @tool
        def git_commit(message: str) -> str:
            """Commit changes with a message.

            Args:
                message: The commit message.
            """
            import subprocess
            subprocess.run(["git", "add", "."], capture_output=True)
            result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True)
            return result.stdout or result.stderr

        return git_commit

    @classmethod
    def _create_execute_tool(cls):
        """创建命令执行工具（受限）"""
        # 白名单命令
        ALLOWED_COMMANDS = [
            "python", "python3", "pip", "npm", "node",
            "ls", "dir", "cat", "type",
            "pytest", "pytest --cov",
            "black", "ruff", "eslint",
        ]

        @tool
        def execute(command: str, cwd: str = ".") -> str:
            """Execute a shell command (whitelist only).

            Args:
                command: The command to execute.
                cwd: The working directory.
            """
            import subprocess
            import shlex

            # 安全检查：只允许白名单命令
            cmd_parts = shlex.split(command)
            if not cmd_parts:
                return "Error: Empty command"

            base_cmd = cmd_parts[0]

            # 简单的白名单检查
            is_allowed = any(
                base_cmd.startswith(allowed) or base_cmd == allowed
                for allowed in ["python", "pip", "npm", "node", "ls", "dir", "cat", "type", "pytest", "black", "ruff", "eslint"]
            )

            if not is_allowed:
                return f"Error: Command '{base_cmd}' not in whitelist"

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd
            )

            output = result.stdout + result.stderr
            return output or "Command executed (no output)"

        return execute

    @classmethod
    def _create_run_tests_tool(cls):
        """创建测试运行工具"""
        @tool
        def run_tests(test_path: str = "tests/", coverage: bool = True) -> str:
            """Run tests with optional coverage.

            Args:
                test_path: Path to tests directory.
                coverage: Whether to generate coverage report.
            """
            import subprocess

            cmd = ["pytest", test_path]
            if coverage:
                cmd.append("--cov")

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout + result.stderr

        return run_tests

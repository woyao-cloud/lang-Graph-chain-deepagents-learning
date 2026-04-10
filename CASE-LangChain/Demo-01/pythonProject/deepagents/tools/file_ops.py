"""
File Operations Tools - 文件操作工具
FR-EXEC-001.2: 工具调用
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional

from langchain.tools import tool


class FileOperations:
    """
    文件操作工具集
    提供安全的文件读写编辑功能
    """

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".vue",
        ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
        ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
        ".md", ".txt", ".rst", ".html", ".css", ".scss",
        ".sql", ".sh", ".bash", ".ps1", ".bat",
    }

    # 禁止访问的目录
    FORBIDDEN_PATHS = {
        ".git", ".svn", "node_modules", "__pycache__",
        ".venv", "venv", ".env", ".idea", ".vscode",
    }

    @classmethod
    def is_safe_path(cls, path: str) -> bool:
        """检查路径是否安全"""
        abs_path = os.path.abspath(path)

        # 检查是否包含禁止的目录
        parts = Path(abs_path).parts
        for forbidden in cls.FORBIDDEN_PATHS:
            if forbidden in parts:
                return False

        # 检查文件扩展名
        ext = Path(abs_path).suffix.lower()
        if ext and ext not in cls.ALLOWED_EXTENSIONS:
            return False

        return True

    @classmethod
    def read_file(cls, file_path: str) -> str:
        """安全读取文件"""
        if not cls.is_safe_path(file_path):
            raise ValueError(f"Access denied: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    def write_file(cls, file_path: str, content: str) -> str:
        """安全写入文件"""
        if not cls.is_safe_path(file_path):
            raise ValueError(f"Access denied: {file_path}")

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"File written: {file_path}"

    @classmethod
    def edit_file(cls, file_path: str, old_string: str, new_string: str) -> str:
        """安全编辑文件"""
        if not cls.is_safe_path(file_path):
            raise ValueError(f"Access denied: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_string not in content:
            raise ValueError(f"String not found: {old_string[:50]}...")

        new_content = content.replace(old_string, new_string, 1)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"File edited: {file_path}"

    @classmethod
    def glob_files(cls, pattern: str, base_dir: str = ".") -> List[str]:
        """搜索文件"""
        import glob
        import os

        results = []
        full_pattern = os.path.join(base_dir, pattern)
        for match in glob.glob(full_pattern, recursive=True):
            if cls.is_safe_path(match):
                results.append(match)

        return results


# LangChain Tools
@tool
def read_file(file_path: str) -> str:
    """Read the contents of a file.

    Args:
        file_path: The path to the file to read.
    """
    return FileOperations.read_file(file_path)


@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file.

    Args:
        file_path: The path to the file to write.
        content: The content to write.
    """
    return FileOperations.write_file(file_path, content)


@tool
def edit_file(file_path: str, old_string: str, new_string: str) -> str:
    """Edit a file by replacing old_string with new_string.

    Args:
        file_path: The path to the file to edit.
        old_string: The exact string to replace.
        new_string: The replacement string.
    """
    return FileOperations.edit_file(file_path, old_string, new_string)


@tool
def glob(pattern: str) -> str:
    """Find files matching a glob pattern.

    Args:
        pattern: The glob pattern (e.g., "src/**/*.py").
    """
    results = FileOperations.glob_files(pattern)
    return "\n".join(results) if results else "No matches found"


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
        if os.path.isfile(file) and FileOperations.is_safe_path(file):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if re.search(pattern, line):
                            matches.append(f"{file}:{i}: {line.rstrip()}")
            except Exception:
                pass

    return "\n".join(matches) if matches else "No matches found"

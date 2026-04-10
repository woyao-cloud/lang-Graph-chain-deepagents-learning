"""
Tests for Tools
FR-EXEC-001.2: 工具调用
"""

import pytest
import tempfile
import os

from myagent.tools.file_ops import FileOperations


class TestFileOperations:
    """文件操作测试"""

    def test_is_safe_path_allowed(self):
        """测试安全路径检查 - 允许"""
        # Python 文件应该是安全的
        assert FileOperations.is_safe_path("src/main.py") == True
        assert FileOperations.is_safe_path("tests/test_main.py") == True
        assert FileOperations.is_safe_path("docs/README.md") == True

    def test_is_safe_path_forbidden(self):
        """测试安全路径检查 - 禁止"""
        # node_modules 应该被禁止
        assert FileOperations.is_safe_path("node_modules/package.json") == False
        # .git 应该被禁止
        assert FileOperations.is_safe_path(".git/config") == False
        # venv 应该被禁止
        assert FileOperations.is_safe_path("venv/lib/python.py") == False

    def test_read_file(self):
        """测试文件读取"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')")
            temp_path = f.name

        try:
            content = FileOperations.read_file(temp_path)
            assert content == "print('hello')"
        finally:
            os.unlink(temp_path)

    def test_write_file(self):
        """测试文件写入"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            result = FileOperations.write_file(file_path, "test content")

            assert os.path.exists(file_path)
            with open(file_path) as f:
                assert f.read() == "test content"

    def test_edit_file(self):
        """测试文件编辑"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("old content")
            temp_path = f.name

        try:
            result = FileOperations.edit_file(temp_path, "old", "new")
            with open(temp_path) as f:
                assert f.read() == "new content"
        finally:
            os.unlink(temp_path)

    def test_glob_files(self):
        """测试文件搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            open(os.path.join(tmpdir, "test1.py"), 'w').close()
            open(os.path.join(tmpdir, "test2.py"), 'w').close()
            open(os.path.join(tmpdir, "readme.txt"), 'w').close()

            results = FileOperations.glob_files("*.py", tmpdir)
            assert len(results) == 2


class TestCommandWhitelist:
    """命令白名单测试"""

    def test_allowed_commands(self):
        """测试允许的命令"""
        from myagent.tools.command import CommandWhitelist

        # Python 命令应该允许
        is_allowed, needs_confirm = CommandWhitelist.is_allowed("python test.py")
        assert is_allowed == True

        # pytest 应该允许
        is_allowed, needs_confirm = CommandWhitelist.is_allowed("pytest tests/")
        assert is_allowed == True

    def test_dangerous_commands_require_confirmation(self):
        """测试危险命令需要确认"""
        from myagent.tools.command import CommandWhitelist

        # rm -rf 是危险的
        is_allowed, needs_confirm = CommandWhitelist.is_allowed("rm -rf /tmp/test")
        assert is_allowed == False
        assert needs_confirm == True

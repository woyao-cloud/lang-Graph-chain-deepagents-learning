"""
Schema Checker - API Schema 校验
FR-QA-001.3: Schema 检查
"""

import json
import yaml
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass


@dataclass
class SchemaViolation:
    """Schema 违规"""
    path: str
    message: str
    severity: str  # "error", "warning", "info"


class SchemaChecker:
    """
    API Schema 校验器
    校验 OpenAPI/JSON Schema 规范
    """

    def __init__(self):
        self.violations: List[SchemaViolation] = []

    def check_openapi(self, spec: Dict[str, Any]) -> List[SchemaViolation]:
        """
        校验 OpenAPI 规范

        Args:
            spec: OpenAPI 规范字典

        Returns:
            违规列表
        """
        self.violations = []

        # 检查基本字段
        self._check_openapi_fields(spec)

        # 检查 paths
        if "paths" in spec:
            for path, path_item in spec["paths"].items():
                self._check_path(path, path_item)

        # 检查 components
        if "components" in spec:
            self._check_components(spec["components"])

        return self.violations

    def _check_openapi_fields(self, spec: Dict):
        """检查 OpenAPI 基本字段"""
        required_fields = ["openapi", "info", "paths"]
        optional_fields = ["servers", "components", "security", "tags"]

        # 检查 openapi 版本
        if "openapi" not in spec:
            self.violations.append(SchemaViolation(
                path="/",
                message="Missing 'openapi' field",
                severity="error"
            ))
        elif not re.match(r"3\.\d+\.\d+", str(spec.get("openapi", ""))):
            self.violations.append(SchemaViolation(
                path="/openapi",
                message=f"Invalid OpenAPI version: {spec.get('openapi')}",
                severity="error"
            ))

        # 检查 info
        if "info" not in spec:
            self.violations.append(SchemaViolation(
                path="/info",
                message="Missing 'info' field",
                severity="error"
            ))
        else:
            info = spec["info"]
            if "title" not in info:
                self.violations.append(SchemaViolation(
                    path="/info/title",
                    message="Missing 'title' in info",
                    severity="warning"
                ))
            if "version" not in info:
                self.violations.append(SchemaViolation(
                    path="/info/version",
                    message="Missing 'version' in info",
                    severity="warning"
                ))

    def _check_path(self, path: str, path_item: Dict):
        """检查 Path Item"""
        # 检查路径格式
        if not path.startswith("/"):
            self.violations.append(SchemaViolation(
                path=f"/paths/{path}",
                message=f"Path must start with '/': {path}",
                severity="error"
            ))

        # 检查 HTTP 方法
        http_methods = ["get", "post", "put", "patch", "delete", "options", "head", "trace"]
        for method in http_methods:
            if method in path_item:
                self._check_operation(path, method, path_item[method])

    def _check_operation(self, path: str, method: str, operation: Dict):
        """检查 Operation"""
        op_path = f"/paths/{path}/{method}"

        # 检查 summary
        if "summary" not in operation:
            self.violations.append(SchemaViolation(
                path=op_path,
                message=f"Missing 'summary' for {method.upper()} {path}",
                severity="warning"
            ))

        # 检查 responses
        if "responses" not in operation:
            self.violations.append(SchemaViolation(
                path=op_path,
                message=f"Missing 'responses' for {method.upper()} {path}",
                severity="error"
            ))
        else:
            self._check_responses(op_path, operation["responses"])

    def _check_responses(self, op_path: str, responses: Dict):
        """检查 Responses"""
        # 检查是否有 200/201 成功响应
        success_codes = ["200", "201", "202", "204"]
        has_success = any(code in responses for code in success_codes)

        if not has_success:
            self.violations.append(SchemaViolation(
                path=f"{op_path}/responses",
                message="No success response (200/201/202/204) defined",
                severity="warning"
            ))

        # 检查响应定义
        for code, response in responses.items():
            if isinstance(response, dict) and "$ref" not in response:
                if "description" not in response:
                    self.violations.append(SchemaViolation(
                        path=f"{op_path}/responses/{code}",
                        message=f"Missing 'description' in response {code}",
                        severity="warning"
                    ))

    def _check_components(self, components: Dict):
        """检查 Components"""
        # 检查 schemas
        if "schemas" in components:
            for schema_name, schema in components["schemas"].items():
                self._check_schema(f"/components/schemas/{schema_name}", schema)

    def _check_schema(self, path: str, schema: Dict):
        """检查 Schema"""
        if isinstance(schema, dict):
            # 检查 type
            if "type" not in schema and "$ref" not in schema:
                self.violations.append(SchemaViolation(
                    path=path,
                    message="Schema missing 'type' or '$ref'",
                    severity="warning"
                ))

            # 检查 object 类型的属性
            if schema.get("type") == "object" and "properties" not in schema:
                self.violations.append(SchemaViolation(
                    path=path,
                    message="Object schema missing 'properties'",
                    severity="warning"
                ))

    def check_json_schema(self, schema: Dict[str, Any]) -> List[SchemaViolation]:
        """
        校验 JSON Schema

        Args:
            schema: JSON Schema 字典

        Returns:
            违规列表
        """
        self.violations = []

        # 基本校验
        if "$schema" not in schema:
            self.violations.append(SchemaViolation(
                path="/",
                message="Missing '$schema' field",
                severity="warning"
            ))

        if "type" not in schema:
            self.violations.append(SchemaViolation(
                path="/",
                message="Missing 'type' field",
                severity="error"
            ))

        return self.violations

    def load_and_check_file(self, file_path: str) -> List[SchemaViolation]:
        """
        加载并校验文件

        Args:
            file_path: 文件路径

        Returns:
            违规列表
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 根据扩展名判断格式
        if file_path.endswith(".yaml") or file_path.endswith(".yml"):
            spec = yaml.safe_load(content)
        elif file_path.endswith(".json"):
            spec = json.loads(content)
        else:
            return [SchemaViolation(
                path="/",
                message=f"Unsupported file format: {file_path}",
                severity="error"
            )]

        # 判断 schema 类型
        if "openapi" in spec:
            return self.check_openapi(spec)
        elif "$schema" in spec or "type" in spec:
            return self.check_json_schema(spec)
        else:
            return [SchemaViolation(
                path="/",
                message="Unknown schema type",
                severity="error"
            )]

    def generate_report(self) -> str:
        """生成校验报告"""
        if not self.violations:
            return "Schema validation passed!"

        lines = ["# Schema Validation Report", ""]

        error_count = sum(1 for v in self.violations if v.severity == "error")
        warning_count = sum(1 for v in self.violations if v.severity == "warning")

        lines.append(f"**Errors:** {error_count}")
        lines.append(f"**Warnings:** {warning_count}")
        lines.append("")

        for v in self.violations:
            icon = "ERROR" if v.severity == "error" else "WARN"
            lines.append(f"- [{icon}] {v.path}: {v.message}")

        return "\n".join(lines)


# 便捷函数
def validate_openapi_spec(spec: Dict[str, Any]) -> tuple[bool, List[SchemaViolation]]:
    """
    校验 OpenAPI 规范

    Returns:
        (passed, violations)
    """
    checker = SchemaChecker()
    violations = checker.check_openapi(spec)
    return len([v for v in violations if v.severity == "error"]) == 0, violations


def validate_schema_file(file_path: str) -> tuple[bool, List[SchemaViolation]]:
    """
    校验 Schema 文件

    Returns:
        (passed, violations)
    """
    checker = SchemaChecker()
    violations = checker.load_and_check_file(file_path)
    return len([v for v in violations if v.severity == "error"]) == 0, violations

"""Python code static analysis"""

import ast
import hashlib
import subprocess
import json
import tempfile
import os
from typing import List, Set, Tuple
from pathlib import Path

from .validation_result import (
    ValidationResult,
    SecurityIssue,
    SeverityLevel,
    ResourceEstimate,
)


class PythonAnalyzer:
    """Static analyzer for Python code"""
    
    # Prohibited modules that pose security risks
    PROHIBITED_MODULES = {
        "os",
        "subprocess",
        "socket",
        "urllib",
        "urllib2",
        "urllib3",
        "requests",
        "http",
        "httplib",
        "ftplib",
        "telnetlib",
        "smtplib",
        "poplib",
        "imaplib",
        "__import__",
        "importlib",
        "sys",
        "ctypes",
        "multiprocessing",
        "threading",
        "asyncio",
    }
    
    # Prohibited built-in functions
    PROHIBITED_BUILTINS = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",  # File operations should be restricted
        "input",  # Interactive input not allowed
    }
    
    def __init__(self):
        """Initialize Python analyzer"""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.security_issues: List[SecurityIssue] = []
    
    def analyze(self, code: str) -> ValidationResult:
        """
        Perform complete static analysis on Python code
        
        Args:
            code: Python source code to analyze
            
        Returns:
            ValidationResult with analysis findings
        """
        self.errors = []
        self.warnings = []
        self.security_issues = []
        
        # Calculate code hash
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        # Step 1: Syntax validation
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return ValidationResult(
                is_valid=False,
                language="python",
                code_hash=code_hash,
                errors=self.errors,
                warnings=self.warnings,
                security_issues=self.security_issues,
            )
        
        # Step 2: AST-based security analysis
        self._analyze_ast(tree, code)
        
        # Step 3: Bandit security scan
        self._run_bandit_scan(code)
        
        # Step 4: Resource estimation
        resource_estimate = self._estimate_resources(tree)
        
        # Determine if code is valid
        is_valid = (
            len(self.errors) == 0
            and not any(
                issue.severity == SeverityLevel.CRITICAL
                for issue in self.security_issues
            )
        )
        
        return ValidationResult(
            is_valid=is_valid,
            language="python",
            code_hash=code_hash,
            errors=self.errors,
            warnings=self.warnings,
            security_issues=self.security_issues,
            resource_estimate=resource_estimate,
        )
    
    def _analyze_ast(self, tree: ast.AST, code: str) -> None:
        """Analyze AST for security issues"""
        code_lines = code.split("\n")
        
        for node in ast.walk(tree):
            # Check for prohibited imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.PROHIBITED_MODULES:
                        self.security_issues.append(
                            SecurityIssue(
                                severity=SeverityLevel.CRITICAL,
                                issue_type="prohibited_import",
                                message=f"Prohibited module import: {alias.name}",
                                line_number=node.lineno,
                                code_snippet=self._get_code_snippet(code_lines, node.lineno),
                            )
                        )
            
            # Check for prohibited from imports
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module in self.PROHIBITED_MODULES:
                    self.security_issues.append(
                        SecurityIssue(
                            severity=SeverityLevel.CRITICAL,
                            issue_type="prohibited_import",
                            message=f"Prohibited module import: {node.module}",
                            line_number=node.lineno,
                            code_snippet=self._get_code_snippet(code_lines, node.lineno),
                        )
                    )
            
            # Check for prohibited built-in function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.PROHIBITED_BUILTINS:
                        self.security_issues.append(
                            SecurityIssue(
                                severity=SeverityLevel.CRITICAL,
                                issue_type="prohibited_builtin",
                                message=f"Prohibited built-in function: {node.func.id}",
                                line_number=node.lineno,
                                code_snippet=self._get_code_snippet(code_lines, node.lineno),
                            )
                        )
    
    def _run_bandit_scan(self, code: str) -> None:
        """Run Bandit security scanner on code"""
        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
            ) as tmp_file:
                tmp_file.write(code)
                tmp_path = tmp_file.name
            
            try:
                # Run bandit with JSON output
                result = subprocess.run(
                    ["bandit", "-f", "json", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                
                # Parse bandit output
                if result.stdout:
                    bandit_data = json.loads(result.stdout)
                    for issue in bandit_data.get("results", []):
                        severity_map = {
                            "LOW": SeverityLevel.LOW,
                            "MEDIUM": SeverityLevel.MEDIUM,
                            "HIGH": SeverityLevel.HIGH,
                        }
                        
                        self.security_issues.append(
                            SecurityIssue(
                                severity=severity_map.get(
                                    issue.get("issue_severity", "MEDIUM"),
                                    SeverityLevel.MEDIUM,
                                ),
                                issue_type=issue.get("test_id", "unknown"),
                                message=issue.get("issue_text", "Security issue detected"),
                                line_number=issue.get("line_number"),
                                code_snippet=issue.get("code"),
                            )
                        )
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
        
        except subprocess.TimeoutExpired:
            self.warnings.append("Bandit scan timed out")
        except FileNotFoundError:
            self.warnings.append("Bandit not available for security scanning")
        except Exception as e:
            self.warnings.append(f"Bandit scan failed: {str(e)}")
    
    def _estimate_resources(self, tree: ast.AST) -> ResourceEstimate:
        """Estimate resource usage from AST analysis"""
        has_loops = False
        has_recursion = False
        max_depth = 0
        complexity = 1
        
        # Track function definitions for recursion detection
        function_names: Set[str] = set()
        
        for node in ast.walk(tree):
            # Check for loops
            if isinstance(node, (ast.For, ast.While)):
                has_loops = True
                complexity += 2
            
            # Check for function definitions
            if isinstance(node, ast.FunctionDef):
                function_names.add(node.name)
            
            # Check for recursive calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in function_names:
                        has_recursion = True
                        complexity += 5
            
            # Track nesting depth
            depth = self._get_node_depth(node, tree)
            max_depth = max(max_depth, depth)
        
        # Estimate memory (MB) - base + complexity factor
        estimated_memory = 64 + (complexity * 2)
        
        # Estimate CPU time (seconds) - base + complexity factor
        estimated_cpu = 0.1 + (complexity * 0.05)
        
        # Add penalties for loops and recursion
        if has_loops:
            estimated_cpu += 0.5
        if has_recursion:
            estimated_cpu += 1.0
        
        return ResourceEstimate(
            estimated_memory_mb=min(estimated_memory, 512),  # Cap at 512MB
            estimated_cpu_seconds=min(estimated_cpu, 30.0),  # Cap at 30s
            complexity_score=complexity,
            has_loops=has_loops,
            has_recursion=has_recursion,
            max_depth=max_depth,
        )
    
    def _get_node_depth(self, target_node: ast.AST, tree: ast.AST) -> int:
        """Calculate nesting depth of a node in the AST"""
        depth = 0
        
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child == target_node:
                    return depth + 1
            depth += 1
        
        return 0
    
    def _get_code_snippet(self, code_lines: List[str], line_number: int) -> str:
        """Extract code snippet around a line number"""
        if 1 <= line_number <= len(code_lines):
            return code_lines[line_number - 1].strip()
        return ""

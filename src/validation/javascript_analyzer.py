"""JavaScript/TypeScript code static analysis"""

import hashlib
import re
from typing import List, Set

from .validation_result import (
    ValidationResult,
    SecurityIssue,
    SeverityLevel,
    ResourceEstimate,
)


class JavaScriptAnalyzer:
    """Static analyzer for JavaScript and TypeScript code"""
    
    # Prohibited Node.js modules
    PROHIBITED_MODULES = {
        "fs",
        "child_process",
        "net",
        "http",
        "https",
        "dgram",
        "dns",
        "tls",
        "crypto",
        "os",
        "process",
        "cluster",
        "worker_threads",
        "vm",
    }
    
    # Prohibited global objects and functions
    PROHIBITED_GLOBALS = {
        "eval",
        "Function",
        "require",
        "import",
        "XMLHttpRequest",
        "fetch",
        "WebSocket",
    }
    
    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        (r"eval\s*\(", "eval() usage detected"),
        (r"Function\s*\(", "Function constructor usage detected"),
        (r"setTimeout\s*\([^,]*,\s*['\"]", "setTimeout with string argument"),
        (r"setInterval\s*\([^,]*,\s*['\"]", "setInterval with string argument"),
        (r"__proto__", "Prototype pollution risk"),
        (r"constructor\s*\[", "Constructor access detected"),
    ]
    
    def __init__(self):
        """Initialize JavaScript analyzer"""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.security_issues: List[SecurityIssue] = []
    
    def analyze(self, code: str, language: str = "javascript") -> ValidationResult:
        """
        Perform static analysis on JavaScript/TypeScript code
        
        Args:
            code: JavaScript or TypeScript source code
            language: "javascript" or "typescript"
            
        Returns:
            ValidationResult with analysis findings
        """
        self.errors = []
        self.warnings = []
        self.security_issues = []
        
        # Calculate code hash
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        # Step 1: Basic syntax validation
        self._validate_syntax(code)
        
        # Step 2: Security pattern analysis
        self._analyze_security_patterns(code)
        
        # Step 3: Import/require analysis
        self._analyze_imports(code)
        
        # Step 4: Resource estimation
        resource_estimate = self._estimate_resources(code)
        
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
            language=language,
            code_hash=code_hash,
            errors=self.errors,
            warnings=self.warnings,
            security_issues=self.security_issues,
            resource_estimate=resource_estimate,
        )
    
    def _validate_syntax(self, code: str) -> None:
        """Basic syntax validation for JavaScript/TypeScript"""
        # Check for balanced braces
        brace_count = 0
        paren_count = 0
        bracket_count = 0
        
        in_string = False
        in_comment = False
        string_char = None
        
        lines = code.split("\n")
        for line_num, line in enumerate(lines, 1):
            i = 0
            while i < len(line):
                char = line[i]
                
                # Handle comments
                if not in_string and i < len(line) - 1:
                    if line[i:i+2] == "//":
                        break  # Rest of line is comment
                    if line[i:i+2] == "/*":
                        in_comment = True
                        i += 2
                        continue
                    if line[i:i+2] == "*/" and in_comment:
                        in_comment = False
                        i += 2
                        continue
                
                if in_comment:
                    i += 1
                    continue
                
                # Handle strings
                if char in ('"', "'", "`") and (i == 0 or line[i-1] != "\\"):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                
                # Count brackets when not in string
                if not in_string:
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                    elif char == "(":
                        paren_count += 1
                    elif char == ")":
                        paren_count -= 1
                    elif char == "[":
                        bracket_count += 1
                    elif char == "]":
                        bracket_count -= 1
                
                i += 1
        
        # Check for unbalanced brackets
        if brace_count != 0:
            self.errors.append(f"Unbalanced braces: {brace_count} unclosed")
        if paren_count != 0:
            self.errors.append(f"Unbalanced parentheses: {paren_count} unclosed")
        if bracket_count != 0:
            self.errors.append(f"Unbalanced brackets: {bracket_count} unclosed")
    
    def _analyze_security_patterns(self, code: str) -> None:
        """Analyze code for dangerous security patterns"""
        lines = code.split("\n")
        
        for pattern, message in self.DANGEROUS_PATTERNS:
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    self.security_issues.append(
                        SecurityIssue(
                            severity=SeverityLevel.CRITICAL,
                            issue_type="dangerous_pattern",
                            message=message,
                            line_number=line_num,
                            code_snippet=line.strip(),
                        )
                    )
        
        # Check for prohibited globals
        for global_name in self.PROHIBITED_GLOBALS:
            pattern = rf"\b{re.escape(global_name)}\b"
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    self.security_issues.append(
                        SecurityIssue(
                            severity=SeverityLevel.CRITICAL,
                            issue_type="prohibited_global",
                            message=f"Prohibited global usage: {global_name}",
                            line_number=line_num,
                            code_snippet=line.strip(),
                        )
                    )
    
    def _analyze_imports(self, code: str) -> None:
        """Analyze import and require statements"""
        lines = code.split("\n")
        
        # Pattern for require() statements
        require_pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        
        # Pattern for import statements
        import_pattern = r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]"
        
        for line_num, line in enumerate(lines, 1):
            # Check require statements
            for match in re.finditer(require_pattern, line):
                module_name = match.group(1)
                if module_name in self.PROHIBITED_MODULES:
                    self.security_issues.append(
                        SecurityIssue(
                            severity=SeverityLevel.CRITICAL,
                            issue_type="prohibited_import",
                            message=f"Prohibited module import: {module_name}",
                            line_number=line_num,
                            code_snippet=line.strip(),
                        )
                    )
            
            # Check import statements
            for match in re.finditer(import_pattern, line):
                module_name = match.group(1)
                if module_name in self.PROHIBITED_MODULES:
                    self.security_issues.append(
                        SecurityIssue(
                            severity=SeverityLevel.CRITICAL,
                            issue_type="prohibited_import",
                            message=f"Prohibited module import: {module_name}",
                            line_number=line_num,
                            code_snippet=line.strip(),
                        )
                    )
    
    def _estimate_resources(self, code: str) -> ResourceEstimate:
        """Estimate resource usage from code analysis"""
        has_loops = False
        has_recursion = False
        complexity = 1
        max_depth = 0
        
        lines = code.split("\n")
        function_names: Set[str] = set()
        
        # Detect loops
        loop_patterns = [r"\bfor\s*\(", r"\bwhile\s*\(", r"\bdo\s*{"]
        for pattern in loop_patterns:
            if re.search(pattern, code):
                has_loops = True
                complexity += 2
        
        # Detect function definitions and recursion
        func_pattern = r"function\s+(\w+)\s*\("
        arrow_func_pattern = r"const\s+(\w+)\s*=\s*\([^)]*\)\s*=>"
        
        for match in re.finditer(func_pattern, code):
            function_names.add(match.group(1))
        
        for match in re.finditer(arrow_func_pattern, code):
            function_names.add(match.group(1))
        
        # Check for recursive calls
        for func_name in function_names:
            pattern = rf"\b{re.escape(func_name)}\s*\("
            if len(re.findall(pattern, code)) > 1:
                has_recursion = True
                complexity += 5
        
        # Estimate nesting depth
        current_depth = 0
        for line in lines:
            current_depth += line.count("{") - line.count("}")
            max_depth = max(max_depth, current_depth)
        
        # Estimate memory (MB)
        estimated_memory = 64 + (complexity * 2)
        
        # Estimate CPU time (seconds)
        estimated_cpu = 0.1 + (complexity * 0.05)
        
        if has_loops:
            estimated_cpu += 0.5
        if has_recursion:
            estimated_cpu += 1.0
        
        return ResourceEstimate(
            estimated_memory_mb=min(estimated_memory, 512),
            estimated_cpu_seconds=min(estimated_cpu, 30.0),
            complexity_score=complexity,
            has_loops=has_loops,
            has_recursion=has_recursion,
            max_depth=max_depth,
        )

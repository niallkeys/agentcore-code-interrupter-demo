"""Main code validator orchestrator"""

from typing import Literal
from datetime import datetime

from .python_analyzer import PythonAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer
from .validation_result import ValidationResult
from ..models.errors import ValidationError


class CodeValidator:
    """
    Main validator that orchestrates code analysis for different languages
    """
    
    def __init__(self):
        """Initialize code validator with language-specific analyzers"""
        self.python_analyzer = PythonAnalyzer()
        self.javascript_analyzer = JavaScriptAnalyzer()
    
    def validate(
        self,
        code: str,
        language: Literal["python", "javascript", "typescript"],
    ) -> ValidationResult:
        """
        Validate code for security, syntax, and resource usage
        
        Args:
            code: Source code to validate
            language: Programming language of the code
            
        Returns:
            ValidationResult with complete analysis
            
        Raises:
            ValidationError: If validation cannot be performed
        """
        if not code or not code.strip():
            raise ValidationError(
                "Code cannot be empty",
                errors=["Empty code provided"],
            )
        
        # Route to appropriate analyzer
        if language == "python":
            result = self.python_analyzer.analyze(code)
        elif language in ("javascript", "typescript"):
            result = self.javascript_analyzer.analyze(code, language)
        else:
            raise ValidationError(
                f"Unsupported language: {language}",
                errors=[f"Language '{language}' is not supported"],
            )
        
        # Add validation timestamp
        result.validation_timestamp = datetime.utcnow().isoformat() + "Z"
        
        # If validation failed, raise detailed error
        if not result.is_valid:
            raise ValidationError(
                "Code validation failed",
                errors=result.errors,
                warnings=result.warnings,
                security_issues=[issue.message for issue in result.security_issues],
            )
        
        return result
    
    def validate_safe(
        self,
        code: str,
        language: Literal["python", "javascript", "typescript"],
    ) -> ValidationResult:
        """
        Validate code without raising exceptions
        
        Args:
            code: Source code to validate
            language: Programming language of the code
            
        Returns:
            ValidationResult (may have is_valid=False)
        """
        try:
            return self.validate(code, language)
        except ValidationError:
            # Return the validation result from the analyzer
            if language == "python":
                return self.python_analyzer.analyze(code)
            else:
                return self.javascript_analyzer.analyze(code, language)

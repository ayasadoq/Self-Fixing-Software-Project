import os
import ast
import coverage
import pytest
from typing import Dict, List, Any, Optional
from pathlib import Path
from google.generativeai import GenerativeModel

class TestValidator:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.model = GenerativeModel('gemini-pro')
        self.coverage = coverage.Coverage()

    def validate_tests(self, test_file: str) -> Dict[str, Any]:
        """
        Validate a test file and suggest improvements.
        """
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the test file
            tree = ast.parse(content)
            
            # Analyze test structure
            test_analysis = self._analyze_test_structure(tree)
            
            # Check test coverage
            coverage_data = self._check_test_coverage(test_file)
            
            # Generate improvement suggestions
            suggestions = self._generate_suggestions(test_analysis, coverage_data)
            
            return {
                "status": "success",
                "test_analysis": test_analysis,
                "coverage_data": coverage_data,
                "suggestions": suggestions
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error validating tests: {str(e)}"
            }

    def _analyze_test_structure(self, tree: ast.AST) -> Dict[str, Any]:
        """
        Analyze the structure of test file.
        """
        analysis = {
            "total_tests": 0,
            "test_classes": 0,
            "test_methods": 0,
            "fixtures": 0,
            "assertions": 0,
            "complexity": 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith('Test'):
                    analysis["test_classes"] += 1
            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    analysis["test_methods"] += 1
                    analysis["total_tests"] += 1
                elif node.name.startswith('fixture'):
                    analysis["fixtures"] += 1
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id.startswith('assert'):
                        analysis["assertions"] += 1
        
        # Calculate complexity
        analysis["complexity"] = self._calculate_complexity(tree)
        
        return analysis

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """
        Calculate cyclomatic complexity of the test file.
        """
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.ExceptHandler)):
                complexity += 1
        return complexity

    def _check_test_coverage(self, test_file: str) -> Dict[str, Any]:
        """
        Check test coverage for the module being tested.
        """
        try:
            # Start coverage measurement
            self.coverage.start()
            
            # Run the tests
            pytest.main([test_file])
            
            # Stop coverage measurement
            self.coverage.stop()
            self.coverage.save()
            
            # Get coverage data
            coverage_data = {
                "statements": self.coverage.report(),
                "missing_lines": self.coverage.get_missing(),
                "branch_coverage": self.coverage.report(branch=True)
            }
            
            return coverage_data
        except Exception as e:
            return {
                "error": f"Error checking coverage: {str(e)}"
            }

    def _generate_suggestions(self, analysis: Dict[str, Any], coverage: Dict[str, Any]) -> List[str]:
        """
        Generate suggestions for improving tests.
        """
        suggestions = []
        
        # Check test count
        if analysis["total_tests"] < 5:
            suggestions.append("Consider adding more test cases to improve coverage")
        
        # Check assertions
        if analysis["assertions"] < analysis["total_tests"]:
            suggestions.append("Some test methods might be missing assertions")
        
        # Check complexity
        if analysis["complexity"] > 10:
            suggestions.append("Consider breaking down complex test methods into smaller, focused tests")
        
        # Check coverage
        if coverage.get("statements", 0) < 80:
            suggestions.append("Aim for at least 80% code coverage")
        
        # Generate specific suggestions using Gemini
        prompt = f"""Based on this test analysis:
        {analysis}
        And coverage data:
        {coverage}
        Generate specific suggestions for improving the test suite.
        """
        
        try:
            response = self.model.generate_content(prompt)
            suggestions.extend(response.text.strip().split('\n'))
        except Exception as e:
            print(f"Error generating suggestions: {e}")
        
        return suggestions

    def enhance_test_coverage(self, test_file: str) -> Dict[str, Any]:
        """
        Enhance test coverage by generating additional test cases.
        """
        try:
            # Get the module being tested
            module_path = self._get_module_path(test_file)
            
            # Analyze current coverage
            coverage_data = self._check_test_coverage(test_file)
            
            # Generate new test cases
            new_tests = self._generate_test_cases(module_path, coverage_data)
            
            # Append new tests to the test file
            if new_tests:
                with open(test_file, 'a', encoding='utf-8') as f:
                    f.write('\n\n' + new_tests)
            
            return {
                "status": "success",
                "new_tests_added": bool(new_tests),
                "message": "Test coverage enhanced successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error enhancing test coverage: {str(e)}"
            }

    def _get_module_path(self, test_file: str) -> str:
        """
        Get the path of the module being tested.
        """
        # Remove 'test_' prefix and '.py' extension
        module_name = os.path.basename(test_file)[5:-3]
        return os.path.join(self.project_root, f"{module_name}.py")

    def _generate_test_cases(self, module_path: str, coverage_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate new test cases using Gemini.
        """
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                module_content = f.read()
            
            prompt = f"""Generate additional test cases for this Python module:
            {module_content}
            
            Current coverage data:
            {coverage_data}
            
            Focus on:
            1. Edge cases
            2. Error conditions
            3. Boundary values
            4. Missing scenarios
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating test cases: {e}")
            return None

# --- Tool Definition: test_validator_validate ---
def test_validator_validate(test_file: str) -> dict:
    """
    Validate a test file and suggest improvements.

    Args:
        test_file (str): Path to the test file to validate.

    Returns:
        dict: Validation results and suggestions.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    validator = TestValidator(project_root)
    
    return validator.validate_tests(test_file)

# --- Tool Definition: test_validator_enhance ---
def test_validator_enhance(test_file: str) -> dict:
    """
    Enhance test coverage by generating additional test cases.

    Args:
        test_file (str): Path to the test file to enhance.

    Returns:
        dict: Results of the enhancement process.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    validator = TestValidator(project_root)
    
    return validator.enhance_test_coverage(test_file) 
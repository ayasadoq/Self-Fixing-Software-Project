import os
import ast
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import datetime
from google.generativeai import GenerativeModel

class DocumentationGenerator:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.model = GenerativeModel('gemini-pro')

    def generate_api_docs(self, file_path: str) -> str:
        """
        Generate API documentation for a Python file using AST analysis and Gemini.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            api_docs = []

            # Process each top-level node
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    doc = self._generate_node_documentation(node, content)
                    if doc:
                        api_docs.append(doc)

            return '\n\n'.join(api_docs)
        except Exception as e:
            print(f"Error generating API docs for {file_path}: {e}")
            return ""

    def _generate_node_documentation(self, node: ast.AST, file_content: str) -> Optional[str]:
        """
        Generate documentation for a specific AST node.
        """
        try:
            # Extract context
            context = self._extract_context(node, file_content)
            
            # Generate documentation using Gemini
            prompt = f"""Generate detailed API documentation for this Python code:
            
            {context}
            
            Include:
            1. Description
            2. Parameters/Attributes
            3. Return values
            4. Examples
            5. Notes
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating node documentation: {e}")
            return None

    def _extract_context(self, node: ast.AST, file_content: str) -> str:
        """
        Extract relevant context from the file for documentation generation.
        """
        try:
            start_line = node.lineno
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
            
            lines = file_content.split('\n')
            context_lines = lines[start_line-1:end_line]
            
            return '\n'.join(context_lines)
        except Exception as e:
            print(f"Error extracting context: {e}")
            return ""

    def update_readme(self, changes: Dict[str, List[str]]) -> str:
        """
        Update README.md with project information and recent changes.
        """
        readme_path = os.path.join(self.project_root, 'README.md')
        
        # Generate README content using Gemini
        prompt = f"""Generate a comprehensive README.md for a Python project with these recent changes:
        
        {changes}
        
        Include:
        1. Project Overview
        2. Features
        3. Installation
        4. Usage
        5. Contributing
        6. License
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return content
        except Exception as e:
            print(f"Error updating README: {e}")
            return ""

    def enhance_code_comments(self, file_path: str) -> bool:
        """
        Enhance code comments using Gemini for better documentation.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the file
            tree = ast.parse(content)
            
            # Find complex code blocks that might need better documentation
            complex_blocks = self._find_complex_blocks(tree)
            
            for block in complex_blocks:
                # Generate better comments
                prompt = f"""Generate clear and concise comments for this code block:
                
                {block['code']}
                
                Focus on:
                1. Purpose
                2. Algorithm/Logic
                3. Edge cases
                4. Performance considerations
                """
                
                response = self.model.generate_content(prompt)
                new_comments = response.text.strip()
                
                # Insert new comments
                content = self._insert_comments(content, block['start_line'], new_comments)
            
            # Write back the enhanced content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error enhancing code comments: {e}")
            return False

    def _find_complex_blocks(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """
        Find complex code blocks that might need better documentation.
        """
        complex_blocks = []
        
        for node in ast.walk(tree):
            # Look for complex functions, classes, or blocks
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if self._is_complex_node(node):
                    complex_blocks.append({
                        'start_line': node.lineno,
                        'end_line': node.end_lineno,
                        'code': self._get_node_source(node)
                    })
        
        return complex_blocks

    def _is_complex_node(self, node: ast.AST) -> bool:
        """
        Determine if a node is complex enough to need better documentation.
        """
        # Count number of statements
        stmt_count = len(list(ast.walk(node)))
        
        # Check for nested structures
        has_nested = any(isinstance(child, (ast.FunctionDef, ast.ClassDef)) 
                        for child in ast.walk(node))
        
        # Check for complex control flow
        has_complex_flow = any(isinstance(child, (ast.If, ast.For, ast.While, ast.Try))
                             for child in ast.walk(node))
        
        return stmt_count > 10 or has_nested or has_complex_flow

    def _get_node_source(self, node: ast.AST) -> str:
        """
        Get the source code for a node.
        """
        try:
            return ast.unparse(node)
        except:
            return str(node)

    def _insert_comments(self, content: str, line_num: int, comments: str) -> str:
        """
        Insert comments at the specified line number.
        """
        lines = content.split('\n')
        comment_lines = comments.split('\n')
        
        # Insert comments before the line
        lines[line_num-1:line_num-1] = [f"# {line}" for line in comment_lines]
        
        return '\n'.join(lines)

    def generate_architecture_doc(self) -> str:
        """
        Generate architecture documentation for the project.
        """
        # Get project structure
        structure = self._get_project_structure()
        
        # Generate architecture doc using Gemini
        prompt = f"""Generate architecture documentation for a Python project with this structure:
        
        {structure}
        
        Include:
        1. System Overview
        2. Component Diagram
        3. Data Flow
        4. Dependencies
        5. Design Patterns
        6. Security Considerations
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            # Write to ARCHITECTURE.md
            arch_path = os.path.join(self.project_root, 'ARCHITECTURE.md')
            with open(arch_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return content
        except Exception as e:
            print(f"Error generating architecture doc: {e}")
            return ""

    def _get_project_structure(self) -> str:
        """
        Get the project structure as a string.
        """
        structure = []
        
        for root, dirs, files in os.walk(self.project_root):
            level = root.replace(self.project_root, '').count(os.sep)
            indent = ' ' * 4 * level
            structure.append(f"{indent}{os.path.basename(root)}/")
            
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                if f.endswith('.py'):
                    structure.append(f"{sub_indent}{f}")
        
        return '\n'.join(structure)

    def generate_release_notes(self, version: str, changes: Dict[str, List[str]]) -> str:
        """
        Generate release notes for a new version.
        """
        prompt = f"""Generate release notes for version {version} with these changes:
        
        {changes}
        
        Include:
        1. Version Overview
        2. New Features
        3. Bug Fixes
        4. Breaking Changes
        5. Migration Guide
        6. Contributors
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            # Write to RELEASE_NOTES.md
            notes_path = os.path.join(self.project_root, 'RELEASE_NOTES.md')
            with open(notes_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return content
        except Exception as e:
            print(f"Error generating release notes: {e}")
            return "" 
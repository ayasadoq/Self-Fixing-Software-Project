# auto_pr_creator_agent/agent.py

import os
import subprocess
import shutil # For copying files if needed, not directly used in this version but useful for file ops
import datetime
import ast
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import black
import isort
from google.adk.agents import Agent
from google.generativeai import GenerativeModel
from .github_integration import create_pull_request

# --- Helper Functions for Advanced Fixes ---

def format_with_black(file_path: str) -> bool:
    """
    Format a Python file using Black.
    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get the current Black configuration
        mode = black.Mode()
        
        # Format the content
        formatted_content = black.format_str(content, mode=mode)
        
        # Check if changes were made
        if formatted_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            return True
        return False
    except Exception as e:
        print(f"Error formatting with Black: {e}")
        return False

def sort_imports(file_path: str) -> bool:
    """
    Sort imports in a Python file using isort.
    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get the current isort configuration
        config = isort.Config()
        
        # Sort the imports
        sorted_content = isort.code(content, config=config)
        
        # Check if changes were made
        if sorted_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sorted_content)
            return True
        return False
    except Exception as e:
        print(f"Error sorting imports: {e}")
        return False

def generate_docstring(node: ast.AST, file_content: str) -> str:
    """
    Generate a docstring for a function or class using Google's Gemini model.
    """
    try:
        # Initialize Gemini model
        model = GenerativeModel('gemini-pro')
        
        # Extract context from the file
        context = extract_context(node, file_content)
        
        # Generate docstring using Gemini
        prompt = f"""Generate a Google-style docstring for this Python code:
        
        {context}
        
        The docstring should:
        1. Start with a one-line summary
        2. Include Args, Returns, and Raises sections if applicable
        3. Follow Google's docstring style guide
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating docstring: {e}")
        return ""

def extract_context(node: ast.AST, file_content: str) -> str:
    """
    Extract relevant context from the file for docstring generation.
    """
    try:
        # Get the line numbers for the node
        start_line = node.lineno
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
        
        # Get the lines from the file
        lines = file_content.split('\n')
        context_lines = lines[start_line-1:end_line]
        
        return '\n'.join(context_lines)
    except Exception as e:
        print(f"Error extracting context: {e}")
        return ""

def fix_indentation(file_path: str, line_num: int, issue_symbol: str) -> Optional[str]:
    """
    Fix indentation issues in a Python file.
    Returns the fixed line or None if no fix was applied.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not 1 <= line_num <= len(lines):
            return None
        
        line = lines[line_num - 1]
        
        # Handle different indentation issues
        if issue_symbol == "E111":  # indentation is not a multiple of four
            # Count current indentation
            indent = len(line) - len(line.lstrip())
            # Round to nearest multiple of 4
            new_indent = (indent + 2) // 4 * 4
            return ' ' * new_indent + line.lstrip()
        
        elif issue_symbol == "E114":  # indentation is not a multiple of four (comment)
            # Similar to E111 but for comment lines
            indent = len(line) - len(line.lstrip())
            new_indent = (indent + 2) // 4 * 4
            return ' ' * new_indent + line.lstrip()
        
        elif issue_symbol == "E117":  # over-indented
            # Reduce indentation by 4 spaces
            return line[4:] if line.startswith('    ') else line
        
        return None
    except Exception as e:
        print(f"Error fixing indentation: {e}")
        return None

def apply_sophisticated_fix(file_path: str, line_num: int, original_line: str, issue_symbol: str, file_content: str) -> str:
    """
    Applies sophisticated fixes to code issues using various tools and techniques.
    """
    fixed_line = original_line
    
    # Handle trailing whitespace
    if "W291" in issue_symbol or "C0303" in issue_symbol:
        fixed_line = original_line.rstrip()
    
    # Handle missing newline at end of file
    elif "W292" in issue_symbol:
        if not original_line.endswith('\n'):
            fixed_line = original_line + '\n'
    
    # Handle docstring issues
    elif any(x in issue_symbol for x in ["C0114", "C0115", "C0116"]):
        try:
            # Parse the file to get the AST
            tree = ast.parse(file_content)
            
            # Find the node at the current line
            for node in ast.walk(tree):
                if hasattr(node, 'lineno') and node.lineno == line_num:
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                        docstring = generate_docstring(node, file_content)
                        if docstring:
                            # Insert the docstring after the definition line
                            return original_line + '\n' + '    ' + '"""' + docstring + '"""\n'
        except Exception as e:
            print(f"Error handling docstring: {e}")
    
    # Handle indentation issues
    elif issue_symbol.startswith("E11"):
        fixed_indentation = fix_indentation(file_path, line_num, issue_symbol)
        if fixed_indentation:
            fixed_line = fixed_indentation
    
    return fixed_line

# --- Tool Definition: auto_pr_creator_process_issues ---

def auto_pr_creator_process_issues(issues_report: dict) -> dict:
    """
    Receives a report of issues from the Bug Hunter, applies sophisticated fixes,
    and prepares a Git commit/branch for a pull request.
    """
    if not issues_report.get("issues_found", False):
        print("Auto-PR Creator: No issues reported by Bug Hunter. No action needed.")
        return {"status": "success", "message": "No issues to fix."}

    issues = issues_report.get("issues", [])
    if not issues:
        print("Auto-PR Creator: Issues_found is True, but issues list is empty. No action needed.")
        return {"status": "success", "message": "Issues_found is True, but issues list is empty."}

    print(f"Auto-PR Creator: Received {len(issues)} issues to process.")

    target_codebase_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'target_codebase'))
    changes_made = {} # To track changes per file

    # Group issues by file
    issues_by_file = {}
    for issue in issues:
        file_name = issue.get("file")
        if file_name:
            full_file_path = os.path.join(target_codebase_path, file_name)
            if full_file_path not in issues_by_file:
                issues_by_file[full_file_path] = []
            issues_by_file[full_file_path].append(issue)

    for file_path, file_issues in issues_by_file.items():
        if not os.path.exists(file_path):
            print(f"Warning: File not found for issues: {file_path}")
            continue

        # Read the entire file content for context
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            lines = file_content.splitlines(True)

        file_changed = False
        new_lines = list(lines)

        # First, try to fix issues that require full file context
        if any(issue.get("symbol", "").startswith("C01") for issue in file_issues):
            # Format the entire file with Black
            if format_with_black(file_path):
                file_changed = True
                print(f"  Applied Black formatting to {file_path}")

            # Sort imports
            if sort_imports(file_path):
                file_changed = True
                print(f"  Sorted imports in {file_path}")

        # Then handle individual line issues
        file_issues.sort(key=lambda x: x.get('line', 0), reverse=True)
        for issue in file_issues:
            line_num = issue.get("line")
            if isinstance(line_num, int) and 1 <= line_num <= len(lines):
                original_line_index = line_num - 1
                original_line_content = new_lines[original_line_index]
                fixed_line_content = apply_sophisticated_fix(
                    file_path, line_num, original_line_content,
                    issue.get("symbol", ""), file_content
                )

                if fixed_line_content != original_line_content:
                    new_lines[original_line_index] = fixed_line_content
                    file_changed = True
                    print(f"  Applied fix in {file_path}, line {line_num} for issue {issue.get('symbol')}")
                    if file_path not in changes_made:
                        changes_made[file_path] = []
                    changes_made[file_path].append(f"Fixed {issue.get('symbol')} on line {line_num}: {issue.get('message')}")

        if file_changed:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  Changes written to {file_path}")

    if not changes_made:
        return {"status": "success", "message": "No fixable issues found or fixes were identical to original code."}

    # --- Git Operations ---
    print("Auto-PR Creator: Performing Git operations...")
    branch_name = f"auto-fix-{(datetime.datetime.now() + datetime.timedelta(hours=1)).strftime('%Y%m%d-%H%M%S')}"
    commit_message = f"feat: Automated fixes for static analysis issues\n\n"
    for file_path, file_changes in changes_made.items():
        commit_message += f"File: {os.path.basename(file_path)}\n"
        for change_desc in file_changes:
            commit_message += f"  - {change_desc}\n"
    commit_message += "\nAutomated by Auto-PR Creator Agent."

    try:
        repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        os.chdir(repo_path)

        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True, text=True)
        print(f"Auto-PR Creator: Created and switched to branch '{branch_name}'")

        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        print("Auto-PR Creator: Staged all changes.")

        subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True, text=True)
        print("Auto-PR Creator: Committed changes.")

        push_result = subprocess.run(
            ["git", "push", "origin", branch_name],
            check=False,
            capture_output=True,
            text=True
        )

        if push_result.returncode != 0:
            print(f"Auto-PR Creator: Git push failed: {push_result.stderr}")
            return {
                "status": "error",
                "message": "Git push failed. You might need to set up Git credentials or SSH keys.",
                "details": push_result.stderr,
                "branch_name": branch_name,
                "commit_message": commit_message,
                "changes_made": changes_made
            }
        else:
            print(f"Auto-PR Creator: Successfully pushed branch '{branch_name}'.")
            
            # Create pull request using GitHub API
            pr_result = create_pull_request(branch_name, changes_made, commit_message)
            
            if pr_result and pr_result["status"] == "success":
                return {
                    "status": "success",
                    "message": "Issues fixed, committed, branch pushed, and PR created.",
                    "branch_name": branch_name,
                    "commit_message": commit_message,
                    "changes_made": changes_made,
                    "pull_request": pr_result
                }
            else:
                return {
                    "status": "partial_success",
                    "message": "Issues fixed and branch pushed, but PR creation failed.",
                    "branch_name": branch_name,
                    "commit_message": commit_message,
                    "changes_made": changes_made,
                    "pull_request_error": pr_result.get("message") if pr_result else "GitHub API not configured"
                }

    except subprocess.CalledProcessError as e:
        os.chdir(os.path.dirname(__file__))
        return {"status": "error", "message": f"Git command failed: {e.cmd}, Output: {e.stderr}", "details": changes_made}
    except Exception as e:
        os.chdir(os.path.dirname(__file__))
        return {"status": "error", "message": f"An unexpected error occurred during Git operations: {e}", "details": changes_made}
    finally:
        os.chdir(os.path.dirname(__file__))



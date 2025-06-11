# auto_pr_creator_agent/agent.py

import os
import subprocess
import shutil # For copying files if needed, not directly used in this version but useful for file ops
import datetime
from google.adk.agents import Agent

# --- Helper Function for Applying Simple Fixes ---
def apply_simple_fix(file_path: str, line_num: int, original_line: str, issue_symbol: str) -> str:
    """
    Applies a simple, rule-based fix to a specific line based on the issue type.
    This is a very basic implementation. More complex fixes would require AST manipulation
    or an LLM's understanding.
    """
    fixed_line = original_line

    # Example: Fix for trailing whitespace (Flake8 W291, Pylint C0303)
    if "W291" in issue_symbol or "C0303" in issue_symbol:
        fixed_line = original_line.rstrip() # Remove trailing whitespace

    # Example: Fix for missing new line at end of file (Flake8 W292)
    # This is harder to fix line by line, typically handled by adding a new line
    # when writing the entire file, but for a single line context, we'll ignore it here.

    # Example: Fix for missing docstring (Pylint C0114, C0115, C0116) - simplistic
    # For simplicity, we won't auto-generate docstrings here. It requires deeper context.

    # Example: Fix for bad indentation (Flake8 E111, E114, E117)
    # This requires knowing the correct indentation level, which is complex.
    # We will add a placeholder for now.
    if issue_symbol.startswith("E11"): # Flake8 indentation errors
         # This is a placeholder. Real fix needs context.
         # For example, if it's an 'unexpected indentation', we might try to unindent.
         # This would need to be very carefully designed.
         pass # Will be handled by isort/black typically

    # Return the (potentially) fixed line. If no fix applied, it's the original line.
    return fixed_line


# --- Tool Definition: auto_pr_creator_process_issues ---
@tool # Use the @tool decorator for tools exposed to the LLM
def auto_pr_creator_process_issues(issues_report: dict) -> dict:
    """
    Receives a report of issues from the Bug Hunter, attempts to apply simple fixes,
    and prepares a Git commit/branch for a pull request.

    Args:
        issues_report (dict): A dictionary containing 'issues_found' (bool) and
                              'issues' (list of dicts) from the Bug Hunter agent.

    Returns:
        dict: Status of the fix attempt and Git operations, and details of changes.
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
            # Reconstruct full path for the file in target_codebase
            full_file_path = os.path.join(target_codebase_path, file_name)
            if full_file_path not in issues_by_file:
                issues_by_file[full_file_path] = []
            issues_by_file[full_file_path].append(issue)

    for file_path, file_issues in issues_by_file.items():
        if not os.path.exists(file_path):
            print(f"Warning: File not found for issues: {file_path}")
            continue

        lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines() # Keep newline characters

        file_changed = False
        new_lines = list(lines) # Create a mutable copy to modify

        # Sort issues by line number in descending order to avoid index shifting problems
        # when modifying lines (modifying higher lines first is safer)
        file_issues.sort(key=lambda x: x.get('line', 0), reverse=True)

        for issue in file_issues:
            line_num = issue.get("line")
            if isinstance(line_num, int) and 1 <= line_num <= len(lines):
                original_line_index = line_num - 1 # Convert to 0-based index
                original_line_content = new_lines[original_line_index]
                fixed_line_content = apply_simple_fix(
                    file_path, line_num, original_line_content, issue.get("symbol", "")
                )

                if fixed_line_content != original_line_content:
                    new_lines[original_line_index] = fixed_line_content
                    file_changed = True
                    print(f"  Applied fix in {file_path}, line {line_num} for issue {issue.get('symbol')}")
                    if file_path not in changes_made:
                        changes_made[file_path] = []
                    changes_made[file_path].append(f"Fixed {issue.get('symbol')} on line {line_num}: {issue.get('message')}")
                else:
                    print(f"  No fix applied for {issue.get('symbol')} on line {line_num} in {file_path} (or fix was identical).")
            else:
                print(f"  Warning: Invalid line number {line_num} for issue {issue.get('symbol')} in {file_path}")

        if file_changed:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  Changes written to {file_path}")
        else:
            print(f"  No changes needed for {file_path} based on simple fixes.")


    if not changes_made:
        return {"status": "success", "message": "No fixable issues found or fixes were identical to original code."}

    # --- Git Operations Simulation (for now) ---
    # In a real scenario, you'd use GitPython or subprocess to run Git commands.
    # For this step, we'll just indicate what would happen.

    print("Auto-PR Creator: Simulating Git operations...")
    branch_name = f"auto-fix-{(datetime.datetime.now() + datetime.timedelta(hours=1)).strftime('%Y%m%d-%H%M%S')}" # Add 1 hour for local time
    commit_message = f"feat: Automated fixes for static analysis issues\n\n"
    for file_path, file_changes in changes_made.items():
        commit_message += f"File: {os.path.basename(file_path)}\n"
        for change_desc in file_changes:
            commit_message += f"  - {change_desc}\n"
    commit_message += "\nAutomated by Auto-PR Creator Agent."


    # Placeholder for actual Git commands (to be implemented later with GitPython)
    try:
        repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Your_project_root
        os.chdir(repo_path) # Change current directory to repo root for git commands

        # git checkout -b <branch_name>
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True, text=True)
        print(f"Auto-PR Creator: Created and switched to branch '{branch_name}'")

        # git add . (add all changed files)
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        print("Auto-PR Creator: Staged all changes.")

        # git commit -m "..."
        subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True, text=True)
        print("Auto-PR Creator: Committed changes.")

        # git push origin <branch_name> (Will require authentication)
        # This part will fail if you don't have credential helper set up or SSH keys.
        # We'll handle authentication challenges later.
        print(f"Auto-PR Creator: Attempting to push branch '{branch_name}' to origin. (May require authentication)")
        push_result = subprocess.run(
            ["git", "push", "origin", branch_name],
            check=False, # Don't raise error on failed push due to auth
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
            return {
                "status": "success",
                "message": "Issues fixed, committed, and branch pushed.",
                "branch_name": branch_name,
                "commit_message": commit_message,
                "changes_made": changes_made,
                "pull_request_suggestion": f"Please create a Pull Request from '{branch_name}' on GitHub."
            }

    except subprocess.CalledProcessError as e:
        os.chdir(os.path.dirname(__file__)) # Change back to agent's directory
        return {"status": "error", "message": f"Git command failed: {e.cmd}, Output: {e.stderr}", "details": changes_made}
    except Exception as e:
        os.chdir(os.path.dirname(__file__)) # Change back to agent's directory
        return {"status": "error", "message": f"An unexpected error occurred during Git operations: {e}", "details": changes_made}
    finally:
        # Always change back to the original directory of the agent
        # This is important for ADK to find other modules if needed
        os.chdir(os.path.dirname(__file__))


# --- Agent Definition ---
# This defines your Auto-PR Creator agent within the ADK framework.
root_agent = Agent(
    name="Auto_PR_Creator_Agent", # Unique name for your agent
    model="gemini-2.0-flash",
    description=(
        "An AI agent that receives bug reports, attempts to apply simple code fixes, "
        "and automates the Git workflow (branching, committing, pushing) for creating pull requests."
    ),
    instruction=(
        "You are an Auto-PR Creator. Your role is to take a structured list of issues, "
        "apply automated fixes, and then manage the Git repository to create a new branch, "
        "commit the changes, and push them. "
        "When given a report of issues, always call the 'auto_pr_creator_process_issues' tool."
    ),
    tools=[auto_pr_creator_process_issues], # Register the tool function
)
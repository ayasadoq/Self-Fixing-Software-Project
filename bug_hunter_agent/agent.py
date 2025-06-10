# bug_hunter_agent/agent.py

import os
import subprocess
import json
from google.adk.agents import Agent
# NO LONGER NEEDED: from google.adk.agents import tool # REMOVE THIS LINE

# --- Tool Definition: bug_hunter_scan_code ---
# The @tool decorator is REMOVED from here.
def bug_hunter_scan_code() -> dict: # This line stays the same, just the decorator above it is removed
    """
    Scans the 'target_codebase' directory for code quality issues and potential bugs
    using pylint and flake8.

    Returns:
        dict: A dictionary containing the status of the scan, whether issues were found,
              and a list of identified issues if any.
    """
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'target_codebase'))

    if not os.path.isdir(target_dir):
        return {
            "status": "error",
            "message": f"Target codebase directory not found: {target_dir}. Please ensure it exists."
        }

    all_issues = []
    print(f"Bug Hunter: Starting scan of '{target_dir}'...")

    # --- Run Pylint ---
    try:
        pylint_command = ["pylint", "-r", "n", "--output-format=json", target_dir]
        pylint_result = subprocess.run(
            pylint_command,
            capture_output=True,
            text=True,
            check=False
        )

        if pylint_result.stdout:
            try:
                pylint_issues = json.loads(pylint_result.stdout)
                for issue in pylint_issues:
                    all_issues.append({
                        "tool": "pylint",
                        "file": os.path.basename(issue.get('path', 'unknown')),
                        "line": issue.get('line', 'N/A'),
                        "column": issue.get('column', 'N/A'),
                        "type": issue.get('type', 'N/A'),
                        "symbol": issue.get('symbol', 'N/A'),
                        "message": issue.get('message', 'No message provided.'),
                        "confidence": issue.get('confidence', 'N/A')
                    })
            except json.JSONDecodeError:
                print("Bug Hunter: Pylint did not produce valid JSON output.")
        if pylint_result.stderr:
            print(f"Bug Hunter: Pylint stderr: {pylint_result.stderr}")

    except FileNotFoundError:
        return {
            "status": "error",
            "message": "Pylint not found. Ensure it's installed in your virtual environment."
        }
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred while running Pylint: {e}"}

    # --- Run Flake8 ---
    try:
        flake8_command = ["flake8", target_dir]
        flake8_result = subprocess.run(
            flake8_command,
            capture_output=True,
            text=True,
            check=False
        )

        if flake8_result.stdout:
            for line in flake8_result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        file_path = os.path.basename(parts[0].strip())
                        try:
                            line_num = int(parts[1].strip())
                            col_num = int(parts[2].strip())
                        except ValueError:
                            line_num, col_num = 'N/A', 'N/A'

                        code_and_message = ":".join(parts[3:]).strip()
                        issue_code_match = code_and_message.split(' ')[0]
                        message_text = " ".join(code_and_message.split(' ')[1:])

                        all_issues.append({
                            "tool": "flake8",
                            "file": file_path,
                            "line": line_num,
                            "column": col_num,
                            "type": issue_code_match[0] if issue_code_match else 'N/A',
                            "symbol": issue_code_match if issue_code_match else 'N/A',
                            "message": message_text
                        })
        if flake8_result.stderr:
            print(f"Bug Hunter: Flake8 stderr: {flake8_result.stderr}")

    except FileNotFoundError:
        return {
            "status": "error",
            "message": "Flake8 not found. Ensure it's installed in your virtual environment."
        }
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred while running Flake8: {e}"}

    # --- Final Report ---
    if all_issues:
        print(f"Bug Hunter: Scan complete. Found {len(all_issues)} issues.")
        return {"status": "success", "issues_found": True, "issues": all_issues}
    else:
        print("Bug Hunter: Scan complete. No issues found.")
        return {"status": "success", "issues_found": False, "issues": []}

# --- Agent Definition ---
root_agent = Agent(
    name="Bug_Hunter_Agent",
    model="gemini-2.0-flash",
    description=(
        "An AI agent specialized in scanning Python code for quality issues, "
        "potential bugs, and style violations using static analysis tools like Pylint and Flake8."
    ),
    instruction=(
        "You are a dedicated Bug Hunter. Your primary task is to receive a request "
        "to scan a codebase and use your 'bug_hunter_scan_code' tool. "
        "Report all findings clearly, indicating if issues were found or if the code is clean."
    ),
    tools=[bug_hunter_scan_code], # This line remains unchanged; the function itself is the tool.
)
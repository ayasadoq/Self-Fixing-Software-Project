# docs_updater_agent/agent.py

import os
import subprocess
import datetime
from typing import Dict, List, Any
from google.adk.agents import Agent
from .doc_generator import DocumentationGenerator

# --- Tool Definition: docs_updater_update_changelog ---
def docs_updater_update_changelog(last_n_commits: int = 5) -> dict:
    """
    Retrieves the last N Git commit messages from the project's root,
    extracts relevant changes, and updates documentation files.

    Args:
        last_n_commits (int): The number of recent commits to analyze.

    Returns:
        dict: Status of the documentation updates and any issues encountered.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    doc_generator = DocumentationGenerator(project_root)

    print(f"Docs Updater: Updating documentation from repository '{project_root}'...")

    try:
        # Change directory to the repository root to run git commands
        original_dir = os.getcwd()
        os.chdir(project_root)

        # Get the last N commit logs
        git_log_command = ["git", "log", f"-n{last_n_commits}", "--pretty=format:%h|%an|%ad|%s", "--date=short", "--no-merges"]
        git_log_result = subprocess.run(
            git_log_command,
            capture_output=True,
            text=True,
            check=True
        )
        commit_lines = git_log_result.stdout.strip().split('\n')

        # Process commits and categorize changes
        changes = {
            "features": [],
            "fixes": [],
            "docs": [],
            "other": []
        }

        for line in commit_lines:
            if not line:
                continue
            parts = line.split('|', 3)
            if len(parts) == 4:
                commit_hash, author, date, subject = parts
                if subject.lower().startswith("feat:"):
                    changes["features"].append(f"- {subject[5:].strip()} (_{author}, {date}_)")
                elif subject.lower().startswith("fix:"):
                    changes["fixes"].append(f"- {subject[4:].strip()} (_{author}, {date}_)")
                elif subject.lower().startswith("docs:"):
                    changes["docs"].append(f"- {subject[5:].strip()} (_{author}, {date}_)")
                else:
                    changes["other"].append(f"- {subject.strip()} (_{author}, {date}_)")

        # Update various documentation files
        results = {}

        # 1. Update CHANGELOG.md
        changelog_path = os.path.join(project_root, 'CHANGELOG.md')
        today_date = datetime.date.today().strftime('%Y-%m-%d')
        
        changelog_content = f"## {today_date}\n\n"
        for category, entries in changes.items():
            if entries:
                changelog_content += f"### {category.title()}\n"
                changelog_content += '\n'.join(entries) + '\n\n'

        with open(changelog_path, 'a', encoding='utf-8') as f:
            f.write(changelog_content)
        results['changelog'] = changelog_path

        # 2. Update README.md
        readme_content = doc_generator.update_readme(changes)
        results['readme'] = 'README.md'

        # 3. Generate API Documentation
        api_docs_dir = os.path.join(project_root, 'docs', 'api')
        os.makedirs(api_docs_dir, exist_ok=True)

        # Find all Python files in the project
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, project_root)
                    api_doc = doc_generator.generate_api_docs(file_path)
                    
                    if api_doc:
                        doc_path = os.path.join(api_docs_dir, f"{rel_path}.md")
                        os.makedirs(os.path.dirname(doc_path), exist_ok=True)
                        with open(doc_path, 'w', encoding='utf-8') as f:
                            f.write(api_doc)
                        results[f'api_doc_{rel_path}'] = doc_path

        # 4. Enhance Code Comments
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if doc_generator.enhance_code_comments(file_path):
                        results[f'enhanced_comments_{file}'] = file_path

        # 5. Generate Architecture Documentation
        arch_doc = doc_generator.generate_architecture_doc()
        if arch_doc:
            results['architecture'] = 'ARCHITECTURE.md'

        # 6. Generate Release Notes
        version = datetime.date.today().strftime('%Y.%m.%d')
        release_notes = doc_generator.generate_release_notes(version, changes)
        if release_notes:
            results['release_notes'] = 'RELEASE_NOTES.md'

        print(f"Docs Updater: Documentation updated successfully.")
        return {
            "status": "success",
            "message": "Documentation updated successfully",
            "updated_files": results
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "message": "Git not found. Ensure Git is installed and in your PATH."
        }
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Git command failed: {e.cmd}, Output: {e.stderr}", "details": e.stdout}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred during documentation update: {e}"}
    finally:
        os.chdir(original_dir)



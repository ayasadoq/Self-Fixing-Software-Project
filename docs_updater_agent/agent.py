# docs_updater_agent/agent.py

import os
import subprocess
import datetime
from google.adk.agents import tool

# --- Tool Definition: docs_updater_update_changelog ---
@tool # Use the @tool decorator for tools exposed to the LLM
def docs_updater_update_changelog(last_n_commits: int = 5) -> dict:
    """
    Retrieves the last N Git commit messages from the project's root,
    extracts relevant changes, and updates a CHANGELOG.md file.

    Args:
        last_n_commits (int): The number of recent commits to analyze.

    Returns:
        dict: Status of the changelog update and any issues encountered.
    """
    changelog_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CHANGELOG.md'))
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Your_project_root

    print(f"Docs Updater: Updating changelog at '{changelog_path}' from repository '{repo_path}'...")

    try:
        # Change directory to the repository root to run git commands
        original_dir = os.getcwd()
        os.chdir(repo_path)

        # Get the last N commit logs (formatted as short hash, author, date, subject)
        # --no-merges to avoid merge commits which often just duplicate messages
        git_log_command = ["git", "log", f"-n{last_n_commits}", "--pretty=format:%h|%an|%ad|%s", "--date=short", "--no-merges"]
        git_log_result = subprocess.run(
            git_log_command,
            capture_output=True,
            text=True,
            check=True # Raise an error if git command fails
        )
        commit_lines = git_log_result.stdout.strip().split('\n')

        changelog_entries = []
        for line in commit_lines:
            if not line:
                continue
            parts = line.split('|', 3) # Split into hash, author, date, subject
            if len(parts) == 4:
                commit_hash, author, date, subject = parts
                # Simple parsing for conventional commits or general changes
                if subject.lower().startswith("feat:"):
                    entry_type = "Features"
                    message = subject[5:].strip()
                elif subject.lower().startswith("fix:"):
                    entry_type = "Bug Fixes"
                    message = subject[4:].strip()
                elif subject.lower().startswith("docs:"):
                    entry_type = "Documentation"
                    message = subject[5:].strip()
                else:
                    entry_type = "Other Changes"
                    message = subject.strip()

                changelog_entries.append(f"- {message} (_{author}, {date}_)")
            else:
                print(f"Docs Updater: Warning - Could not parse commit line: {line}")


        # Read existing changelog content if it exists
        existing_content = ""
        if os.path.exists(changelog_path):
            with open(changelog_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

        new_changelog_content = ""
        if not existing_content.strip().startswith("# Changelog"):
            new_changelog_content += "# Changelog\n\n"

        # Add a new section for today's updates (or append to latest if date matches)
        today_date = datetime.date.today().strftime('%Y-%m-%d')
        # Check if a section for today already exists in the existing content
        if f"## {today_date}" not in existing_content:
            new_changelog_content += f"## {today_date}\n"
            for entry in changelog_entries:
                new_changelog_content += f"{entry}\n"
            new_changelog_content += "\n" # Add a newline after the new section
        else:
            # If section exists, try to append to it. This is simplistic.
            # A robust solution would parse markdown and insert.
            # For now, we'll overwrite the section for simplicity or prepend to the file.
            print("Docs Updater: Note - Changelog section for today already exists. Appending to top.")
            # Simple prepend for demonstration. For real world, merge content.
            new_changelog_content += f"## {today_date}\n"
            for entry in changelog_entries:
                new_changelog_content += f"{entry}\n"
            new_changelog_content += "\n" + existing_content # Prepend new content


        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(new_changelog_content)

        print(f"Docs Updater: CHANGELOG.md updated successfully with {len(changelog_entries)} entries.")
        return {
            "status": "success",
            "message": f"CHANGELOG.md updated successfully with {len(changelog_entries)} entries.",
            "updated_file": "CHANGELOG.md",
            "entries_added": changelog_entries
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "message": "Git not found. Ensure Git is installed and in your PATH."
        }
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Git command failed: {e.cmd}, Output: {e.stderr}", "details": e.stdout}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred during changelog update: {e}"}
    finally:
        # Change back to the original directory of the agent
        os.chdir(original_dir)



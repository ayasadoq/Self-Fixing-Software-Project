# orchestrator_agent/agent.py

from google.adk.agents import Agent
# Import the specific tool functions from your other agent modules
from bug_hunter_agent.agent import bug_hunter_scan_code
from auto_pr_creator_agent.agent import auto_pr_creator_process_issues
from docs_updater_agent.agent import docs_updater_update_changelog

# --- Orchestrator Agent Definition ---
# This is the single root agent that will coordinate everything.
root_agent = Agent(
    name="Self_Fixing_Project_Orchestrator", # The main name you'll see in the Dev UI
    model="gemini-2.0-flash",
    description=(
        "The central orchestrator for an autonomous self-fixing software project. "
        "It coordinates the Bug Hunter, Auto-PR Creator, and Docs Updater agents "
        "to automatically detect, fix, and document code issues."
    ),
    instruction=(
        "You are the master orchestrator for the Self-Fixing Software Project. "
        "Your primary goal is to ensure the codebase is clean, well-maintained, and documented. "
        "Follow these steps, using the appropriate tools: "
        "1. **Always start by using the 'bug_hunter_scan_code' tool to identify any issues in the 'target_codebase'.**\n"
        "2. If issues are found, immediately call the 'auto_pr_creator_process_issues' tool, "
        "passing the list of 'issues' received from the bug hunter's scan.\n"
        "3. After the 'auto_pr_creator_process_issues' tool has successfully created and pushed a branch, "
        "call the 'docs_updater_update_changelog' tool to update the project's documentation. "
        "4. Report the overall status of the operation: whether issues were found, fixed, and documented."
    ),
    # All relevant tools are listed here for the Orchestrator to use
    tools=[
        bug_hunter_scan_code,
        auto_pr_creator_process_issues,
        docs_updater_update_changelog
    ],
)